"""Modal-independent, non-destructive run artifact transfers.

The volume adapter supplies listdir(path, recursive=True), read_file(path), and
batch_upload(force=False).put_file(BytesIO, path). Locks coordinate callers on
one local filesystem only: they are not distributed locks or remote ledger CAS.
"""

from __future__ import annotations

import fnmatch
import io
import json
import os
import stat
import tempfile
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


@dataclass
class TransferSummary:
    created: list[str] = field(default_factory=list)
    identical: list[str] = field(default_factory=list)
    appended: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    quarantine: str | None = None


class ArtifactTransferError(RuntimeError):
    """A refused or failed transfer; summary includes partial progress and quarantine."""

    def __init__(self, summary: TransferSummary):
        self.summary = summary
        details = summary.conflicts + summary.failures
        message = "; ".join(details) or "artifact transfer failed"
        if summary.quarantine:
            message += f"; preserved incoming bytes in {summary.quarantine}"
        super().__init__(message)


@dataclass
class _Incoming:
    path: str
    data: bytes
    existing: bytes | None = None
    action: str = "new"


@dataclass
class _Evidence:
    path: str
    incoming: bytes | None
    existing: bytes | None
    reason: str


class _ReadFailure(RuntimeError):
    def __init__(self, partial: bytes, cause: Exception):
        self.partial = partial
        super().__init__(f"remote read failed ({cause}); received {len(partial)} bytes, possibly incomplete")


def _normalize_remote(path: str) -> str:
    if not isinstance(path, str) or not path or "\\" in path or ":" in path or "\x00" in path:
        raise ValueError("invalid remote path")
    # Modal returns both /runs/... and runs/...; only this single root slash is an alias.
    relative = path[1:] if path.startswith("/") else path
    parts = relative.split("/")
    if any(part in {"", ".", ".."} or part.rstrip(" .") != part for part in parts):
        raise ValueError("empty, traversal, or ambiguous path segment")
    if parts[0] != "runs":
        raise ValueError("remote artifact is outside runs")
    # Avoid Windows device aliases even when running this code on POSIX.
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
    }
    if any(part.split(".", 1)[0].upper() in reserved for part in parts):
        raise ValueError("reserved device path")
    return relative


def _entry_kind(entry: Any) -> str:
    value = getattr(entry, "type", None)
    name = getattr(value, "name", value)
    if isinstance(name, str):
        name = name.upper().rsplit(".", 1)[-1]
        if name in {"FILE", "REGULAR_FILE"}:
            return "file"
        if name in {"DIRECTORY", "DIR"}:
            return "directory"
        if name in {"SYMLINK", "LINK"}:
            return "symlink"
    if value == 1:
        return "file"
    if value == 2:
        return "directory"
    if value == 3:
        return "symlink"
    is_dir = getattr(entry, "is_dir", None)
    if callable(is_dir):
        is_dir = is_dir()
    if isinstance(is_dir, bool):
        return "directory" if is_dir else "file"
    return "unknown"


def _is_run_ledger(relative: str) -> bool:
    return relative.count("/") == 2 and relative.endswith("/ledger.jsonl")


def _read_remote(volume: Any, path: str) -> bytes:
    chunks = bytearray()
    try:
        for chunk in volume.read_file(path):
            chunks.extend(chunk)
    except Exception as exc:
        raise _ReadFailure(bytes(chunks), exc) from exc
    return bytes(chunks)


