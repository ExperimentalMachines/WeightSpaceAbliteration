"""The append-only check's two exceptions: restoring a file git stored with converted line endings.

A raw pwc response may be restored to the bytes its own ledger entry recorded; another run file (``harness.json``)
to the bytes a schema-0 receipt, named by a ``gate_log`` entry, hashed as its input.

Each test builds a throwaway git repository with ``core.autocrlf=false`` and the ``-text`` attribute, so the bytes
git stores are exactly the bytes written. The fixture files have CRLF line endings and a non-ASCII character,
like files written on Windows.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_append_only.py"
RUN = "runs/r1"
RAW = "{\r\n  \"title\": \"Café probes\"\r\n}\r\n".encode("utf-8")
OTHER = "{\r\n  \"title\": \"Another paper\"\r\n}\r\n".encode("utf-8")

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _entry(seq: int, raw: bytes, path: str) -> bytes:
    digest = hashlib.sha256(raw).hexdigest()
    entry = {"seq": seq, "op": "paper_lookup", "output_hash": digest,
             "params": {"raw_response_path": path, "response_sha256": digest}}
    return (json.dumps(entry, sort_keys=True) + "\n").encode("utf-8")


def _check(repo: Path, *args: str) -> int:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True).returncode


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A committed run whose two lookups were stored with LF endings, so neither matches its ledger hash."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "core.autocrlf", "false")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "test")
    (tmp_path / ".gitattributes").write_bytes(b"runs/**/paper_lookups/*.json -text\n")
    lookups = tmp_path / RUN / "paper_lookups"
    lookups.mkdir(parents=True)
    (lookups / "0001.json").write_bytes(RAW.replace(b"\r\n", b"\n"))
    (lookups / "0002.json").write_bytes(OTHER.replace(b"\r\n", b"\n"))
    (tmp_path / RUN / "harness.json").write_bytes(b"{}\n")
    ledger = _entry(1, RAW, "paper_lookups/0001.json") + _entry(2, OTHER, "paper_lookups/0002.json")
    (tmp_path / RUN / "ledger.jsonl").write_bytes(ledger)
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def _stage(repo: Path, relative: str, content: bytes) -> None:
    (repo / relative).write_bytes(content)
    _git(repo, "add", "-A")


def test_restoring_the_recorded_bytes_passes_staged_and_in_ci(repo):
    _stage(repo, f"{RUN}/paper_lookups/0001.json", RAW)
    assert _check(repo) == 0
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
    _git(repo, "commit", "-qm", "restore")
    assert _check(repo, "--base", base) == 0


def test_bytes_the_ledger_never_recorded_are_refused(repo):
    _stage(repo, f"{RUN}/paper_lookups/0001.json", b"{\"title\": \"edited\"}\n")
    assert _check(repo) == 1


def test_another_lookups_bytes_are_refused(repo):
    _stage(repo, f"{RUN}/paper_lookups/0001.json", OTHER)  # hashed in the ledger, but for 0002.json
    assert _check(repo) == 1


def test_bytes_recorded_only_in_another_runs_ledger_are_refused(repo):
    (repo / "runs/r2").mkdir()
    (repo / "runs/r2/ledger.jsonl").write_bytes(_entry(1, b"new\r\n", "paper_lookups/0001.json"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "r2")
    _stage(repo, f"{RUN}/paper_lookups/0001.json", b"new\r\n")
    assert _check(repo) == 1


def test_an_entry_appended_in_the_same_change_cannot_authorise_the_rewrite(repo):
    ledger = repo / RUN / "ledger.jsonl"
    ledger.write_bytes(ledger.read_bytes() + _entry(3, b"forged\r\n", "paper_lookups/0001.json"))
    _stage(repo, f"{RUN}/paper_lookups/0001.json", b"forged\r\n")
    assert _check(repo) == 1


def test_files_outside_paper_lookups_need_a_receipt_to_be_restored(repo):
    _stage(repo, f"{RUN}/harness.json", RAW)  # bytes the ledger does record, but not for this file
    assert _check(repo) == 1


# The receipt-input exception (harness.json). HARNESS is what a gate hashed on Windows; git stored it with LF.
HARNESS = "{\r\n  \"judge\": \"Café judge\",\r\n  \"stage\": \"split\"\r\n}\r\n".encode("utf-8")


def _receipt(harness: bytes, *, schema: int | None = None) -> dict:
    """A gate receipt whose inputs hash ``harness`` for harness.json; schema 0 unless ``schema`` is given."""
    from gdkit.gates import receipt_hash

    body = {"cheap": True, "gate": "split_integrity", "gate_code_hash": "0" * 64, "ledger_head": "1" * 64,
            "run_id": "r1", "inputs": {"harness.json": hashlib.sha256(harness).hexdigest()},
            "result": {"ok": True, "passed": True}}
    if schema is not None:
        body["receipt_schema"] = schema
    body["receipt_hash"] = receipt_hash(body)
    return body


def _gate_log(receipt: dict) -> bytes:
    entry = {"seq": 3, "op": "gate_log", "params": {"gate": receipt["gate"], "inputs": ["harness.json"],
                                                    "receipt_sha256": receipt["receipt_hash"]}}
    return (json.dumps(entry, sort_keys=True) + "\n").encode("utf-8")


def _commit_receipt(repo: Path, receipt: dict | None, *, gate_log: dict | None = None) -> None:
    """Commit harness.json as LF (what git stored), the receipt, and a gate_log entry naming ``gate_log``."""
    (repo / ".gitattributes").write_bytes(b"runs/**/paper_lookups/*.json -text\nruns/**/harness.json -text\n")
    (repo / RUN / "harness.json").write_bytes(HARNESS.replace(b"\r\n", b"\n"))
    if receipt is not None:
        (repo / RUN / "receipts").mkdir(exist_ok=True)
        (repo / RUN / "receipts" / "split_integrity.json").write_bytes(json.dumps(receipt, indent=2).encode())
    if gate_log is not None:
        ledger = repo / RUN / "ledger.jsonl"
        ledger.write_bytes(ledger.read_bytes() + _gate_log(gate_log))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "receipt")


def test_restoring_the_bytes_a_logged_schema_0_receipt_hashed_passes_staged_and_in_ci(repo):
    receipt = _receipt(HARNESS)
    _commit_receipt(repo, receipt, gate_log=receipt)
    _stage(repo, f"{RUN}/harness.json", HARNESS)
    assert _check(repo) == 0
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
    _git(repo, "commit", "-qm", "restore")
    assert _check(repo, "--base", base) == 0


def test_a_schema_1_receipt_cannot_authorise_a_restore(repo):
    # Schema-1 receipts write no gate_log entry. Even with one added by hand, the rule does not trust them.
    receipt = _receipt(HARNESS, schema=1)
    _commit_receipt(repo, receipt, gate_log=receipt)
    _stage(repo, f"{RUN}/harness.json", HARNESS)
    assert _check(repo) == 1


def test_a_receipt_whose_body_no_longer_matches_its_hash_cannot_authorise(repo):
    receipt = _receipt(b"other bytes\r\n")
    _commit_receipt(repo, {**receipt, "inputs": {"harness.json": hashlib.sha256(HARNESS).hexdigest()}},
                    gate_log=receipt)  # the gate_log names the real hash; the inputs were edited afterwards
    _stage(repo, f"{RUN}/harness.json", HARNESS)
    assert _check(repo) == 1


def test_a_receipt_no_gate_log_entry_names_cannot_authorise(repo):
    _commit_receipt(repo, _receipt(HARNESS))
    _stage(repo, f"{RUN}/harness.json", HARNESS)
    assert _check(repo) == 1


def test_a_receipt_added_in_the_same_change_cannot_authorise(repo):
    receipt = _receipt(HARNESS)
    _commit_receipt(repo, None, gate_log=receipt)
    (repo / RUN / "receipts").mkdir()
    (repo / RUN / "receipts" / "split_integrity.json").write_bytes(json.dumps(receipt, indent=2).encode())
    _stage(repo, f"{RUN}/harness.json", HARNESS)
    assert _check(repo) == 1


def test_a_change_beyond_line_endings_is_refused_even_when_a_receipt_hashed_it(repo):
    edited = HARNESS.replace(b"split", b"probe")
    receipt = _receipt(edited)
    _commit_receipt(repo, receipt, gate_log=receipt)
    _stage(repo, f"{RUN}/harness.json", edited)
    assert _check(repo) == 1


def test_deleting_or_moving_a_lookup_is_refused(repo):
    (repo / RUN / "paper_lookups" / "0001.json").unlink()
    _git(repo, "add", "-A")
    assert _check(repo) == 1
    _git(repo, "reset", "-q", "--hard")
    _git(repo, "mv", f"{RUN}/paper_lookups/0002.json", "moved.json")
    assert _check(repo) == 1


def test_the_ledger_and_manifest_rules_are_unchanged(repo):
    ledger = repo / RUN / "ledger.jsonl"
    _stage(repo, f"{RUN}/ledger.jsonl", ledger.read_bytes() + b"{}\n")
    assert _check(repo) == 0
    _stage(repo, f"{RUN}/ledger.jsonl", b"{}\n")
    assert _check(repo) == 1


def test_the_split_manifest_is_written_with_lf_on_every_platform():
    """The split_build entry hashes the manifest bytes, so the writer must not use the platform's line endings."""
    import ast

    source = (SCRIPT.parents[1] / "harness" / "build_splits.py").read_text(encoding="utf-8")
    calls = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)
             and getattr(node.func, "attr", None) == "write_text" and "manifest.json" in ast.unparse(node.func)]
    assert calls, "the manifest writer was not found"
    for call in calls:
        newline = {k.arg: k.value for k in call.keywords}.get("newline")
        assert isinstance(newline, ast.Constant) and newline.value == "\n"
