"""The append-only check's one exception: restoring a raw pwc response to the bytes its own entry recorded.

Each test builds a throwaway git repository with ``core.autocrlf=false`` and the ``-text`` attribute, so the bytes
git stores are exactly the bytes written. The fixture response has CRLF line endings and a non-ASCII character,
like a pwc response written on Windows.
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


def test_files_outside_paper_lookups_get_no_exception(repo):
    _stage(repo, f"{RUN}/harness.json", RAW)  # bytes the ledger does record, but not for this file
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
