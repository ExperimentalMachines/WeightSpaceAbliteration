"""Immutable local host sessions, compatible with gdkit's canonical host events.

Full records and raw probe streams are private evidence, not ledger payloads. The
cooperative run lock does not protect against arbitrary writers or provide distributed CAS.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import locale
import os
import subprocess
import uuid
from pathlib import Path
from typing import Sequence

from gdkit import host as gdhost
from gdkit.ledger import Ledger, verify
from harness.artifact_guard import (
    ArtifactConflict, require_fresh_paths, require_regular_file, run_write_lock,
    safe_artifact_path,
)

COLLECTOR_LIMITATIONS = [
    "gdkit's ancillary git collector normalizes stdout and does not retain its raw subprocess streams.",
    "Raw requested probe stdout/stderr bytes are retained separately, including available timeout output.",
    "Same-host checking compares gdkit summaries: normalized successful stdout, status and versions; "
    "not stderr, failed-probe output, private identity fields or git state.",
    "A timed-out subprocess may not have flushed all output; unavailable tools have no output bytes.",
    "Probe text uses the local encoding with replacement; exact bytes are authoritative, and gdkit may refuse undecodable probes.",
]


def _bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _text(payload: bytes) -> str:
    # Match subprocess text=True's universal newline conversion. Replacement
    # text is only a derivative; the sidecar preserves every original byte.
    with io.TextIOWrapper(io.BytesIO(payload), encoding=locale.getencoding(), errors="replace") as stream:
        return stream.read().strip()


def _probe(command: Sequence[str]) -> tuple[dict, dict]:
    command = list(command)
    if not command or any(not isinstance(arg, str) or not arg for arg in command):
        raise ValueError("probe commands must contain nonempty string arguments")
    stdout, stderr = b"", b""
    reason = None
    try:
        proc = subprocess.run(command, capture_output=True, timeout=30)
        stdout, stderr = proc.stdout, proc.stderr
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        returncode, reason = None, "timed out after 30 seconds; captured output may be partial"
    except OSError as exc:
        returncode, reason = None, str(exc)
    full = {
        "command": command, "available": returncode == 0, "returncode": returncode,
        "stdout": _text(stdout), "stderr": _text(stderr),
    }
    raw = {
        "command": command, "returncode": returncode,
        "stdout_base64": base64.b64encode(stdout).decode("ascii"),
        "stderr_base64": base64.b64encode(stderr).decode("ascii"),
        "stdout_sha256": _sha(stdout), "stderr_sha256": _sha(stderr),
    }
    if reason is not None:
        full["reason"] = raw["reason"] = reason
    return full, raw


def collect_session_host(*, packages: Sequence[str] = (), probes: Sequence[Sequence[str]] = ()) -> tuple[dict, dict]:
    """Collect without importing GPU libraries; return private full and raw evidence.

    gdkit's basic collector is preserved verbatim in the raw sidecar. Its git
    subprocess streams are unavailable; that collector limitation is explicit.
    Requested probes use a binary collector so stderr is never silently truncated.
    """
    full = gdhost.collect_host(packages=packages, probes=())
    raw = {"gdkit_collector": full, "probes": [], "limitations": COLLECTOR_LIMITATIONS}
    # Avoid aliasing the original gdkit snapshot when adding our probe records.
    full = {**full, "probes": [], "collector_limitations": COLLECTOR_LIMITATIONS}
    for command in probes:
        probe, evidence = _probe(command)
        full["probes"].append(probe)
        raw["probes"].append(evidence)
    return full, raw


def _ledger(run_dir: Path, *, recording: bool = False) -> tuple[Path, bytes, list[dict]]:
    path = require_regular_file(run_dir, "ledger.jsonl")
    payload = path.read_bytes()
    if not payload or not payload.endswith(b"\n"):
        raise ArtifactConflict("host recording requires a nonempty ledger with a final newline; freeze the run first")
    if verify(path) == 0:
        raise ArtifactConflict("host recording requires existing ledger entries; freeze the run first")
    records = [json.loads(line) for line in payload.splitlines() if line.strip()]
    run_id = records[0].get("run_id")
    if not isinstance(run_id, str) or not run_id or any(
        entry.get("run_id") != run_id or entry.get("mode") != "registered" for entry in records
    ):
        raise ArtifactConflict("host provenance requires a consistent registered ledger identity")
    if recording and run_id != run_dir.name:
        raise ArtifactConflict("ledger run_id does not match the run directory")
    if path.read_bytes() != payload:
        raise ArtifactConflict("ledger changed while checking host provenance")
    return path, payload, records


def _future_run(run_dir: Path, records: list[dict]) -> None:
    # Normal recording is deliberately not a migration mechanism for old runs.
    require_fresh_paths(run_dir, ["host.json"])
    if any(entry.get("op") == "host_provisioned" for entry in records):
        raise ArtifactConflict("legacy host_provisioned run cannot be migrated by normal host recording; use a fresh linked run")
    host_entries = [entry for entry in records if entry.get("op") == "host"]
    for entry in host_entries:
        if entry.get("event") is not True:
            raise ArtifactConflict("legacy non-event host record cannot be migrated by normal host recording")
        _verify_entry(run_dir, entry)
    canonical = bool(host_entries)
    receipts = safe_artifact_path(run_dir, "receipts")
    if receipts.exists() or receipts.is_symlink():
        safe_artifact_path(run_dir, "receipts/parent-check")
        for receipt in receipts.iterdir():
            if receipt.suffix != ".json":
                raise ArtifactConflict("unrecognized receipt evidence cannot be migrated by normal host recording")
            payload = json.loads(require_regular_file(run_dir, f"receipts/{receipt.name}").read_bytes())
            version = payload.get("contract_version")
            if type(version) is not int or version < 3:
                raise ArtifactConflict("legacy gate evidence cannot be migrated by normal host recording; use a fresh linked run")
    if not canonical:
        for relative in ("receipts", "logs", "execution"):
            path = safe_artifact_path(run_dir, relative)
            if path.exists() or path.is_symlink():
                raise ArtifactConflict("existing gate evidence cannot be migrated by normal host recording; use a fresh linked run")


def _write_private(run_dir: Path, relative: str, payload: bytes) -> None:
    path = safe_artifact_path(run_dir, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Recheck parents after mkdir and create exclusively, including on Windows.
    path = safe_artifact_path(run_dir, relative)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def record_session_host(
    run_dir: Path, *, packages: Sequence[str] = (), probes: Sequence[Sequence[str]] = (),
    require_probes: bool = False,
) -> dict:
    """Own the run lock once, create immutable evidence, append an event, return params.

    Append failure preserves any newly created evidence as unbound evidence; it
    never deletes files, rolls back a ledger, or replaces an existing session.
    """
    run_dir = Path(run_dir)
    require_fresh_paths(run_dir, ["host.json"])
    with run_write_lock(run_dir):
        ledger_path, before, records = _ledger(run_dir, recording=True)
        _future_run(run_dir, records)
        session_id = uuid.uuid4().hex
        relative = f"hosts/{session_id}.json"
        raw_relative = f"hosts/private/{session_id}.json"
        require_fresh_paths(run_dir, [relative, raw_relative])
        ledger = Ledger(ledger_path, run_dir.name, "registered")
        full, raw = collect_session_host(packages=packages, probes=probes)
        if require_probes and (not probes or any(not probe["available"] for probe in full["probes"])):
            raise ArtifactConflict("required host probes are missing or failed; no verified session recorded")
        raw_payload = _bytes(raw)
        raw_ref = {"path": raw_relative, "sha256": _sha(raw_payload)}
        full = {**full, "session_id": session_id, "raw": raw_ref, "required_probes": require_probes}
        payload = _bytes(full)
        params = {
            "path": relative, "sha256": _sha(payload), "summary": gdhost.host_summary(full),
            "session_id": session_id, "raw": raw_ref, "required_probes": require_probes,
        }
        if ledger_path.read_bytes() != before:
            raise ArtifactConflict("ledger changed during host collection; refusing to append")
        ledger.ensure_current()
        _future_run(run_dir, records)
        require_fresh_paths(run_dir, [relative, raw_relative])
        _write_private(run_dir, raw_relative, raw_payload)
        _write_private(run_dir, relative, payload)
        if ledger_path.read_bytes() != before:
            raise ArtifactConflict("ledger changed before host append; preserving unbound session evidence")
        ledger.record_event("host", params=params, input_hash=raw_ref["sha256"], output_hash=params["sha256"])
        return params


def _verify_entry(run_dir: Path, entry: dict) -> dict:
    params = entry.get("params", {})
    session = params.get("session_id")
    if not isinstance(session, str) or len(session) != 32 or any(c not in "0123456789abcdef" for c in session):
        raise gdhost.HostError("legacy/incomplete host event: no canonical session identity")
    if params.get("path") != f"hosts/{session}.json":
        raise gdhost.HostError("host session path does not match its identity")
    path = require_regular_file(run_dir, params["path"])
    payload = path.read_bytes()
    if _sha(payload) != params.get("sha256") or entry.get("output_hash") != params.get("sha256"):
        raise gdhost.HostError("host file does not match its canonical event hash")
    full = json.loads(payload)
    if full.get("session_id") != session or gdhost.host_summary(full) != params.get("summary"):
        raise gdhost.HostError("host file identity/summary does not match its canonical event")
    required = params.get("required_probes")
    if type(required) is not bool or full.get("required_probes") != required:
        raise gdhost.HostError("host probe requirements are not bound to the session")
    if required and (not full.get("probes") or any(not probe.get("available") for probe in full["probes"])):
        raise gdhost.HostError("required host probes were not successful")
    raw = params.get("raw", {})
    if (not isinstance(raw, dict) or raw.get("path") != f"hosts/private/{session}.json"
            or full.get("raw") != raw or entry.get("input_hash") != raw.get("sha256")):
        raise gdhost.HostError("host raw evidence is not bound to its canonical event")
    raw_payload = require_regular_file(run_dir, raw["path"]).read_bytes()
    if _sha(raw_payload) != raw.get("sha256"):
        raise gdhost.HostError("host raw evidence does not match its recorded hash")
    return {**params, "host_sha256": params["sha256"], "event_hash": entry["entry_hash"], "event_seq": entry["seq"]}


def verify_recorded_host(run_dir: Path, host_sha256: str) -> dict:
    """Read-only historical integrity check, never collecting the auditor's host.

    An earlier session remains valid even after later sessions have been appended.
    Renaming/moving the archive is permitted; ledger identity remains internally checked.
    """
    run_dir = Path(run_dir)
    _, _, records = _ledger(run_dir)
    for entry in reversed(records):
        if (entry.get("op") == "host" and entry.get("event") is True
                and entry.get("params", {}).get("sha256") == host_sha256):
            return {**_verify_entry(run_dir, entry), "integrity_verified": True}
    raise gdhost.HostError("no canonical host event matches the receipt's host hash (legacy/incomplete provenance)")


def require_current_host(run_dir: Path) -> dict:
    """Require canonical intact evidence and gdkit's actual checked=True result."""
    run_dir = Path(run_dir)
    ledger_path, before, records = _ledger(run_dir)
    latest = next((entry for entry in reversed(records)
                   if entry.get("op") == "host" and entry.get("event") is True), None)
    if latest is None:
        raise gdhost.HostError("no canonical host session; legacy-only or unchecked hosts cannot run new gates")
    reference = _verify_entry(run_dir, latest)
    result = gdhost.require_same_host(run_dir)
    if result.get("checked") is not True or result.get("host_sha256") != reference["sha256"]:
        raise gdhost.HostError("gdkit did not check the bound canonical host session")
    if ledger_path.read_bytes() != before:
        raise gdhost.HostError("ledger changed during same-host checking")
    # Recheck bytes after gdkit's collection too, before handing the binding to execution.
    _verify_entry(run_dir, latest)
    return {**reference, **result}


from harness.execution import register_module

register_module(__name__)
