# `runs/`

**Audience:** someone auditing a result, or trying to reproduce one without trusting it.

One directory per run. The directory name is the run id, and the run id appears in every ledger entry,
every receipt and every attestation, so a receipt cannot be moved between runs.

```
runs/<run_id>/
  ledger.jsonl        append-only, hash-chained; the run's whole history
  harness.json        which model, parent, judges, tasks — a declaration, not a pre-registration answer
  splits/
    manifest.json     committed: arm counts, per-file sha256, exclusion ID lists and their hash
    *.jsonl           ignored: the rows themselves, rebuilt from pinned sources
  receipts/<gate>.json
  paper_lookups/NNNN.json
  results/            ignored: generated text, activations, probe output
```

## One run per model

The pre-registration names five base models. Each gets its **own run**, sharing the frozen answers and
the same split manifest, with the model in the run id — `20261107T112342Z-weightspace-abliteration`
for the first, `…-qwen3-30b-a3b` for the next. Receipts, attestations and promotions are then scoped to
one model, and a model that fails can be abandoned without touching the others. A model matrix inside a
single run would make `promote` responsible for models it never ran.

`tools/start_run.py --model <slug>` appends the slug to the default run id and writes `run_meta.json`.

## What a run must record

Enforced by code, not by convention:

| step | forced by | what it binds |
|---|---|---|
| freeze the answers | `prereg.freeze_run` | answer digest as both input and output hash |
| record the host | `scripts/record_host.py` | raw `nvidia-smi`/`nvcc`/version text as input, structured record as output |
| every gate | `gates.py` wrapper | receipt hash as input, gate log hash as output |
| every paper lookup | `gdkit.pwc_lookup` | request hash, response hash, raw response on disk |
| the split | `build_splits.py` + `split_*` entries | source hashes, manifest hash, exclusion hash |

`gdkit.ledger` refuses any entry in registered mode that lacks an input hash and an output hash, so this
is a property of the format rather than a habit. What it does **not** force is that a gate declares
every file it read; the wrapper now adds `harness.json` for that reason, and a new gate must add its own
inputs to `inputs` in `gates.py:main`.

Gate logs are written to `runs/<id>/logs/<gate>.log` and hashed into a `gate_log` entry that also names
the receipt and the ledger head at execution time. The log files are ignored by git; the hash is not.

## The ledger

Every entry carries `seq`, `ts`, `op`, `params`, `prev_hash` and `entry_hash`. Registered mode also
requires an `input_hash` and an `output_hash` on every entry, so an entry cannot be added without saying
what it read and what it produced.

| seq | op | what it records |
|---|---|---|
| 0 | `preregistration` | the 22 answers, verbatim, and their digest |
| 1–14 | `paper_lookup` | each search and paper record, with request/response hashes and the pwc version |
| 15 | `split_build` | arm counts, exclusion hash, and the deviations from the pre-registered arithmetic |
| later | gate receipts, `method_selected`, `host_provisioned` | as they happen |

Verify the chain:

```bash
python -c "from gdkit.ledger import verify; print(verify('runs/<run_id>/ledger.jsonl'))"
```

Detects accidental change. Does not stop a full rewrite — that is what the attestation and the git
history are for.

## What must never be committed

`splits/*.jsonl` and `results/` contain harmful prompts and model generations. They are ignored by
`.gitignore` and must stay that way: the pre-registration promises hashes and a fetch script, not rows.
