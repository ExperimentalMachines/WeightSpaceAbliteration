# `harness/`

**Audience:** someone about to run, audit or extend a gate.

The harness is the only place a model is loaded. It holds three things:

- `gates.py` — eleven gates and the registry `gdkit` uses to attest them.
- `build_splits.py` — materialises the frozen split from pinned sources and hashes it.
- `methods/` — the weight-edit interface and implemented methods.

## Gates

| gate | cost | reads | produces |
|---|---|---|---|
| `split_integrity` | cheap | `splits/*.jsonl`, `splits/manifest.json` | hash comparison, row counts |
| `arm_counts` | cheap | `splits/manifest.json` | arm sizes vs the pre-registration |
| `exclusions_applied` | cheap | `splits/*.jsonl`, manifest exclusions | leaked-ID list |
| `direction_derivation` | expensive | `splits/derivation.jsonl`, `splits/harmless.jsonl` | `results/direction.npz` |
| `refusal_eval` | expensive | `splits/<arm>.jsonl` | `results/refusal_<arm>.jsonl` |
| `judge_agreement` | expensive | `results/refusal_primary.jsonl` | agreement rate, Cohen's kappa |
| `over_refusal_eval` | expensive | `splits/over_refusal.jsonl` | refusal rate on answerable items |
| `kl_divergence` | expensive | `splits/harmless.jsonl` | first-token KL against the parent |
| `activation_extraction` | expensive | `splits/probe_pos.jsonl`, `splits/probe_neg.jsonl` | `results/activations.npz` |
| `probe_train` | expensive | `results/activations.npz` | AUC per layer, best layer |
| `capability_suite` | expensive | `harness.json` | lm-eval results per task |

The split builder now emits the required arms. `judge_agreement` and `probe_train` also
consume outputs of earlier gates; input presence is wiring evidence, not scientific validation.

## Running

```bash
python -m harness.gates --run <temporary-run> --dry-run       # wiring only, no model
python scripts/build_release.py build --repo . --output .omp/releases --working-tree
python scripts/build_release.py verify .omp/releases/<release_id> --source-root .
python scripts/record_host.py --run <temporary-run>           # CPU/package metadata by default
python -m harness.gates --run <temporary-run> --gate split_integrity --release .omp/releases/<release_id>
python scripts/verify_execution.py --run <temporary-run> --receipt receipts/split_integrity.json --release .omp/releases/<release_id>
```

These commands require a prepared temporary fixture with a valid ledger and gate inputs;
they do not initialize a study run. Only local implementation/verification is approved.
Existing registered runs are not migrated, and no future measurement run has been created.

When importing code directly from an immutable bundle, set `PYTHONDONTWRITEBYTECODE=1`
before import; extra files such as `__pycache__` make the bundle fail verification. The
runner sets this explicitly. A Git-revision bundle identifies committed bytes, not human
review; the tested working-tree bundles here remain development-only and uncommitted.

New execution uses harness contract 3 within gdkit's existing receipt schema 1. The receipt
binds immutable `execution/<gate>.json`, the canonical session host, enumerated file inputs,
exact output digests under `result.artifacts`, and gdkit's captured log. The execution
manifest binds a verified code release, bounded live callable identities/constants, and
runtime package information. It is not an OS-level I/O trace or scientific-validity certificate.

The verifier reports artifact validity separately from current-ledger freshness and
`gate_passed`. A valid historical receipt may be stale, or may faithfully record a failed
gate. `--require-current` additionally refuses stale receipts. Without an available release,
or with a different execution interpreter, execution identity verification is incomplete.

`--smoke` checks the same inputs without loading a model and reports which gates are ready.

Candidate-producing gates call `require_admitted()`. It raises unless the run's ledger contains a
`method_selected` entry, and only when `harness.json` sets `"stage": "candidate"`. The parent baseline
is exempt: it is measured before any method exists.

### Non-destructive execution and transfer

The repository gate CLI refuses an occupied receipt, final/partial log, execution manifest,
failure record, or gate-owned measurement output before invoking gdkit. Configured refusal arms are
included; an existing `results/lm_eval/` directory blocks capability execution even
if empty. Unrelated gates may share the `results/`, `logs/`, and `receipts/` directories.
An interrupted attempt therefore blocks reuse rather than silently replacing evidence.

`scripts/record_host.py` refuses legacy migration and appends canonical `host` events pointing
to immutable `hosts/<session_id>.json` and private raw probe evidence. A later session does
not replace an earlier host. Default collection imports no GPU library and records CPU/Python/
package identity; explicit `--probe` commands add hardware evidence. `--require-probes` refuses
missing/failed probes. The GPU runner requires GPU and CUDA/cuDNN probes. Historical host
verification checks the recorded hashes, not the auditor's machine.

