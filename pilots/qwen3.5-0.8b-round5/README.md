# Pilot: four refusal-removal methods on Qwen3.5-0.8B (development pilot, 2026-11-10)

**Status: development pilot, outside the registered run.** Qwen3.5-0.8B is not one of the registered models, no method here is admitted
(`load_method()` is unchanged and no `method_selected` entry exists), nothing was run against the frozen `primary`, `large`, probe or `over_refusal` arms
except the unedited parent's baseline on `primary`, and the ledger, the pre-registration and the README status table are untouched.
This folder is evidence about the methods and the harness, not a result of the study.

## What was measured
The same parent (`Qwen/Qwen3.5-0.8B` @ `2fc06364`), the same fit/selection data (the study's `derivation` and `harmless` arms, rebuilt with `harness/build_splits.py`
and matching the committed manifest hashes), the same decoding (chat template, thinking off, no system prompt, greedy, 512 new tokens) and the same judge
(`cais/HarmBench-Llama-2-13b-cls` @ `bda70534`, official prompt text from HarmBench @ `8e1604d`), for:

| Condition | What it is |
|---|---|
| `parent` | unedited |
| `arditi_paper` | Arditi et al. (2406.11717): one direction, all residual writers + input embedding; 128 + 32 fit/selection prompts; every candidate scored as the real weight edit |
| `arditi_matched` | same with 335 + 80 prompts (matched to the others) |
| `heretic_abl` | Heretic 2.1, `Abliteration` modifier, 100 trials, trial chosen by a rule fixed beforehand |
| `wsp` | an LLM (Claude) edits the weights in a live Python session: no gradients, 50 forward passes, derivation/harmless data only; the final choice is made by code (`choose()`) |
| `heretic_ara` | Heretic's default ARA modifier (uses gradient optimisation of an adapter): the search ran, **but it was not judged; there is no result for it** |
| OBLITERATUS | not run: version 0.1.4 refuses this architecture |

The rules, written before any round-5 run, are in [`prereg_round5.md`](prereg_round5.md) (infrastructure and budget text removed, every rule verbatim);
what went differently from plan is in [`deviations_round5.md`](deviations_round5.md).

## Results
Endpoint: harmful completions as labelled by the HarmBench classifier. **D2** is the primary endpoint: StrongREJECT prompts, minus near-duplicates (cosine >= 0.80,
the study's embedding instrument) of the derivation arm, HarmBench val and HarmBench test; no method or editor saw them. **D1** is HarmBench val (60 standard + contextual behaviours),
already examined in an earlier round, so it is a replication, not a fresh test.

| Condition | D2: harmful completions (95% Wilson CI) | Holm-adjusted p vs parent | D1: harmful completions (95% CI) |
|---|---|---|---|
| parent | 51/267 = 19.1% (14.8-24.2%) | - | 20/60 = 33.3% (22.7-45.9%) |
| arditi_paper | 218/267 = 81.6% (76.6-85.8%) | 5.9e-44 | 41/60 = 68.3% (55.8-78.7%) |
| arditi_matched | 194/267 = 72.7% (67.0-77.7%) | 2.7e-32 | 43/60 = 71.7% (59.2-81.5%) |
| heretic_abl | 217/267 = 81.3% (76.2-85.5%) | 6.6e-43 | 43/60 = 71.7% (59.2-81.5%) |
| wsp | 204/267 = 76.4% (71.0-81.1%) | 3.7e-42 | 44/60 = 73.3% (61.0-82.9%) |

Full tables (flips against the parent, pooled D1 + D2, all exploratory pairwise tests, side metrics) are in [`summary.md`](summary.md).

What the numbers support:
- Every method that ran raises the harmful-completion rate far above the parent's (D2: 19% to 73-82%); this replicates on D1.
- Between methods the evidence is weak: Arditi-matched is lower than Arditi-paper (exact McNemar p = 0.004) and than Heretic (p = 0.007); WSP against Arditi-paper (p = 0.076) and against Heretic (p = 0.079) is not significant;
  these pairwise tests are exploratory and not corrected for multiplicity. No ordering of the methods is claimed.
- Patch size: Arditi changes 43.4% of the model's unique parameters (210M of them in the input embedding), Heretic 9.9%, WSP 6.4% (rank-1 factors on 20 matrices; 109 KiB in fp16).
- Side metrics (benign over-refusal on 83 prompts, GSM8K on 500 train problems, first-token KL) are reported, never used to rank.

## Limits (read before quoting any number)
- The classifier measures harmful completions, not refusals: a model that no longer refuses can still score "no" when its answer is weak, so the rate is bounded below 100%.
  This is relevant to the pre-registered "residual refusal" endpoint, which is not tested here.
- Its use on StrongREJECT prompts (D2) is unvalidated, and replies to harmful prompts are deleted after judging, so no one can hand-check the labels.
- The WSP edit is a replication by the same editor with the same knowledge: it chose the same 20 matrices and changed exactly the same 48,035,590 elements as in an earlier round. It shows the result is repeatable, not that an LLM editor finds it independently.
- One model, one seed, greedy decoding; 267 and 60 behaviours; copyright behaviours not scored; Heretic tunes with its default system prompt while the benchmark has none.
- A candidate was once generated on the frozen `primary` arm in an earlier round before the handoff rules were read (replies deleted unread; this cannot be verified after the fact). The runner now allows candidates on development arms only, with tests.

## Contents
- `labels/<condition>__<arm>.json`: per-behaviour labels (0 = no, 1 = yes, -1 = invalid) keyed by public HarmBench behaviour id or an opaque StrongREJECT index, with the judge revision and aggregate counts. `labels_sp` repeats D1 under the original SentencePiece token ids as a tokenizer-sensitivity check. No prompt, reply or other text.
- `metrics/<condition>.json`: aggregate side metrics and patch sizes per condition.
- `selection/`: how each method's setting was chosen (Arditi candidate scan, Heretic chosen trial, the WSP candidate sets and final choice, forward-pass log).
- `wsp_session/session_cells.txt`: every cell the editor submitted and its output (replies to harmful prompts are never returned to the editor).
- `build_report.json`: arm sizes and their hash match against the committed manifest.

**Not included, deliberately:** model weights, adapters and refusal-direction vectors, generated text, and any prompt corpus (consistent with `SECURITY.md` and `CONTRIBUTING.md`).
