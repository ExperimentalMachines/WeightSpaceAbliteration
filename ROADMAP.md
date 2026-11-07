# Roadmap

Status as of 2026-11-07. Nothing here is a promise; the pre-registration is the only thing that binds.

## Blocking a first result

1. **Provision the execution host** and record GPU model, VRAM and count as a `host_provisioned` ledger
   entry. `base_model_revision` carries a TODO and must not be edited.
2. ~~Emit the four missing split arms~~ — done. `harmless`, `over_refusal`, `probe_neg`, `probe_pos`
   and `probe_heldout` now exist, and `--smoke` reports nine gates ready.
3. ~~Fix the gate/split contract~~ — done; cheap gates re-run against the rebuilt split.
4. **Implement a method** — one of `abliteration`, `heretic_style`, `obliteratus_style` — answer the
   review checklist, and admit it with a `method_selected` entry.
5. **Run the expensive gates** on the parent first, then on the candidate. Attest each receipt.

## Known defects

- `from_pretrained` is called with `dtype=`; transformers 5.x accepts it, older versions expect
  `torch_dtype=`. Pass whichever the pinned version wants, explicitly.
- The harness assumes `device_map="auto"` and bf16, which is a guess until the host exists.
- Resolved: the split is built with bge-small-en-v1.5, and the decision rules were restated as rates
  (≤11/293, ≤594/15,640) rather than counts. Recorded in ledger entry 17 and `decision_rules.json`.

## Decided on 2026-11-07

- **Probe evaluation**: both a random 80/20 split and a category holdout, the latter training on
  copyright, illegal, cybercrime_intrusion, harassment_bullying and harmful, and evaluating on
  chemical_biological plus misinformation_disinformation.
- **Probe negatives**: XSTest safe 250 plus OR-Bench hard-1k 1,319.
- **Exclusion instrument**: `BAAI/bge-small-en-v1.5` at `5c38ec7c`, cosine 0.80, truncation 128.
- **Seeds**: capability 0–2, probe 0–4. Generation stays at temperature 0.
- **Method order**: `abliteration`, then `heretic_style`, then `obliteratus_style`; each reviewed
  against the checklist before the next begins.

## After the first result

- Attest and promote. `promote` re-runs the cheap gates and checks every receipt.
- Record the result as a gate receipt plus a results directory, and update the README status table from
  "no result" to the actual numbers, including the interval.
- If the answer is *no*, say so in the abstract. The pre-registration was written to make that a
  publishable outcome.

## Not planned

- Redistributing the corpora. The whole data policy rests on not doing it.
- A leaderboard. The study compares methods under one fixed protocol; ranking models is a different
  project with different incentives.
- Any method that tunes on the evaluation arm.
