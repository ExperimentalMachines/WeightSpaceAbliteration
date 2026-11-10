# Run protocol

A run is the unit of evidence in this study. It holds one model, one frozen pre-registration, one split
manifest, and every gate receipt produced against them. This document states the conditions under which
a run's artifacts count, and where each condition is enforced in code.

Procedure is described, not prescribed. Where the harness refuses, the refusal is the rule.

## Lifecycle

Each step produces one kind of ledger entry. A step whose entry is absent has not happened, whatever
else exists on disk.

| step | command | entry | enforced by |
|---|---|---|---|
| freeze the answers | `python tools/start_run.py --model <slug>` | `preregistration` | `gdkit.prereg.freeze_run` |
| record the machine | `python scripts/record_host.py --run <run>` | `host_provisioned` | `harness/preflight.py:require_host` |
| build the split | `python harness/build_splits.py --run-id <run>` | `split_build` | `harness/build_splits.py` |
| check wiring | `python -m harness.gates --run <run> --smoke` | none | — |
| run a gate | `python -m harness.gates --run <run> --gate <name>` | `gate_log` | `harness/gates.py` |
| admit a method | review, then one entry | `method_selected` | `harness/gates.py:require_admitted` |
| switch stage | one entry | `stage_transition` | `harness/preflight.py:require_stage_consistency` |
| promote | `gdkit.promote` | — | receipt and attestation checks |

## Rules

### `host-before-gates`

A gate may run only if the run holds a `host_provisioned` entry whose fingerprint matches the machine
running now. The fingerprint covers GPU identity, driver, CUDA and cuDNN versions, the torch build and
the Python version.

*Threat:* results that depend on hardware, driver or library versions cannot be distinguished from
effects of the method unless the environment is fixed per run. Recording once and later running on a
different machine is the case the fingerprint exists to catch.

*Enforced by:* `harness/preflight.py:require_host`, called at the start of every gate.

*Refusal:*
```
ProtocolViolation[host-before-gates]: no host_provisioned entry
  run:    runs/<id>
  remedy: python scripts/record_host.py --run runs/<id>
```

### `admission-before-candidate`

A candidate may be evaluated only after a `method_selected` entry exists. The parent baseline is exempt:
it is measured before any method exists, and refusing it would make the comparison impossible.

*Threat:* a number produced by an unreviewed edit is an artifact that looks like a result and cannot be
withdrawn once cited.

*Enforced by:* `harness/gates.py:require_admitted`, on every gate that would produce candidate numbers.

### `stage-from-ledger`

The stage is the last `stage_transition` entry, or `baseline` if none exists. `harness.json` carries a
copy and is checked against the ledger.

*Threat:* a stage stored only in a mutable file is a one-line route around the admission rule.

*Enforced by:* `harness/preflight.py:require_stage_consistency`.

### `one-model-one-run`

A run binds one model, recorded in `run_scope.json` at its creation. Loading a different model inside a
run is refused, and the model registry is closed: a new model is an extension recorded in the ledger,
not an edit to a frozen answer.

*Threat:* receipts are scoped by run id. One run carrying two models makes every receipt ambiguous, and
promotion would then attest to a model it never ran.

*Enforced by:* `harness/preflight.py:require_run_model`; `tools/start_run.py --model` for creation.

### `gate-log-bound`

Every receipt has exactly one `gate_log` entry, and the log file named there hashes to the entry's output
hash.

*Threat:* a receipt without the run's output is a claim that cannot be audited; a log that can be edited
afterwards is not evidence.

*Enforced by:* `harness/gates.py` on write; `harness/preflight.py:require_log_binding` on audit.

### `runs-append-only`

Ledgers may only grow. Receipts, logs, attestations and scope files may be added, never modified or
deleted. `splits/manifest.json` may be replaced, because a rebuild carries its own ledger entry.

*Threat:* an editable history is not a history. The chain of hashes detects an edit; the append-only
check prevents one from being committed in the first place.

*Enforced by:* `.githooks/pre-commit` and CI, both calling `scripts/check_append_only.py`.

### `no-hand-hashes`

Hashes are computed from files by the tooling. An entry whose hashes were typed by a person attests to
nothing, because nothing can recompute them.

*Enforced by:* convention in `tools/README.md`, plus `harness/preflight.py` recomputing what it can and
reporting artifacts it cannot find.

### `shared-freeze`

All runs carry the same pre-registration digest and the same split-manifest hash. A run that diverged
from the freeze is a different study wearing the same name.

*Enforced by:* `scripts/verify_ledger.py`, run in CI.

## Deviations

A refusal is data, not an obstacle. When a check refuses, the operator stops, reads the slug, and
decides one of three things:

1. **The refusal is correct.** Perform the missing step. Nothing else changes.
2. **The refusal reveals a real problem.** Append a `deviation` entry stating what happened, which rule
   was involved, what was decided, and who decided it. Then proceed or abandon.
3. **The run is unrecoverable.** Abandon it in the ledger — append a `deviation` entry with the reason,
   leave the directory in place — and start a new run. Directories are never deleted.

What may never be done in response to a refusal:

- editing the ledger, a receipt, or a log;
- editing `harness.json` to change the stage;
- recomputing a hash by hand and writing it in;
- deleting a run directory to make a failure disappear;
- switching the run to explore mode to skip the checks.

Each of those is detectable, and the detection is the point: an entry that does not match its content is
worse than a missing entry, because it looks like evidence.

## What the protocol does not contain

Thresholds, margins and decision rules live in the pre-registration, frozen and hashed as entry 0. They
are not repeated here, so that this document cannot become a second place to change them.
