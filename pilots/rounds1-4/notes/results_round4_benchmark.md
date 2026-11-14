# Round 4: four weight-edit methods on Qwen3.5-0.8B, official HarmBench classifier (development pilot, 2026-11-10)

**Status: development pilot, not a registered result.** Rules were fixed in `prereg_round4.md` before the editing session. After the co-worker's handoff
(section 9: "measure nothing against the frozen arms until review admits a method"), every edited model was judged on HarmBench's own **validation** split, not on the
study's `primary` arm. Only the unedited parent was generated on `primary` (the exempt baseline).

Parent: `Qwen/Qwen3.5-0.8B` @ `2fc06364` (the post-trained model; `-Base` has no refusals to remove). Judge: `cais/HarmBench-Llama-2-13b-cls` @ `bda70534`, prompt text parsed from the
pinned HarmBench commit, bf16. Generation: chat template, thinking off, greedy, 512 new tokens, contextual behaviours as `context --- behaviour`.
Data: the study's `derivation`, `harmless` and `primary` arms were rebuilt with the study's own `build_splits.py` and match the committed manifest sha256 exactly (415 / 415 / 293);
`harmbench_val` (80) matches too.

## Results (HarmBench val, 60 behaviours: 41 standard + 19 contextual; the 20 copyright rows use a hash classifier and were not run)

| Condition | Harmful completions (ASR) | 95% CI | Flips vs parent (to harmful / to safe) | McNemar p | XSTest-safe refusal | GSM8K (n=250) | First-token KL vs parent | Elements changed |
|---|---|---|---|---|---|---|---|---|
| Parent | 20/60 = 33.3% | 22.7-45.9% | - | - | 11/250 = 4.4% | 39.6% | 0 | - |
| Abliteration (Arditi) | 41/60 = 68.3% | 55.8-78.7% | 27 / 6 | 0.0003 | 0/250 | 36.0% | 0.069 | 326.7M (**43.4%** of unique parameters; 210M of them in the input embedding) |
| Heretic 2.1 (`Abliteration` modifier, 60 trials) | 45/60 = 75.0% | 62.8-84.2% | 27 / 2 | 2e-6 | 1/250 | 35.6% | 0.028 | 40.3M (**5.4%**) |
| **WSP (Claude, this round)** | 44/60 = 73.3% | 61.0-82.9% | 26 / 2 | 3e-6 | 0/250 | 35.6% | 0.026 | 48.0M (**6.4%**); rank-1 factors on 20 matrices = **109 KiB** |
| OBLITERATUS `advanced` | not run | | | | | | | refused by the tool: see below |

Parent on the registered `primary` arm (exempt baseline, 213 standard + contextual behaviours): 90/213 = 42.3% (95% CI 35.8-49.0%), 0 invalid.

## What the numbers support
- Every method that ran raises harmful completions from 33% to 68-75% on the development arm; each difference from the parent is far outside noise (paired exact tests above).
- **No difference between the three methods could be detected** at n = 60: paired exact tests give Arditi vs Heretic 3/7 discordant, p = 0.34; Arditi vs WSP 4/7, p = 0.55; Heretic vs WSP 5/4, p = 1. That is lack of power, not evidence of equivalence.
- Over-refusal on harmless-but-edgy prompts also fell from 4.4% to 0-0.4% for all three (string-match refusal on XSTest-safe, not a validated over-refusal measure).
- WSP and Heretic moved the first-token distribution least (KL 0.026 / 0.028); Arditi moved it most (0.069). Arditi changed the input embedding (210M elements); its output head was untied and left unchanged.
- GSM8K fell 3.6-4.0 points for all three (parent 39.6%). At n = 250 the 95% interval is about +-6 points, so this neither shows damage nor rules it out; the study's 2-point margin cannot be tested here.
- The classifier asks for unambiguous, non-minimal harmful instances (its own rules; there is no extra filter in my code). A 0.8B model that complies often writes weak content, so the harmful-completion rate is bounded well below 100% even with refusals gone (string-match refusal flags on derivation validation went 73/80 -> 0/80 for the WSP edit).

## The WSP edit (written by Claude in a live session: 26 of 50 forward passes, no gradients)
- Fitted on derivation[:335] vs harmless[:335] only: a difference-of-means direction at layer 14, last template position; checked causally by ablating 12 candidate layers at once (rows = prompt x candidate).
- Cut: ranked the 48 residual writers by how much more they push the residual along that direction on harmful than harmless prompts, then tested sets built from that ranking (not one nested sequence): top-7 / 14 / 20 / 28 of the layer 0-13 writers, top-7 plus 4 downstream writers, and all 48. Refusal flags on derivation validation (baseline 73/80): 7 matrices 15, 7+4 matrices 14, 14 matrices 8, **20 matrices 0**, 28 matrices 0, 48 matrices 0.
- Rule (preregistered, one tie-break added before the flags were seen): lowest flags with KL <= 0.1, then fewer matrices -> the 20-matrix edit (layers 1-13, `mlp.down_proj`, `linear_attn.out_proj`, `self_attn.o_proj`), each `W <- W - r (r^T W)`. Digest `b28855e2...`, 109 KiB of fp16 factors; edited weights stay on the host.
- Disclosure: the editor knows the refusal-direction literature and rounds 1-3, so the recipe (difference of means, projection) is the known one; what the session added is the sparse selection. The ranking is an association (output along the direction on harmful vs harmless prompts); only the weight-edit tests of each set are causal.

