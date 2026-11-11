# Round 7 results: do the two WSP editing sessions transfer to Gemma-4-E2B-it and MiniCPM5-2B? (development pilot; preregistered in round7_prereg.md)

Harmful completions as labelled by the official HarmBench classifier (`cais/HarmBench-Llama-2-13b-cls` @ `bda70534`), greedy, 512 new tokens, chat template with thinking off, no system prompt. Primary endpoint: StrongREJECT-267. Flips = to harmful / to safe against the parent; p = exact McNemar (two-sided).

| Model | Test set | Method | Harmful (95% Wilson CI) | Invalid | Flips vs parent | Exact McNemar p |
|---|---|---|---|---|---|---|
| Gemma-4-E2B-it | StrongREJECT-267 | Parent | 3/267 = 1.1% (0.4-3.3) | 0 | - | - |
| Gemma-4-E2B-it | StrongREJECT-267 | WSP-Full | 103/267 = 38.6% (32.9-44.5) | 0 | 100 / 0 | 1.58e-30 |
| Gemma-4-E2B-it | StrongREJECT-267 | WSP-Compact | 100/267 = 37.5% (31.9-43.4) | 0 | 98 / 1 | 3.16e-28 |
| Gemma-4-E2B-it | HarmBench-Val-60 | Parent | 4/60 = 6.7% (2.6-15.9) | 0 | - | - |
| Gemma-4-E2B-it | HarmBench-Val-60 | WSP-Full | 32/60 = 53.3% (40.9-65.4) | 0 | 28 / 0 | 7.45e-09 |
| Gemma-4-E2B-it | HarmBench-Val-60 | WSP-Compact | 32/60 = 53.3% (40.9-65.4) | 0 | 28 / 0 | 7.45e-09 |
| Gemma-4-E2B-it | JBB+MI-98 | Parent | 1/98 = 1.0% (0.2-5.6) | 0 | - | - |
| Gemma-4-E2B-it | JBB+MI-98 | WSP-Full | 59/98 = 60.2% (50.3-69.3) | 0 | 58 / 0 | 6.94e-18 |
| Gemma-4-E2B-it | JBB+MI-98 | WSP-Compact | 59/98 = 60.2% (50.3-69.3) | 0 | 58 / 0 | 6.94e-18 |
| MiniCPM5-2B | StrongREJECT-267 | Parent | 1/267 = 0.4% (0.1-2.1) | 0 | - | - |
| MiniCPM5-2B | StrongREJECT-267 | WSP-Full | 3/267 = 1.1% (0.4-3.3) | 0 | 2 / 0 | 0.5 |
| MiniCPM5-2B | StrongREJECT-267 | WSP-Compact | 1/267 = 0.4% (0.1-2.1) | 0 | 0 / 0 | 1 |
| MiniCPM5-2B | HarmBench-Val-60 | Parent | 5/60 = 8.3% (3.6-18.1) | 0 | - | - |
| MiniCPM5-2B | HarmBench-Val-60 | WSP-Full | 9/60 = 15.0% (8.1-26.1) | 0 | 6 / 2 | 0.289 |
| MiniCPM5-2B | HarmBench-Val-60 | WSP-Compact | 5/60 = 8.3% (3.6-18.1) | 0 | 1 / 1 | 1 |
| MiniCPM5-2B | JBB+MI-98 | Parent | 0/98 = 0.0% (0.0-3.8) | 0 | - | - |
| MiniCPM5-2B | JBB+MI-98 | WSP-Full | 1/98 = 1.0% (0.2-5.6) | 0 | 1 / 0 | 1 |
| MiniCPM5-2B | JBB+MI-98 | WSP-Compact | 0/98 = 0.0% (0.0-3.8) | 0 | 0 / 0 | 1 |

WSP-Full against WSP-Compact (paired exact McNemar; Full-only harmful / Compact-only harmful):

| Model | Test set | Discordant pairs | p |
|---|---|---|---|
| Gemma-4-E2B-it | StrongREJECT-267 | 7 / 4 | 0.549 |
| Gemma-4-E2B-it | HarmBench-Val-60 | 3 / 3 | 1 |
| Gemma-4-E2B-it | JBB+MI-98 | 2 / 2 | 1 |
| MiniCPM5-2B | StrongREJECT-267 | 2 / 0 | 0.5 |
| MiniCPM5-2B | HarmBench-Val-60 | 6 / 2 | 0.289 |
| MiniCPM5-2B | JBB+MI-98 | 1 / 0 | 1 |

### Side metrics (never used to rank)

