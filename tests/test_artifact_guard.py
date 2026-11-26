"""Temporary-run non-destruction checks; host collection is CPU metadata only."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from gdkit.ledger import Ledger, LedgerError, verify
from harness import artifact_guard as guard
from harness import gates, preflight
from harness import host as host_provenance
from scripts import record_host


MEASUREMENTS = {
    "split_integrity": [],
    "arm_counts": [],
    "exclusions_applied": [],
    "direction_derivation": ["results/direction.npz", "results/direction_derivation.json"],
    "refusal_eval": ["results/refusal_eval.json", "results/refusal_primary.jsonl",
                     "results/refusal_large.jsonl", "results/refusal_custom-arm.jsonl"],
    "judge_agreement": ["results/judge_agreement.json"],
    "over_refusal_eval": ["results/over_refusal.json"],
    "kl_divergence": ["results/kl_divergence.json"],
    "activation_extraction": ["results/activations.npz", "results/activation_extraction.json"],
    "probe_train": ["results/probe_train.json"],
    "capability_suite": ["results/lm_eval", "results/capability_suite.json"],
}
OWNED_OUTPUTS = [
    (name, relative)
    for name, measurements in MEASUREMENTS.items()
    for relative in [f"receipts/{name}.json", f"logs/{name}.log", f"logs/{name}.log.partial",
                     f"execution/{name}.json", f"failures/{name}.json", *measurements]
]


def unexpected(*args, **kwargs):
    pytest.fail("refusal must happen before preflight, model/host collection or artifact writes")


@pytest.fixture
def run_dir(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "harness.json").write_text(json.dumps({
        "refusal_eval": {"arms": ["primary", "large", "custom-arm"]},
    }), encoding="utf-8")
    return run


def write_file(run, relative, payload=b"existing partial evidence\n"):
    path = run / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def symlink(link, target, *, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")


def freeze_test_ledger(run):
    path = run / "ledger.jsonl"
    digest = hashlib.sha256(b"temporary guard fixture").hexdigest()
    Ledger(path, run.name, "registered").record(
        "preregistration", rows_before=0, rows_after=0,
        input_hash=digest, output_hash=digest,
    )
    return path


@pytest.mark.parametrize("name,relative", OWNED_OUTPUTS)
def test_each_owned_output_blocks_before_preflight_or_model(run_dir, monkeypatch, name, relative):
    path = write_file(run_dir, relative)
    before = path.read_bytes()
    for check in ("require_host", "require_stage_consistency", "require_run_model"):
        monkeypatch.setattr(preflight, check, unexpected)
    monkeypatch.setattr(gates, "_load_model", unexpected)
    assert gates.main(["--run", str(run_dir), "--gate", name]) == 1
    assert path.read_bytes() == before
    assert not (run_dir / guard.LOCK_NAME).exists()
    assert not (run_dir / "ledger.jsonl").exists()


def test_empty_capability_directory_is_occupied(run_dir):
    (run_dir / "results" / "lm_eval").mkdir(parents=True)
    with pytest.raises(guard.ArtifactConflict, match="existing artifact"):
        guard.require_fresh_gates(run_dir, ["capability_suite"])


@pytest.mark.parametrize("relative", ["receipts/refusal_eval.json", "logs/refusal_eval.log.partial",
                                      "results/refusal_custom-arm.jsonl"])
def test_directory_at_file_output_is_occupied(run_dir, relative):
    (run_dir / relative).mkdir(parents=True)
    with pytest.raises(guard.ArtifactConflict, match="existing artifact"):
        guard.require_fresh_gates(run_dir, ["refusal_eval"])


def test_shared_directories_and_unrelated_gate_outputs_are_allowed(run_dir):
    for parent in ("receipts", "logs", "results"):
        (run_dir / parent).mkdir()
    original = write_file(run_dir, "results/probe_train.json")
    write_file(run_dir, "logs/probe_train.log.partial")
    write_file(run_dir, "receipts/probe_train.json")
    guard.require_fresh_gates(run_dir, ["direction_derivation", "arm_counts"])
    assert original.read_bytes() == b"existing partial evidence\n"
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_refusal_default_arms_are_discovered_without_configuration(run_dir):
    (run_dir / "harness.json").unlink()
    write_file(run_dir, "results/refusal_large.jsonl")
    with pytest.raises(guard.ArtifactConflict, match="refusal_large"):
        guard.require_fresh_gates(run_dir, ["refusal_eval"])


@pytest.mark.parametrize("arm", ["", ".", "..", "../escape", "a/b", "a\\b", "C:escape", "/absolute",
                                "name.jsonl", "space arm", "CON", None, 1])
def test_unsafe_configured_arms_refused_before_lock(run_dir, arm):
    (run_dir / "harness.json").write_text(json.dumps({"refusal_eval": {"arms": [arm]}}), encoding="utf-8")
    with pytest.raises(guard.ArtifactConflict, match="unsafe refusal arm"):
        with guard.gate_write_guard(run_dir, ["refusal_eval"]):
            unexpected()
    assert not (run_dir / guard.LOCK_NAME).exists()
    assert not (run_dir / "results").exists()


@pytest.mark.parametrize("arms", ["primary", None, {}, ["primary", "primary"], ["primary", "PRIMARY"]])
def test_malformed_or_duplicate_arm_lists_refused(run_dir, arms):
    (run_dir / "harness.json").write_text(json.dumps({"refusal_eval": {"arms": arms}}), encoding="utf-8")
    with pytest.raises(guard.ArtifactConflict):
        guard.require_fresh_gates(run_dir, ["refusal_eval"])


@pytest.mark.parametrize("names", [["unknown"], ["split_integrity", "unknown"],
                                  ["split_integrity", "split_integrity"], ["../escape"], []])
def test_unknown_duplicate_and_unsafe_gate_names_refused_without_writes(run_dir, names):
    before = set(run_dir.iterdir())
    with pytest.raises(guard.ArtifactConflict):
        with guard.gate_write_guard(run_dir, names):
            unexpected()
    assert set(run_dir.iterdir()) == before


@pytest.mark.parametrize("broken", [False, True])
def test_existing_symlink_output_is_occupied(run_dir, tmp_path, broken):
    target = tmp_path / "target"
    if not broken:
        target.write_bytes(b"do not change\n")
    (run_dir / "results").mkdir()
    symlink(run_dir / "results" / "direction.npz", target)
    with pytest.raises(guard.ArtifactConflict, match="existing artifact"):
        guard.require_fresh_gates(run_dir, ["direction_derivation"])
    if not broken:
        assert target.read_bytes() == b"do not change\n"


@pytest.mark.parametrize("parent", ["results", "logs", "receipts"])
def test_symlink_output_parents_refused(run_dir, tmp_path, parent):
    target = tmp_path / "elsewhere"
    target.mkdir()
    symlink(run_dir / parent, target, directory=True)
    with pytest.raises(guard.ArtifactConflict, match="unsafe artifact parent"):
        with guard.gate_write_guard(run_dir, ["direction_derivation"]):
            unexpected()
    assert list(target.iterdir()) == []
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_symlink_run_or_ancestor_refused(run_dir, tmp_path):
    alias = tmp_path / "alias"
    symlink(alias, run_dir, directory=True)
    with pytest.raises(guard.ArtifactConflict, match="unsafe artifact parent"):
        guard.require_fresh_gates(alias, ["arm_counts"])
    container_alias = tmp_path / "container-alias"
    symlink(container_alias, tmp_path, directory=True)
    with pytest.raises(guard.ArtifactConflict, match="unsafe artifact parent"):
        guard.require_fresh_gates(container_alias / run_dir.name, ["arm_counts"])


def test_non_directory_parent_and_traversal_refused(run_dir):
    write_file(run_dir, "logs")
    with pytest.raises(guard.ArtifactConflict, match="unsafe artifact parent"):
        guard.require_fresh_gates(run_dir, ["arm_counts"])
    with pytest.raises(guard.ArtifactConflict, match="unsafe run path"):
        guard.require_fresh_gates(run_dir / ".." / run_dir.name, ["arm_counts"])


def test_symlink_configuration_refused(run_dir, tmp_path):
    (run_dir / "harness.json").unlink()
    target = write_file(tmp_path, "external.json", b'{"refusal_eval":{"arms":["primary"]}}')
    symlink(run_dir / "harness.json", target)
    with pytest.raises(guard.ArtifactConflict, match="unsafe harness configuration"):
        guard.require_fresh_gates(run_dir, ["refusal_eval"])


def test_lock_reentrancy_and_contender_cannot_overwrite_owner(run_dir):
    lock = run_dir / guard.LOCK_NAME
    with guard.run_write_lock(run_dir):
        token = lock.read_bytes()
        with pytest.raises(guard.ArtifactConflict, match="writer lock"):
            with guard.run_write_lock(run_dir):
                unexpected()

        def contend():
            with pytest.raises(guard.ArtifactConflict, match="writer lock"):
                with guard.gate_write_guard(run_dir, ["arm_counts"]):
                    unexpected()

        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(contend).result()
        assert lock.read_bytes() == token
    assert not lock.exists()
    with guard.run_write_lock(run_dir):
        assert lock.exists()
    assert not lock.exists()


@pytest.mark.parametrize("as_directory", [False, True])
def test_preexisting_stale_lock_is_preserved(run_dir, as_directory):
    lock = run_dir / guard.LOCK_NAME
    if as_directory:
        lock.mkdir()
    else:
        lock.write_bytes(b"old writer\n")
    with pytest.raises(guard.ArtifactConflict, match="writer lock"):
        with guard.run_write_lock(run_dir):
            unexpected()
    assert lock.is_dir() if as_directory else lock.read_bytes() == b"old writer\n"


def test_broken_symlink_lock_is_preserved(run_dir, tmp_path):
    lock = run_dir / guard.LOCK_NAME
    symlink(lock, tmp_path / "missing-lock-target")
    with pytest.raises(guard.ArtifactConflict, match="writer lock"):
        with guard.run_write_lock(run_dir):
            unexpected()
    assert lock.is_symlink()


def test_lock_cleanup_preserves_partial_outputs_on_execution_failure(run_dir):
    with pytest.raises(RuntimeError, match="gate failed"):
        with guard.gate_write_guard(run_dir, ["direction_derivation"]):
            write_file(run_dir, "results/direction.npz", b"partial measurement")
            raise RuntimeError("gate failed")
    assert not (run_dir / guard.LOCK_NAME).exists()
    assert (run_dir / "results/direction.npz").read_bytes() == b"partial measurement"
    with pytest.raises(guard.ArtifactConflict, match="existing artifact"):
        guard.require_fresh_gates(run_dir, ["direction_derivation"])


def test_lock_cleanup_when_locked_recheck_fails(run_dir, monkeypatch):
    real_check = guard.require_fresh_gates
    calls = 0

    def raced_check(run, names):
        nonlocal calls
        calls += 1
        if calls == 2:
            write_file(run, "logs/arm_counts.log.partial", b"other evidence")
        real_check(run, names)

    monkeypatch.setattr(guard, "require_fresh_gates", raced_check)
    with pytest.raises(guard.ArtifactConflict, match="existing artifact"):
        with guard.gate_write_guard(run_dir, ["arm_counts"]):
            unexpected()
    assert not (run_dir / guard.LOCK_NAME).exists()
    assert (run_dir / "logs/arm_counts.log.partial").read_bytes() == b"other evidence"


@pytest.mark.parametrize("mode", ["--smoke", "--dry-run"])
def test_read_only_gate_modes_do_not_acquire_guard(run_dir, monkeypatch, mode):
    write_file(run_dir, "splits/manifest.json", b"{}")
    write_file(run_dir, "logs/arm_counts.log", b"old log\n")
    monkeypatch.setattr(gates, "gate_write_guard", unexpected)
    gates.main(["--run", str(run_dir), mode])
    assert (run_dir / "logs/arm_counts.log").read_bytes() == b"old log\n"
    assert not (run_dir / guard.LOCK_NAME).exists()


@pytest.mark.parametrize("kind", ["file", "directory", "broken-symlink"])
def test_existing_host_refused_before_collect_or_ledger_mutation(run_dir, tmp_path, monkeypatch, kind):
    ledger = freeze_test_ledger(run_dir)
    before = ledger.read_bytes()
    host = run_dir / "host.json"
    if kind == "file":
        host.write_bytes(b"existing host\n")
    elif kind == "directory":
        host.mkdir()
    else:
        symlink(host, tmp_path / "missing-host")
    monkeypatch.setattr(host_provenance, "collect_session_host", unexpected)
    monkeypatch.setattr(Ledger, "record", unexpected)
    assert record_host.main(["--run", str(run_dir)]) == 1
    assert ledger.read_bytes() == before
    assert not (run_dir / guard.LOCK_NAME).exists()
    if kind == "file":
        assert host.read_bytes() == b"existing host\n"
    elif kind == "directory":
        assert host.is_dir()
    else:
        assert host.is_symlink()


@pytest.mark.parametrize("kind", ["missing", "empty", "corrupt", "unterminated", "symlink"])
def test_invalid_existing_ledger_refused_before_host_collection(run_dir, tmp_path, monkeypatch, kind):
    ledger = run_dir / "ledger.jsonl"
    if kind == "empty":
        ledger.write_bytes(b"")
    elif kind == "corrupt":
        ledger.write_bytes(b'{"seq": 0, "entry_hash": "bad"}\n')
    elif kind == "unterminated":
        freeze_test_ledger(run_dir)
        ledger.write_bytes(ledger.read_bytes().rstrip(b"\n"))
    elif kind == "symlink":
        target = tmp_path / "other-run"
        target.mkdir()
        symlink(ledger, freeze_test_ledger(target))
    before = ledger.read_bytes() if ledger.exists() else None
    monkeypatch.setattr(host_provenance, "collect_session_host", unexpected)
    assert record_host.main(["--run", str(run_dir)]) == 1
    assert (ledger.read_bytes() if ledger.exists() else None) == before
    assert not (run_dir / "host.json").exists()
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_host_creation_is_byte_exact_and_ledger_append_only(run_dir, monkeypatch):
    ledger = freeze_test_ledger(run_dir)
    before = ledger.read_bytes()
    real_collect = host_provenance.collect_session_host

    def collect(**kwargs):
        assert (run_dir / guard.LOCK_NAME).is_file()
        with pytest.raises(guard.ArtifactConflict):
            with guard.run_write_lock(run_dir):
                unexpected()
        return real_collect(**kwargs)

    monkeypatch.setattr(host_provenance, "collect_session_host", collect)
    assert record_host.main(["--run", str(run_dir)]) == 0
    entry = json.loads(ledger.read_bytes().splitlines()[-1])
    params = entry["params"]
    host = (run_dir / params["path"]).read_bytes()
    record = json.loads(host)
    assert host == (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    assert ledger.read_bytes().startswith(before)
    assert verify(ledger) == 2
    assert entry["op"] == "host" and entry["event"] is True
    assert entry["output_hash"] == params["sha256"] == hashlib.sha256(host).hexdigest()
    raw = (run_dir / params["raw"]["path"]).read_bytes()
    assert entry["input_hash"] == params["raw"]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert not (run_dir / "host.json").exists()
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_host_exclusive_create_preserves_racing_host_and_ledger(run_dir, monkeypatch):
    ledger = freeze_test_ledger(run_dir)
    before = ledger.read_bytes()
    real_collect = host_provenance.collect_session_host

    def collect(**kwargs):
        write_file(run_dir, "host.json", b"racing writer evidence\n")
        return real_collect(**kwargs)

    monkeypatch.setattr(host_provenance, "collect_session_host", collect)
    assert record_host.main(["--run", str(run_dir)]) == 1
    assert (run_dir / "host.json").read_bytes() == b"racing writer evidence\n"
    assert ledger.read_bytes() == before
    assert not (run_dir / "hosts").exists()
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_host_record_is_preserved_if_ledger_append_fails(run_dir, monkeypatch):
    ledger = freeze_test_ledger(run_dir)
    before = ledger.read_bytes()

    def fail_append(*args, **kwargs):
        raise LedgerError("append refused")

    monkeypatch.setattr(Ledger, "record", fail_append)
    assert record_host.main(["--run", str(run_dir)]) == 1
    hosts = list((run_dir / "hosts").glob("*.json"))
    assert len(hosts) == 1
    record = json.loads(hosts[0].read_bytes())
    raw = (run_dir / record["raw"]["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == record["raw"]["sha256"]
    original = hosts[0].read_bytes()
    assert record_host.main(["--run", str(run_dir)]) == 1
    assert hosts[0].read_bytes() == original
    assert ledger.read_bytes() == before
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_collection_failure_does_not_create_host_or_change_ledger(run_dir, monkeypatch):
    ledger = freeze_test_ledger(run_dir)
    before = ledger.read_bytes()

    def fail_collect(**kwargs):
        raise RuntimeError("collection failed")

    monkeypatch.setattr(host_provenance, "collect_session_host", fail_collect)
    with pytest.raises(RuntimeError, match="collection failed"):
        record_host.main(["--run", str(run_dir)])
    assert not (run_dir / "hosts").exists()
    assert ledger.read_bytes() == before
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_host_dry_run_remains_read_only_even_with_existing_host(run_dir, monkeypatch):
    host = write_file(run_dir, "host.json", b"original host\n")
    ledger = write_file(run_dir, "ledger.jsonl", b"invalid existing ledger\n")
    monkeypatch.setattr(record_host, "record_session_host", unexpected)
    assert record_host.main(["--run", str(run_dir), "--dry-run"]) == 0
    assert host.read_bytes() == b"original host\n"
    assert ledger.read_bytes() == b"invalid existing ledger\n"
    assert not (run_dir / "hosts").exists()
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_direct_host_script_import_and_refusal_from_other_directory(run_dir, tmp_path):
    host = write_file(run_dir, "host.json", b"original host\n")
    script = Path(record_host.__file__).resolve()
    proc = subprocess.run([sys.executable, str(script), "--run", str(run_dir)],
                          cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "refusing to replace existing artifact" in proc.stderr
    assert host.read_bytes() == b"original host\n"
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_injected_registry_gate_without_output_contract_is_refused(run_dir, monkeypatch):
    monkeypatch.setitem(gates.REGISTRY, "toy", object())
    with pytest.raises(guard.ArtifactConflict, match="unknown"):
        with guard.gate_write_guard(run_dir, ["toy"]):
            unexpected()
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_lock_cleanup_does_not_remove_replaced_owner_token(run_dir):
    lock = run_dir / guard.LOCK_NAME
    with guard.run_write_lock(run_dir):
        lock.write_bytes(b"replacement owner\n")
    assert lock.read_bytes() == b"replacement owner\n"


def test_host_contender_refused_before_collection(run_dir, monkeypatch):
    ledger = freeze_test_ledger(run_dir)
    before = ledger.read_bytes()
    monkeypatch.setattr(host_provenance, "collect_session_host", unexpected)
    with guard.run_write_lock(run_dir):
        token = (run_dir / guard.LOCK_NAME).read_bytes()
        assert record_host.main(["--run", str(run_dir)]) == 1
        assert (run_dir / guard.LOCK_NAME).read_bytes() == token
    assert ledger.read_bytes() == before
    assert not (run_dir / "host.json").exists()
    assert not (run_dir / guard.LOCK_NAME).exists()


def test_host_refuses_changed_ledger_before_creating_host(run_dir, monkeypatch):
    ledger = freeze_test_ledger(run_dir)
    original = ledger.read_bytes()

    real_collect = host_provenance.collect_session_host

    def collect(**kwargs):
        ledger.write_bytes(original + b"concurrent evidence\n")
        return real_collect(**kwargs)

    monkeypatch.setattr(host_provenance, "collect_session_host", collect)
    assert record_host.main(["--run", str(run_dir)]) == 1
    assert ledger.read_bytes() == original + b"concurrent evidence\n"
    assert not (run_dir / "host.json").exists()
    assert not (run_dir / guard.LOCK_NAME).exists()
