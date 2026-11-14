> **SUPERSEDED.** Round-1 report. Several claims here were overstated; see `experiment_audit.md` and `results_round2.md`.

# Results: editing weights to weaken over-refusal in Qwen3.5-0.8B (2026-11-05)

No fine-tuning. Direct weight edits only; gradients used only to score weights. Greedy decoding, thinking off, string-match refusal labels
(a lower bound on refusals; see `stage1_report.md`). Raw files in `results/`. Edited weights were not saved or published.

## Headline
**The guardrail was not broken in any strong sense.** The best edit that respects the safety stop rule lowers refusal of benign-but-edgy
prompts from 36.8% to 33.1% (-3.7 points, 95% CI -5.4 to -2.0) on held-out OR-Bench-Hard, and changes harmful-prompt refusal by
-1.4 points. The model is not "unlocked"; the effect is small but real. The published reference (Wang et al., Llama 2 7B) went 14.8% to 65.6%
benign compliance, a far larger change.

## What was tried (all choices made on validation sets; final sets used once)
| Arm | Idea | Outcome |
|---|---|---|
| A, direction edit | Take the "over-refusal" direction (benign-refused minus benign-answered activations, with the ordinary harmful-refusal direction removed from it) and project it out of the matrices that write into the residual stream | Selective but weak. Strong settings also cut harmful refusal (layers 12-18 at full strength: benign 16-28%, harmful 41-56%; rejected) |
| C, importance-score edit | Zero the weights with highest gradient x weight for the model's own benign refusals, protecting weights important for harmful refusals and for math | Not selective. 18 settings from 64 to 2,048 weights: benign and harmful refusal fell together about 1:1; none with a real effect passed the stop rule. Zeroing 1,024 weights took benign refusal 42% to 12% and harmful 69% to 42% |
| Control | Zero 131,072 random writer weights | No effect (benign 42.0%, harmful 67.0%), so the weights in arm C do matter; they just carry refusal in general |
| B, LLM-written edit | Planned as optional | Not run (decided out of scope) |

## Held-out final results (never used for any choice)
Refusal rate, % (n in header). GSM8K = accuracy on 250 problems.

| Condition | XSTest safe (250) | OR-Bench-Hard (819) | XSTest unsafe (200) | OR-Bench-Toxic (355) | GSM8K |
|---|---|---|---|---|---|
| Unedited | 4.0 | 36.8 | 66.5 | 65.9 | 40.4 |
| Full edit (48 matrices, all layers) | 4.8 | 35.7 | 66.0 | 66.2 | 37.6 |
| **Minimal edit (16 matrices, layers 12-19)** | 4.8 | **33.1** | 65.5 | 64.2 | 38.4 |
| Unedited, writer matrices at int8 | 4.0 | 36.1 | 68.0 | 65.9 | |
| Minimal edit + int8 | 5.2 | 32.5 | 67.0 | 64.2 | |
| Unedited, writer matrices at int4 | 29.6 | 57.1 | 65.5 | 77.5 | |
| Minimal edit + int4 | 20.0 | 53.2 | 57.5 | 74.9 | 19.2 |

Paired change of the minimal edit vs unedited (percentage points, 95% bootstrap CI, prompts flipped to refuse / to answer):
OR-Bench-Hard -3.7 [-5.4, -2.0] (9 / 39); XSTest safe +0.8 [-0.8, +2.4]; XSTest unsafe -1.0 [-4.5, +2.5]; OR-Bench-Toxic -1.7 [-3.9, +0.6].
Harmful refusal pooled over both harmful sets: 66.1% to 64.7%. Stop rule (no more than 2 points): passed, but OR-Bench-Toxic alone sits at -1.7.
GSM8K 40.4 to 38.4 is within noise for n = 250 (about +/-3 points).

## Important caveat: the validation gain did not generalise
On the 200-prompt validation set the full edit looked like 42.0% to 35.0% benign refusal. On the final set the same edit gives
36.8% to 35.7% (CI -3.4 to +1.2): no detectable effect. That earlier number was selection noise from picking the best of many settings.
The minimal edit was also chosen on validation (best of 15 subsets); its final-set effect (-3.7) is an unbiased estimate because the final set
played no part in choosing it.

## Patch size
| | Full edit | Minimal edit |
|---|---|---|
| Matrices changed | 48 | 16 |
| bf16 elements that differ | 113,090,587 (15.0% of 752M) | 37,580,493 (5.0%) |
| As a sparse patch (6 bytes per changed weight) | 678.5 MB | 225.5 MB |
| Compressed XOR delta (zlib) | 131.0 MB | 43.4 MB |
| **As a rank-1 recipe (one direction + one row per matrix, fp16)** | **272,384 bytes** | **92,160 bytes (90 KiB)** |
| Whole checkpoint (bf16, text model) | 1,504,786,048 bytes | |

So the "0.016% of weights" framing of the Sparks result does not describe a direction-projection edit: this edit touches 5% of all weights. Its
real information content is tiny, though: 90 KiB, 0.006% of the checkpoint size, if shipped as a rank-1 recipe instead of a weight diff.

## Visibility (weights only; `results/stage6_visibility.json`)
- Each edited matrix changes by 2.4% to 2.9% of its norm.
- The change is rank 1 in all 16 matrices (at least 99.6% of its energy in one singular direction), all along the same direction (cosine ~1.0 with the edit direction).
- Energy of an edited matrix along that direction is 7.7e-5 (after) versus 1.2e-3 (before) and 1.3e-3 (unedited matrices): about 17 times less than normal.
 An auditor who knows or guesses the direction sees it at once. **Not tested:** whether an auditor without the base model and without the direction
 can find it; related detection work exists (arXiv:2607.01854, not read).

## Quantization
8-bit round-trip of the edited matrices: the effect survives (benign refusal 32.5% vs 33.1%). 4-bit round-trip (simple symmetric per-row) damages the unedited model
itself (benign refusal 36.8% to 57.1%), so 4-bit survival cannot be judged with this quantizer; relative to the int4 baseline the edit lowers benign refusal by about 4 points
(57.1 to 53.2), but harmful refusal on XSTest fell 8 points there. Only the 48 writer matrices were quantized; everything else stayed bf16. This is not a real GGUF/AWQ test.

## Limits
One model, one seed-free greedy run, string-match labels, no LLM judge, no human check beyond 18 replies, 16-matrix subset selected from 15 candidates on 200+100 prompts,
GSM8K without thinking mode, over-refusal measured mainly on one benchmark (XSTest-safe is near the floor at 4%). The pre-set gate (XSTest-safe refusal at least 10%) failed;
OR-Bench-Hard was used instead (deviation recorded in `stage1_report.md`).

## Cost
| Item | Cost |
|---|---|
| (omitted) | execution-host and billing details are not published here |
| (omitted) | execution-host and billing details are not published here |
| (omitted) | execution-host and billing details are not published here |
About 25 minutes of host time were wasted on two log-watcher scripts that hung. The host is stopped (not deleted); the 20 GB storage still bills a small storage fee.
