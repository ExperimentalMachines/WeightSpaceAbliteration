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
| record compute | run method once, record timing | `compute_evidence` | `harness/preflight.py:require_compute_evidence` |
| record tensor inventory | dump state-dict keys from pinned model | `tensor_inventory` | `harness/preflight.py:require_tensor_inventory` |
| admit a method | review, then one entry | `method_selected` | `harness/gates.py:require_admitted` |
| record upstream issue | ledger entry + companion .md | `upstream_issue` | `harness/preflight.py:require_upstream_clear` |
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

### `upstream-clear`

A gate may not run while a blocking upstream issue (severity `blocking`, status `open`) has no
recorded workaround. The issue must be recorded as a ledger entry and a companion Markdown file.

*Threat:* a result produced while a known dependency bug is unfixed is a result whose provenance
is suspect. Recording the workaround makes the code path auditable; refusing without one prevents
unauditable results.

*Enforced by:* `harness/preflight.py:require_upstream_clear`, called at the start of every gate.

*Refusal:*
```
ProtocolViolation[upstream-clear]: blocking upstream issue has no recorded workaround
  detail: transformers-qwen35-linear-attn-key-names (blocking, status=open)
  run:    runs/<id>
  remedy: apply a workaround and record it, or downgrade severity if the assessment changed
```

See [`docs/upstream_issues/README.md`](../upstream_issues/README.md) for the recording format.

### `compute-before-admission`

A method may not be admitted (`method_selected` entry) until a `compute_evidence` entry exists in
the run's ledger, recording GPU model, wall-clock time, and peak memory for one `apply()` call.

*Threat:* a method whose cost is unknown cannot be assessed for feasibility, and an estimate
substituted for evidence is not a measurement.

*Enforced by:* `harness/preflight.py:require_compute_evidence`, called by `require_admitted`.

### `tensor-inventory-before-admission`

A method may not be admitted until a `tensor_inventory` entry exists in the run's ledger, recording
the state-dict key names, shapes, and dtypes of every target tensor as loaded by the pinned
`transformers` version.

*Threat:* a method that targets tensor names verified only on toy tensors may silently miss or
misidentify targets on the real model. The inventory is the check that the method's assumptions
match the model's reality.

*Enforced by:* `harness/preflight.py:require_tensor_inventory`, called by `require_admitted`.

### `retroactive-dating`

An entry recorded after its event must declare `recorded_retroactively: true` in its params,
along with `event_occurred_at`, `entry_recorded_at`, and `reconstruction_evidence`.

*Threat:* a ledger entry written today about a gate that ran yesterday is indistinguishable from
one written at the time unless it says which it is. Without this rule, the ledger's timestamps
are unreliable.

*Enforced by:* `harness/preflight.py:require_retroactive_dating`, on audit.

### `gate-non-vacuity`

Every gate receipt must include a census (`discovered`, `checked`, `passed`, `failed`, `skipped`,
`blocked`) and the census invariants must hold: `discovered == checked + blocked + skipped` and
`checked == passed + failed`. A gate with policy `REQUIRED_NONEMPTY` must discover at least one item.

*Threat:* a gate that returns success without examining anything is indistinguishable from one that
examined everything and found nothing wrong.

*Enforced by:* `harness/verification/accounting.py:Census`, validated after every gate.

### `contract-version`

Every gate receipt carries a `contract_version` field. When the set of checks or their non-vacuity
requirements change, the version is bumped. A PASS under one version is not equivalent to a PASS
under another.

*Threat:* tightening a gate without versioning the change makes old and new receipts
indistinguishable, so a receipt produced under weaker rules looks like evidence under stronger ones.

*Enforced by:* `harness/verification/__init__.py:CONTRACT_VERSION`, recorded in every receipt.

See [`docs/PROVENANCE.md`](../PROVENANCE.md) for the full provenance model these rules serve.

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
