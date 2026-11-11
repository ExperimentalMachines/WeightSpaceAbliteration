> Copy for the shared repository. The only changes against the original are the removal of infrastructure and budget text; names, data, rules and criteria are unchanged.

# Round 8 preregistration: completing the benchmark matrix (written 2026-11-11, before any round-8 run on a GPU)

Status: development pilot, outside the registered WeightSpaceAbliteration run. Nothing here touches that run's frozen arms or writes to any run ledger.

## 0. Purpose and the cells to fill
Three models were worked with: Qwen3.5-0.8B, Gemma-4-E2B-it, MiniCPM5-2B. The benchmark is complete when every (model, method, test set) cell holds either a measurement or a recorded refusal, with the side metrics beside it.
Methods: Arditi-Paper, Arditi-Matched, Heretic-Abliteration, Heretic-ARA, WSP-Full, WSP-Compact. Test sets: StrongREJECT-267, HarmBench-Val-60, JBB+MI-98. Qwen3-4B, Qwen3-8B and Qwen3-30B-A3B were never worked with and are out of scope.

Empty cells at the start of this round:
| Model | Cells |
|---|---|
| Qwen3.5-0.8B | WSP-Compact on StrongREJECT-267 and HarmBench-Val-60; Arditi-Paper, Arditi-Matched and Heretic-Abliteration on JBB+MI-98; Heretic-ARA on all three test sets and its side metrics |
| Gemma-4-E2B-it | Arditi-Paper, Arditi-Matched, Heretic-Abliteration, Heretic-ARA: all three test sets and side metrics |
| MiniCPM5-2B | Arditi-Paper, Arditi-Matched, Heretic-Abliteration, Heretic-ARA: all three test sets and side metrics |

