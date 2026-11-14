# Pilot round 9: fixed rank-k weight edits on MiniCPM5-2B (exploratory; not preregistered)

This is development work outside any registered run. There is no preregistration for this round, no receipts, and no method is admitted. The conditions below were fixed before any result was seen and nothing was selected on test data, but nothing here was frozen or hashed beforehand. Treat every number as a screen.

## Names
All of these are weight-space programming (WSP) edits: a direct weight edit with no gradients and no training. They differ in who or what chooses the edit.

| Name | Who chooses the edit | Rank | Status |
|---|---|---|---|
| WSP-Full, WSP-Compact (round 7/8) | an LLM editor in a session, coded choice rule | 1 | run |
| WSP-Subspace-Session | an LLM editor in a session, inside a frozen universe of builders, ranks, layers and strengths | k | designed, not run |
| **WSP-SG** (WSP-Subspace-Grid, this round) | nobody: a fixed builder at fixed settings, no session, no selection | k | run |

A WSP-SG row shows what a fixed rank-k edit does. It is not evidence about what an LLM editor would choose or achieve.

## What was run
Model: MiniCPM5-2B (same pinned snapshot as round 8). Test sets, classifier, decoding and judge batch size as round 8: **StrongREJECT-267**, **HarmBench-Val-60**, **JBB+MI-98**; `cais/HarmBench-Llama-2-13b-cls` @ `bda70534`; greedy, 512 new tokens, no system prompt, thinking off, judge batch 4. Replies were deleted after judging.

Each condition fits a basis at one (layer, last-position) cell on `derivation[0:250]` and `harmless[0:250]` of the study's split (the parent's residual states; never the test sets), and removes it at strength 1.0 from all 84 residual-writing matrices (`W' = W - U U^T W`, rebuilt and checked bit-exact against a digest). The embedding and output head are unchanged. B1 is the mean difference; B2 the top-k right singular vectors of the harmful states minus the harmless mean; B3 seeded k-means centroids minus the harmless mean; B5 first removes the top-8 harmless second-moment directions from the basis. Condition names are `WSP-SG-<builder>-k<rank>[-null8]-L<layer>`.

## Results
Parent, WSP-Full and the Heretic rows are the round 7/8 values in `../README.md`; the side metrics are in `metrics/`, the per-prompt labels in `labels/`, paired tests in `analysis.json`.

| Condition | StrongREJECT-267 | HarmBench-Val-60 | JBB+MI-98 | First-token KL | GSM8K | Over-refusal /83 |
|---|---|---|---|---|---|---|
| Parent | 0.4% | 8.3% | 0.0% | 0 | 72.4% | 59 |
| WSP-Full | 1.1% | 15.0% | 1.0% | 0.0964 | 73.8% | 52 |
| Heretic-Abliteration | 34.5% | 51.7% | 17.3% | 0.9998 | 71.4% | 6 |
| Heretic-ARA | 46.8% | 63.3% | 51.0% | 0.6956 | 70.8% | 18 |
| WSP-SG B1 rank 1, L24 | 18.0% | 40.0% | 12.2% | 0.805 | 73.0% | 26 |
| WSP-SG B2 rank 2, L24 | 40.4% | 50.0% | 42.9% | 2.177 | 84.6% | 5 |
| WSP-SG B2 rank 4, L24 | 30.3% | 40.0% | 31.6% | 2.746 | 67.8% | 21 |
| WSP-SG B2 rank 8, L24 | 12.7% | 8.3% | 7.1% | 3.623 | 7.8% | 0 |
| WSP-SG B3 rank 4, L24 | 30.7% | 31.7% | 39.8% | 2.820 | 67.6% | 8 |
| WSP-SG B2 rank 4 + B5 null 8, L24 | 4.5% | 13.3% | 7.1% | 0.987 | 75.4% | 49 |
| WSP-SG B2 rank 4, L20 | 8.6% | 6.7% | 9.2% | 4.227 | 15.4% | 1 |

Paired exact McNemar against the round 7/8 parent (Holm over the seven conditions per test set): every StrongREJECT-267 cell has an adjusted p below 0.004 (`analysis.json`).

## Reading
- Every condition raises the harmful rate above the parent on StrongREJECT-267. Rank 2 is the highest (40.4%, 50.0%, 42.9%) and is above the rank-1 edit B1 (18.0%) at matched layer, position and writers. Ranks 4 and 8 are lower than rank 2, so more directions is not simply better. No paired test against the Heretic rows was run.
- None of these edits is admissible by the study's convention: every first-token KL is 0.79 to 4.2 against the 0.1 limit used in selection. GSM8K collapses at rank 8 (7.8%) and at layer 20 (15.4%). The rank-2 GSM8K value (84.6%, parent 72.4%) is unexplained and should not be read as a gain.
- The B5 variant cuts KL to 0.99 and keeps GSM8K near the parent, but nearly removes the effect and raises over-refusal to 49 of 83.

## Limits
One run per condition, greedy decoding, 60 to 267 prompts per set; one layer and position per condition (layers 24 and 20, last token); no selection step, so none of these is "the" WSP-Subspace edit; the classifier's validity on these prompt sets is unvalidated; the first-token KL here uses the study's inputs and is not comparable with Heretic's own scorer (see `../round8/round8_summary.md`); the toolchain is not the study's pinned one and there is no host record, so nothing here can be promoted into a registered run. Not done: writer subsets, a fresh-prompt selection session, other models, a capability suite beyond GSM8K.

## Not included
Model weights, factors, refusal-direction vectors, generated text and any prompt corpus (consistent with `SECURITY.md` and `CONTRIBUTING.md`).
