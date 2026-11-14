# Response to the independent audit of round 4 (2026-11-10)

Audit: `audit_round4_gpt.md` (`completion(model="slow")`, self-identified as ChatGPT / OpenAI; the requested "gpt-6.1-sol" cannot be selected from this environment and the model version is unverified).
Every audit point was checked against the stored data or the code before acting. Verdicts are mine.

| # | Audit point | Verdict | What I did |
|---|---|---|---|
| 1 | Frozen-arm guard only blocks `primary_eval` | **Confirmed** | `b_run.measure` now uses an allowlist: a candidate may only use `val_eval`; the parent may also use `primary_eval`. 11 regression tests (`tests/test_b_run_guard.py`) cover `primary`, `large`, probe arms and unknown names. |
| 2 | Frozen-arm incident cannot be independently cleared; deletion removed evidence | **Partly agree** | Correct that "never read" is only my statement and cannot be verified from artifacts. The transcript shows the only commands run on those files were a directory listing and `rm`. Deletion followed the safety rule for harmful replies. Disclosed as unverifiable in the note's incident 1. No further remedy is possible. |
| 3 | "Elements changed" uses inconsistent denominators; tied embedding double-counted | **Confirmed, real error** | The table divided by 1,006,672,704 (the `state_dict` count, which includes the tied embedding twice) instead of 752,393,024 unique parameters. Corrected shares: Arditi **43.4%** (not 32.5%), Heretic **5.4%** (not 4.0%), WSP **6.4%** (not 4.8%). `tools/bench_report.py` now divides by the unique count and `b_run.diff_against_parent` counts tied storage once. The audit's other guess was wrong: Arditi did **not** rewrite the output head (`edits.project_out_embedding` unties it first; the changed-tensor list has 48 writers + the embedding and no `lm_head`). |
| 4 | WSP "nested sets" description inaccurate | **Confirmed** | Reworded: sets built from one ranking (top-7/14/20/28, top-7 plus 4 downstream, all 48), not one nested sequence. |
| 5 | "Not distinguishable" rests on interval overlap, no between-method test | **Confirmed** | Added paired exact McNemar tests between methods from the stored labels: Arditi vs Heretic 3/7 discordant p = 0.34; Arditi vs WSP 4/7 p = 0.55; Heretic vs WSP 5/4 p = 1. Reworded to "no difference could be detected; lack of power, not equivalence". |
| 6 | "Unambiguous, non-minimal" is not implemented in code | **Partly agree** | The wording comes from the classifier's own prompt rules, not from my code. Reworded to say so. |
| 7 | Arditi selected under hooks, evaluated as weights; 1.18-nat discrepancy | **Re-run** | (a) Diagnostic redone as distribution distance: mean total variation 0.043 (harmful selection prompts) and 0.023 (harmless), refusal mass 0.0091 hook vs 0.0080 weights; the 1.18 figure reproduces exactly and is a tail-token maximum. (b) Selection re-run scoring every candidate as the real weight edit: same candidate (layer 10, position -5), 2 of 162 kept (KL 0.0998), identical side metrics, 41/60 harmful, labels identical to the hook-selected run (60/60). The discrepancy did not change any result. |
| 8 | Heretic's internal KL (0.094) is a different measurement from the reported 0.028 | **Agree, not an error** | The reported KL is one uniform metric for all conditions; Heretic's own scorer uses its own prompts and system prompt. Noted, not re-run. |
| 9 | Judge tokenizer: code requests slow, note says fast; parity unverified | **Confirmed, real** | The runtime tokenizer is a fast `LlamaTokenizer`; it differs from the original SentencePiece model in whitespace and markdown pieces in 60 of 120 checked inputs (6 differ in length). Judging the same generations both ways gave identical labels in 120/120 calls (parent and Arditi). Heretic and WSP generations could not be re-judged (artifacts lost). |
| 10 | Paired parent comparisons and Wilson intervals check out | Agree | Nothing to do. |

Comparability points raised by the audit: Heretic's system prompt (disclosed, not re-run); Arditi's smaller selection set (128 + 32 prompts, the paper's setting, against 335 + 80 for the others; disclosed, not changed); padding side: `evaluate.load_model` sets `padding_side = "left"` and `b_run external` does too (checked in code). Not re-run.

## Not re-run, and why
- OBLITERATUS: the tool refuses this architecture; forcing it would be a new condition.
- Anything on `primary`: prohibited.
- Heretic, WSP: artifacts were lost with the first host storage (the stopped host could not restart). The audit's findings did not require regenerating them; doing so would cost a 60-trial Heretic run and a new editing session.

## Cost of this audit round
[execution-host and billing detail omitted]
