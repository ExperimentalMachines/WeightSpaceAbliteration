# `harness/`

**Audience:** someone about to run, audit or extend a gate.

The harness is the only place a model is loaded. It holds three things:

- `gates.py` — eleven gates and the registry `gdkit` uses to attest them.
- `build_splits.py` — materialises the frozen split from pinned sources and hashes it.
- `methods/` — the weight-edit contract, deliberately unimplemented.

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

Four gates read arms the builder does not yet emit — `harmless`, `over_refusal`, `probe_pos`,
`probe_neg`. They are listed here as they are, not as they should be: extending `build_splits.py` is
what unblocks them.

## Running

```bash
python -m harness.gates --run runs/<run_id> --dry-run          # wiring only, no model
python -m harness.gates --run runs/<run_id> --gate split_integrity
```

A gate run writes `receipts/<gate>.json`, bound to the run id, the gate's source hash, the ledger head
at execution time, and the sha256 of every file it read.

`--smoke` checks the same inputs without loading a model and reports which gates are ready.

Candidate-producing gates call `require_admitted()`. It raises unless the run's ledger contains a
`method_selected` entry, and only when `harness.json` sets `"stage": "candidate"`. The parent baseline
is exempt: it is measured before any method exists.

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
