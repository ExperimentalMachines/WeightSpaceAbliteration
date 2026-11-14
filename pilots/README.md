# `pilots/`

Development pilots that came **before or beside** the registered runs. None of this is a result of the registered study: there are no receipts here, no method is admitted (`load_method()` is unchanged, there is no `method_selected` entry),
and edited models were never run on the study's frozen arms. Each pilot has its own folder with the labels, side metrics, selection records and editor sessions behind every number.

| Folder | Model | Rounds | Preregistrations |
|---|---|---|---|
| `qwen3.5-0.8b/` | Qwen3.5-0.8B | 5, 6 | `prereg_round5.md`, `prereg_round6.md` |
| `gemma-4-e2b-it/` | Gemma-4-E2B-it | 7 | `round7_prereg.md` |
| `minicpm5-2b/` | MiniCPM5-2B | 7 | `round7_prereg.md` |
| `round8/` | all three | 8 | `round8_prereg.md` |
| `rounds1-4/` | Qwen3.5-0.8B | 1 to 4 | `notes/prereg_round2.md`, `notes/prereg_round3.md`, `notes/prereg_round4.md` |
| `round9/` | MiniCPM5-2B | 9 | none (exploratory, not preregistered) |

Round 7 (WSP-Full and WSP-Compact on the two small registered models) has one preregistration and one summary for both models: `round7_prereg.md`, `round7_summary.md`.
Round 8 (completing the matrix: Arditi, Heretic and the missing WSP-Compact cells) lives in `round8/`, separate from the published Qwen3.5-0.8B files so that nothing published is overwritten; its summary is `round8_summary.md` there.
Rounds 1 to 4 (the earlier Qwen3.5-0.8B pilots: over-refusal edits in rounds 1 to 3, the first four-method refusal-removal benchmark in round 4) are in `rounds1-4/`; its `README.md` lists what each round was and what was left out.
Round 9 (fixed rank-k weight edits, WSP-SG, on MiniCPM5-2B; exploratory, no preregistration) is in `round9/`; its summary is `round9_summary.md` there. WSP-SG is a WSP method with no LLM editor and no selection step, so its rows are not comparable to WSP-Full and WSP-Compact as "what an editor chose".

## Names
Test sets: **StrongREJECT-267**, **HarmBench-Val-60**, **JBB+MI-98**. Conditions: **Parent**, **Arditi-Paper**, **Arditi-Matched**, **Heretic-Abliteration**, **Heretic-ARA**, **WSP-Full**, **WSP-Compact**.
"Harmful" means the official HarmBench classifier (`cais/HarmBench-Llama-2-13b-cls` @ `bda70534`) labels the completion an instance of the harmful behaviour. Greedy decoding, 512 new tokens, no system prompt.

## All methods, all models, all test sets
"Weights changed" is the share of the model's own parameter count; the KL is first-token KL to the parent. "not run" means a method was not run on that model. Every cell of the three worked-with models now holds a measurement or a recorded result.

