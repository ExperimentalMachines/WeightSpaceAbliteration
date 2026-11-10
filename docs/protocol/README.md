# Protocol index

The conditions under which this study's artifacts count, and where each one is enforced.

```
freeze ──► host ──► split ──► gates (cheap) ──► method admitted ──► gates (candidate) ──► promotion
  │         │        │            │                    │                    │                │
entry 0   host_    split_build  gate_log          method_selected     gate_log        receipts +
          provisioned                                                                    attestation
```

Everything to the right of `method admitted` is refused while the ledger lacks that entry.

## Documents

| document | covers |
|---|---|
| [`RUN_PROTOCOL.md`](RUN_PROTOCOL.md) | the lifecycle, every rule, and the deviation route |
| [`../README.md`](../../README.md) | what the repository is, in one page |
| [`../../harness/README.md`](../../harness/README.md) | what the harness produces, and how to add a gate |
| [`../../runs/README.md`](../../runs/README.md) | the run directory as output rather than source |

## Rules

| slug | in one line | enforced by |
|---|---|---|
| `host-before-gates` | a gate needs a host entry whose fingerprint matches this machine | `harness/preflight.py:require_host` |
| `admission-before-candidate` | candidates wait for `method_selected` | `harness/gates.py:require_admitted` |
| `stage-from-ledger` | the ledger decides the stage; `harness.json` is a checked cache | `harness/preflight.py:require_stage_consistency` |
| `one-model-one-run` | a run binds one model | `harness/preflight.py:require_run_model` |
| `gate-log-bound` | every receipt has one log entry, hashed | `harness/gates.py`, `harness/preflight.py` |
| `runs-append-only` | ledgers grow; nothing under `runs/` is edited | `.githooks/pre-commit`, CI |
| `no-hand-hashes` | hashes come from files, never from a keyboard | `tools/README.md` |
| `shared-freeze` | every run carries the same freeze digest | `scripts/verify_ledger.py` |

## Checking a run

```bash
python -m harness.preflight runs/<id>            # what is missing, in lifecycle order
python -m harness.preflight runs/<id> --check    # raise on the first violation
python scripts/verify_ledger.py                  # chain integrity and drift, all runs
```

## Installing the commit hook

```bash
git config core.hooksPath .githooks
```

The same check runs in CI, so a clone that skipped this line is still caught at the pull request.
