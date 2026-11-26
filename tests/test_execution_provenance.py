"""Tiny CPU-only filesystem/ledger/receipt fixtures; no model or registered-run writes."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from harness.releases import RUNTIME_FILES, build_release


TOY_GATES = '''from __future__ import annotations
import json
from pathlib import Path
from harness.execution import register_module

PROMPT = "original fixture helper constant"

def helper(value):
    return value + " checked"

def toy(run_dir: Path):
    cfg = json.loads((run_dir / "harness.json").read_text())
    value = (run_dir / "input.txt").read_text()
    print("fixture started", flush=True)
    if cfg.get("fail"):
        raise RuntimeError("fixture interrupted")
    if cfg.get("interrupt"):
        raise KeyboardInterrupt("fixture interrupted")
    if cfg.get("mutate_input"):
        (run_dir / "input.txt").write_text("changed")
    if cfg.get("mutate_helper"):
        helper.__code__ = replacement.__code__
    if cfg.get("mutate_constant"):
        globals()["PROMPT"] = "changed"
    if cfg.get("mutate_host"):
        manifest = json.loads((run_dir / "execution/toy.json").read_text())
        path = run_dir / manifest["host"]["path"]
        path.write_bytes(path.read_bytes() + b"changed")
    if not cfg.get("missing"):
        (run_dir / "results").mkdir(exist_ok=True)
        (run_dir / "results" / "out.txt").write_text(helper(value))
    if cfg.get("directory"):
        (run_dir / "results" / "nested").mkdir()
        (run_dir / "results" / "nested" / "item.txt").write_text("nested output")
    return {"passed": not cfg.get("failed_result", False), "ok": True}

def replacement(value):
    return value + " REPLACED"

register_module(__name__)
'''

DRIVER = '''import hashlib, json, sys
from pathlib import Path
from gdkit.gates import Gate
from gdkit.ledger import Ledger
from gdkit.prereg import freeze_run
from harness import gates
from harness.execution import run_bound_gate, verify_execution
from harness.artifact_guard import run_write_lock
from harness.host import record_session_host
source, release, run = map(Path, sys.argv[1:4])
operation = sys.argv[4]
if operation == "execute":
    project = run.parent / "project.yaml"
    project.write_text("study_question: fixture\\n")
    if not (run / "ledger.jsonl").exists():
        freeze_run(Ledger(run / "ledger.jsonl", run.name, "registered"), project)
        record_session_host(run)
    head = json.loads((run / "ledger.jsonl").read_text().splitlines()[-1])["entry_hash"]
    cfg = json.loads((run / "harness.json").read_text())
    if cfg.get("pre_mutate_helper"):
        gates.helper = gates.replacement
    if cfg.get("pre_mutate_constant"):
        gates.PROMPT = "changed"
    outputs = ["results/out.txt"] + (["results/nested"] if cfg.get("directory") else [])
    try:
        with run_write_lock(run):
            path = run_bound_gate(run, Gate("toy", True, gates.toy), release_dir=release,
                                  source_root=source, inputs=["harness.json", "input.txt"],
                                  outputs=outputs, run_id=run.name, ledger_head=head)
        result = json.loads(path.read_text())["result"]
        print(json.dumps({"receipt": str(path), "passed": result["passed"]}))
        sys.exit(0 if result["passed"] else 1)
    except Exception as exc:
        print(type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        sys.exit(1)
if operation == "stale":
    digest = hashlib.sha256(b"fixture-note").hexdigest()
    Ledger(run / "ledger.jsonl", run.name, "registered").record_event(
        "fixture-note", input_hash=digest, output_hash=digest)
report = verify_execution(run, run / "receipts/toy.json",
                          release_dir=None if operation == "no-release" else release,
                          source_root=source if operation == "source" else None)
print(json.dumps(report))
'''


@pytest.fixture
def fixture_tree(tmp_path):
    """Real release payload, imported in a separate interpreter for registry isolation."""
    repository = Path(__file__).resolve().parents[1]
    source = tmp_path / "source"
    source.mkdir()
    for relative in RUNTIME_FILES:
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / relative, target)
    (source / "harness/gates.py").write_text(TOY_GATES, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "core.hooksPath=", "commit", "--allow-empty", "-qm", "fixture root"], check=True)
    release = build_release(source, tmp_path / "releases", working_tree=True)
    run = tmp_path / "fixture-run"
    run.mkdir()
    (run / "input.txt").write_text("tiny input", encoding="utf-8")
    (run / "harness.json").write_text("{}", encoding="utf-8")
    driver = tmp_path / "driver.py"
    driver.write_text(DRIVER, encoding="utf-8")

    def invoke(operation="execute", *, check=False, hash_seed=None):
        env = {**os.environ, "PYTHONPATH": str(source)}
        # This fixture is explicitly local, even if the parent shell retains runner variables.
        for name in ("WSA_EXECUTION_KIND", "WSA_RELEASE_ID", "WSA_IMAGE_ID"):
            env.pop(name, None)
        if hash_seed is not None:
            env["PYTHONHASHSEED"] = str(hash_seed)
        result = subprocess.run([sys.executable, str(driver), str(source), str(release), str(run), operation],
                                cwd=source, env=env, capture_output=True, text=True)
        if check and result.returncode:
            pytest.fail(f"fixture subprocess failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
        return result

    return source, release, run, invoke


def _configure(run, **values):
    (run / "harness.json").write_text(json.dumps(values), encoding="utf-8")


def _report(invoke, operation="verify"):
    proc = invoke(operation, check=True)
    return json.loads(proc.stdout)


def test_bound_receipt_uses_real_log_inputs_outputs_and_runtime(fixture_tree):
    source, release, run, invoke = fixture_tree
    invoke(check=True)
    receipt = json.loads((run / "receipts/toy.json").read_text())
    assert receipt["receipt_schema"] == 1 and receipt["contract_version"] == 3
    assert set(receipt["inputs"]) == {"execution/toy.json", "harness.json", "input.txt"}
    assert set(receipt["result"]["artifacts"]) == {"results/out.txt"}
    assert b"fixture started" in (run / "logs/toy.log").read_bytes()
    manifest = json.loads((run / "execution/toy.json").read_text())
    assert manifest["runtime"]["kind"] == "local-process"
    assert manifest["runtime"]["modal_image_identity"] is None
    assert manifest["host"]["checked"] is True
    assert _report(invoke)["validity"] == "valid"
    assert _report(invoke, "source")["execution_identity"] == "release-bound"
    assert _report(invoke, "no-release")["validity"] == "incomplete"


@pytest.mark.parametrize("relative", ["input.txt", "results/out.txt", "logs/toy.log", "execution/toy.json"])
def test_input_output_log_and_manifest_mutations_are_invalid(fixture_tree, relative):
    _, _, run, invoke = fixture_tree
    invoke(check=True)
    path = run / relative
    path.write_bytes(path.read_bytes() + b"changed")
    assert _report(invoke)["validity"] == "invalid"


def test_host_record_mutation_is_invalid_without_collecting_auditor_host(fixture_tree):
    _, _, run, invoke = fixture_tree
    invoke(check=True)
    manifest = json.loads((run / "execution/toy.json").read_text())
    host = run / manifest["host"]["path"]
    host.write_bytes(host.read_bytes() + b"changed")
    assert _report(invoke)["validity"] == "invalid"


def test_mutable_source_detected_only_when_current_source_requested(fixture_tree):
    source, _, _, invoke = fixture_tree
    invoke(check=True)
    path = source / "harness/gates.py"
    path.write_text(path.read_text() + "\n# later mutable working copy\n")
    assert _report(invoke)["validity"] == "valid"  # archived release still available
    assert _report(invoke, "source")["validity"] == "invalid"


def test_mutated_available_release_never_validates_identity(fixture_tree):
    _, release, _, invoke = fixture_tree
    invoke(check=True)
    path = release / "harness/gates.py"
    path.write_bytes(path.read_bytes() + b"\n# changed snapshot\n")
    assert _report(invoke)["validity"] == "invalid"


@pytest.mark.parametrize("flag", ["fail", "interrupt", "missing", "mutate_input", "mutate_helper", "mutate_constant", "mutate_host"])
def test_exception_or_mid_execution_mutation_keeps_failure_evidence(fixture_tree, flag):
    _, _, run, invoke = fixture_tree
    _configure(run, **{flag: True})
    assert invoke().returncode != 0
    assert not (run / "receipts/toy.json").exists()
    failure = json.loads((run / "failures/toy.json").read_text())
    assert failure["status"] == "execution-failed" and failure["log"]["sha256"]
    assert b"Traceback" in (run / "logs/toy.log").read_bytes()
    before = {p.relative_to(run): p.read_bytes() for p in run.rglob("*") if p.is_file()}
    assert invoke().returncode != 0
    assert {p.relative_to(run): p.read_bytes() for p in run.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("flag", ["pre_mutate_helper", "pre_mutate_constant"])
def test_in_memory_helper_and_constant_replacement_refused_before_execution(fixture_tree, flag):
    _, _, run, invoke = fixture_tree
    _configure(run, **{flag: True})
    assert invoke().returncode != 0
    assert not (run / "receipts/toy.json").exists()
    assert not (run / "results/out.txt").exists()


def test_directory_closure_detects_added_and_missing_outputs(fixture_tree):
    _, _, run, invoke = fixture_tree
    _configure(run, directory=True)
    invoke(check=True)
    assert _report(invoke)["validity"] == "valid"
    (run / "results/nested/extra.txt").write_text("unexpected")
    assert _report(invoke)["validity"] == "invalid"
    (run / "results/nested/extra.txt").unlink()
    (run / "results/out.txt").unlink()
    assert _report(invoke)["validity"] == "invalid"


def test_failed_check_has_honest_failed_receipt(fixture_tree):
    _, _, run, invoke = fixture_tree
    _configure(run, failed_result=True)
    assert invoke().returncode != 0
    receipt = json.loads((run / "receipts/toy.json").read_text())
    assert receipt["result"]["passed"] is False
    assert _report(invoke)["validity"] == "valid"  # provenance validity is not a passing scientific result


def test_stale_classification_does_not_rewrite_history(fixture_tree):
    _, _, run, invoke = fixture_tree
    invoke(check=True)
    receipt = run / "receipts/toy.json"
    before = receipt.read_bytes()
    report = _report(invoke, "stale")
    assert report["validity"] == "valid" and report["currentness"] == "stale"
    assert receipt.read_bytes() == before


def test_verifier_cli_is_read_only_and_freshness_is_optional(fixture_tree):
    source, release, run, invoke = fixture_tree
    invoke(check=True)
    command = [sys.executable, str(source / "scripts/verify_execution.py"),
               "--run", str(run), "--receipt", "receipts/toy.json", "--release", str(release)]
    before = {p.relative_to(run): p.read_bytes() for p in run.rglob("*") if p.is_file()}
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["validity"] == "valid"
    assert {p.relative_to(run): p.read_bytes() for p in run.rglob("*") if p.is_file()} == before
    _report(invoke, "stale")
    proc = subprocess.run([*command, "--require-current"], capture_output=True, text=True)
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["currentness"] == "stale"


def test_configured_refusal_and_dependent_input_closures(tmp_path):
    from harness.gates import gate_artifacts

    run = tmp_path / "run"
    (run / "splits").mkdir(parents=True)
    (run / "results").mkdir()
    (run / "harness.json").write_text(json.dumps({
        "refusal_eval": {"arms": ["custom"]}, "probe": {"neg_arm": "negative-custom"},
    }))
    (run / "splits/manifest.json").write_text("{}")
    for relative in ("splits/custom.jsonl", "splits/negative-custom.jsonl", "splits/primary.jsonl",
                     "results/activations.npz", "results/refusal_primary.jsonl"):
        (run / relative).write_bytes(b"fixture")
    inputs, outputs = gate_artifacts(run, "refusal_eval")
    assert inputs == ["harness.json", "splits/custom.jsonl", "splits/manifest.json"]
    assert outputs == ["results/refusal_custom.jsonl", "results/refusal_eval.json"]
    assert "splits/negative-custom.jsonl" in gate_artifacts(run, "probe_train")[0]
    assert "results/activations.npz" in gate_artifacts(run, "probe_train")[0]
    assert "splits/primary.jsonl" in gate_artifacts(run, "judge_agreement")[0]
    assert "results/lm_eval" in gate_artifacts(run, "capability_suite")[1]


def test_actual_local_gate_cli_binds_release_and_host_without_loading_models(tmp_path):
    from gdkit.ledger import Ledger
    from gdkit.prereg import freeze_run
    from harness import gates
    from harness.execution import verify_execution
    from harness.host import record_session_host

    repository = Path(__file__).resolve().parents[1]
    release = build_release(repository, tmp_path / "releases", working_tree=True)
    run = tmp_path / "fixture"
    (run / "splits").mkdir(parents=True)
    project = tmp_path / "project.yaml"
    project.write_text("study_question: fixture\n")
    freeze_run(Ledger(run / "ledger.jsonl", "fixture", "registered"), project)
    (run / "harness.json").write_text("{}")
    counts = {"derivation": 415, "harmless": 415, "primary": 293, "large": 15640,
              "enriched": 6836, "treadon": 158, "zaakirio": 432, "harmbench_val": 80,
              "over_refusal": 1569, "probe_neg": 1569, "probe_pos": 201, "probe_heldout": 92}
    (run / "splits/manifest.json").write_text(json.dumps({"arms": {key: {"count": value} for key, value in counts.items()}}))
    record_session_host(run)
    assert gates.main(["--run", str(run), "--gate", "arm_counts", "--release", str(release)]) == 0
    path = run / "receipts/arm_counts.json"
    assert verify_execution(run, path, release_dir=release)["validity"] == "valid"
    before = path.read_bytes()
    assert gates.main(["--run", str(run), "--gate", "arm_counts"]) == 1
    assert path.read_bytes() == before
    # A model-consuming gate must refuse before loading anything when identity is absent.
    (run / "splits/derivation.jsonl").write_text("")
    (run / "splits/harmless.jsonl").write_text("")
    assert gates.main(["--run", str(run), "--gate", "direction_derivation", "--release", str(release)]) == 1
    assert not (run / "execution/direction_derivation.json").exists()
    assert not (run / "results/direction.npz").exists()
    # An explicit mutable branch is not a pinned identity either.
    (run / "harness.json").write_text(json.dumps({"model": {"id": "fixture", "revision": "main"}}))
    assert gates.main(["--run", str(run), "--gate", "direction_derivation", "--release", str(release)]) == 1
    assert not (run / "execution/direction_derivation.json").exists()
    assert not (run / "results/direction.npz").exists()


def test_historical_verification_is_independent_of_auditor_hash_seed(fixture_tree):
    _, _, _, invoke = fixture_tree
    invoke(check=True, hash_seed=1)
    audited = invoke("verify", check=True, hash_seed=91)
    assert json.loads(audited.stdout)["validity"] == "valid"
