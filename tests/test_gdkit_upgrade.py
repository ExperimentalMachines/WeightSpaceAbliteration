"""The gdkit fa1e4d5 upgrade: every gate returns `passed`, gate logs live in the receipt, and old receipts
keep the gate_log binding they were written with."""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from gdkit.gates import Gate, run_gate
from gdkit.ledger import Ledger
from gdkit.prereg import freeze_run
from harness import gates as harness_gates
from harness import preflight
from harness.protocol_rules import ProtocolViolation


def test_every_gate_returns_a_passed_field_in_every_return():
    def own_returns(function):
        """Returns of the function itself, not of helpers defined inside it."""
        found, stack = [], list(function.body)
        while stack:
            node = stack.pop()
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            if isinstance(node, ast.Return) and node.value is not None:
                found.append(node.value)
            stack.extend(ast.iter_child_nodes(node))
        return found

    for name, gate in harness_gates.REGISTRY.items():
        tree = ast.parse(inspect.getsource(gate.check))
        returns = own_returns(tree.body[0])
        assert returns, name
        for value in returns:
            assert isinstance(value, ast.Dict), f"{name}: return is not a dict literal"
            keys = [k.value for k in value.keys if isinstance(k, ast.Constant)]
            assert "passed" in keys, f"{name}: a return has no 'passed'"


def test_over_refusal_passes_only_at_or_below_the_pre_registered_ten_percent():
    source = inspect.getsource(harness_gates.check_over_refusal_eval)
    assert '"passed": rate <= 0.10' in source


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


def test_main_writes_the_log_into_the_receipt_and_adds_no_ledger_entry(tmp_path, monkeypatch, capsys):
    run = _run(tmp_path)
    monkeypatch.setitem(harness_gates.REGISTRY, "toy", Gate("toy", True, _gate))
    for check in ("require_host", "require_stage_consistency", "require_run_model"):
        monkeypatch.setattr(preflight, check, lambda run_dir: None)
    (run / "splits").mkdir()
    before = (run / "ledger.jsonl").read_bytes()
    assert harness_gates.main(["--run", str(run), "--gate", "toy"]) == 0
    assert (run / "ledger.jsonl").read_bytes() == before  # no gate_log entry: the receipt stays current
    receipt = json.loads((run / "receipts" / "toy.json").read_text(encoding="utf-8"))
    log = (run / "logs" / "toy.log").read_bytes()
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