Modal session entrypoints require explicit `run` and `release_id` and precheck the entire
gate list before host recording. Unknown/duplicate names are rejected. Runtime patch APIs
and the separate `fast_session` wrapper have been removed; historical corrected helper
computations are static imports. This does not validate the legacy refusal metric.

The artifact-transfer library `harness/artifact_sync.py` remains separate from code delivery:

| Transfer | Existing identical bytes | Existing different bytes |
|---|---|---|
| Pull | Skip without rewriting | Preserve incoming bytes in a private sibling quarantine and fail |
| Upload | Skip without rewriting | Preserve available copies in quarantine and fail before upload |
| Pull ledger | Skip | Append only a verified, same-run, complete-line prefix extension |
| Upload ledger | Skip | Refuse; bulk upload has no atomic compare-and-append operation |

New pulled files use atomic no-replace publication. Explicit artifact uploads use `force=False`;
they are not invoked by code delivery. Pulls include session hosts, execution/failure records,
and partial gate logs. Preflight conflicts prevent the batch from starting; runtime failures
report partial progress without deleting evidence or truncating a partially appended ledger.
The exception reports the private quarantine location outside the repository.

The old blind `upload_repo` entrypoint is replaced by `upload_release --release <directory>
--reviewed`. It accepts only a verified Git-revision bundle, requires an explicit review
attestation, and writes only under `releases/<release_id>/` with `force=False`. Identical files
are reused; conflicting or unexpected bytes stop publication. Interrupted matching uploads
can add only missing files, never replace existing ones. Working-tree bundles are local-only.
Do not invoke any remote operation without separate approval.

Per-run `.artifact-write.lock` files coordinate guarded writers on one filesystem.
Stale locks require investigation, not automatic removal. These are **not distributed
Modal locks**: never run concurrent writers against the same volume/run. Direct
gdkit calls, its CLI, and direct `check_*` calls bypass the repository producer guard.
This protection does not authorize reruns, recover historical overwritten bytes,
or validate the scientific measurements.

### Explicit limitations before remote/model execution

- Release manifests identify source bytes, not human review or actual downloaded model weights.
  Model-consuming gates require explicit model IDs and full immutable commit revisions; the
  configured references are recorded as unvalidated artifact references, not weight-byte proof.
- The local image definition now uses a registry-digest-pinned Python 3.11.15 base,
  uv 0.12.18 and one lock-governed installation; supplemental runtime installs were removed.
  This definition has not been built. Apt Git/OS inventory, actual built-image identity,
  required data resources, Linux/CUDA behavior and remote validation remain unverified.
- The experimental `gates_optimized.py` is not included in the runtime release allowlist.
  Its previously identified problems are not hidden by a successful local provenance check.
- Existing GPU-decorated `smoke_test` is not a CPU-only remote smoke. No CPU-only remote
  validation, GPU equivalence/throughput test, or scientific calibration has been performed.
- Scientific definitions, thresholds, controls-v2, and historical artifacts remain unchanged.
  Engineering validity does not make HarmBench-negative output explicit refusal.

### Dependency and image preparation

The selected workflow is declared through `lm-eval[hf,ifeval]` and
`transformers[sentencepiece,tiktoken]`, with recorded supplemental pins in `pyproject.toml`.
The project requires uv 0.12.18; run `uv lock --check` to check project/lock correspondence.
The gdkit Git commit is unchanged, and its setuptools build input is constrained with
hashes taken from the existing lock.

The Modal definition requires SDK 1.6.4 and uses `Image.uv_sync` with `--locked --no-dev
--no-python-downloads`. Its `frozen=False` parameter prevents the SDK from also adding
`--frozen`: `--locked` is the stricter metadata-consistency check and refuses lock updates.
Code delivery remains separate from dependency installation.

Local verification used an isolated environment under `.omp/dependency-update/`; the
existing project `.venv` was deliberately not synchronized. See the execution log for
the exact validation environment and results. Import success is not model/benchmark
validation, and the existing local NLTK data is not proof of image provisioning.

Future authorized Modal commands must use the pinned SDK, for example through
`uvx --from modal==1.6.4 --python 3.11.15 modal ...`. A Modal local entrypoint can still
prepare app images; it is not an offline substitute for the local builder/verifier scripts.

## Configuration

The expensive gates read `harness.json` in the run directory: model and parent with pinned revisions,
both judges, capability tasks, batch size. It is not a pre-registration answer — it is a harness
declaration, and the host fields in it are still `TODO`.

## Attesting

```bash
python -m gdkit.cli --registry harness.gates:REGISTRY attest runs/<run_id> <gate> --project .gdkit/project.yaml
```

Prints the receipt hash. That hash is what an SSH-signed attestation approves. `promote` refuses an
expensive gate without one.
