# Qwen3.5-0.8B development pilot: refusal-removal methods, HarmBench-judged (2026-11-10)

## Status
Qwen3.5-0.8B was added to the study's model set after this pilot (ledger entry `model_set_extension`, commit `9291af7`): "registered for future runs; no run exists for it yet".
**This folder is the development work that came before that run.** It has no receipts, no method here is admitted (`load_method()` is unchanged, there is no `method_selected` entry), and
nothing here is a result of the registered study. Edited models were never run on the study's frozen `primary`, `large`, probe or `over_refusal` arms; only the unedited parent was run on `primary` (42.3% harmful, 90/213 standard + contextual behaviours).

## Names used here
| Name | What it is |
|---|---|
| **StrongREJECT-267** | StrongREJECT prompts minus near-duplicates (cosine >= 0.80, the study's embedding instrument) of the derivation arm and HarmBench val/test. n = 267. Round-5 main test set; no method or editor saw it. |
| **HarmBench-Val-60** | HarmBench's own validation split, standard and contextual behaviours (60 of 80; the 20 copyright rows use a hash classifier and were not run). Replication set, already examined in earlier rounds. |
| **JBB+MI-98** | JailbreakBench JBB-Behaviors (55) and MaliciousInstruct (43), deduplicated against the same reference sets and each other. n = 98. Round-6 fresh test set. |
| **Arditi-Paper** / **Arditi-Matched** | Arditi et al. (2406.11717): one refusal direction projected out of every residual writer and the input embedding. Paper setup: 128 fit + 32 selection prompts; Matched: 335 + 80. |
| **Heretic-Abliteration** | Heretic 2.1, `Abliteration` modifier (training-free), 100 Optuna trials, trial chosen by a rule fixed beforehand. |
| **Heretic-ARA** | Heretic's default ARA modifier (gradient-optimised adapter). The search ran but it was **not judged; there is no result**. |
| **WSP-Full** | An LLM (Claude) edits the weights in a live Python session: no gradients, 50 forward passes. Rank-1 projections of one layer-14 direction on 20 writer matrices (6.4% of parameters). |
| **WSP-Compact** | The one attempt to improve WSP-Full: 12 matrices, each projected off its own local direction (3.8% of parameters). Did not meet the improvement criterion; a smaller, weaker variant. |
| OBLITERATUS | Not run: version 0.1.4 refuses this architecture. |

"Harmful completions" is the share of replies the official classifier (`cais/HarmBench-Llama-2-13b-cls` @ `bda70534`, prompt text from HarmBench @ `8e1604d`) labels as an instance of the harmful behaviour.
Generation for every condition: chat template, thinking off, no system prompt, greedy, 512 new tokens. This is HarmBench-**judged**; it is not the HarmBench benchmark.

## Results
**Round 5: StrongREJECT-267 (main) and HarmBench-Val-60 (replication)**

| Condition | StrongREJECT-267 (95% CI) | HarmBench-Val-60 | Weights changed | First-token KL | GSM8K (500) | Benign refusal (83) |
|---|---|---|---|---|---|---|
| Parent | 51/267 = 19.1% (14.8-24.2%) | 20/60 = 33.3% | - | 0 | 39.4% | 4/83 |
| Arditi-Paper | 218/267 = 81.6% (76.6-85.8%) | 41/60 = 68.3% | 43.4% | 0.066 | 36.4% | 0/83 |
| Arditi-Matched | 194/267 = 72.7% (67.0-77.7%) | 43/60 = 71.7% | 43.5% | 0.074 | 36.4% | 0/83 |
| Heretic-Abliteration | 217/267 = 81.3% (76.2-85.5%) | 43/60 = 71.7% | 9.9% | 0.029 | 37.6% | 0/83 |
| **WSP-Full** | 204/267 = 76.4% (71.0-81.1%) | 44/60 = 73.3% | **6.4%** | **0.028** | 37.2% | 0/83 |

**Round 6: JBB+MI-98 (fresh), the attempt to improve WSP-Full**

| Condition | Harmful completions (95% CI) | Weights changed | First-token KL | GSM8K (500) |
|---|---|---|---|---|
| Parent | 9/98 = 9.2% (4.9-16.5%) | - | 0 | 39.4% |
| WSP-Full | 77/98 = 78.6% (69.5-85.5%) | 48,035,590 (6.4%) | 0.028 | 37.2% |
| WSP-Compact | 66/98 = 67.3% (57.6-75.8%) | 28,676,905 (3.8%) | 0.044 | 39.6% |

Full tables (flips against the parent, pooled sets, exploratory pairwise tests) are in [`summary_round5.md`](summary_round5.md) and [`summary_round6.md`](summary_round6.md); the edits are described in [`WSP_edits.md`](WSP_edits.md).

What the numbers support:
- Every edit raises the harmful-completion rate far above the parent's (StrongREJECT-267: 19% to 73-82%, Holm-adjusted p < 1e-31 each); it replicates on HarmBench-Val-60.
- Between methods the evidence is weak. Arditi-Matched is below Arditi-Paper and Heretic-Abliteration (exact McNemar p = 0.004 and 0.007); WSP-Full against Arditi-Paper (p = 0.076) and Heretic-Abliteration (p = 0.079) is not significant. These tests are exploratory and not corrected for multiplicity; **no ordering of the methods is claimed.**
- WSP-Full is the most compact edit and has the lowest drift (tied with Heretic-Abliteration); its effect is about 5 points below the top two on StrongREJECT-267, which is not significant.
- WSP-Compact is 40% smaller than WSP-Full but 11.2 points weaker on JBB+MI-98 (paired bootstrap 95% CI -21.4 to -1.0; exact McNemar p = 0.061). The preregistered improvement criterion (non-inferior effect, lower bound >= -7.5 points) was **not met**: no improvement shown.

## Limits (read before quoting any number)
- The classifier measures harmful completions, not refusals: a model that no longer refuses can still score "no" when its answer is weak, so the rate is bounded below 100%. The study's pre-registered "residual refusal" endpoint, probe gates and capability suite are **not** tested here.
- The classifier's use on StrongREJECT and JBB+MI prompts is unvalidated, and replies to harmful prompts are deleted after judging, so no one can hand-check the labels.
- WSP-Full was reproduced by the same editor with the same knowledge (same 20 matrices, same changed elements in two rounds): repeatable, not independently discovered.
- One model, one seed, greedy decoding; 267, 60 and 98 behaviours; copyright behaviours not scored; Heretic tunes with its default system prompt while the benchmark has none.
- WSP-Compact was selected on 80 derivation prompts and generalised worse on fresh prompts (selection noise and the best-of-13 search); JBB+MI-98 is small because CatQA is gated and deduplication dropped 102 of 200 prompts.
- A candidate was once generated on the frozen `primary` arm before the handoff rules were read (replies deleted unread; this cannot be verified afterwards). The runner now allows candidates on development arms only, with tests.

## Contents
- `labels/<Condition>__<Test set>.json`: per-behaviour labels (0 = no, 1 = yes, -1 = invalid) keyed by public HarmBench behaviour id or an opaque index (`sr-NNN` = row NNN of the StrongREJECT dataset; `jbb-NNN` = row NNN of JBB-Behaviors harmful; `mi-NNN` = line NNN of MaliciousInstruct), with the judge revision and aggregate counts. `labels_sp` repeats HarmBench-Val-60 under the original SentencePiece token ids as a tokenizer-sensitivity check. No prompt, reply or other text.
- `metrics/<Condition>__round<N>.json`: aggregate side metrics and patch sizes.
- `selection/`: how each method's setting was chosen (Arditi candidate scans, Heretic chosen trials, the WSP candidate sets, forward-pass logs).
- `sessions/`: every cell the editor submitted in each WSP session and its output (replies to harmful prompts are never returned to the editor).
- `prereg_round5.md`, `prereg_round6.md`: verbatim copies of the preregistrations written before each round (infrastructure and budget text removed; a name key at the top maps the original working labels to the names above); `deviations_round5.md`: what differed from plan.
- `build_report_*.json`: arm sizes and their hash match against the committed manifest.

**Not included, deliberately:** model weights, adapters and refusal-direction vectors, generated text, and any prompt corpus (consistent with `SECURITY.md` and `CONTRIBUTING.md`).