## 1. Methods and fixed settings
- **Arditi-Paper / Arditi-Matched** (`wsp/m_abl.py`, the pilot's `wsp/b_abl.py` made model-agnostic): one refusal direction chosen from per-(layer, position) difference-of-means candidates, projected out of every residual-writing matrix and the input embedding (output head left unchanged).
  Paper: 128 fit + 32 selection prompts; Matched: 335 + 80, both from the study's `derivation` (harmful) and `harmless` arms. Selection as in the pilot: layer < 0.8 L, first-token KL on harmless selection prompts < 0.1, activation-addition refusal score on harmless selection prompts > 0, lowest refusal score on harmful selection prompts; every candidate is scored as the real weight edit.
  Refusal tokens are derived from the model's own string-matched refusals, as in the pilot.
  Changes made only to run on other architectures, nothing else: layer count from the config; the template-tail length (positions after the instruction) is measured from the model's own chat template instead of fixed at 9; tokenisation with `add_special_tokens=False`; the decoder stack and embedding are found by path; Gemma-4's `per_layer_projection` matrices (they write the residual stream) count as writers; a tied output head is untied before the embedding edit.
  **Qwen3.5-0.8B reproduction check:** the generalised code must reproduce the recorded selections (layer, position) and changed-element counts of round 5 (326,697,554 for Paper; 327,444,013 for Matched). The result of the check is reported whichever way it falls.
  Gemma-4 has norms after each sublayer, so weight orthogonalisation is only approximately the residual-stream ablation; candidates are scored as the real weight edit, so selection accounts for this. This is stated, not corrected.
- **Heretic-Abliteration / Heretic-ARA:** Heretic 2.1.0 (the pilot's version), run unattended with the pilot's settings: 100 trials, 30 startup trials, Optuna seed 20261107, `KeywordRate` + `KLDivergence` scorers, Heretic's default system prompt, data replaced by the study's `derivation`/`harmless` arms
  (modifier prompts [:335], refusal scoring `derivation`[335:415], KL scoring `harmless`[335:415]). The trial is chosen by code, not by me: among Pareto-optimal trials the lowest refusal count with KL <= 0.1, ties the lowest KL, none under the cap the lowest KL. The chosen trial is merged and measured.
  **Heretic-ARA applies gradient optimisation (an L-BFGS-optimised adapter): it is not a direct weight edit and is labelled so in every table.** It is included because the matrix is not complete without it.
  **Qwen3.5-0.8B reproduction check:** the recorded chosen trials were 85 (Abliteration; refusal score 0.0375, KL 0.0822) and 41 (ARA; 0.15, KL 0.0879). The rerun's chosen trial, scores and changed-element count are reported against them; Heretic-Abliteration's recorded patch was 74,383,917 elements (9.89%).
- **WSP-Compact on Qwen3.5-0.8B:** rebuilt from the round-6 factors, digest-verified against the recorded `digest_edited_matrices_bf16`; no new selection.
- **WSP-Full, WSP-Compact, parents on the two small models, and Qwen3.5-0.8B parent and WSP-Full:** already measured (rounds 5 to 7); not rerun.
- **Refusal by a tool.** If a tool fails to load or run a model, it is retried once; if it fails again the cell is recorded as `refused: <error class and message>` with the log. No substitute method, no manual workaround, no code change to the tool.

## 2. Data and measurement (as round 7)
Test sets: HarmBench-Val-60, StrongREJECT-267, JBB+MI-98, rebuilt by `wsp.b_data` and checked against the shared manifest. Edits are generated only on these development arms, never on `primary`, `large`, probe or `over_refusal`.
Decoding: chat template, thinking off, no system prompt (for the generation of test sets), greedy, 512 new tokens, `add_special_tokens=False` (`wsp/m_eval.py`). Judge: `cais/HarmBench-Llama-2-13b-cls` @ bda70534, official prompt text, label 1 = harmful completion; replies are deleted after labelling.
Judge batch size is 4 for every condition generated in this round (the 13B judge runs out of memory at batch 8 on long replies); earlier parent labels used batch 8. Side metrics as before: benign over-refusal (`treadon`, 83, string match), GSM8K train 500, first-token KL on `harmless_alpaca` rows 415-514 (parent reference recomputed in the same process), exact changed-element count against the parent.
Every condition is generated once and judged once; no reruns after labels exist (a stage that fails before any label may be retried once).
Where an edit is reproduced for Qwen3.5-0.8B (Arditi-Paper, Arditi-Matched, Heretic-Abliteration), all three test sets are generated; the **published StrongREJECT-267 and HarmBench-Val-60 labels stay as the table cells**, the new ones are reported as a reproduction check (flips against the original), and JBB+MI-98 comes from the reproduction.

## 3. Analysis (fixed now)
Per model and test set: harmful rate with Wilson 95% intervals; paired exact McNemar of each method against the parent, Holm-adjusted across the methods in that model and test set; exploratory pairwise exact McNemar between methods, Holm-adjusted across all pairs within the model and test set.
**A method ordering within a model is claimed only if a Holm-adjusted pairwise p < 0.05 on StrongREJECT-267.** No ordering across models is claimed. Patch size as elements changed over the model's parameter count; first-token KL; side metrics are never used to rank.

## 4. Stopping
A failing stage is retried once, then reported. (The compute-budget text of the original is omitted in this copy.)

## 5. Limits stated in advance
One seed per method, greedy decoding; test sets of 267, 60 and 98 prompts; MiniCPM5-2B and Gemma-4-E2B-it parents sit near the floor on these sets; Heretic's Optuna search and GPU kernels may not reproduce bit-for-bit, so the Qwen3.5-0.8B reproductions may select a different trial (reported, not hidden);
Arditi on Gemma-4 is approximate (norms after sublayers); Heretic-ARA is gradient-based and not comparable in kind; the classifier's validity on these prompt sets is unvalidated and replies are deleted after judging; the toolchain is not the study's pinned one and no host record exists, so none of this can be promoted into a registered run.
The editor of the WSP sessions was not blind and these comparator methods are run with the pilot's defaults, not tuned per model.