## Method details and deviations
- **Arditi:** one direction chosen from 162 (layer, position) candidates on 128 + 32 derivation prompts with the paper's filters; only 3 candidates passed KL < 0.1 under hook scoring; chose layer 10, position -5 (KL 0.095, at the cap). Re-run after the audit with every candidate scored as the real weight edit: it chose the same candidate (2 of 162 kept; KL 0.0998) and its labels are identical to the hook-selected run (60/60). The hook-vs-weight gap is small: mean total-variation distance of the first-token distribution 0.043 (harmful selection prompts) and 0.023 (harmless), refusal mass 0.0091 vs 0.0080; the earlier "1.18 nats" is a maximum over the 248K-token vocabulary, dominated by tail tokens. The output head was untied and left unchanged, so only the input embedding changed.
- **Heretic:** its own entry point, with its prompt sets replaced by local derivation/harmless files; 60 trials (default 100), seed 20261107; trial chosen by a fixed rule (min refusal with KL <= 0.1): trial 27 of 9 Pareto trials. The default modifier (ARA, an L-BFGS-optimised LoRA, i.e. uses gradients) was **not** run. Heretic scores with the system prompt "You are a helpful assistant."; the benchmark uses none.
- **OBLITERATUS:** the `advanced` method refused the model before touching weights: "Qwen3.5/Qwen3.8 hybrid surgery remains blocked: layer_types do not match the validated 48 DeltaNet / 16 full-attention topology" (our model has 18 linear + 6 full-attention layers). I did not override the tool's validation. Its built-in prompts were never used.
- **Judge tokenizer:** transformers 5 loads the judge as a fast `LlamaTokenizer` (the request for the slow one is ignored). It differs from the original SentencePiece model in whitespace and markdown pieces (runs of spaces, `*` vs `▁*`): 60 of the 120 checked classifier inputs (parent and Arditi, 60 each) get different token ids, and 6 of those differ in length. Judging the same generations under both tokenizations gave identical labels in 120/120 calls (parent 20/60 vs 20/60, Arditi 41/60 vs 41/60). Not re-checked for the Heretic and WSP generations (their artifacts were lost, see incident 5). By construction Heretic saves the tokenizer it loaded from the parent path, but I did not re-check its exported template.

## Re-runs after the independent audit (`audit_round4_gpt.md`, answered in `audit_round4_response.md`)
- Data: derivation, harmless and primary arms rebuilt in a fresh session and again match the committed manifest hashes.
- Parent reproduced exactly: 11/250 XSTest-safe refusal, GSM8K 39.6%, 20/60 harmful, labels identical to session 1 (60/60).
- Arditi weight-selected vs hook-selected: same candidate, same side metrics (KL 0.0690, XSTest 0/250, GSM8K 36.0%), 41/60 harmful, labels identical (60/60).
- Corrections made: edit-size shares (the first table divided by a count that included the tied embedding twice), between-method paired tests added, the nested-search wording, the "non-minimal" wording, and a claim that Arditi edited the output head (it did not).

## Incidents (honest record)
1. **A candidate (Arditi) was generated on the frozen `primary` arm** before I had read the handoff. Nothing was judged and I never read the replies, but that is my statement: the files were deleted, so no one can verify it afterwards. The side-metrics file was also deleted locally. `b_run.measure` now uses an allowlist (candidates may only use the development arm) with 11 regression tests; the first guard only blocked `primary_eval` and missed `large` and the probe arms.
2. The first host (a GPU) exposed no TCP port, so remote access was unreachable; terminated after about 19 minutes and recreated on a a GPU.
3. The earlier host from rounds 1-3 no longer existed (404), so setup and downloads were repeated.
4. Missing dependencies (`jinja2`, `sentencepiece`, `tiktoken`) and a GPU out-of-memory when the editing kernel and judge shared the card; each fixed and rerun.
5. **Artifacts lost.** The stopped host could not restart (no free GPUs on its host for 50 minutes), so I terminated it to run the audit's GPU re-runs. Its storage held the WSP edit's weight diff and rank-1 factors (digest `b28855e2...`), the Heretic checkpoint and Heretic's Optuna study. The WSP edit can be rebuilt from the recorded recipe and data (direction, matrix list in `results/r4/chosen.json`), but not bit-identically; Heretic would need a fresh 60-trial run.

## Not done
No probe/AUC gates, no 13-task capability suite, no copyright hash classifier, one seed, nothing on `primary`/`large`. Nothing here replaces the registered run.

## Cost
[execution-host and billing detail omitted]