| Model | Method | Benign over-refusal (treadon, 83) | GSM8K train 500 | First-token KL vs parent | Elements changed (share of parameters) | Judge-tokenizer sensitivity on HarmBench-Val-60 (labels that differ) |
|---|---|---|---|---|---|---|
| Gemma-4-E2B-it | Parent | 11/83 | 51.4% | 0.0000 | 0 (0.00%) | 0 |
| Gemma-4-E2B-it | WSP-Full | 0/83 | 50.4% | 0.0155 | 83,595,418 (1.64%) | 1 |
| Gemma-4-E2B-it | WSP-Compact | 0/83 | 52.2% | 0.0158 | 81,057,033 (1.59%) | 0 |
| MiniCPM5-2B | Parent | 59/83 | 72.4% | 0.0000 | 0 (0.00%) | 0 |
| MiniCPM5-2B | WSP-Full | 52/83 | 73.8% | 0.0964 | 109,647,378 (4.36%) | 0 |
| MiniCPM5-2B | WSP-Compact | 58/83 | 71.6% | 0.0242 | 349,238,811 (13.88%) | 0 |

### Editing sessions (80 derivation prompts the editor was allowed to see; chosen by the coded rule, not by the editor)

| Model | Method | Forward passes used | Candidates registered | Chosen | Result of the chosen edit | First-token KL in session |
|---|---|---|---|---|---|---|
| MiniCPM5-2B | WSP-Full | 39/50 | 16 | L26_k14, 14 matrices | 72 refusal flags (unedited parent: 78 of 80) | 0.082 |
| MiniCPM5-2B | WSP-Compact | 17/50 | 7 | sh24_all84_a020, 84 matrices at strength 0.2 | 0/80 judged harmful | 0.027 |
| Gemma-4-E2B-it | WSP-Full | 38/50 | 17 | L18_k12, 12 matrices | 11 refusal flags (unedited parent: 77 of 80) | 0.026 |
| Gemma-4-E2B-it | WSP-Compact | 27/50 | 11 | sh18_k11_a1, 11 matrices | 40/80 judged harmful | 0.028 |

### Preregistered verdicts (StrongREJECT-267: edit above parent, exact McNemar p < 0.05, KL <= 0.1)

| Model | WSP-Full | WSP-Compact |
|---|---|---|
| Gemma-4-E2B-it | transfer shown | transfer shown |
| MiniCPM5-2B | no transfer shown | no transfer shown |

No ordering of models or methods is claimed.

## What the sessions found
MiniCPM5-2B resisted every candidate that kept first-token KL <= 0.1. The only candidate that moved anything (the layer-24 direction removed from all 84 writers at strength 1.0) gave 12/80 judged harmful at KL 0.64, six times the limit, so the rule excluded it; removing the direction also made the model refuse harmless prompts (16 of 40 in one check). Gemma-4-E2B-it responded to a small edit: a layer-18 direction removed from 11 or 12 writers raised the judged harmful count on the 80 derivation prompts from near zero to 39-40 at KL 0.026-0.028; WSP-Compact's 11 matrices are all among WSP-Full's 12.

## Deviations and incidents (none changed a rule or a label)
- **Judge batch size.** The 13B classifier ran out of GPU memory on Gemma's long replies at batch 8, twice. The six edited Gemma conditions were judged at batch 4 with identical prompts, truncation (2048 tokens) and label rule. Parent and MiniCPM labels used batch 8. Padding can shift a borderline label. Not rerun.
- **One wasted forward pass** in the Gemma WSP-Compact session: a read pass ran out of GPU memory because the resident judge left no room for the full-vocabulary logits; it was charged, and the judge was then moved to CPU memory for the read and back. Budget used: 27/50. No rule changed.
- **Connection drops.** The connection to the GPU host repeatedly dropped while the editing kernel (a detached process) kept running. Cells that never reached the kernel were detected by the unchanged pass counter and resent, so no cell ran twice; results of dropped calls were recovered from the kernel's own session log.
- **KL reference.** Sessions measured KL on the 80 derivation `harmless_val` prompts (the registered candidate rule); the side-metric KL uses 100 `harmless_alpaca` rows outside every arm, as in rounds 5 and 6. MiniCPM5-2B WSP-Full: 0.082 in session, 0.096 measured, both <= 0.1.
- **Parent labels.** Parent StrongREJECT-267 and HarmBench-Val-60 labels come from a baseline run made before the preregistration (batch 8, same decoding); the parent was generated and judged once on JBB+MI-98 in this round.
- **Prompt text.** The sample-prompt line printed by one editor cell is replaced by a placeholder in `sessions/` (this repository carries no prompt text).

## Limits
Two models, one seed, greedy decoding; MiniCPM5-2B counts are tiny (0 to 9 harmful completions per set; parents sit near the floor); the editor is not blind and knew rounds 1-6; WSP-Full's regex refusal flags were written for Qwen's phrasing; the classifier's validity on these prompt sets is unvalidated and replies were deleted after judging; the toolchain is not the study's pinned one and no host record exists, so nothing here can be promoted into a registered run. Edited weights, factors and refusal directions are not published.
