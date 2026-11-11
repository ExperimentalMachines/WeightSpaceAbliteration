#!/usr/bin/env python3
"""Checks that run before a gate, and an offline audit of a run.

    python -m harness.preflight runs/<id>          # what is missing, in lifecycle order
    python -m harness.preflight runs/<id> --check  # raise on the first violation

Every check raises `ProtocolViolation`, which names its rule slug and links to the protocol section.
The checks recompute; none of them is satisfied by an entry merely existing, because an entry can
describe a state that has since changed.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from harness.protocol_rules import ProtocolViolation


def entries(run_dir: Path) -> list[dict]:
    path = run_dir / "ledger.jsonl"
    if not path.exists():
        raise ProtocolViolation("runs-append-only", run_dir, "no ledger", "freeze the run first")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def last_entry(run_dir: Path, op: str) -> dict | None:
    for entry in reversed(entries(run_dir)):
        if entry.get("op") == op:
            return entry
    return None


def host_fingerprint() -> str:
    """What makes this machine this machine, as far as the numbers are concerned."""
    parts = []
    try:
        smi = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,uuid,driver_version,memory.total,compute_cap",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=20,
        )
        parts.append(smi.stdout.strip() if smi.returncode == 0 else "nvidia-smi unavailable")
    except (OSError, subprocess.SubprocessError):
        parts.append("nvidia-smi unavailable")
    try:
        import torch

        parts.append(f"torch {torch.__version__} cuda {torch.version.cuda} cudnn {torch.backends.cudnn.version()}")
    except Exception:
        parts.append("torch unavailable")
    parts.append(f"python {sys.version.split()[0]} {sys.platform}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def require_host(run_dir: Path) -> None:
    entry = last_entry(run_dir, "host_provisioned")
    if entry is None:
        raise ProtocolViolation(
            "host-before-gates", run_dir, "no host_provisioned entry",
            f"python scripts/record_host.py --run {run_dir.as_posix()}",
        )
    recorded = entry.get("params", {}).get("fingerprint")
    current = host_fingerprint()
    if recorded is None:
        raise ProtocolViolation(
            "host-before-gates", run_dir, "host entry carries no fingerprint",
            f"python scripts/record_host.py --run {run_dir.as_posix()}",
        )
    if recorded != current:
        raise ProtocolViolation(
            "host-before-gates", run_dir,
            f"fingerprint {current[:12]} does not match the recorded {recorded[:12]}",
            f"python scripts/record_host.py --run {run_dir.as_posix()}",
        )


def ledger_stage(run_dir: Path) -> str:
    stage = "baseline"
    for entry in entries(run_dir):
        if entry.get("op") == "stage_transition":
            stage = entry.get("params", {}).get("to", stage)
    return stage


def require_stage_consistency(run_dir: Path) -> None:
    cfg_path = run_dir / "harness.json"
    if not cfg_path.exists():
        return
    declared = json.loads(cfg_path.read_text(encoding="utf-8")).get("stage", "baseline")
    actual = ledger_stage(run_dir)
    if declared != actual:
        raise ProtocolViolation(
            "stage-from-ledger", run_dir,
            f"harness.json says {declared!r}, the ledger says {actual!r}",
            "append a stage_transition entry rather than editing harness.json",
        )


def require_run_model(run_dir: Path) -> None:
    cfg_path = run_dir / "harness.json"
    scope_path = run_dir / "run_scope.json"
    if not cfg_path.exists() or not scope_path.exists():
        return
    declared = json.loads(cfg_path.read_text(encoding="utf-8")).get("model", {}).get("id")
    bound = json.loads(scope_path.read_text(encoding="utf-8")).get("model", {}).get("id")
    if declared != bound:
        raise ProtocolViolation(
            "one-model-one-run", run_dir,
            f"harness.json loads {declared!r}, this run is bound to {bound!r}",
            "a different model means a different run",
        )


def require_log_binding(run_dir: Path) -> None:
    receipts = run_dir / "receipts"
    if not receipts.exists():
        return
    bound: dict[str, str] = {}
    for entry in entries(run_dir):
        if entry.get("op") == "gate_log":
            params = entry.get("params", {})
            bound[params.get("receipt_sha256", "")] = params.get("log", "")
    for receipt_path in sorted(receipts.glob("*.json")):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        digest = receipt.get("receipt_hash", "")
        if digest not in bound:
            raise ProtocolViolation(
                "gate-log-bound", run_dir,
                f"{receipt_path.name} has no gate_log entry",
                "re-run the gate through `python -m harness.gates`",
            )
        log_path = run_dir / bound[digest]
        if not log_path.exists():
            raise ProtocolViolation(
                "gate-log-bound", run_dir, f"{bound[digest]} is missing",
                "logs are evidence; restore it from the machine that ran the gate",
            )
        entry = next(e for e in entries(run_dir)
                     if e.get("op") == "gate_log" and e["params"].get("receipt_sha256") == digest)
        actual = hashlib.sha256(log_path.read_bytes()).hexdigest()
        if actual != entry.get("output_hash"):
            raise ProtocolViolation(
                "gate-log-bound", run_dir, f"{bound[digest]} does not match its recorded hash",
                "the log was edited after the fact; that is a deviation, not a repair",
            )



def require_upstream_clear(run_dir: Path) -> None:
    """Refuse to run gates while a blocking upstream issue has no recorded workaround.

    See ``docs/upstream_issues/README.md`` and ``docs/PROVENANCE.md`` § Upstream issue recording.
    """
    for entry in entries(run_dir):
        if entry.get("op") != "upstream_issue":
            continue
        params = entry.get("params", {})
        if params.get("severity") == "blocking" and params.get("status") == "open":
            slug = params.get("slug", "<unknown>")
            raise ProtocolViolation(
                "upstream-clear", run_dir,
                f"blocking upstream issue {slug!r} has no recorded workaround (status=open)",
                "apply a workaround and record it, or downgrade severity if the assessment changed",
            )


def require_compute_evidence(run_dir: Path) -> None:
    """Refuse method admission unless compute evidence has been recorded.

    The method review checklist (``harness/methods/README.md`` §8) requires observed GPU-hours.
    This check ensures that requirement is code-enforced, not just a human checkbox.

    See ``docs/PROVENANCE.md`` § Compute evidence.
    """
    entry = last_entry(run_dir, "compute_evidence")
    if entry is None:
        raise ProtocolViolation(
            "compute-before-admission", run_dir,
            "no compute_evidence entry; the method review requires measured GPU-hours before admission",
            "run the method on the registered model, record wall-clock time and peak memory",
        )


def require_tensor_inventory(run_dir: Path) -> None:
    """Refuse method admission unless a tensor inventory has been recorded.

    The method's target list must be verified against the actual state-dict key names of the
    registered model loaded by the pinned transformers version.

    See ``docs/PROVENANCE.md`` § Tensor inventory.
    """
    entry = last_entry(run_dir, "tensor_inventory")
    if entry is None:
        raise ProtocolViolation(
            "tensor-inventory-before-admission", run_dir,
            "no tensor_inventory entry; target tensor names must be verified against the pinned model",
            "load the registered model with the pinned transformers, dump state_dict keys and shapes",
        )


def require_retroactive_dating(run_dir: Path) -> None:
    """Check that retroactively recorded entries declare themselves as such.

    An entry whose ``event_occurred_at`` differs from its ``ts`` by more than 60 seconds without
    declaring ``recorded_retroactively: true`` is a masquerade.

    See ``docs/PROVENANCE.md`` § Reconstructed events.
    """
    from datetime import datetime, timezone

    for entry in entries(run_dir):
        params = entry.get("params", {})
        event_at = params.get("event_occurred_at")
        if event_at is None:
            continue
        ts = entry.get("ts")
        if ts is None:
            continue
        try:
            event_dt = datetime.fromisoformat(event_at)
            entry_dt = datetime.fromisoformat(ts)
            if event_dt.tzinfo is None:
                event_dt = event_dt.replace(tzinfo=timezone.utc)
            if entry_dt.tzinfo is None:
                entry_dt = entry_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        delta = abs((entry_dt - event_dt).total_seconds())
        is_retro = params.get("recorded_retroactively", False)
        if delta > 60 and not is_retro:
            raise ProtocolViolation(
                "retroactive-dating", run_dir,
                f"entry seq={entry.get('seq')} has event_occurred_at {event_at} but ts {ts} "
                f"(delta {delta:.0f}s) without recorded_retroactively=true",
                "add recorded_retroactively, entry_recorded_at, and reconstruction_evidence to params",
            )
        if is_retro:
            missing = []
            if "entry_recorded_at" not in params:
                missing.append("entry_recorded_at")
            if "reconstruction_evidence" not in params:
                missing.append("reconstruction_evidence")
            if missing:
                raise ProtocolViolation(
                    "retroactive-dating", run_dir,
                    f"entry seq={entry.get('seq')} declares recorded_retroactively but lacks "
                    + ", ".join(missing),
                    "add the missing fields to the entry's params",
                )

CHECKS = (
    ("host-before-gates", require_host),
    ("stage-from-ledger", require_stage_consistency),
    ("one-model-one-run", require_run_model),
    ("gate-log-bound", require_log_binding),
    ("upstream-clear", require_upstream_clear),
    ("retroactive-dating", require_retroactive_dating),
)

ADMISSION_CHECKS = (
    ("compute-before-admission", require_compute_evidence),
    ("tensor-inventory-before-admission", require_tensor_inventory),
)

REQUIRED_ORDER = (
    ("preregistration", "the answers are frozen"),
    ("host_provisioned", "the machine is recorded"),
    ("split_build", "the split is built and hashed"),
    ("compute_evidence", "compute cost is measured (before admission)"),
    ("tensor_inventory", "target tensors verified against pinned model (before admission)"),
    ("method_selected", "a method is admitted (candidates only)"),
)


def report(run_dir: Path) -> int:
    ops = [entry.get("op") for entry in entries(run_dir)]
    print(f"run: {run_dir.as_posix()}")
    print(f"entries: {len(ops)}   stage: {ledger_stage(run_dir)}")
    print("\nlifecycle:")
    for op, description in REQUIRED_ORDER:
        mark = "present" if op in ops else "missing"
        print(f"  {mark:8s} {op:18s} {description}")
    print("\nchecks:")
    failed = 0
    for slug, check in CHECKS:
        try:
            check(run_dir)
            print(f"  pass     {slug}")
        except ProtocolViolation as exc:
            failed += 1
            print(f"  REFUSED  {slug}")
            if exc.detail:
                print(f"           {exc.detail}")
            if exc.remedy:
                print(f"           remedy: {exc.remedy}")
    return 0 if failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="harness.preflight")
    parser.add_argument("run")
    parser.add_argument("--check", action="store_true", help="raise on the first violation")
    args = parser.parse_args(argv)
    run_dir = Path(args.run)
    if args.check:
        for _, check in CHECKS:
            check(run_dir)
        print("preflight: pass")
        return 0
    return report(run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
