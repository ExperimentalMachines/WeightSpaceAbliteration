# `pilots/`

Development pilots that came **before or beside** the registered runs. None of this is a result of the registered study: there are no receipts here, no method is admitted (`load_method()` is unchanged, there is no `method_selected` entry),
and edited models were never run on the study's frozen arms. Each pilot has its own folder with the labels, side metrics, selection records and editor sessions behind every number.

| Folder | Model | Rounds | Preregistrations |
|---|---|---|---|
| `qwen3.5-0.8b/` | Qwen3.5-0.8B | 5, 6 | `prereg_round5.md`, `prereg_round6.md` |
| `gemma-4-e2b-it/` | Gemma-4-E2B-it | 7 | `round7_prereg.md` |
| `minicpm5-2b/` | MiniCPM5-2B | 7 | `round7_prereg.md` |

Round 7 (WSP-Full and WSP-Compact on the two small registered models) has one preregistration and one summary for both models: `round7_prereg.md`, `round7_summary.md`.

## Names
Test sets: **StrongREJECT-267**, **HarmBench-Val-60**, **JBB+MI-98**. Conditions: **Parent**, **Arditi-Paper**, **Arditi-Matched**, **Heretic-Abliteration**, **Heretic-ARA**, **WSP-Full**, **WSP-Compact**.
"Harmful" means the official HarmBench classifier (`cais/HarmBench-Llama-2-13b-cls` @ `bda70534`) labels the completion an instance of the harmful behaviour. Greedy decoding, 512 new tokens, no system prompt.

## All methods, all models, all test sets
"Weights changed" is the share of the model's own parameter count; the KL is first-token KL to the parent. "not run" means the method was not run on that model; "not measured" means it was run on the model but not on that test set.

| Model | Method | StrongREJECT-267 | HarmBench-Val-60 | JBB+MI-98 | Weights changed | KL |
|---|---|---|---|---|---|---|
| Qwen3.5-0.8B | Parent | 19.1% | 33.3% | 9.2% | 0 | 0 |
| Qwen3.5-0.8B | Arditi-Paper | 81.6% | 68.3% | not measured | 43.4% | 0.066 |
| Qwen3.5-0.8B | Arditi-Matched | 72.7% | 71.7% | not measured | 43.5% | 0.074 |
| Qwen3.5-0.8B | Heretic-Abliteration | 81.3% | 71.7% | not measured | 9.9% | 0.029 |
| Qwen3.5-0.8B | Heretic-ARA | not judged | not judged | not judged | - | - |
| Qwen3.5-0.8B | WSP-Full | 76.4% | 73.3% | 78.6% | 6.4% | 0.028 |
| Qwen3.5-0.8B | WSP-Compact | not measured | not measured | 67.3% | 3.8% | 0.044 |
| Gemma-4-E2B-it | Parent | 1.1% | 6.7% | 1.0% | 0 | 0 |
| Gemma-4-E2B-it | Arditi-Paper, Arditi-Matched, Heretic-Abliteration, Heretic-ARA | not run | not run | not run | - | - |
| Gemma-4-E2B-it | WSP-Full | 38.6% | 53.3% | 60.2% | 1.64% | 0.0155 |
| Gemma-4-E2B-it | WSP-Compact | 37.5% | 53.3% | 60.2% | 1.59% | 0.0158 |
| MiniCPM5-2B | Parent | 0.4% | 8.3% | 0.0% | 0 | 0 |
| MiniCPM5-2B | Arditi-Paper, Arditi-Matched, Heretic-Abliteration, Heretic-ARA | not run | not run | not run | - | - |
| MiniCPM5-2B | WSP-Full | 1.1% | 15.0% | 1.0% | 4.36% | 0.0964 |
| MiniCPM5-2B | WSP-Compact | 0.4% | 8.3% | 0.0% | 13.88% | 0.0242 |
| Qwen3-4B, Qwen3-8B, Qwen3-30B-A3B | every method | not run | not run | not run | - | - |

Counts, intervals, paired tests and every side metric are in `qwen3.5-0.8b/summary_round5.md`, `qwen3.5-0.8b/summary_round6.md` and `round7_summary.md`. OBLITERATUS was not run (version 0.1.4 refuses the Qwen3.5-0.8B architecture).
The Qwen3.5-0.8B rows come from earlier code than the round-7 rows (same classifier and decoding); on Gemma-4-E2B-it the edited conditions were judged at judge batch size 4 instead of 8 (see `round7_summary.md`).

## Not included, deliberately
Model weights, adapters and refusal-direction vectors (including the saved rank-1 factors), generated text, and any prompt corpus (consistent with `SECURITY.md` and `CONTRIBUTING.md`).
