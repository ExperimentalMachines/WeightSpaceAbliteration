"""The gdkit fa1e4d5 upgrade: every gate returns `passed`, gate logs live in the receipt, and old receipts
keep the gate_log binding they were written with."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from gdkit.gates import Gate, run_gate
from gdkit.ledger import Ledger
from gdkit.prereg import freeze_run
from harness import gates as harness_gates
from harness import preflight
from harness.protocol_rules import ProtocolViolation


def _run(tmp_path: Path) -> Path:
    run = tmp_path / "runs" / "r1"
    run.mkdir(parents=True)
    project = tmp_path / "project.yaml"
    project.write_text("study_question: q\n", encoding="utf-8")
    freeze_run(Ledger(run / "ledger.jsonl", "r1", "registered"), project)
    return run


def _head(run: Path) -> str:
    return json.loads((run / "ledger.jsonl").read_text(encoding="utf-8").splitlines()[-1])["entry_hash"]


def _gate(run_dir):
    print("checked")
    return {"passed": True, "ok": True}


def test_gdkit_writes_real_captured_log_without_a_ledger_append(tmp_path):
    run = _run(tmp_path)
    before = (run / "ledger.jsonl").read_bytes()
    run_gate(run, Gate("split_integrity", True, _gate), inputs=[],
             run_id="r1", ledger_head=_head(run), capture_log=True)
    assert (run / "ledger.jsonl").read_bytes() == before  # no gate_log entry: the receipt stays current
    receipt = json.loads((run / "receipts" / "split_integrity.json").read_text(encoding="utf-8"))
    log = (run / "logs" / "split_integrity.log").read_bytes()
    assert receipt["receipt_schema"] == 1 and receipt["ledger_head"] == _head(run)
    assert receipt["log"]["sha256"] == hashlib.sha256(log).hexdigest() and b"checked" in log
    preflight.require_log_binding(run)


def _schema_1_receipt(run: Path) -> Path:
    return run_gate(run, Gate("toy", True, _gate), inputs=[], run_id="r1", ledger_head=_head(run), capture_log=True)


def test_a_schema_1_receipt_binds_its_log_through_the_receipt(tmp_path):
    run = _run(tmp_path)
    _schema_1_receipt(run)
    preflight.require_log_binding(run)
    (run / "logs" / "toy.log").write_bytes(b"edited\n")
    with pytest.raises(ProtocolViolation, match="does not match its recorded hash"):
        preflight.require_log_binding(run)
    (run / "logs" / "toy.log").unlink()
    with pytest.raises(ProtocolViolation, match="is missing"):
        preflight.require_log_binding(run)


def test_a_schema_1_receipt_without_a_log_is_a_violation(tmp_path):
    run = _run(tmp_path)
    run_gate(run, Gate("toy", True, _gate), inputs=[], run_id="r1", ledger_head=_head(run))  # no capture_log
    with pytest.raises(ProtocolViolation, match="names no log"):
        preflight.require_log_binding(run)


def test_a_schema_0_receipt_still_needs_its_gate_log_entry(tmp_path):
    """Receipts written by gdkit 8cf73ec keep the rule they were written under."""
    from gdkit.gates import receipt_hash

    run = _run(tmp_path)
    body = {"run_id": "r1", "gate": "old", "cheap": True, "gate_code_hash": "0" * 64, "inputs": {},
            "result": {"ok": True}, "ledger_head": _head(run)}
    body["receipt_hash"] = receipt_hash(body)
    (run / "receipts").mkdir()
    (run / "receipts" / "old.json").write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(ProtocolViolation, match="has no gate_log entry"):
        preflight.require_log_binding(run)
    (run / "logs").mkdir()
    (run / "logs" / "old.log").write_bytes(b"old output\n")
    Ledger(run / "ledger.jsonl", "r1", "registered").record(
        "gate_log", rows_before=0, rows_after=0,
        params={"gate": "old", "receipt_sha256": body["receipt_hash"], "log": "logs/old.log"},
        input_hash=body["receipt_hash"], output_hash=hashlib.sha256(b"old output\n").hexdigest())
    preflight.require_log_binding(run)


def test_fresh_harness_execution_requires_explicit_release_before_host_collection(tmp_path, capsys):
    run = _run(tmp_path)
    before = (run / "ledger.jsonl").read_bytes()
    assert harness_gates.main(["--run", str(run), "--gate", "arm_counts"]) == 1
    assert "--release is required" in capsys.readouterr().err
    assert (run / "ledger.jsonl").read_bytes() == before
    assert not (run / "receipts").exists()
    assert not (run / "execution").exists()


def test_read_only_verifier_labels_historical_receipt_without_upgrading_it(tmp_path):
    from harness.execution import verify_execution

    run = _run(tmp_path)
    path = _schema_1_receipt(run)
    original = path.read_bytes()
    report = verify_execution(run, path)
    assert report["legacy"] is True and report["validity"] == "legacy-incomplete"
    assert report["execution_identity"] == "unvalidated"
    assert path.read_bytes() == original
