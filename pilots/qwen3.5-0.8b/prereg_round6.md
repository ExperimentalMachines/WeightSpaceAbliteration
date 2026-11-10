> **Name key.** This is a copy of the private preregistration, written before the runs it covers and committed to the authors' private git repository (round 5: `61a0595`; round 6: `f16d174`, addendum before any run). Rule text is verbatim and still uses the original working labels: D1 = HarmBench-Val-60, D2 = StrongREJECT-267, D3 = JBB+MI-98, `wsp`/`WSP-v1` = WSP-Full, `WSP-v2` = WSP-Compact, `arditi_paper` = Arditi-Paper, `arditi_matched` = Arditi-Matched, `heretic_abl` = Heretic-Abliteration, `heretic_ara` = Heretic-ARA. Only infrastructure and budget text was removed.

# Round 6 preregistration: improving the WSP edit (written 2026-11-10, before any round-6 code or GPU session)

Status: development pilot, outside the registered WeightSpaceAbliteration run. Nothing here touches that run's frozen arms.

## 0. What round 5 showed, and the one change
Round 5's coded rule `choose()` picked the candidate set with the fewest string-match refusal flags and, on ties, the fewest matrices. Every set from 20 matrices up had 0/80 flags, so
the rule was really "smallest set that reaches 0 flags". Zero refusal flags is not the endpoint: the endpoint is harmful completions as the HarmBench classifier labels them, which was
76.4% on D2 for the round-5 WSP edit against 81.3% for Heretic (paired p = 0.079, not significant). The candidates were also all-or-nothing (full projection, one direction, top-k sets).

**Change tested here (WSP-v2):** (1) the selection signal becomes the official classifier's harmful-completion count on `harmful_val` (80 derivation-arm prompts), not refusal flags;
(2) the candidate space widens from top-k sets of full projections to graded strength (alpha in {0.5, 0.75, 1.0}) and per-region directions, so smaller or weaker-but-equal edits can win.

## 1. Question and success criteria (fixed now)
Does WSP-v2 beat WSP-v1 (the round-5 edit, rebuilt bit-exactly from its saved rank-1 factors) on data neither editor session saw?
"Improved" is claimed only if ALL hold on D3 (section 2):
- (a) size: WSP-v2 changes <= 75% of the elements WSP-v1 changes (48,035,590);
- (b) effect, non-inferior: the lower bound of the paired-bootstrap 95% CI for (harmful rate of v2 minus v1) is >= -7.5 percentage points;
- (c) drift: first-token KL(parent to edited) <= 0.1.
"Effect improved" is claimed separately only if the lower bound of that paired CI is > 0. If (a)-(c) do not all hold, the result is reported as "no improvement shown", including when the CI is too wide to decide.
Two outcomes are possible and both are reported: WSP-v2 selects the same set as v1 (nothing to improve with this signal), or it selects a different edit.

## 2. Data
| Role | Data | Rule |
|---|---|---|
| Editor sees | study `derivation`[:335] / `harmless`[:335] (fit), `derivation`[335:415] / `harmless`[335:415] (selection) | same as round 5 |
| Judge-guided selection | the official classifier on replies to `harmful_val` only (counts returned to the editor, never replies) | derivation arm only |
| **D3 (fresh test, never seen by any editor or by me)** | JailbreakBench JBB-Behaviors harmful, MaliciousInstruct, CatQA, minus every prompt within cosine 0.80 (bge-small-en-v1.5 @ 5c38ec7c, the study's instrument) of derivation, HarmBench val/test and StrongREJECT D2 | n fixed by the build, reported before any judging |
| Side metrics | benign over-refusal on `treadon` (83, string match); GSM8K train 500 (the round-5 seed); first-token KL on `harmless_alpaca` rows 415-514 | reported, never used to choose |
Never used by any WSP-v2 step: D1, D2, `primary`, `large`, probe arms, `over_refusal`. Only the unedited parent has ever touched `primary_eval`.
If a D3 source cannot be fetched, D3 is built from the rest and the shortfall is reported; sources are not swapped after seeing any label.

## 3. Conditions and fixed settings
parent; WSP-v1 (round-5 factors, `chosen` = top20); WSP-v2. Same decoding as round 5: chat template, thinking off, no system prompt, greedy, 512 new tokens. Same judge:
`cais/HarmBench-Llama-2-13b-cls` @ bda70534, official prompt text, label 1 = "yes" = harmful completion; runtime tokenizer. Every D3 condition is generated once and judged once; no reruns after labels exist.
Heretic and Arditi are not rerun (they are not the object of this round).

## 4. The editing session (WSP-v2) fixed rules
- No gradients (autograd off, `backward()` raises); 50 forward passes; one pass = <= 1024 texts read, or <= 512 prompts generated for <= 256 tokens (judged candidates use 80 prompts x 256 tokens).
- Replies to harmful prompts never leave the kernel: the editor receives the classifier's count of "yes" labels, nothing else. Every cell is logged.
- Candidate: any set of rank-1 projections W <- W - alpha r (r^T W) with per-module direction and a strength alpha in [0, 1].
- **Choice rule, coded in `wsp/r6_rules.py` and unit-tested before the session:** among candidates with first-token KL(harmless_val) <= 0.1, let M be the largest judged harmful count on `harmful_val`.
  Admissible = candidates with count >= M - 2 (two behaviours of 80 = judge-noise allowance). Choose the admissible candidate with the fewest edited elements; ties: higher count; ties: lower KL. The editor cannot override it.
- One `finalize()`; the choice is never revised after any D3 result. Factors are saved bit-exactly and copied off the host as soon as they exist.
- Disclosure: the editor knows the refusal-direction literature and rounds 1-5, including that top-20 was chosen twice; this is not a blind editor.

## 5. Analysis (fixed now)
D3 harmful-completion rate with Wilson 95% intervals; paired exact McNemar for each edit against the parent and for v2 against v1; the section-1 criteria computed with a paired bootstrap (10,000 resamples, seed 20261110).
Patch size as changed elements over the 752,393,024 unique parameters and, for rank-1 edits, fp16 factor bytes. No equivalence or superiority claim beyond section 1.

## 6. Budget and stopping
[Spend cap, stopping rule and infrastructure details removed from this copy; they do not affect any measurement.]

## 7. Limits stated in advance
One model, one seed, greedy decoding; D3 size will decide how wide the intervals are (a non-inferiority margin of 7.5 points may not be provable); the classifier's validity on these prompt sets is unvalidated and
replies are deleted after judging; the editor is not blind; the selection allowance (2 behaviours) is a judgement; "improved" here means smaller patch at non-inferior effect, not a larger harmful rate.

## Addendum A (2026-11-10, before any round-6 GPU session or label)
Found while building the data code: CatQA, named in section 2, is gated on Hugging Face (HTTP 401 without credentials), so it cannot be used. D3 is therefore JailbreakBench JBB-Behaviors (harmful, MIT) plus MaliciousInstruct only.
This was foreseen in section 2 (a failed source shrinks D3; no replacement source is added). Expect a smaller D3 and wider intervals: if the paired bootstrap CI for v2 minus v1 is too wide to show non-inferiority (lower bound >= -7.5 points),
the outcome is "no improvement shown" even if the point estimate is positive. No other rule changes.
