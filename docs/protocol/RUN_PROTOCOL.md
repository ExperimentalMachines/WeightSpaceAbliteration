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
| run a gate | `python -m harness.gates --run <run> --gate <name>` | receipt with its `log` hash (schema 1); `gate_log` for schema 0 receipts | `harness/gates.py` |
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

Every receipt is bound to the log of the run that wrote it.

- A schema 1 receipt names its log and the log's hash in the receipt itself. gdkit writes the log while the
  gate runs and hashes it when the gate ends. The file must exist and hash to that value.
- A schema 0 receipt was written before the gdkit upgrade of 2026-11-11. It has exactly one `gate_log`
  entry, and the log file named there hashes to the entry's output hash. Schema 0 receipts are kept as
  history: they are verified, never rewritten.

*Threat:* a receipt without the run's output is a claim that cannot be audited; a log that can be edited
afterwards is not evidence.

*Enforced by:* `gdkit.gates.run_gate(capture_log=True)` on write; `harness/preflight.py:require_log_binding`
on audit.

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

## Recorded deviations

### 2026-11-11 — `probe_train`: layer chosen on validation, AUC corrected, interval and baselines added

*Applies to:* both runs, `20261107T112342Z-weightspace-abliteration` and
`20261110T135200Z-weightspace-abliteration-qwen3.5-0.8b`. Each ledger has a `deviation` entry for it.
Neither run had a `probe_train` receipt when the change was made, so no number already reported changes.

*Decided by:* Experimental Machines (owner_signer).

*What was wrong.* `check_probe_train` chose the layer with the highest held-out-category AUC and reported
that same AUC. The held-out categories therefore both chose the layer and scored it, and the reported
number was the largest of many noisy estimates. Separately, `_auc` ranked scores in descending order, so it
returned 1 − AUC, and it broke tied scores in arbitrary order. The probe also had no penalty. With more
hidden dimensions than fit rows, a layer can separate its fit split perfectly. Its weights then grow until
the optimiser stops, so its log-loss describes the optimiser rather than the layer.

*What the gate now does* (`harness/gates.py`, `probe_report`). Every constant below is fixed in code, not
set per run:

1. **Evaluation negatives.** A fixed pool of negatives is set aside before any seed is used. For each
   source (`or_bench_hard`, `xstest_safe`), the pool takes the share `1 − train_fraction` of items with the
   lowest SHA-256 of `wsa-probe-eval-pool-v1:<item id>`. No seed fits or validates on the pool. Both AUCs
   are scored against it: the in-distribution AUC uses the test positives, and the held-out-category AUC
   uses the held-out positives.
2. **Splits.** For each seed, the training-category positives are split into fit, validation and test, and
   the remaining negatives into fit and validation. Validation is 0.25 of the training portion
   (`PROBE_VALIDATION_FRACTION`).
3. **Probe.** Each layer is standardised with its fit split's mean and SD. The probe is a logistic
   regression with an L2 penalty of 0.01 on the weights (`PROBE_L2`); the bias is not penalised. It is
   fitted by LBFGS starting from zero, so the fit is deterministic.
4. **Layer selection, from validation only.** The rule takes the layer with the highest mean validation
   AUC across seeds. Among layers tied exactly at that AUC, it takes the lowest mean validation log-loss,
   then the lowest layer index. The report gives the number of layers tied at the top. The held-out
   categories and the pool are never used to choose the layer. The per-layer table is kept as description
   only.
5. **AUC.** The Mann–Whitney form, with ranks in ascending order and tied scores given their average rank
   (midranks). A tie between a positive and a negative counts as one half.
6. **Bootstrap interval.** 2,000 resamples (`PROBE_BOOTSTRAP`). Each resample draws both the held-out
   positives and the evaluation negatives with replacement, stratified by class, and applies the same draw
   to every seed. The fitted probes are kept fixed, and the statistic is the mean held-out AUC over seeds.
   The interval runs from the 2.5th to the 97.5th percentile.
7. **Permutation baseline.** 1,000 shuffles (`PROBE_PERMUTATIONS`), whatever the number of seeds. Each
   shuffle relabels every training-category item once, and every seed refits on its own fit split with
   those labels. An item that is in several seeds' fit splits therefore keeps one label. The upper-tail
   p-value is (1 + shuffles at or above the real AUC) / 1,001. It tests only whether the held-out AUC is
   above chance.
8. **Random-direction baseline.** 1,000 untrained random unit directions (`PROBE_RANDOM_DIRECTIONS`) in the
   standardised space of the training-category items. A random direction's AUC is symmetric about 0.5, so
   the folded value max(AUC, 1 − AUC) is reported: its median and its 95th, 97.5th and 99th percentiles.

*How the result is read.* The gate reports both ends of the interval and judges neither. Against the
pre-registered thresholds:

- held-out-category success against 0.60 requires the **upper** end of the 95% bootstrap interval at the
  chosen layer to be ≤ 0.60;
- the kill rule at 0.90 requires the **lower** end to be ≥ 0.90.

Success and kill are both read from the interval, not from the permutation p-value. The pre-registration in
`.gdkit/project.yaml` is unchanged; this note records how its thresholds are applied to the new interval.

*Papers consulted.* Each paper was checked with `pwc paper info <id>` and is cited only for what its
abstract states. The lookups are recorded as `paper_lookup` entries in the Qwen run's ledger.

| arXiv | paper | used for |
|---|---|---|
| 1610.01644 | Alain & Bengio, *Understanding intermediate layers using linear classifier probes* | linear probes trained independently of the model, at every layer |
| 2102.12452 | Belinkov, *Probing Classifiers: Promises, Shortcomings, and Advances* | the probing framework has known methodological limitations |
| 2006.00995 | Elazar et al., *Amnesic Probing* | probing performance does not support behavioural or causal conclusions on its own |
| 2306.03819 | Belrose et al., *LEACE: Perfect linear concept erasure in closed form* | linear concept information, removed from every layer |
| 2502.13283 | Wu et al., *Benefits of Early Stopping in Gradient Descent for Overparameterized Logistic Regression* | overparameterised logistic regression diverges in norm without regularisation; link to explicit L2 |
| 2602.00158 | Gao et al., *RAPTOR: Ridge-Adaptive Logistic Probes* | L2-regularised logistic probes on LLM layer representations |
| 1811.12808 | Raschka, *Model Evaluation, Model Selection, and Algorithm Selection in Machine Learning* | separate data for model selection and evaluation; the bootstrap for uncertainty of performance estimates |
| 2205.11134 | Bestgen, *Please, Don't Forget the Difference and the Confidence Interval when Seeking for the State-of-the-Art Status* | bootstrap confidence intervals in place of significance testing alone |

Not cited, because the lookup failed or the paper was not found: arXiv 1411.2664; Hewitt & Liang on
control tasks for probes; Phipson & Smyth on permutation p-values. The p-value formula above is given
without a citation.

## What the protocol does not contain

Thresholds, margins and decision rules live in the pre-registration, frozen and hashed as entry 0. They
are not repeated here, so that this document cannot become a second place to change them.