| Model | Method | StrongREJECT-267 | HarmBench-Val-60 | JBB+MI-98 | Weights changed | KL |
|---|---|---|---|---|---|---|
| Qwen3.5-0.8B | Parent | 19.1% | 33.3% | 9.2% | 0 | 0 |
| Qwen3.5-0.8B | Arditi-Paper | 81.6% | 68.3% | 85.7% (round 8) | 43.4% | 0.066 |
| Qwen3.5-0.8B | Arditi-Matched | 72.7% | 71.7% | 76.5% (round 8) | 43.5% | 0.074 |
| Qwen3.5-0.8B | Heretic-Abliteration | 81.3% | 71.7% | 80.6% (round 8) | 9.9% | 0.029 |
| Qwen3.5-0.8B | Heretic-ARA (gradient-based) | 66.3% (round 8) | 66.7% (round 8) | 62.2% (round 8) | 3.90% | 0.038 |
| Qwen3.5-0.8B | WSP-Full | 76.4% | 73.3% | 78.6% | 6.4% | 0.028 |
| Qwen3.5-0.8B | WSP-Compact | 74.5% (round 8) | 70.0% (round 8) | 67.3% | 3.8% | 0.044 |
| Gemma-4-E2B-it | Parent | 1.1% | 6.7% | 1.0% | 0 | 0 |
| Gemma-4-E2B-it | Arditi-Paper | 62.2% | 78.3% | 78.6% | 16.7% | 0.041 |
| Gemma-4-E2B-it | Arditi-Matched | 63.3% | 75.0% | 75.5% | 16.7% | 0.049 |
| Gemma-4-E2B-it | Heretic-Abliteration | 49.1% | 70.0% | 67.3% | 2.63% | 0.052 |
| Gemma-4-E2B-it | Heretic-ARA (gradient-based) | 71.9% | 90.0% | 92.9% | 5.01% | 0.037 |
| Gemma-4-E2B-it | WSP-Full | 38.6% | 53.3% | 60.2% | 1.64% | 0.0155 |
| Gemma-4-E2B-it | WSP-Compact | 37.5% | 53.3% | 60.2% | 1.59% | 0.0158 |
| MiniCPM5-2B | Parent | 0.4% | 8.3% | 0.0% | 0 | 0 |
| MiniCPM5-2B | Arditi-Paper, Arditi-Matched | no admissible direction | no admissible direction | no admissible direction | - | - |
| MiniCPM5-2B | Heretic-Abliteration | 34.5% | 51.7% | 17.3% | 14.65% | **0.9998** |
| MiniCPM5-2B | Heretic-ARA (gradient-based) | 46.8% | 63.3% | 51.0% | 10.92% | **0.6956** |
| MiniCPM5-2B | WSP-Full | 1.1% | 15.0% | 1.0% | 4.36% | 0.0964 |
| MiniCPM5-2B | WSP-Compact | 0.4% | 8.3% | 0.0% | 13.88% | 0.0242 |
| MiniCPM5-2B | WSP-SG B1 rank 1, L24 (round 9) | 18.0% | 40.0% | 12.2% | 22.49% | 0.805 |
| MiniCPM5-2B | WSP-SG B2 rank 2, L24 (round 9) | 40.4% | 50.0% | 42.9% | 25.48% | 2.177 |
| MiniCPM5-2B | WSP-SG B2 rank 4, L24 (round 9) | 30.3% | 40.0% | 31.6% | 26.63% | 2.746 |
| MiniCPM5-2B | WSP-SG B2 rank 8, L24 (round 9) | 12.7% | 8.3% | 7.1% | 27.14% | 3.623 |
| MiniCPM5-2B | WSP-SG B3 rank 4, L24 (round 9) | 30.7% | 31.7% | 39.8% | 26.65% | 2.820 |
| MiniCPM5-2B | WSP-SG B2 rank 4 + null 8, L24 (round 9) | 4.5% | 13.3% | 7.1% | 26.63% | 0.987 |
| MiniCPM5-2B | WSP-SG B2 rank 4, L20 (round 9) | 8.6% | 6.7% | 9.2% | 26.64% | 4.227 |
| Qwen3-4B, Qwen3-8B, Qwen3-30B-A3B | every method | not run | not run | not run | - | - |

Counts, intervals, paired tests and every side metric are in `qwen3.5-0.8b/summary_round5.md`, `qwen3.5-0.8b/summary_round6.md`, `round7_summary.md` and `round8/round8_summary.md`. OBLITERATUS was not run (version 0.1.4 refuses the Qwen3.5-0.8B architecture).
The Qwen3.5-0.8B rows come from earlier code than the round-7 and round-8 rows (same classifier and decoding); the Qwen3.5-0.8B cells marked "round 8" are new measurements, the others are the published pilot values; on Gemma-4-E2B-it and MiniCPM5-2B the round-8 conditions were judged at judge batch size 4 instead of 8 (see the summaries). Heretic-ARA applies gradient optimisation, so it is not a direct weight edit.
MiniCPM5-2B Arditi is a result, not a gap: no single direction passed the preregistered selection filters (288 candidates; the candidate table is in `round8/selection/`). The MiniCPM5-2B Heretic edits have a large first-token KL in the study's prompt format (0.9998 and 0.6956) although Heretic's own scorer, which uses the same formula on different inputs (other harmless rows, a system prompt, the template's default thinking setting, a detected response prefix), rated the chosen trials at 0.09 and 0.06; see `round8/round8_summary.md`.
Method orderings by harmful rate, where they meet the preregistered rule (Holm-adjusted pairwise p < 0.05 on StrongREJECT-267), are listed per model in `round8/round8_summary.md`; no ordering across models is claimed.
WSP-SG (round 9, `round9/round9_summary.md`) is a WSP method with no LLM editor and no selection step: fixed rank-k edits on all residual writers of MiniCPM5-2B, exploratory and not preregistered. Every WSP-SG first-token KL is far above the 0.1 selection limit, so none of these edits is admissible by the study's convention; the rows show what the edit family can do, not what an editor chose.

## Not included, deliberately
Model weights, adapters and refusal-direction vectors (including the saved rank-1 factors), generated text, and any prompt corpus (consistent with `SECURITY.md` and `CONTRIBUTING.md`).
