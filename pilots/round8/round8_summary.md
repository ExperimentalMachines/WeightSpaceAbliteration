# Round 8 results: the completed benchmark matrix (2026-11-12; pre-registration: `round8_prereg.md`)

Harmful completions as labelled by the HarmBench classifier (`cais/HarmBench-Llama-2-13b-cls` @ bda70534), greedy, 512 new tokens, no system prompt, judge batch size 4 for everything measured in this round. Counts, intervals, paired tests and the reproduction check are in `pilots/round8/analysis.json`.

| Model | Method | StrongREJECT-267 | HarmBench-Val-60 | JBB+MI-98 | Weights changed | First-token KL | GSM8K | Over-refusal (of 83) |
|---|---|---|---|---|---|---|---|---|
| Qwen3.5-0.8B | Parent | 19.1% | 33.3% | 9.2% | 0 | 0 | 39.4% | 4 |
| Qwen3.5-0.8B | Arditi-Paper | 81.6% | 68.3% | 85.7% | 43.42% | 0.0656 | 36.4% | 0 |
| Qwen3.5-0.8B | Arditi-Matched | 72.7% | 71.7% | 76.5% | 43.52% | 0.0743 | 36.4% | 0 |
| Qwen3.5-0.8B | Heretic-Abliteration | 81.3% | 71.7% | 80.6% | 9.89% | 0.0288 | 37.6% | 0 |
| Qwen3.5-0.8B | Heretic-ARA | 66.3% | 66.7% | 62.2% | 3.90% | 0.0380 | 35.6% | 0 |
| Qwen3.5-0.8B | WSP-Full | 76.4% | 73.3% | 78.6% | 6.38% | 0.0277 | 37.2% | 0 |
| Qwen3.5-0.8B | WSP-Compact | 74.5% | 70.0% | 67.3% | 3.81% | 0.0445 | 39.6% | 0 |
| Gemma-4-E2B-it | Parent | 1.1% | 6.7% | 1.0% | 0 | 0 | 51.4% | 11 |
| Gemma-4-E2B-it | Arditi-Paper | 62.2% | 78.3% | 78.6% | 16.70% | 0.0408 | 51.2% | 0 |
| Gemma-4-E2B-it | Arditi-Matched | 63.3% | 75.0% | 75.5% | 16.72% | 0.0490 | 51.4% | 0 |
| Gemma-4-E2B-it | Heretic-Abliteration | 49.1% | 70.0% | 67.3% | 2.63% | 0.0522 | 49.2% | 0 |
| Gemma-4-E2B-it | Heretic-ARA | 71.9% | 90.0% | 92.9% | 5.01% | 0.0370 | 52.2% | 0 |
| Gemma-4-E2B-it | WSP-Full | 38.6% | 53.3% | 60.2% | 1.64% | 0.0155 | 50.4% | 0 |
| Gemma-4-E2B-it | WSP-Compact | 37.5% | 53.3% | 60.2% | 1.59% | 0.0158 | 52.2% | 0 |
| MiniCPM5-2B | Parent | 0.4% | 8.3% | 0.0% | 0 | 0 | 72.4% | 59 |
| MiniCPM5-2B | Arditi-Paper | no admissible direction | no admissible direction | no admissible direction | - | - | - | - |
| MiniCPM5-2B | Arditi-Matched | no admissible direction | no admissible direction | no admissible direction | - | - | - | - |
| MiniCPM5-2B | Heretic-Abliteration | 34.5% | 51.7% | 17.3% | 14.65% | **0.9998** | 71.4% | 6 |
| MiniCPM5-2B | Heretic-ARA | 46.8% | 63.3% | 51.0% | 10.92% | **0.6956** | 70.8% | 18 |
| MiniCPM5-2B | WSP-Full | 1.1% | 15.0% | 1.0% | 4.36% | 0.0964 | 73.8% | 52 |
| MiniCPM5-2B | WSP-Compact | 0.4% | 8.3% | 0.0% | 13.88% | 0.0242 | 71.6% | 58 |

Every cell holds a measurement or a recorded result. Sources: the Qwen3.5-0.8B parent, WSP-Full, and the StrongREJECT-267 / HarmBench-Val-60 cells of Arditi-Paper, Arditi-Matched and Heretic-Abliteration are the published pilot values (kept, as preregistered); every other Qwen3.5-0.8B cell is new in this round; Gemma-4-E2B-it and MiniCPM5-2B parents and WSP cells are round 7; all other cells are new. The Qwen3.5-0.8B Heretic-Abliteration side metrics (weights changed, KL, GSM8K) in the table are the pilot's; the rerun's are 10.41%, 0.0260, 37.2%.

