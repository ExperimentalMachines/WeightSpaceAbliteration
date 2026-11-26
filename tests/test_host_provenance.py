"""Real CPU collectors and ledger/file primitives in temporary runs only."""
from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from gdkit import host as gdhost
from gdkit.gates import Gate, run_gate
from gdkit.ledger import Ledger, verify

from harness import host
from harness.artifact_guard import ArtifactConflict, LOCK_NAME
from harness.preflight import require_host
from harness.protocol_rules import ProtocolViolation
from scripts import record_host


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def unexpected(*args, **kwargs):
    pytest.fail("historical verification/refusal must not collect a current host")


@pytest.fixture
def run(tmp_path):
    path = tmp_path / "temporary-cpu-run"
    path.mkdir()
    frozen = b"temporary CPU fixture only\n"
    (path / "fixture.txt").write_bytes(frozen)
    Ledger(path / "ledger.jsonl", path.name, "registered").record(
        "preregistration", rows_before=0, rows_after=0,
        input_hash=sha(frozen), output_hash=sha(frozen),
    )
    return path


def records(run):
    return [json.loads(line) for line in (run / "ledger.jsonl").read_bytes().splitlines()]


def tiny_gate(run_dir):
    payload = (run_dir / "fixture.txt").read_bytes()
    print("read", len(payload), "fixture bytes")
    return {"passed": bool(payload), "fixture_sha256": sha(payload)}


def test_two_sessions_and_real_gdkit_checked_cpu_host(run):
    initial = (run / "ledger.jsonl").read_bytes()
    first = host.record_session_host(run)
    first_bytes = (run / first["path"]).read_bytes()
    first_raw = (run / first["raw"]["path"]).read_bytes()
    assert gdhost.require_same_host(run) == {"checked": True, "host_sha256": first["sha256"]}
    assert require_host(run)["checked"] is True
    second = host.record_session_host(run)
    assert first["session_id"] != second["session_id"]
    assert first["path"] != second["path"]
    assert first["sha256"] != second["sha256"]
    assert (run / first["path"]).read_bytes() == first_bytes
    assert (run / first["raw"]["path"]).read_bytes() == first_raw
    assert (run / "ledger.jsonl").read_bytes().startswith(initial)
    assert not (run / "host.json").exists()
    assert verify(run / "ledger.jsonl") == 3
    for entry, reference in zip(records(run)[1:], (first, second)):
        assert entry["op"] == "host" and entry["event"] is True
        assert entry["params"] == reference
        assert entry["output_hash"] == sha((run / reference["path"]).read_bytes())
        assert entry["input_hash"] == sha((run / reference["raw"]["path"]).read_bytes())
    assert host.require_current_host(run)["host_sha256"] == second["sha256"]
    assert not (run / LOCK_NAME).exists()


