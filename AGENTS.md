# AGENTS.md

Instructions for any coding agent working in this repository. Read this before you change anything, and again
after pulling `main`.

## What this repository is

A pre-registered study of weight-space abliteration. Its claims count only if the run records hold up: every
step of a registered run is an entry in a hash-chained ledger (`runs/<run_id>/ledger.jsonl`), and every gate
result is a receipt bound to its log. The rules are in `docs/protocol/RUN_PROTOCOL.md` (the lifecycle, every
rule and why it exists) and `docs/PROVENANCE.md`. `docs/protocol/README.md` is the index.

`pilots/` is development work outside any registered run. Pilot rounds have their own pre-registration copies
and summaries there and do not write to `runs/`.

## Rules you must not break

- **Never edit `.gdkit/project.yaml`.** It is the pre-registration, frozen and hashed as entry 0 of each run.
  Ask the owner (Experimental Machines) before touching any pre-registration wording.
- **Never edit, reorder or delete a ledger line, a receipt or a log under `runs/`.** Ledgers may only grow.
  A correction is a new `deviation` entry that says what happened, what was decided and who decided it; see
  `RUN_PROTOCOL.md#deviations`. `scripts/check_append_only.py` enforces this in the commit hook and in CI.
- **Do not run `python -m harness.gates --gate ...` on an existing run folder** unless the owner asked for that
  gate on that run. It writes a new receipt over the old one, and the append-only check will refuse the commit.
- **Never write a hash by hand.** Hashes come from the tools that produced the bytes.
- **Merge with merge commits only; never squash or rebase a branch that is already pushed.** Ledger entries
  name commits by SHA (the 2026-11-11 probe deviation in both ledgers names `316617d`). A squash or rebase
  gives those commits new SHAs, and the recorded SHA would no longer be in `main`'s history. Use
  `gh pr merge <n> --merge`, and afterwards check `git merge-base --is-ancestor <sha> origin/main` for every
  SHA a ledger entry names.
- **Do not switch a run to explore mode** to get past a refusal. A refusal is data: read the slug, then follow
  `RUN_PROTOCOL.md#deviations`.

## Setup

```sh
uv sync                                  # installs gdkit pinned in pyproject.toml (currently fa1e4d5)
git config core.hooksPath .githooks      # enables the append-only pre-commit hook in your clone
```

## Before you push

```sh
python -m pytest -q tests
python scripts/verify_ledger.py
python -m harness.preflight runs/<run_id>        # for each run you touched
python scripts/check_append_only.py              # staged changes against HEAD
```

Known, expected preflight refusals on both current runs: `host-before-gates` (no `host_provisioned` entry yet);
and on `20261107T112342Z-weightspace-abliteration` also `gate-log-bound` (`arm_counts` has no `gate_log`). Do
not "fix" these by editing anything; they need the missing steps or a deviation.

## Files hashed byte-for-byte (Windows line endings)

Some run files are hashed exactly as written: raw pwc responses (`runs/*/paper_lookups/*.json`) and the split
manifest (`runs/*/splits/manifest.json`). On Windows these used to be written with CRLF and then committed as
LF, so no committed copy matched its ledger hash. They are now marked `-text` in `.gitattributes` and stored
byte-exact. If you add a new kind of hashed run file:

- write it with explicit bytes (`write_bytes`, or `write_text(..., newline="\n")`);
- add a `-text` line for it in `.gitattributes`;
- check the hash against the committed blob (`git cat-file blob HEAD:<path>`), not the working copy.

Run pwc lookups with `PYTHONUTF8=1` on Windows: pwc-cli crashes when it prints non-cp1252 JSON into a pipe,
and `gdkit.pwc_lookup` then records an `UNAVAILABLE` entry, which blocks promotion.

## What changed on 2026-11-11 (PR #1, merged to `main`)

If your branch started before this merge, pull `main` and re-run the checks above. Nothing under `pilots/` was
touched, and no pilot script imports the changed code.

1. **gdkit pinned to `fa1e4d5`** (`pyproject.toml`, `uv.lock`, CI). Run `uv sync`.
2. **Receipts carry their log.** Gates run through `gdkit.gates.run_gate(capture_log=True)`. A new (schema 1)
   receipt names `logs/<gate>.log` and its sha256; no `gate_log` ledger entry is written any more. Old
   (schema 0) receipts keep their `gate_log` entries and are verified, never rewritten.
   `harness/preflight.py:require_log_binding` checks both forms.
3. **Every gate returns `passed`.** `over_refusal` passes iff its rate is at most 0.10; `kl_divergence` and
   `probe_train` pass when the measurement completes; the others mirror `ok`.
4. **`probe_train` was changed** (recorded as a deviation in both ledgers and in
   `RUN_PROTOCOL.md#recorded-deviations`). The old code chose its layer with the held-out categories and its
   `_auc` returned 1 − AUC. Now: layer chosen on a validation split; per-layer standardisation with L2 0.01; a
   fixed evaluation pool of negatives chosen by item ID per source; midrank AUC; a 2,000-resample bootstrap 95%
   interval over both classes; a 1,000-shuffle permutation baseline (tests "above chance" only); a
   1,000-direction random-direction baseline. **Reading rule:** success against 0.60 needs the interval's upper
   end ≤ 0.60; the kill rule at 0.90 needs its lower end ≥ 0.90; read from the interval, not the p-value. Any
   AUC computed with the old `harness.gates._auc` is inverted and should not be compared with new numbers.
5. **Hashed run files restored byte-exact** (see the section above), recorded as a second deviation in each
   ledger. `harness/build_splits.py` writes the manifest with LF.
6. **`scripts/check_append_only.py`** reads git blobs as bytes, does not follow renames, and allows one
   exception: a `paper_lookups` file rewritten to the exact bytes its own pre-existing ledger entry recorded.
   CI checks out full history (`fetch-depth: 0`) so the PR check can find its base commit.

Open items, not decided yet (ask the owner before acting on them): gates do not record a census; there is no
guard against an empty population; "controls passing" is undefined; there is no positive control on the parent
model; the two negative sources may be confounded with the label; the seeds wording in the pre-registration
(`manual_seed` was a no-op for the probe).
