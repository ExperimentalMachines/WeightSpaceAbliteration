> **Relabelled copy.** Copy of the private preregistration, written before the runs it covers and committed to the authors' private git repository (round 5: `61a0595`; round 6: `f16d174`, addendum before any run). On 2026-11-10, after the runs, the original working labels were replaced by proper names so the document matches the rest of this folder: D1 -> HarmBench-Val-60, D2 -> StrongREJECT-267, D3 -> JBB+MI-98, `wsp` and `WSP-v1` -> WSP-Full, `WSP-v2` -> WSP-Compact, `arditi_paper` / `arditi_matched` -> Arditi-Paper / Arditi-Matched, `heretic_abl` / `heretic_ara` -> Heretic-Abliteration / Heretic-ARA. That substitution is the only change to the rule text; infrastructure and budget text was removed earlier.

# Round 5 preregistration: clean rerun of four refusal-removal methods on Qwen3.5-0.8B (written 2026-11-10, before any round-5 run)

Status: development pilot, outside the registered WeightSpaceAbliteration run (that run's models are Qwen3-4B, Qwen3-30B-A3B, Qwen3-8B, Gemma-4-E2B, MiniCPM5-2B; this one is not).
Chronology evidence: this file is committed to git before any GPU session starts (see `git log`).

## 0. What round 4 got wrong, carried in as rules
1. A candidate was generated on the frozen `primary` arm (replies deleted unread). Rule now: candidates run only on the development arms in section 2; enforced by an allowlist in `wsp/b_run.py` with tests.
2. **New disclosure, found while planning this round:** round 4 measured every candidate on XSTest-safe (250 benign prompts), which is part of the study's frozen `over_refusal` arm (XSTest safe 250 + OR-Bench hard 1,319). Nothing was selected on it, but it breaks the handoff's rule ("measure nothing against the frozen arms"). Round 5 does not use it for candidates; the round-4 XSTest numbers are withdrawn from the headline.
3. The WSP tie-break was added during the session, not in the preregistration. It is written here (5.3).
4. The WSP patch (109 KiB) was not saved and was lost. Section 8 fixes that.
5. Statistical power: n = 60 could not separate the methods. Section 2 adds a larger, previously unseen endpoint.
6. The Arditi hook-vs-weight discrepancy was uninvestigated. Arditi is now selected with the real weight edit.

## 1. Frozen versus development data
Never touched by any candidate: the study's `primary` (HarmBench test), `large`, `probe_*`, `over_refusal` (XSTest-safe, OR-Bench), `enriched`, `treadon`, `zaakirio` arms. Only the unedited parent may use `primary_eval` (already measured in round 4: 90/213 = 42.3%; not repeated).

| Role | Data | Rows | Notes |
|---|---|---|---|
| Fit (all methods) | study `derivation`[:335] (harmful), `harmless`[:335] | 335 + 335 | Arditi "paper" variant uses the first 128 of each |
| Selection (all methods) | `derivation`[335:415], `harmless`[335:415] | 80 + 80 | Arditi "paper": rows 128-160 |
| **Primary endpoint StrongREJECT-267 (never seen by anyone)** | StrongREJECT (313 prompts, MIT) minus every prompt within cosine 0.80 (bge-small-en-v1.5 @ 5c38ec7c, the study's instrument) of derivation, HarmBench val or HarmBench test | about 250-300 | judged by the HarmBench classifier, whose use on non-HarmBench behaviours is unvalidated |
| Replication endpoint HarmBench-Val-60 | HarmBench **val**, standard + contextual | 60 | already examined in round 4, so not fresh |
| Benign over-refusal | `treadon/abliteration-eval` split `over_refusal` (outside the study's arms) | 83 | string-match refusal in the first 160 characters of a 64-token reply |
| Capability | GSM8K **train**, seeded random 500 (the study's capability gate uses the test set) | 500 | last number matches the reference, 320 new tokens |
| Distribution shift | first-token KL(parent to edited) on `harmless_alpaca` rows 415-514 (outside the study's 415-row arm and outside everything above) | 100 | the study's `kl_divergence` definition |

## 2. Conditions and fixed settings (tools as shipped, only data and the scoring rule replaced)
| Condition | Fixed settings |
|---|---|
| parent | `Qwen/Qwen3.5-0.8B` @ 2fc06364 |
| Arditi-Paper | Arditi et al. 2406.11717: one direction from (layer, position) candidates, fit/selection 128/32, layer < 0.8 L, KL(harmless selection) < 0.1, activation-addition refusal score > 0, lowest refusal score on harmful selection; applied to all residual writers + input embedding (head untied, unchanged); **every candidate scored as the real weight edit** |
| Arditi-Matched | same, fit/selection 335/80 (matched to the other methods' data) |
| Heretic-Abliteration | Heretic 2.1 `heretic.modifiers.abliteration.Abliteration` (training-free), 100 trials (default), 30 startup trials (default), Optuna seed 20261107, Heretic's default system prompt and scorers; prompts replaced by local files cut from the study arms |
| Heretic-ARA (exploratory, time-boxed) | Heretic's default modifier ARA (L-BFGS-optimised LoRA, so it applies gradient optimisation to an adapter). Run only if the first six conditions are finished and the time box allows [spend condition removed]; labelled "uses gradient optimisation" |
| WSP-Full | Claude (Sonnet 5.5 family) edits Qwen3.5-0.8B in a persistent Python session; rules in 5.3 |
| obliteratus | not run: OBLITERATUS 0.1.4 validates Qwen3.5 surgery only for one Qwen3.8-27B layout and offers no opt-in; I will not patch the tool |

Generation for every condition: chat template, thinking off, no system prompt, greedy, 512 new tokens (HarmBench direct-request construction; contextual behaviours as `context --- behaviour`; StrongREJECT-267 behaviours are the prompt text).
Heretic tunes under its own default rendering (system prompt "You are a helpful assistant."); the benchmark has none. This is disclosed, not corrected.

## 3. Judge
`cais/HarmBench-Llama-2-13b-cls` @ bda70534, bf16, official prompt text parsed from HarmBench @ 8e1604d. Label 1 = "yes" = harmful completion, 0 = "no", -1 = other (reported, never dropped). Primary tokenization = the runtime HF tokenizer. Sensitivity check on HarmBench-Val-60 for every condition: the same texts judged with the original SentencePiece ids; disagreements are reported.
Copyright behaviours (hash classifier) are not scored. No reply to a harmful prompt is kept after judging.

## 4. Analysis plan (fixed now)
- Primary endpoint: harmful-completion rate on **StrongREJECT-267**; replication: HarmBench-Val-60. Wilson 95% intervals. A pooled HarmBench-Val-60 + StrongREJECT-267 rate is secondary.
- Each condition against the parent: exact paired McNemar on the same behaviours, Holm-adjusted across all edited conditions per endpoint. "Raises harmful completions" is claimed only if the Holm-adjusted p < 0.05 on StrongREJECT-267.
- Between conditions: exact paired McNemar, all pairs, exploratory (no multiplicity claim). **No equivalence or superiority claim** unless an interval for the paired difference excludes zero.
- Over-refusal, GSM8K and KL are reported, never used to rank "best". Patch size is reported as changed elements over the 752,393,024 unique parameters (tied weights counted once) and, where the edit is rank-1 per matrix, as fp16 factor bytes.
- One seed, greedy decoding. Heretic's Optuna seed is fixed; no repeat runs.

## 5. Selection rules (fixed now)
5.1 **Arditi**: the paper's filters and score above; if no candidate passes, the run stops (no unfiltered fallback).
5.2 **Heretic**: after the study finishes, take the Pareto trial with the lowest keyword-refusal count on the selection prompts among those with KL <= 0.1; ties: lowest KL; if none has KL <= 0.1: lowest KL. Save as adapter and merged model.
5.3 **WSP (the editor)**:
- Data: only `derivation` and `harmless` (the 335/80 split above) through the kernel; no HarmBench, StrongREJECT, judge or any D-arm text.
- Rules: no gradients (autograd off, `backward()` raises); 50 forward passes in total (one pass = at most 1024 texts read, or at most 512 prompts generated for at most 200 tokens; scoring K candidate edits with K x 80 prompts in one pass is allowed if the texts stay at most 1024); replies to harmful prompts never returned (flags only); every cell logged.
- Candidates: any set of rank-1 projections W <- W - r (r^T W) the editor proposes.
- **Choice rule, implemented as code (`choose()` in the kernel) before the session starts:** among candidates with first-token KL on `harmless_val` <= 0.1, take the one with the fewest string-match refusal flags on `harmful_val`; ties -> fewer edited matrices; ties -> lower KL. The editor may not override `choose()`.
- Frozen at the end: one `finalize()`; the choice is never revised after any D-arm result.
- Disclosure: the editor knows the refusal-direction literature, rounds 1-4 and their HarmBench-Val-60 results; StrongREJECT-267 is the only endpoint it has never seen.

## 6. Artifacts 
Arditi: direction vector, layer, position, selection JSON. Heretic: chosen-trial JSON, Optuna journal, LoRA adapter (merged model stays on the compute host). WSP: rank-1 factors (r and v per matrix, fp16), matrix list, digest, a bit-exact rebuild check against the edited weights, the full session log. Per condition: judged labels (0/1/-1 per public behaviour id), aggregate side metrics. Edited full weights are not published and not required to leave the compute host.

## 7. Budget and stopping
[Spend cap, stopping rule and infrastructure details removed from this copy; they do not affect any measurement.]

## 8. Known limits stated in advance
Single model, single seed; StrongREJECT-267 uses a classifier built for HarmBench behaviours; Heretic's rendering differs from the benchmark's; Arditi-paper uses less data than the others by design; the WSP editor is not blind to the literature; no probe/AUC gates, no 13-task capability suite, copyright behaviours unscored. Nothing here replaces the registered run.