def test_local_cli_appends_two_sessions_without_replacement(run, tmp_path):
    script = Path(record_host.__file__).resolve()
    results = []
    for _ in range(2):
        proc = subprocess.run([sys.executable, str(script), "--run", str(run)],
                              cwd=tmp_path, capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        results.append(json.loads(proc.stdout))
    assert results[0]["path"] != results[1]["path"]
    for reference in results:
        assert sha((run / reference["path"]).read_bytes()) == reference["sha256"]
    assert host.require_current_host(run)["checked"] is True


def test_requested_probe_bytes_preserved_and_private_text_absent_from_ledger(run):
    stdout = b"  PRIVATE_machine_account_path\r\n"
    stderr = b"PRIVATE_stderr_" + b"x" * 7000 + b"\r\n"
    code = f"import os; os.write(1, {stdout!r}); os.write(2, {stderr!r})"
    reference = host.record_session_host(run, probes=[[sys.executable, "-c", code]])
    raw_bytes = (run / reference["raw"]["path"]).read_bytes()
    evidence = json.loads(raw_bytes)
    probe = evidence["probes"][0]
    assert base64.b64decode(probe["stdout_base64"]) == stdout
    assert base64.b64decode(probe["stderr_base64"]) == stderr
    assert probe["stdout_sha256"] == sha(stdout)
    assert probe["stderr_sha256"] == sha(stderr)
    assert sha(raw_bytes) == reference["raw"]["sha256"]
    assert evidence["limitations"]
    full = json.loads((run / reference["path"]).read_bytes())
    assert len(full["probes"][0]["stderr"]) > 7000
    assert b"PRIVATE_" not in (run / "ledger.jsonl").read_bytes()
    assert "user" not in reference["summary"] and "cwd" not in reference["summary"]
    assert "executable" not in reference["summary"]["python"]
    assert "node" not in reference["summary"]["platform"]
    assert host.require_current_host(run)["checked"] is True


def test_historical_check_selects_earlier_event_without_auditor_collection(run, tmp_path, monkeypatch):
    first = host.record_session_host(run)
    second = host.record_session_host(run)
    archive = tmp_path / "off-machine-renamed-archive"
    run.rename(archive)
    monkeypatch.setattr(gdhost, "collect_host", unexpected)
    monkeypatch.setattr(gdhost, "require_same_host", unexpected)
    before = {str(path.relative_to(archive)): path.read_bytes() for path in archive.rglob("*") if path.is_file()}
    for reference in (first, second):
        result = host.verify_recorded_host(archive, reference["sha256"])
        assert result["integrity_verified"] is True
        assert result["path"] == reference["path"]
        assert result["event_hash"] in [entry["entry_hash"] for entry in records(archive)]
        assert "checked" not in result
    after = {str(path.relative_to(archive)): path.read_bytes() for path in archive.rglob("*") if path.is_file()}
    assert after == before
    with pytest.raises(gdhost.HostError, match="no canonical host event"):
        host.verify_recorded_host(archive, sha(b"unknown host"))


@pytest.mark.parametrize("part", ["path", "raw"])
def test_historical_and_runtime_reject_mutated_evidence(run, monkeypatch, part):
    reference = host.record_session_host(run)
    path = run / (reference["path"] if part == "path" else reference["raw"]["path"])
    path.write_bytes(path.read_bytes() + b" ")
    monkeypatch.setattr(gdhost, "collect_host", unexpected)
    with pytest.raises(gdhost.HostError, match="hash"):
        host.verify_recorded_host(run, reference["sha256"])
    with pytest.raises(gdhost.HostError, match="hash"):
        host.require_current_host(run)


def test_current_check_refuses_real_environment_mismatch(run, monkeypatch):
    host.record_session_host(run)
    original = gdhost.collect_host

    def different(**kwargs):
        full = original(**kwargs)
        full["platform"]["machine"] = "different-CPU-fixture"
        return full

    monkeypatch.setattr(gdhost, "collect_host", different)
    with pytest.raises(gdhost.HostError, match="differs"):
        host.require_current_host(run)


def test_current_check_never_accepts_gdkit_unchecked(run, monkeypatch):
    host.record_session_host(run)
    monkeypatch.setattr(gdhost, "require_same_host", lambda _: {"checked": False, "reason": "fixture refusal"})
    with pytest.raises(gdhost.HostError, match="did not check"):
        host.require_current_host(run)


@pytest.mark.parametrize("legacy", ["missing", "host_provisioned", "gdkit-root"])
def test_legacy_is_readable_but_not_new_runtime_or_record_migration(run, monkeypatch, legacy):
    ledger = Ledger(run / "ledger.jsonl", run.name, "registered")
    if legacy == "host_provisioned":
        payload = b"private original legacy record\n"
        (run / "host.json").write_bytes(payload)
        ledger.record("host_provisioned", rows_before=0, rows_after=0,
                      input_hash=sha(payload), output_hash=sha(payload), params={"fingerprint": "legacy"})
    elif legacy == "gdkit-root":
        gdhost.record_host(ledger, run)
    before = {str(path.relative_to(run)): path.read_bytes() for path in run.rglob("*") if path.is_file()}
    monkeypatch.setattr(gdhost, "collect_host", unexpected)
    with pytest.raises((gdhost.HostError, ArtifactConflict)):
        host.require_current_host(run)
    with pytest.raises(ProtocolViolation):
        require_host(run)
    if legacy != "missing":
        with pytest.raises((ArtifactConflict, gdhost.HostError)):
            host.record_session_host(run)
    assert verify(run / "ledger.jsonl") >= 1
    after = {str(path.relative_to(run)): path.read_bytes() for path in run.rglob("*") if path.is_file()}
    assert after == before


@pytest.mark.parametrize("version", [None, 2])
def test_legacy_gate_receipt_prevents_normal_record_migration(run, monkeypatch, version):
    run_gate(run, Gate("cpu_fixture", True, tiny_gate), inputs=["fixture.txt"],
             run_id=run.name, ledger_head=records(run)[-1]["entry_hash"],
             contract_version=version, capture_log=True)
    before = {str(path.relative_to(run)): path.read_bytes() for path in run.rglob("*") if path.is_file()}
    monkeypatch.setattr(gdhost, "collect_host", unexpected)
    with pytest.raises(ArtifactConflict, match="legacy gate evidence"):
        host.record_session_host(run)
    assert before == {str(path.relative_to(run)): path.read_bytes() for path in run.rglob("*") if path.is_file()}


def test_new_contract_gate_does_not_prevent_a_second_host_session(run):
    first = host.record_session_host(run)
    receipt = run_gate(run, Gate("cpu_fixture", True, tiny_gate), inputs=["fixture.txt"],
                       run_id=run.name, ledger_head=records(run)[-1]["entry_hash"],
                       contract_version=3, capture_log=True)
    original_receipt = receipt.read_bytes()
    second = host.record_session_host(run)
    assert second["session_id"] != first["session_id"]
    assert receipt.read_bytes() == original_receipt
    assert host.verify_recorded_host(run, json.loads(original_receipt)["host_check"]["host_sha256"])["integrity_verified"]


@pytest.mark.parametrize("relative,kind", [("hosts/session.json", "file"),
                                          ("hosts/private/session.json", "directory")])
def test_occupied_session_paths_preserve_originals_before_collection(run, monkeypatch, relative, kind):
    session = uuid.UUID("12345678123456781234567812345678")
    relative = relative.replace("session", session.hex)
    target = run / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind == "file":
        target.write_bytes(b"original session evidence\n")
    else:
        target.mkdir()
    before = (run / "ledger.jsonl").read_bytes()
    monkeypatch.setattr(host.uuid, "uuid4", lambda: session)
    monkeypatch.setattr(gdhost, "collect_host", unexpected)
    with pytest.raises(ArtifactConflict, match="existing artifact"):
        host.record_session_host(run)
    assert target.read_bytes() == b"original session evidence\n" if kind == "file" else target.is_dir()
    assert (run / "ledger.jsonl").read_bytes() == before
    assert not (run / LOCK_NAME).exists()


@pytest.mark.parametrize("identity,mode", [("other-run", "registered"), ("temporary-cpu-run", "explore")])
def test_inconsistent_ledger_identity_refuses_without_collection(tmp_path, monkeypatch, identity, mode):
    run = tmp_path / "temporary-cpu-run"
    run.mkdir()
    Ledger(run / "ledger.jsonl", identity, mode).record("fixture", rows_before=0, rows_after=0,
        **({"input_hash": sha(b"in"), "output_hash": sha(b"out")} if mode == "registered" else {}))
    before = (run / "ledger.jsonl").read_bytes()
    monkeypatch.setattr(gdhost, "collect_host", unexpected)
    with pytest.raises(ArtifactConflict, match="identity|run_id"):
        host.record_session_host(run)
    assert (run / "ledger.jsonl").read_bytes() == before
    assert not (run / "hosts").exists()


def test_event_summary_binding_is_checked_before_current_host_collection(run, monkeypatch):
    reference = host.record_session_host(run)
    params = json.loads(json.dumps(reference))
    params["summary"]["platform"]["machine"] = "forged-summary"
    Ledger(run / "ledger.jsonl", run.name, "registered").record_event(
        "host", params=params, input_hash=reference["raw"]["sha256"], output_hash=reference["sha256"],
    )
    assert verify(run / "ledger.jsonl") == 3
    monkeypatch.setattr(gdhost, "collect_host", unexpected)
    with pytest.raises(gdhost.HostError, match="identity/summary"):
        host.verify_recorded_host(run, reference["sha256"])
    with pytest.raises(gdhost.HostError, match="identity/summary"):
        host.require_current_host(run)


def test_legacy_host_event_without_file_still_refuses_migration(run, monkeypatch):
    original = b"unavailable historical host evidence"
    Ledger(run / "ledger.jsonl", run.name, "registered").record(
        "host_provisioned", rows_before=0, rows_after=0,
        input_hash=sha(original), output_hash=sha(original),
    )
    before = (run / "ledger.jsonl").read_bytes()
    monkeypatch.setattr(gdhost, "collect_host", unexpected)
    with pytest.raises(ArtifactConflict, match="legacy host_provisioned"):
        host.record_session_host(run)
    assert (run / "ledger.jsonl").read_bytes() == before
    assert not (run / "hosts").exists()


def test_symlink_session_parent_refuses_without_writing_target(run, tmp_path, monkeypatch):
    target = tmp_path / "external-host-records"
    target.mkdir()
    try:
        (run / "hosts").symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    before = (run / "ledger.jsonl").read_bytes()
    monkeypatch.setattr(gdhost, "collect_host", unexpected)
    with pytest.raises(ArtifactConflict, match="unsafe artifact parent"):
        host.record_session_host(run)
    assert not list(target.iterdir())
    assert (run / "ledger.jsonl").read_bytes() == before
    assert not (run / LOCK_NAME).exists()


@pytest.mark.parametrize("probes", [[], [[sys.executable, "-c", "raise SystemExit(9)"]]])
def test_required_probe_failure_cannot_create_a_verified_session(run, probes):
    before = (run / "ledger.jsonl").read_bytes()
    with pytest.raises(ArtifactConflict, match="required host probes"):
        host.record_session_host(run, probes=probes, require_probes=True)
    assert (run / "ledger.jsonl").read_bytes() == before
    assert not (run / "hosts").exists()


def test_required_probe_success_is_bound_and_rechecked(run):
    reference = host.record_session_host(
        run, probes=[[sys.executable, "-c", "print('stable CPU probe')"]], require_probes=True,
    )
    assert reference["required_probes"] is True
    assert host.require_current_host(run)["checked"] is True
    assert host.verify_recorded_host(run, reference["sha256"])["integrity_verified"] is True
