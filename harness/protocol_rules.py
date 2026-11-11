"""Rule registry: one slug per protocol rule, with the document anchor that governs it.

A refusal names a slug and links to its section, so the message locates the rule rather than
describing it again. Prose and code stay two views of one thing: `docs/protocol/RUN_PROTOCOL.md`
carries the rule table, and every slug raised here must have an anchor there.

    from harness.protocol_rules import ProtocolViolation

    raise ProtocolViolation("host-before-gates", run_dir, detail="fingerprint 3f9a != 77c1")
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path

PROTOCOL = "docs/protocol/RUN_PROTOCOL.md"
DEVIATION = "docs/protocol/RUN_PROTOCOL.md#deviations"


@dataclass(frozen=True)
class Rule:
    slug: str
    statement: str
    enforced_by: str


RULES: dict[str, Rule] = {
    rule.slug: rule
    for rule in (
        Rule(
            "host-before-gates",
            "A gate may run only if the run holds a host_provisioned entry whose fingerprint "
            "matches the machine running now.",
            "harness/preflight.py:require_host",
        ),
        Rule(
            "admission-before-candidate",
            "A candidate may be evaluated only after a method_selected entry exists for the run.",
            "harness/gates.py:require_admitted",
        ),
        Rule(
            "stage-from-ledger",
            "The stage is what the ledger says it is; harness.json is a cache that must agree.",
            "harness/preflight.py:require_stage_consistency",
        ),
        Rule(
            "one-model-one-run",
            "A run binds exactly one model, recorded at its start; it may not load another.",
            "harness/preflight.py:require_run_model",
        ),
        Rule(
            "gate-log-bound",
            "Every receipt's log exists and matches its recorded hash: in the receipt (schema 1) or in its "
            "gate_log entry (schema 0, before gdkit fa1e4d5).",
            "harness/preflight.py:require_log_binding",
        ),
        Rule(
            "runs-append-only",
            "Ledgers may only grow; receipts, logs and attestations may be added, never edited.",
            ".githooks/pre-commit",
        ),
        Rule(
            "no-hand-hashes",
            "Hashes are computed from files by the tooling, never written by hand.",
            "tools/README.md",
        ),
        Rule(
            "shared-freeze",
            "All runs carry the same pre-registration digest and the same split-manifest hash.",
            "scripts/verify_ledger.py",
        ),
        Rule(
            "upstream-clear",
            "A gate may not run while a blocking upstream issue has no recorded workaround.",
            "harness/preflight.py:require_upstream_clear",
        ),
        Rule(
            "compute-before-admission",
            "A method may not be admitted until compute evidence (GPU-hours, peak memory) is recorded.",
            "harness/preflight.py:require_compute_evidence",
        ),
        Rule(
            "tensor-inventory-before-admission",
            "A method may not be admitted until target tensor names are verified against the pinned model.",
            "harness/preflight.py:require_tensor_inventory",
        ),
        Rule(
            "retroactive-dating",
            "An entry recorded after its event must declare recorded_retroactively with evidence.",
            "harness/preflight.py:require_retroactive_dating",
        ),
    )
}


class ProtocolViolation(RuntimeError):
    """A refusal that names its rule, its location, the command that satisfies it, and the protocol."""

    def __init__(self, slug: str, run_dir: Path | str, detail: str = "", remedy: str = "") -> None:
        rule = RULES.get(slug)
        if rule is None:
            raise KeyError(f"unknown protocol rule {slug!r}; add it to harness/protocol_rules.py")
        lines = [f"ProtocolViolation[{slug}]: {rule.statement}"]
        if detail:
            lines.append(f"  detail: {detail}")
        lines.append(f"  run:    {run_dir}")
        if remedy:
            lines.append(f"  remedy: {remedy}")
        lines.append(f"  rule:   {PROTOCOL}#{slug}")
        lines.append(f"  if this refusal is wrong: {DEVIATION}")
        super().__init__("\n".join(textwrap.fill(line, 110) if len(line) > 110 else line for line in lines))
        self.slug = slug
        self.detail = detail
        self.remedy = remedy