def _is_link(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _checked_target(root: Path, relative: str, *, mkdir: bool = False, directory: bool = False) -> Path:
    path = root
    parts = relative.split("/")
    if len(parts) < (1 if directory else 3):
        raise ValueError("artifact must belong to a named run")
    for part in (parts if directory else parts[:-1]):
        path = path / part
        if _is_link(path):
            raise ValueError("symlink or junction parent is not a transfer destination")
        if mkdir:
            try:
                path.mkdir()
            except FileExistsError:
                pass
        if path.exists() and not path.is_dir():
            raise ValueError("parent is not a directory")
        if not path.resolve().is_relative_to(root):
            raise ValueError("parent escapes repository")
    if directory:
        return path
    target = path / parts[-1]
    if _is_link(target):
        raise ValueError("symlink destination (including a broken link)")
    return target


def _existing_bytes(root: Path, relative: str) -> bytes | None:
    target = _checked_target(root, relative)
    try:
        metadata = target.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("destination exists and is not a regular file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(target, flags)
    with os.fdopen(fd, "rb") as handle:
        if not os.path.samestat(metadata, os.fstat(handle.fileno())):
            raise ValueError("destination changed while opening it")
        return handle.read()


def _verify_ledger(data: bytes, relative: str) -> None:
    from gdkit.ledger import verify

    if not data or not data.endswith(b"\n"):
        raise ValueError("ledger must be nonempty and end with a complete newline-terminated entry")
    with tempfile.TemporaryDirectory(prefix="artifact-ledger-verify-") as directory:
        path = Path(directory) / "ledger.jsonl"
        path.write_bytes(data)
        if verify(path) == 0:
            raise ValueError("ledger has no entries")
    run_id = relative.split("/")[1]
    for line in data.decode("utf-8").splitlines():
        if line.strip() and json.loads(line).get("run_id") != run_id:
            raise ValueError(f"ledger entry run_id does not match {run_id}")


def _classify(root: Path, incoming: _Incoming) -> None:
    incoming.existing = _existing_bytes(root, incoming.path)
    is_ledger = _is_run_ledger(incoming.path)
    if is_ledger:
        _verify_ledger(incoming.data, incoming.path)
        if incoming.existing is not None:
            _verify_ledger(incoming.existing, incoming.path)
    if incoming.existing is None:
        incoming.action = "new"
    elif incoming.existing == incoming.data:
        incoming.action = "identical"
    elif is_ledger and incoming.data.startswith(incoming.existing):
        incoming.action = "append"
    else:
        raise ValueError("existing artifact differs; ledger updates must be verified byte-prefix extensions")


@contextmanager
def _transfer_lock(root: Path) -> Iterator[None]:
    path = root.parent / f".{root.name}-artifact-transfer.lock"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise RuntimeError("another guarded transfer holds the local transfer lock; inspect stale locks manually") from exc
    identity = os.fstat(fd)
    try:
        yield
    finally:
        os.close(fd)
        try:
            if os.path.samestat(identity, path.lstat()):
                path.unlink()
        except FileNotFoundError:
            pass


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        count = os.write(fd, view)
        if count <= 0:
            raise OSError("write made no progress")
        view = view[count:]


def _quarantine(root: Path, summary: TransferSummary, evidence: list[_Evidence]) -> None:
    if not evidence:
        return
    directory = Path(tempfile.mkdtemp(prefix=f".{root.name}-artifact-quarantine-", dir=root.parent))
    directory.chmod(0o700)
    summary.quarantine = "../" + directory.name
    index = []
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    for number, item in enumerate(evidence):
        record = {"path": item.path, "reason": item.reason}
        for label, data in (("incoming", item.incoming), ("existing", item.existing)):
            if data is None:
                continue
            name = f"{number:04d}-{label}.bin"
            fd = os.open(directory / name, flags, 0o600)
            try:
                _write_all(fd, data)
                os.fsync(fd)
            finally:
                os.close(fd)
            record[label] = name
        index.append(record)
    fd = os.open(directory / "index.json", flags, 0o600)
    try:
        _write_all(fd, (json.dumps(index, indent=2, ensure_ascii=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def _refuse(root: Path, summary: TransferSummary, evidence: list[_Evidence]) -> None:
    try:
        _quarantine(root, summary, evidence)
    except Exception as exc:
        summary.failures.append(f"quarantine preservation failed: {exc}")
    raise ArtifactTransferError(summary)


def _publish_new(root: Path, incoming: _Incoming) -> None:
    target = _checked_target(root, incoming.path, mkdir=True)
    fd, name = tempfile.mkstemp(prefix=".artifact-incoming-", dir=target.parent)
    temporary = Path(name)
    try:
        try:
            _write_all(fd, incoming.data)
            os.fsync(fd)
        finally:
            os.close(fd)
        _checked_target(root, incoming.path)
        # Unlike rename/replace, link is atomic and cannot replace an existing name.
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _append_ledger(root: Path, incoming: _Incoming) -> None:
    target = _checked_target(root, incoming.path)
    flags = os.O_RDWR | os.O_APPEND | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(target, flags)
    written = 0
    suffix = incoming.data[len(incoming.existing):]
    try:
        with os.fdopen(fd, "r+b", buffering=0) as handle:
            metadata = target.lstat()
            if not stat.S_ISREG(metadata.st_mode) or not os.path.samestat(metadata, os.fstat(handle.fileno())):
                raise ValueError("ledger destination changed while opening it")
            if handle.read() != incoming.existing:
                raise ValueError("ledger changed after preflight; no suffix was appended")
            view = memoryview(suffix)
            while view:
                count = os.write(handle.fileno(), view)
                if count <= 0:
                    raise OSError("append made no progress")
                written += count
                view = view[count:]
            os.fsync(handle.fileno())
    except Exception as exc:
        raise RuntimeError(
            f"ledger append failed after {written}/{len(suffix)} suffix bytes; "
            f"original prefix was not replaced (partial suffix may remain): {exc}"
        ) from exc


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _subtree_directory(path: str, patterns: list[str]) -> bool:
    return any(pattern.endswith("/**") and _matches(path, [pattern[:-3], pattern]) for pattern in patterns)


def _require_unlocked_run(root: Path, relative: str, remote: dict[str, tuple[str, str]]) -> None:
    lock_relative = "/".join(relative.split("/")[:2]) + "/.artifact-write.lock"
    lock = _checked_target(root, lock_relative)
    try:
        lock.lstat()
    except FileNotFoundError:
        pass
    else:
        raise ValueError("local run writer lock is occupied; never transfer a live or stale lock")
    key = os.path.normcase(lock_relative)
    if key in remote or any(name.startswith(key + "/") for name in remote):
        raise ValueError("remote run writer lock is occupied; never upload into an active or stale run")


def pull_run_artifacts(volume: Any, repo_root: Path, patterns: list[str]) -> TransferSummary:
    """Preflight the entire selection, then create, skip, or append without replacing bytes.

    Conflicts preserve every available incoming snapshot in a private sibling quarantine.
    Any conflict or I/O failure raises ArtifactTransferError, including a failed append
    that may have left an incomplete suffix. No rollback ever truncates a ledger.
    """
    root = Path(repo_root).resolve(strict=True)
    summary = TransferSummary()
    evidence: list[_Evidence] = []
    incoming_files: list[_Incoming] = []
    try:
        with _transfer_lock(root), ExitStack() as run_locks:
            entries = list(volume.listdir("runs/", recursive=True))
            seen: set[str] = set()
            for entry in entries:
                raw = entry.path
                kind = _entry_kind(entry)
                try:
                    relative = _normalize_remote(raw)
                except ValueError as exc:
                    data = None
                    if kind == "file":
                        try:
                            data = _read_remote(volume, raw)
                        except _ReadFailure as failure:
                            data = failure.partial
                            summary.failures.append(f"{raw}: {failure}")
                    reason = f"invalid remote path: {exc}"
                    summary.conflicts.append(f"{raw}: {reason}")
                    evidence.append(_Evidence(raw, data, None, reason))
                    continue
                if not _matches(relative, patterns):
                    continue
                key = os.path.normcase(relative)
                duplicate = key in seen
                seen.add(key)
                if kind == "directory":
                    try:
                        target = _checked_target(root, relative, directory=True)
                        if duplicate or not _subtree_directory(relative, patterns):
                            raise ValueError("selected file path is a remote directory")
                        if target.exists() and not target.is_dir():
                            raise ValueError("remote directory collides with a local file")
                    except ValueError as exc:
                        summary.conflicts.append(f"{relative}: {exc}")
                    continue
                if kind != "file":
                    summary.conflicts.append(f"{relative}: selected remote entry is {kind}, not a regular file")
                    continue
                try:
                    data = _read_remote(volume, raw)
                except _ReadFailure as exc:
                    summary.failures.append(f"{relative}: {exc}")
                    evidence.append(_Evidence(relative, exc.partial, None, str(exc)))
                    continue
                incoming = _Incoming(relative, data)
                try:
                    if duplicate:
                        for prior in incoming_files:
                            if os.path.normcase(prior.path) == key:
                                evidence.append(_Evidence(
                                    prior.path, prior.data, prior.existing, "duplicate or aliased remote path"
                                ))
                        raise ValueError("duplicate or aliased remote path")
                    _classify(root, incoming)
                    incoming_files.append(incoming)
                except Exception as exc:
                    reason = str(exc)
                    summary.conflicts.append(f"{relative}: {reason}")
                    evidence.append(_Evidence(relative, data, incoming.existing, reason))
            if summary.conflicts or summary.failures:
                _refuse(root, summary, evidence)
            try:
                from harness.artifact_guard import run_write_lock

                for run in sorted({item.path.split("/")[1] for item in incoming_files}):
                    lock = _checked_target(root, f"runs/{run}/.artifact-write.lock", mkdir=True)
                    run_locks.enter_context(run_write_lock(lock.parent))
            except Exception as exc:
                reason = f"could not acquire local run writer lock: {exc}"
                summary.failures.append(reason)
                evidence.extend(_Evidence(item.path, item.data, item.existing, reason) for item in incoming_files)
                _refuse(root, summary, evidence)
            for incoming in incoming_files:
                try:
                    # Recheck every snapshot under the transfer lock immediately before mutation.
                    current = _existing_bytes(root, incoming.path)
                    if current != incoming.existing:
                        if current == incoming.data:
                            summary.identical.append(incoming.path)
                            continue
                        raise ValueError("destination changed after preflight")
                    if incoming.action == "identical":
                        summary.identical.append(incoming.path)
                    elif incoming.action == "append":
                        _append_ledger(root, incoming)
                        summary.appended.append(incoming.path)
                    else:
                        try:
                            _publish_new(root, incoming)
                        except FileExistsError:
                            current = _existing_bytes(root, incoming.path)
                            if current != incoming.data:
                                raise ValueError("destination appeared during atomic publication") from None
                            summary.identical.append(incoming.path)
                        else:
                            summary.created.append(incoming.path)
                except Exception as exc:
                    reason = str(exc)
                    summary.failures.append(f"{incoming.path}: {reason}")
                    try:
                        current = _existing_bytes(root, incoming.path)
                    except Exception:
                        current = None
                    evidence.append(_Evidence(incoming.path, incoming.data, current, reason))
            if summary.conflicts or summary.failures:
                _refuse(root, summary, evidence)
    except ArtifactTransferError:
        raise
    except Exception as exc:
        summary.failures.append(str(exc))
        _refuse(root, summary, evidence)
    return summary


def upload_run_artifacts(volume: Any, repo_root: Path, paths: list[Path]) -> TransferSummary:
    """Upload snapshots of new run files only; never force or replace a remote artifact.

    Even a valid differing remote ledger is refused: bulk upload has no compare-and-swap
    append. A coordinated remote append is required instead. Both versions are quarantined.
    """
    root = Path(repo_root).resolve(strict=True)
    summary = TransferSummary()
    evidence: list[_Evidence] = []
    snapshots: list[_Incoming] = []
    try:
        with _transfer_lock(root):
            remote: dict[str, tuple[str, str]] = {}
            try:
                entries = list(volume.listdir("runs/", recursive=True))
            except FileNotFoundError:
                entries = []
            for entry in entries:
                relative = _normalize_remote(entry.path)
                key = os.path.normcase(relative)
                if key in remote:
                    raise ValueError(f"duplicate or aliased remote path: {relative}")
                remote[key] = (entry.path, _entry_kind(entry))
            seen: set[str] = set()
            for path in paths:
                data = None
                existing = None
                relative = str(path)
                try:
                    local = Path(path)
                    relative = local.relative_to(root).as_posix() if local.is_absolute() else local.as_posix()
                    relative = _normalize_remote(relative)
                    key = os.path.normcase(relative)
                    if key in seen:
                        raise ValueError("duplicate local upload path")
                    seen.add(key)
                    data = _existing_bytes(root, relative)
                    if data is None:
                        raise ValueError("local upload file is missing")
                    if _is_run_ledger(relative):
                        _verify_ledger(data, relative)
                    _require_unlocked_run(root, relative, remote)
                    for parent in Path(relative).parents:
                        parent_entry = remote.get(os.path.normcase(parent.as_posix()))
                        if parent_entry and parent_entry[1] != "directory":
                            raise ValueError("remote parent is not a directory")
                    entry = remote.get(key)
                    if entry is not None:
                        raw, kind = entry
                        if kind != "file":
                            raise ValueError(f"remote destination is {kind}, not a regular file")
                        existing = _read_remote(volume, raw)
                        if existing == data:
                            summary.identical.append(relative)
                            continue
                        if _is_run_ledger(relative):
                            raise ValueError("remote ledger differs; coordinated append required, bulk replacement refused")
                        raise ValueError("remote artifact differs; replacement refused")
                    # A listed child also establishes a directory even if listing omits directory entries.
                    if any(name.startswith(key + "/") for name in remote):
                        raise ValueError("remote destination contains children and is a directory")
                    snapshots.append(_Incoming(relative, data))
                except Exception as exc:
                    reason = str(exc)
                    if isinstance(exc, _ReadFailure):
                        existing = exc.partial
                        summary.failures.append(f"{relative}: {reason}")
                    else:
                        summary.conflicts.append(f"{relative}: {reason}")
                    evidence.append(_Evidence(relative, data, existing, reason))
            if summary.conflicts or summary.failures:
                _refuse(root, summary, evidence)
            if snapshots:
                # Keep snapshots alive until the context commits; never re-read changing local files.
                streams = [io.BytesIO(item.data) for item in snapshots]
                try:
                    with volume.batch_upload(force=False) as batch:
                        for item, stream in zip(snapshots, streams):
                            batch.put_file(stream, "/" + item.path)
                except Exception as exc:
                    reason = f"batch upload failed (remote may contain a partial batch): {exc}"
                    summary.failures.append(reason)
                    evidence.extend(_Evidence(item.path, item.data, None, reason) for item in snapshots)
                    _refuse(root, summary, evidence)
                finally:
                    for stream in streams:
                        stream.close()
                summary.created.extend(item.path for item in snapshots)
    except ArtifactTransferError:
        raise
    except Exception as exc:
        summary.failures.append(str(exc))
        _refuse(root, summary, evidence)
    return summary
