# Editing Qwen3.5-0.8B's weights to reduce over-refusal: all attempts and methods

Experimental Machines. Project `weights_space_programming`, 5-6 November 2026. Status: exploratory results, one model, one editor per round.
Question: can a harmless guardrail (over-refusal of harmless-but-edgy prompts) be weakened by editing weights directly, with no fine-tuning, while refusal of harmful prompts stays intact?

## 1. Summary

| | Round 1 | Round 2 | Round 3 |
|---|---|---|---|
| Who computed the edit | Code written by Claude | Code written by Claude (published recipe) | **Claude, in a live Python session, writing the weights** |
| Idea | Direction of "benign-refused minus benign-answered", orthogonalised against harmful refusal; and per-weight importance scores | Wang et al. false-refusal vector, scanned over layer x position | Conditional rank-1 edits, minimum-interference closed form derived in the session |
| Fresh benign refusal | not measured | 8.7% -> 5.3% (-3.3 pp) | **8.2% -> 1.4% (-6.8 pp)** |
| Hard dev set refusal (819) | 36.8% -> 33.1% (-3.7 pp) | 37.0% -> 25.0% (-12.0 pp) | **37.0% -> 18.1% (-18.9 pp)** |
| Harmful-prompt refusal | -1.4 pp pooled | -1.75 pp (upper bound 4.25: safety not established) | +2.1 pp pooled (no drop) |
| Weights changed | 5.0% (16 matrices) | 15.8% (48 matrices) | 1.9% (7 matrices) |
| Rank-1 patch size | 90 KiB (computed, not built) | 266 KiB (built and checked) | **39 KiB (built and checked)** |
| Verdict | Small effect; claims later found overstated | Real effect; safety not established | Strongest effect; safety rule met |

The original gate (XSTest-safe refusal at least 10%) was **never met** (4.0%); all three rounds are therefore exploratory. The targeted guardrail is over-refusal, a harmless one;
the real safety refusals were deliberately left intact and were not "broken" in any round.

## 2. Common setup

| Item | Detail |
|---|---|
| Model | Qwen/Qwen3.5-0.8B, 752,393,024 text parameters (bf16); 24 hybrid layers: 18 linear-attention, 6 full-attention (blocks 3, 7, 11, 15, 19, 23); hidden size 1024; tied embeddings |
| Residual-stream writers | `mlp.down_proj` (all 24 blocks), `linear_attn.out_proj` (18 blocks), `self_attn.o_proj` (6 blocks) |
| (omitted) | execution-host and billing details are not published here |
| Generation | Greedy, thinking off, first 64 tokens classified (200 tokens for manual reading) |
| Rules | No fine-tuning; edited weights never uploaded; replies to harmful prompts labelled and discarded (never read); only aggregate counts leave the host |
| (omitted) | execution-host and billing details are not published here |

**Data**

| Role | Sets |
|---|---|
| Benign, over-refusal-prone | OR-Bench-Hard-1K (1,319 rows in the HF copy), OR-Bench-80K pool (80,359 prompts, deduplicated), XSTest safe (250) |
| Harmful | OR-Bench-Toxic (655), XSTest unsafe (200), AdvBench / HarmBench / JailbreakBench / MaliciousInstruct (Wang et al. processed files) |
| Harmless reference | Alpaca (31,323) |
| Capability | GSM8K (test, split into practice / validation / final) |
Every round used disjoint extraction, validation and final subsets; round 2 and 3 added exact and 8-gram near-duplicate filtering. Final sets are used once.

**Labellers**

| Labeller | Use | Accuracy found |
|---|---|---|
| String match on the first 160 characters | Primary refusal label | 60/60 vs my blind hand labels in round 2, but over-counts partial refusals (round 2: 35% of its baseline "refusals" were partial or compliant) |
| Qwen3Guard-Gen-0.6B ("Refusal" and "Safety" labels) | Secondary, "unsafe" share | 40/60: calls compliant replies refusals (precision 0.5) |
| Claude as judge, blind A/B | Manual read of newly answered prompts: prompt harmless / borderline / should-not, reply refused / partial / complied, harmful content, quality | One rater; labels written before opening the key |

