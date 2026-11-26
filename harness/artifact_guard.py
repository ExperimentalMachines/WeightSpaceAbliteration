"""Non-destructive guards for the repository's gate and host CLI producers.

The lock coordinates guarded writers only. Direct gdkit calls and direct ``check_*``
function calls do not acquire it; this is not protection against arbitrary filesystem edits.
"""

from __future__ import annotations

import json
import os
import re
import stat
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class ArtifactConflict(RuntimeError):
    """An occupied or unsafe artifact path must not be written."""


LOCK_NAME = ".artifact-write.lock"
_ARM_NAME = re.compile(r"[A-Za-z0-9_-]+\Z")
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                   *(f"LPT{i}" for i in range(1, 10))}
_MEASUREMENTS: dict[str, tuple[str, ...]] = {
    "split_integrity": (),
    "arm_counts": (),
    "exclusions_applied": (),
    "direction_derivation": ("results/direction.npz", "results/direction_derivation.json"),
    "refusal_eval": ("results/refusal_eval.json",),
    "judge_agreement": ("results/judge_agreement.json",),
    "over_refusal_eval": ("results/over_refusal.json",),
    "kl_divergence": ("results/kl_divergence.json",),
    "activation_extraction": ("results/activations.npz", "results/activation_extraction.json"),
    "probe_train": ("results/probe_train.json",),
    # The whole directory is owned, even when an interrupted run left it empty.
    "capability_suite": ("results/lm_eval", "results/capability_suite.json"),
}


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _is_link(info: os.stat_result) -> bool:
    # Windows junctions and other reparse points must not redirect writes either.
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _check_directories(path: Path) -> None:
    for parent in (*reversed(path.parents), path):
        info = _lstat(parent)
        if info is None:
            continue
        if _is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise ArtifactConflict(f"unsafe artifact parent: {parent} is not a real directory")


def _run_path(run_dir: Path) -> Path:
    path = Path(run_dir)
    if ".." in path.parts:
        raise ArtifactConflict(f"unsafe run path: {path}")
    path = path.absolute()
    _check_directories(path)
    if _lstat(path) is None:
        raise ArtifactConflict(f"run directory does not exist: {path}")
    return path


def safe_artifact_path(run_dir: Path, relative: str) -> Path:
    """Return a contained path after rejecting unsafe or redirected parent directories.

    The leaf may already exist; callers that read it must also reject a symlink leaf.
    """
    part = Path(relative)
    if not relative or part.is_absolute() or part.drive or any(p in ("..", ".") for p in part.parts):
        raise ArtifactConflict(f"unsafe artifact path: {relative!r}")
    if "\\" in relative or ":" in relative:
        raise ArtifactConflict(f"unsafe artifact path: {relative!r}")
    path = _run_path(run_dir) / part
    _check_directories(path.parent)
    return path


def require_fresh_paths(run_dir: Path, relatives: list[str]) -> None:
    """Refuse any existing leaf, including directories and broken symlinks."""
    for relative in relatives:
        path = safe_artifact_path(run_dir, relative)
        if _lstat(path) is not None:
            raise ArtifactConflict(f"refusing to replace existing artifact: {path}")


def _gate_names(names: list[str]) -> None:
    if not names:
        raise ArtifactConflict("at least one gate name is required")
    seen: set[str] = set()
    for name in names:
        if not isinstance(name, str) or not _ARM_NAME.fullmatch(name) or name not in _MEASUREMENTS:
            raise ArtifactConflict(f"unknown or unsafe gate name: {name!r}")
        if name in seen:
            raise ArtifactConflict(f"duplicate gate name: {name}")
        seen.add(name)


def require_regular_file(run_dir: Path, relative: str) -> Path:
    """Require a real existing input file, not a symlink or redirected leaf."""
    path = safe_artifact_path(run_dir, relative)
    info = _lstat(path)
    if info is None or _is_link(info) or not stat.S_ISREG(info.st_mode):
        raise ArtifactConflict(f"required input is not a real file: {path}")
    return path


def _refusal_arms(run_dir: Path) -> list[str]:
    path = safe_artifact_path(run_dir, "harness.json")
    info = _lstat(path)
    arms = ["primary", "large"]
    if info is not None:
        if _is_link(info) or not stat.S_ISREG(info.st_mode):
            raise ArtifactConflict(f"unsafe harness configuration: {path}")
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
            arms = cfg.get("refusal_eval", {}).get("arms", arms)
        except (ValueError, AttributeError) as exc:
            raise ArtifactConflict(f"invalid refusal arm configuration: {path}") from exc
    if not isinstance(arms, list):
        raise ArtifactConflict("refusal_eval.arms must be a list of safe arm names")
    seen: set[str] = set()
    for arm in arms:
        if (not isinstance(arm, str) or not _ARM_NAME.fullmatch(arm)
                or arm.upper() in _RESERVED_NAMES):
            raise ArtifactConflict(f"unsafe refusal arm name: {arm!r}")
        if arm.casefold() in seen:
            raise ArtifactConflict(f"duplicate refusal arm name: {arm}")
        seen.add(arm.casefold())
    return arms


def require_fresh_gates(run_dir: Path, names: list[str]) -> None:
    """Read-only precheck of every selected gate's receipt, logs and measurements.

    Shared parent directories are permitted; only gate-owned leaves are occupied.
    This is advisory without ``gate_write_guard``, which repeats it while locked.
    """
    _gate_names(names)
    outputs: list[str] = []
    for name in names:
        outputs.extend((f"receipts/{name}.json", f"logs/{name}.log", f"logs/{name}.log.partial"))
        outputs.extend((f"execution/{name}.json", f"failures/{name}.json"))
        outputs.extend(_MEASUREMENTS[name])
        if name == "refusal_eval":
            outputs.extend(f"results/refusal_{arm}.jsonl" for arm in _refusal_arms(run_dir))
    require_fresh_paths(run_dir, outputs)


@contextmanager
def run_write_lock(run_dir: Path) -> Iterator[None]:
    """Acquire a non-reentrant, exclusive per-run lock; never remove another owner's lock.

    A crash may leave the lock behind. It must be investigated, not silently stolen.
    """
    path = safe_artifact_path(run_dir, LOCK_NAME)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        # Windows reports an occupied directory as PermissionError, not EEXIST.
        if _lstat(path) is not None:
            raise ArtifactConflict(f"run already has a writer lock: {path}") from exc
        raise
    identity = os.fstat(fd)
    token = f"pid={os.getpid()} token={uuid.uuid4().hex}\n".encode("ascii")
    written = False
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(token)
            handle.flush()
            written = True
            yield
    finally:
        # The handle is closed before unlinking for Windows. The inode and token
        # ensure a replacement lock is never mistaken for the one we acquired.
        current = _lstat(path)
        if (current is not None and not _is_link(current) and stat.S_ISREG(current.st_mode)
                and (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino)
                and (not written or path.read_bytes() == token)):
            path.unlink()


@contextmanager
def gate_write_guard(run_dir: Path, names: list[str]) -> Iterator[None]:
    """Refuse occupied outputs before writes, then hold the run lock through execution."""
    require_fresh_gates(run_dir, names)
    with run_write_lock(run_dir):
        require_fresh_gates(run_dir, names)
        yield
