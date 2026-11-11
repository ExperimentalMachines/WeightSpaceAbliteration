# MiniCPM5-2B development pilot: WSP-Full and WSP-Compact (round 7)

## Status
MiniCPM5-2B is one of the study's registered models. **This folder is development work outside any registered run.** It has no receipts, no method here is admitted (`load_method()` is unchanged), and nothing here is a result of the registered study.
Edited models were never run on the study's frozen `primary`, `large`, probe or `over_refusal` arms.

Parent: `openbmb/MiniCPM5-2B` @ `f97400052a43d642bbc6e9975e2397e3ae6a6b52`. Preregistration: `../round7_prereg.md`. Results, tables, deviations and limits: `../round7_summary.md`. All methods and models side by side: `../README.md`.

## Contents
- `labels/<Condition>__<Test set>.json`: per-behaviour labels (0 = no, 1 = yes, -1 = invalid) keyed by public behaviour id or an opaque index, with the judge and revision. No replies exist anywhere.
- `metrics/<Condition>__round7.json`: aggregate side metrics (over-refusal, GSM8K, first-token KL) and patch sizes.
- `selection/`: every candidate each editing session registered (`*_candidates.json`), the chosen edit with its digest (`*_info.json`), and the forward-pass ledger (`*_passes.json`).
- `sessions/`: every cell the editor submitted in each session and its output (replies to harmful prompts are never returned to the editor).

**Not included, deliberately:** model weights, adapters and refusal-direction vectors (including the saved rank-1 factors), generated text, and any prompt corpus (consistent with `SECURITY.md` and `CONTRIBUTING.md`).