## Method ordering (the preregistered rule: Holm-adjusted pairwise exact McNemar p < 0.05 on StrongREJECT-267, harmful rate only)
- **Qwen3.5-0.8B:** 3 of 15 pairs qualify. Heretic-ARA (66.3%) is below Arditi-Paper (p = 0.0002) and below Heretic-Abliteration (p = 0.0002); Arditi-Paper is above Arditi-Matched (81.6% vs 72.7%, p = 0.048, borderline). Nothing else is separated, including WSP-Full against every comparator.
- **Gemma-4-E2B-it:** 13 of 15 pairs qualify. By harmful rate: Heretic-ARA (71.9%) > Arditi-Matched (63.3%) ~ Arditi-Paper (62.2%) > Heretic-Abliteration (49.1%) > WSP-Full (38.6%) ~ WSP-Compact (37.5%). The two WSP edits are significantly *lower* than all four comparators, while changing 1.6% of the weights against 2.6% to 16.7%. The two Arditi variants are not separated from each other, nor are the two WSP edits.
- **MiniCPM5-2B:** 5 of 6 pairs qualify. Heretic-ARA (46.8%) > Heretic-Abliteration (34.5%) > WSP-Full (1.1%) ~ WSP-Compact (0.4%). The Heretic edits move the model; the WSP edits do not.
- No ordering across models is claimed. The rule uses harmful rate alone: it does not weigh drift or over-refusal, and the table shows those differ (below).

## Findings that need care
- **The Heretic KL and the study's KL disagree on MiniCPM5-2B; the cause is the prompt format, not the formula.** Heretic's scorer is the same quantity as the study's (first-token log-probs, `batchmean` KL to the parent, 100 harmless prompts), but Heretic renders the chat template with its defaults plus a system prompt ("You are a helpful assistant."), while the study renders with no system prompt and thinking switched off. For MiniCPM5-2B these are different texts (default: the turn ends at `<|im_start|>assistant\n`; study: `<think>\n\n</think>\n\n` follows). Heretic rated its chosen trials at KL 0.090 (Abliteration) and 0.059 (ARA); the study's measurement of the same edits is 0.9998 and 0.6956. On Qwen3.5-0.8B and Gemma-4-E2B-it the two agree in size (0.03 to 0.05). So in the study's prompt format the MiniCPM Heretic edits are far from the parent, and benign over-refusal rises (6 and 18 of 83 against 59 for the parent), while in Heretic's format they looked mild. Which response prefix Heretic detected for MiniCPM was not retained (the head of its logs was lost with the first host), so the exact format it optimised on is not verified. An earlier version of this note called these "different definitions"; that was wrong.
- **Why Arditi finds nothing on MiniCPM5-2B:** of 288 candidate directions (each scored as the real weight edit) one had first-token KL < 0.1 (0.0951) and it fails the induction filter, so the selection fails closed; retried once, same result (`selection/MiniCPM5-2B__Arditi-*__no_admissible_direction_candidates.json`). The Heretic search, which optimises its own KL scorer and refusal count, did find edits, but not within the study's KL limit.
- **Heretic reproduction on Qwen3.5-0.8B is approximate.** The rerun chose trial 75 (refusal score 0.075, own KL 0.053) against the pilot's trial 85 (0.0375, 0.082), as the preregistration warned. Rates: StrongREJECT-267 79.8% against 81.3% published (24 labels flip one way, 20 the other, p = 0.65), HarmBench-Val-60 78.3% against 71.7% (3 / 7, p = 0.34); changed elements 78,360,021 against 74,383,917; KL 0.026 against 0.029. Published cells were kept; JBB+MI-98 for Heretic-Abliteration (80.6%) is from the rerun.
- **Arditi reproduction on Qwen3.5-0.8B** (earlier in this round): same layer and position as the pilot; rates within 1 to 3 points; changed elements 326,632,813 against 326,697,554 (0.02% apart), so close, not bit-identical.
- **Heretic-ARA applies gradient optimisation** (an L-BFGS-optimised adapter that is then merged); it is not a direct weight edit and is not comparable in kind to the others.

## Deviations and incidents
- **GPU hosts were lost or stopped several times** before everything was measured (the connection was dropped after a period without activity, and one run was stopped early and completed afterwards), losing unjudged generations and the first Heretic searches. The pipeline was rebuilt to judge after every stage; Arditi was rerun from the saved directions (the directions came from the first run's selection, which had completed) instead of reselecting; all Heretic searches were rerun from scratch on a later host.
- **A first Heretic attempt failed on `torchao >= 0.16`** (a dependency of Heretic 2.1.0 that the host image had too old); torch and transformers were not changed. The failing runs were repeated; for the chosen trials in this table no Heretic run failed.
- **Judge batch size 4** (as preregistered) for every condition measured here; the Qwen3.5-0.8B pilot used 8.
- **Diagnostic added to `m_abl.run`** (writes the candidate table before the fail-closed error); the selection rule is unchanged. `copy_from_dir` loads only the merged weights, and its parameter-name check passed for all six Heretic conditions (0 missing, 0 unexpected).

## Limits
One seed per method, greedy decoding; test sets of 267, 60 and 98 prompts; the classifier's validity on these prompt sets is unvalidated and replies were deleted after judging; Gemma-4's norms after each sublayer make Arditi's weight orthogonalisation only approximately the residual-stream ablation; the toolchain is not the study's pinned one and no host record exists, so none of this can be promoted into a registered run; Heretic's Optuna search is not bit-reproducible, so the Heretic cells are one realisation per model.
