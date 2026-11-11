# Round 8 results: completing the benchmark matrix (2026-11-12; pre-registration: `round8_prereg.md`). INCOMPLETE: stopped before the Heretic conditions could be measured.

Harmful completions as labelled by the HarmBench classifier (`cais/HarmBench-Llama-2-13b-cls` @ bda70534), greedy, 512 new tokens, no system prompt, judge batch size 4. Full tables, paired tests and the reproduction check are in `pilots/round8/analysis.json` .

| Model | Method | StrongREJECT-267 | HarmBench-Val-60 | JBB+MI-98 | Weights changed | KL | GSM8K | Over-refusal (of 83) |
|---|---|---|---|---|---|---|---|---|
| Qwen3.5-0.8B | Parent | 19.1% | 33.3% | 9.2% | 0 | 0 | 39.4% | 4 |
| Qwen3.5-0.8B | Arditi-Paper | 81.6% | 68.3% | 85.7% (new) | 43.42% | 0.0656 | 36.4% | 0 |
| Qwen3.5-0.8B | Arditi-Matched | 72.7% | 71.7% | 76.5% (new) | 43.52% | 0.0743 | 36.4% | 0 |
| Qwen3.5-0.8B | Heretic-Abliteration | 81.3% | 71.7% | **not completed** | 9.89% | 0.0288 | 37.6% | 0 |
| Qwen3.5-0.8B | Heretic-ARA | **not completed** | **not completed** | **not completed** | - | - | - | - |
| Qwen3.5-0.8B | WSP-Full | 76.4% | 73.3% | 78.6% | 6.38% | 0.0277 | 37.2% | 0 |
| Qwen3.5-0.8B | WSP-Compact | 74.5% (new) | 70.0% (new) | 67.3% | 3.81% | 0.0445 | 39.6% | 0 |
| Gemma-4-E2B-it | Parent | 1.1% | 6.7% | 1.0% | 0 | 0 | 51.4% | 11 |
| Gemma-4-E2B-it | Arditi-Paper | 62.2% | 78.3% | 78.6% | 16.70% | 0.0408 | 51.2% | 0 |
| Gemma-4-E2B-it | Arditi-Matched | 63.3% | 75.0% | 75.5% | 16.72% | 0.0490 | 51.4% | 0 |
| Gemma-4-E2B-it | Heretic-Abliteration | **not completed** | **not completed** | **not completed** | - | - | - | - |
| Gemma-4-E2B-it | Heretic-ARA | **not completed** | **not completed** | **not completed** | - | - | - | - |
| Gemma-4-E2B-it | WSP-Full | 38.6% | 53.3% | 60.2% | 1.64% | 0.0155 | 50.4% | 0 |
| Gemma-4-E2B-it | WSP-Compact | 37.5% | 53.3% | 60.2% | 1.59% | 0.0158 | 52.2% | 0 |
| MiniCPM5-2B | Parent | 0.4% | 8.3% | 0.0% | 0 | 0 | 72.4% | 59 |
| MiniCPM5-2B | Arditi-Paper | no admissible direction | no admissible direction | no admissible direction | - | - | - | - |
| MiniCPM5-2B | Arditi-Matched | no admissible direction | no admissible direction | no admissible direction | - | - | - | - |
| MiniCPM5-2B | Heretic-Abliteration | **not completed** | **not completed** | **not completed** | - | - | - | - |
| MiniCPM5-2B | Heretic-ARA | **not completed** | **not completed** | **not completed** | - | - | - | - |
| MiniCPM5-2B | WSP-Full | 1.1% | 15.0% | 1.0% | 4.36% | 0.0964 | 73.8% | 52 |
| MiniCPM5-2B | WSP-Compact | 0.4% | 8.3% | 0.0% | 13.88% | 0.0242 | 71.6% | 58 |

Cells marked "(new)" were measured in this round; the other Qwen3.5-0.8B cells are the published pilot values (unchanged), as fixed in the preregistration. Gemma-4-E2B-it and MiniCPM5-2B parent and WSP cells are round 7.

## What is missing and why
- **Heretic-Abliteration, all three models:** the 100-trial searches finished and the chosen trials are recorded (`selection/`: Qwen trial 75, refusal score 0.075, KL 0.053; MiniCPM trial 58, 0.075, KL 0.090; Gemma trial 68, 0.3875, KL 0.0999). The run was stopped during measurement, before any Heretic generation was judged, so there is no result. Qwen3.5-0.8B keeps its published StrongREJECT-267 and HarmBench-Val-60 values; its JBB+MI-98 cell is missing.
- **Heretic-ARA, all three models:** the searches reached trials 28 to 51 of 100 on a GPU host that was lost, and were not rerun.
- **MiniCPM5-2B Arditi:** not a gap but a result. No candidate passed the preregistered selection filters (288 candidates, each scored as the real weight edit; one had first-token KL < 0.1, 0.0951, and it fails the induction filter). The selection was retried once with the identical outcome; the candidate table is in `selection/MiniCPM5-2B__Arditi-Paper__no_admissible_direction_candidates.json`.
- Qwen3-4B, Qwen3-8B and Qwen3-30B-A3B were out of scope (never worked with).

## Reproduction check on Qwen3.5-0.8B (the model-agnostic Arditi code against the published pilot)
Arditi-Paper chose the same layer and position (10, -5) as the pilot; rate on StrongREJECT-267 82.4% against 81.6% published (12 labels flip one way, 14 the other, p = 0.85), HarmBench-Val-60 68.3% against 68.3% (3 / 3). Arditi-Matched: 73.0% against 72.7% (17 / 18, p = 1.0). Changed elements 326,632,813 against 326,697,554 (0.02% apart), so the edit is close but **not bit-identical** to the pilot's; the likely cause is numerical differences between toolchains, not verified. Published cells were kept in the table, as preregistered.

## Deviations and incidents
- **Two GPU hosts were lost** before their results were saved (the connection was dropped after a period without activity). The first lost all unjudged generations and the searches. The pipeline was then rebuilt to judge after every stage and to rerun Arditi from the saved directions (the directions came from the first run's selection, which had completed) instead of reselecting; the Heretic searches were rerun from scratch.
- **Judge batch size 4** for every condition measured in this round, as preregistered; the earlier Qwen pilot used 8.
- **Diagnostic added to `m_abl.run`** (writes the candidate table before the fail-closed error); the selection rule is unchanged.
- **Heretic needed `torchao >= 0.16`** (a dependency of Heretic 2.1.0 that the host image had too old); torch and transformers were not changed. The first attempt to run Heretic on all three models failed on this import and was repeated.

## Limits
Everything in `round8_prereg.md` section 5 applies. In addition: the matrix is incomplete (see above), so no method ordering is claimed for any model; the Qwen3.5-0.8B pilot comparison between methods (not significant) is unchanged.