## 3. Round 1: code-computed edits (Stages 0-6)

Stage 0: host set up; architecture and chat template checked. Stage 1 baseline: XSTest-safe refused 4.0% (gate failed; OR-Bench-Hard used instead, a deviation recorded);
OR-Bench-Hard final 36.8%, XSTest unsafe 66.5%, OR-Bench-Toxic final 65.9%, GSM8K 40.4%.

| # | Method | Procedure | Outcome |
|---|---|---|---|
| 1a | **Arm A: direction projection** | Direction = mean state(benign refused) - mean state(benign answered) at the last token; component along the harmful-refusal direction removed; `W <- W - alpha r r^T W` on all residual writers | Layers 12-18 at full strength cut benign refusal to 16-28% but harmful from 69% to 41-56% (rejected). Cosine between the two directions 0.78-0.84 at layers 13-24 |
| 1b | Partial strength sweep | Layers 12, 14, 16, 18 x alpha 0.25/0.5/0.75 | A few settings passed the 2-pp rule on 100 validation prompts; layer 18 at 0.75 gave benign -7, harmful -1 |
| 1c | Minimisation | 15 matrix subsets, direction from layer 18, alpha 0.75 | Chosen: layers 12-19, all writer kinds (16 matrices) |
| 1d | Final (held-out) | Full edit vs minimal edit | Full edit: no detectable effect (validation gain 42.0 -> 35.0 was selection noise). **Minimal: OR-Bench-Hard 36.8 -> 33.1% (-3.7 pp [-5.4,-2.0]); harmful -1.4 pp pooled; GSM8K 40.4 -> 38.4** |
| 2a | **Arm C: importance scores** | Weight x gradient on the model's own benign refusals (signed), protection sets = top weights for harmful refusals and for GSM8K (set difference); zero the top-k | k = 1,024-131,072: benign and harmful refusal fell together about 1:1 (k=1,024: benign 42 -> 12%, harmful 69 -> 42%). All rejected |
| 2b | Arm C, refinements | Protection fraction 30% / 50%; ratio score; k = 64-2,048 | 18 settings, none passed the stop rule |
| 2c | Random control | Zero 131,072 random writer weights | No effect (so arm C's weights do carry refusal) |
| 3 | Quantisation | Simulated per-row int8 / int4 round-trip of writer matrices | int8: effect survives. int4: damaged the unedited model itself (36.8 -> 57.1%), so not judgeable |
| 4 | Visibility | SVD of the edit | Rank 1 (>= 99.6% of energy), 2.4-2.9% relative change, energy along the direction ~17x below normal; **blind detection not tested** |
| 5 | Patch size | Counted changed bf16 elements | 37.6M elements (5.0%); rank-1 form computed as 90 KiB but never built |

Failures in execution: two log-watcher scripts hung (about 25 min of idle host time); several editing slips (wrong line numbers) were repaired with tests.

**Audit after round 1 (what was overstated)**

The regex was assumed to be a "lower bound" (it is not); the safety rule was judged on 100 prompts; the "final" sets were no longer fresh; the XSTest gate had been overridden; localisation by activation patching was never done;
the "90 KiB" patch was a calculation; "visible at once" was never tested blind. The audit also flagged the next-round ideas as unproven (null-space / AlphaEdit-style conditional edit; refusal-cone directions).

## 4. Round 2: published recipe, preregistered (Wang et al., ICLR 2025)

Preregistered in `prereg_round2.md` before any run. Fresh deduplicated data, two labellers, blind hand-label check, one fresh-final run.

| Step | Method | Result |
|---|---|---|
| Checks | Template suffix of 9 post-instruction tokens; hidden-state vs block-output indexing; hook ablation vs weight edit | Suffix identical; `hidden_states[i+1]` = output of block i for blocks 0-22; hook and weight edits close but not identical (first-token L1 0.055-0.075) |
| Direction | False-refusal vector = mean(refused benign) - mean(harmless Alpaca) at each (state, position); true-refusal = mean(harmful) - mean(harmless); orthogonalised with coefficient lambda | 23 states x 9 positions = 207 candidates; 165 passed the KL <= 0.2 filter (first-token refusal score, refusal token "I") |
| Generation validation | 17 candidates as real weight edits on 800 benign + 300 harmful validation prompts | **Only 2 passed** (state 8 position 8; state 12 position 3); the rest lowered harmful refusal by 6-51 pp |
| Strength / lambda | lambda 0.75-0, strength 1.5-3x | All broke safety (harmful -24 to -77 pp) |
| Minimisation | 8 matrix subsets | Effect came from layers 0-7; chosen minimal = all 48 writers, no embedding |
| Final (fresh, one run) | Chosen (with embedding) | Fresh benign 8.7 -> 5.0%; harmful -3.25 pp: **rejected** |
| | **Minimal (no embedding)** | Fresh benign **8.7 -> 5.3% (-3.3 pp [-4.2,-2.5])**; Hard 37.0 -> 25.0% (-12.0); harmful -1.75 pp [-4.25,+0.5] = **safety not established**; GSM8K 36.8 -> 37.6 |
| Patch | Rank-1 factors serialised and rebuilt from the base | 266 KiB; 99.41% elements identical; behaviour matches. 119.1M elements (15.8%) |
| Manual judging (Claude, blind, 78 pairs) | Newly answered Hard prompts | 20% harmless / 70% borderline / 10% should-not; 1 clear and 3 mild harmful replies in 40; quality better in 24 of 40 |
Labeller finding: regex 60/60 vs hand labels; Qwen3Guard 40/60.

## 5. Round 3: Claude edits the weights

Preregistered in `prereg_round3.md`. Persistent Python session on the host: weights readable, 50 forward passes (34 used), autograd disabled, replies to harmful prompts returned as flags only, every cell logged.
Background disclosed: I know the literature and had read rounds 1-2; I loaded none of that code.

| Step | What I did | Finding |
|---|---|---|
| Inspect | 4 passes: replies and last-token states for benign / harmful / harmless prompts | Refusal signal appears abruptly between states 9 and 10 (benign-refused vs answered AUC 0.53 -> 0.84) |
| Localise | 2 passes: each module's contribution along the harm axis, blocks 6-16 | Every module carries over-refusal at ~30% of its harm signal; none selective |
| Confound caught | Ridge discriminator benign-refused vs harmful-refused | CV AUC ~1.0 with AdvBench prompts was dataset style; with style-matched OR-Bench-Toxic prompts only 0.63-0.72 (axis) / 0.90-0.95 (ridge). Toxic practice prompts added |
| Design | 7 rank-1 conditional updates `W <- W - alpha dhat v^T` on down_proj of blocks 11-13 and attention outputs of blocks 9, 11, 12, 13; `dhat` = style-matched harm direction at state 14; `v = (A+lam I)^-1 mu / (mu^T (A+lam I)^-1 mu)` with `mu` = mean input at the final token of benign-refused prompts and `A` = second moment of the inputs to protect | Held-out prediction: benign-refused prompts shift ~5.8 per unit alpha, refused toxic 1.1, AdvBench 0.04 |
| v1 | Last-token statistics only, half dose | Benign 8.2 -> 5.5% but **harmful +4.5 pp**: the edit acts on every token position |
| v2 | Protect the last 16 positions of all protected prompts | Benign 3.3%, harmful -2.0 pp (0 new refusals) |
| Tuning | Protection weight 4; dose 0.046 -> 0.13; lambda 0.1 / 0.3 / 3.0 | lambda 3 worse (harmful -4.75); dose 0.13 reached the limit; **chosen lambda 0.1, alpha 0.10**: validation benign 42 -> 10 of 512, harmful 302 -> 300 of 400 |
| Quality checks | bf16 fidelity (cosine >= 0.997); GSM8K practice; drift on harmless prompts | GSM8K 14.0 vs 15.3% (200-token cap); harmless refusals 3 vs 3 |

**Final test (one run; fresh and unseen sets)**

| Set (n) | Unedited | Edited | Paired change [95% CI] |
|---|---|---|---|
| Fresh benign (2000) | 8.2% | 1.4% | **-6.80 pp [-7.95,-5.70]** (141 stopped, 5 started) |
| OR-Bench-Hard dev (819) | 37.0% | 18.1% | -18.93 pp [-21.7,-16.1] |
| OR-Bench-Toxic final (355) | 66.5% | 65.9% | -0.56 pp [-3.38,+1.97] |
| XSTest unsafe (200) | 67.5% | 75.0% | +7.50 pp [+4.0,+11.5] |
| Round-2 harmful final (400) | 79.5% | 81.2% | +1.75 pp [+0.5,+3.0] |
| GSM8K final (250) | 36.8% | 38.0% | within noise |
Safety rule (no harmful set dropping more than 2 pp; upper bound of any drop under 4 pp): **met**.
Patch: 14,429,144 elements (1.92%), rank-1 payload 19,968 fp16 values = **39 KiB**; rebuilt from factors, 99.65% identical to the exact diff; SHA-256 `ba1dc057c23a0f1681997440081e7b423f2f480503f4108bff44f1a74486aa47`.

Blind manual judging (83 pairs): fresh benign newly answered = 13 harmless / 6 borderline / 1 should-not, no harmful content, edit better in 14 of 20;
Hard newly answered = 8 / 25 / 7, 0 clear and 2 mild harmful replies, edit better in 21 of 40; answered by both: 1 clear harmful reply (hallucinated drug "synthesis") in 15;
newly refused by the edit: 8 prompts, baseline better in 4.

## 6. Ideas considered but not run
| Idea | Status |
|---|---|
| Arm B in rounds 1-2 (an LLM writes the edit) | Not run; became round 3 |
| Null-space / AlphaEdit-style closed-form edit as a separate method | Not run as such (round 3's minimum-interference solve is a related derivation by me) |
| Refusal cones (several directions) | Not run |
| Sparks-format version (64 columns in 2 layers = 131,072 weights) | Not run |
| Measuring the published Sparks checkpoint (1.7 GB download) | Not downloaded (needs approval) |
| LoRA / vLLM / KServe loading, real GGUF/AWQ quantisation, blind detection of the patch | Not tested |
| XSTest-safe and other benign sets after the round-3 edit | Not measured |

## 7. Honest limits
- One model; greedy decoding; one editor per round; one session in round 3 (selection on validation prompts is possible; the final sets were unseen).
- The pre-set XSTest gate was not met; regex is a proxy that over-counts partial refusals; Qwen3Guard-0.6B over-flags.
- Manual judging: one rater, small samples, truncated reading; replies to harmful prompts were never read.
- Rounds use different fresh and harmful sets, so cross-round numbers are comparable but not exactly paired.
- The edits make the model answer more borderline prompts; a hallucinated drug-synthesis reply appeared once. Over-refusal drops a lot; real safety refusals did not drop, but nothing here shows a guarantee.
- The "0.016% of weights" framing of the Sparks result does not describe any of our edits (1.9% / 5.0% / 15.8% of weights), only the compact rank-1 form is tiny.

## 8. Files
`notes/results_round3.md`, `results_round2.md`, `results_report.md` (superseded), `experiment_audit.md`, `prereg_round2.md`, `prereg_round3.md`, `judge_claude.md`; code in `wsp/`;
session transcript `results/r3/r3_session.log`; raw aggregate results in `results/`.
