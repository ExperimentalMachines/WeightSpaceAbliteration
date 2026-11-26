"""Local, code-only snapshots; no deployment, image identity, or review certification.

Git snapshots read blobs, never the index or working copy. Development snapshots
are explicitly marked and capture only the same allowlist. Publication uses an
exclusive directory claim and writes the manifest last: interrupted publications
remain occupied and are never repaired in place. Filesystem checks reject links
and Windows reparse points; they do not provide isolation from a hostile process
concurrently replacing filesystem ancestors.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath


class ReleaseError(RuntimeError):
    """An unsafe, incomplete, changed, or occupied release must not be used."""


MANIFEST_NAME = "release-manifest.json"
SCHEMA_VERSION = 1
PAYLOAD_SCOPE = "local-runtime-code-v1"
# Deliberately not a recursive repository copy or an extensible glob. New runtime
# modules require an explicit scope review. No runs, private notes, data, or models.
RUNTIME_FILES = (
    "harness/artifact_guard.py",
    "harness/artifact_sync.py",
    "harness/execution.py",
    "harness/gates.py",
    "harness/host.py",
    "harness/judge_fix.py",
    "harness/preflight.py",
    "harness/protocol_rules.py",
    "harness/releases.py",
    "harness/verification/__init__.py",
    "harness/verification/accounting.py",
    "harness/methods/abliteration.py",
    "harness/methods/base.py",
    "scripts/build_release.py",
    "scripts/record_host.py",
    "scripts/verify_execution.py",
    "modal_runner.py",
    "pyproject.toml",
    "uv.lock",
)
# These packages currently use implicit namespaces. If a revision supplies a
# package initializer it affects imports and therefore must also be bound.
OPTIONAL_PACKAGE_FILES = (
    "harness/__init__.py",
    "harness/methods/__init__.py",
    "scripts/__init__.py",
)
_ALLOWED = frozenset((*RUNTIME_FILES, *OPTIONAL_PACKAGE_FILES))
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def _canonical(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _directory(path: Path, *, create: bool = False) -> Path:
    path = Path(path)
    if ".." in path.parts:
        raise ReleaseError("unsafe directory path: parent traversal")
    path = path.absolute()
    for parent in (*reversed(path.parents), path):
        info = _lstat(parent)
        if info is None and create:
            try:
                parent.mkdir()
            except FileExistsError:
                pass
            info = _lstat(parent)
        if info is None or _is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise ReleaseError(f"required directory is missing or unsafe: {parent.name}")
    return path


def _relative(relative: str) -> PurePosixPath:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ReleaseError("unsafe release file path")
    part = PurePosixPath(relative)
    if part.is_absolute() or part.as_posix() != relative or any(p in (".", "..") for p in part.parts):
        raise ReleaseError(f"unsafe release file path: {relative!r}")
    return part


def _read_file(root: Path, relative: str) -> bytes:
    part = _relative(relative)
    path = root.joinpath(*part.parts)
    _directory(path.parent)
    info = _lstat(path)
    if info is None or _is_link(info) or not stat.S_ISREG(info.st_mode):
        raise ReleaseError(f"required file is missing or unsafe: {relative}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        with os.fdopen(os.open(path, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or (info.st_dev, info.st_ino) != (opened.st_dev, opened.st_ino):
                raise ReleaseError(f"file changed while opening: {relative}")
            return stream.read()
    except OSError as exc:
        raise ReleaseError(f"cannot read release file: {relative}") from exc


def _git(root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, check=False,
        )
    except OSError as exc:
        raise ReleaseError("Git is required to resolve source revisions") from exc
    if result.returncode:
        # Git diagnostics can contain local account paths; do not put them in a
        # public manifest or forward them as provenance metadata.
        raise ReleaseError(f"Git source query failed: {args[0]}")
    return result.stdout


def _revision(root: Path, revision: str) -> str:
    if not isinstance(revision, str) or not revision:
        raise ReleaseError("source revision must be explicit and nonempty")
    if _git(root, "rev-parse", "--show-prefix").strip():
        raise ReleaseError("repo_root must be the Git repository root")
    resolved = _git(root, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}").decode("ascii").strip()
    if not _COMMIT.fullmatch(resolved):
        raise ReleaseError("Git did not resolve a commit identity")
    return resolved


def _git_payload(root: Path, revision: str) -> dict[str, bytes]:
    entries = _git(root, "ls-tree", "-r", "-z", "--full-tree", revision, "--", *sorted(_ALLOWED))
    objects = {}
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, kind, oid = metadata.split(b" ")
        relative = name.decode("utf-8")
        if relative not in _ALLOWED or mode not in (b"100644", b"100755") or kind != b"blob":
            raise ReleaseError(f"unsafe Git runtime file: {relative}")
        objects[relative] = oid.decode("ascii")
    missing = set(RUNTIME_FILES) - objects.keys()
    if missing:
        raise ReleaseError(f"revision lacks required runtime files: {', '.join(sorted(missing))}")
    return {relative: _git(root, "cat-file", "blob", oid) for relative, oid in sorted(objects.items())}


def _working_payload(root: Path) -> dict[str, bytes]:
    payload = {relative: _read_file(root, relative) for relative in RUNTIME_FILES}
    for relative in OPTIONAL_PACKAGE_FILES:
        if _lstat(root / relative) is not None:
            payload[relative] = _read_file(root, relative)
    return payload


def _manifest(payload: dict[str, bytes], revision: str, working_tree: bool) -> dict:
    body = {
        "schema_version": SCHEMA_VERSION,
        "payload_scope": PAYLOAD_SCOPE,
        "source": {
            "kind": "development-working-tree" if working_tree else "git-revision",
            "revision": revision,
            "development": working_tree,
        },
        "files": {relative: _sha256(data) for relative, data in sorted(payload.items())},
    }
    # The manifest is the root of this graph, not one of its own file entries.
    return {**body, "release_id": _sha256(_canonical(body))}


def build_release(
    repo_root: Path, output_root: Path, *, revision: str = "HEAD", working_tree: bool = False,
) -> Path:
    """Publish captured bytes once; reuse an identical existing release only if valid.

    A Git snapshot does not certify human review. Its resolved revision identifies
    the selected source, regardless of unrelated working-tree/index changes. The
    development mode records the selected Git reference, not a claim that its
    working bytes equal or descend from that commit.
    """
    if type(working_tree) is not bool:
        raise ReleaseError("working_tree must be an explicit boolean")
    root = _directory(repo_root)
    destination = Path(output_root).absolute().resolve()
    if any(destination.is_relative_to((root / name).resolve()) for name in ("runs", ".gdkit", ".git")):
        raise ReleaseError("release output must not be inside protected runs, preregistration, or Git metadata")
    commit = _revision(root, revision)
    payload = _working_payload(root) if working_tree else _git_payload(root, commit)
    manifest = _manifest(payload, commit, working_tree)
    output = _directory(output_root, create=True)
    release = output / manifest["release_id"]
    try:
        release.mkdir()
    except FileExistsError:
        existing = verify_release(release)
        if existing != manifest:
            raise ReleaseError("release identity is occupied by different content")
        return release
    for relative, data in sorted(payload.items()):
        path = release.joinpath(*_relative(relative).parts)
        _directory(path.parent, create=True)
        with path.open("xb") as stream:
            stream.write(data)
    with (release / MANIFEST_NAME).open("xb") as stream:
        stream.write(_canonical(manifest))
    return release


def _validate_manifest(manifest: object, raw: bytes) -> dict:
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version", "payload_scope", "source", "files", "release_id",
    }:
        raise ReleaseError("invalid release manifest fields")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != SCHEMA_VERSION:
        raise ReleaseError("unsupported release manifest schema")
    if manifest["payload_scope"] != PAYLOAD_SCOPE:
        raise ReleaseError("unsupported runtime payload scope")
    source = manifest["source"]
    if not isinstance(source, dict) or set(source) != {"kind", "revision", "development"}:
        raise ReleaseError("invalid source identity")
    if type(source["development"]) is not bool or source["kind"] != (
        "development-working-tree" if source["development"] else "git-revision"
    ):
        raise ReleaseError("inconsistent development source identity")
    if not isinstance(source["revision"], str) or not _COMMIT.fullmatch(source["revision"]):
        raise ReleaseError("invalid source revision")
    files = manifest["files"]
    if not isinstance(files, dict) or not set(RUNTIME_FILES).issubset(files):
        raise ReleaseError("manifest lacks required runtime files")
    for relative, digest in files.items():
        _relative(relative)
        if relative not in _ALLOWED:
            raise ReleaseError(f"file outside runtime allowlist: {relative}")
        if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            raise ReleaseError(f"invalid file digest: {relative}")
    identity = manifest["release_id"]
    body = {key: value for key, value in manifest.items() if key != "release_id"}
    if not isinstance(identity, str) or not _DIGEST.fullmatch(identity) or identity != _sha256(_canonical(body)):
        raise ReleaseError("release manifest identity mismatch")
    if raw != _canonical(manifest):
        raise ReleaseError("release manifest must use canonical exact bytes")
    return manifest


def _check_inventory(root: Path, files: set[str]) -> None:
    directories = {
        parent.as_posix() for relative in files for parent in PurePosixPath(relative).parents
        if parent.as_posix() != "."
    }
    pending = [root]
    found = set()
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(root).as_posix()
                info = entry.stat(follow_symlinks=False)
                if _is_link(info):
                    raise ReleaseError(f"unsafe release entry: {relative}")
                if stat.S_ISDIR(info.st_mode) and relative in directories:
                    pending.append(path)
                elif stat.S_ISREG(info.st_mode) and relative in files:
                    found.add(relative)
                else:
                    raise ReleaseError(f"unexpected release entry: {relative}")
    missing = files - found
    if missing:
        raise ReleaseError(f"release lacks required files: {', '.join(sorted(missing))}")


def verify_release(release_dir: Path) -> dict:
    """Verify canonical manifest identity, exact payload, safe paths, and no extras."""
    root = _directory(release_dir)
    raw = _read_file(root, MANIFEST_NAME)
    try:
        parsed = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ReleaseError("invalid release manifest JSON") from exc
    manifest = _validate_manifest(parsed, raw)
    if root.name != manifest["release_id"]:
        raise ReleaseError("release directory name does not match manifest identity")
    _check_inventory(root, set(manifest["files"]) | {MANIFEST_NAME})
    for relative, digest in manifest["files"].items():
        if _sha256(_read_file(root, relative)) != digest:
            raise ReleaseError(f"release file hash mismatch: {relative}")
    return manifest


def verify_source(release_dir: Path, source_root: Path) -> dict:
    """Bind the actual selected source bytes, without demanding an unrelated clean tree.

    This is a disk-source check, not proof against in-memory monkeypatches or a
    substitute for execution's registered-callable checks. Git filters/line ending
    conversions are not normalized: actual runtime bytes must match exactly.
    """
    manifest = verify_release(release_dir)
    root = _directory(source_root)
    for relative, digest in manifest["files"].items():
        if _sha256(_read_file(root, relative)) != digest:
            raise ReleaseError(f"source file hash mismatch: {relative}")
    for relative in OPTIONAL_PACKAGE_FILES:
        if relative not in manifest["files"] and _lstat(root / relative) is not None:
            raise ReleaseError(f"source has unbound package initializer: {relative}")
    return manifest
