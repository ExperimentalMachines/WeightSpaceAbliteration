# Historical Qwen primary arm: source routing and target context

**2026-11-18 UTC · Read-only item-ID audit.** The source route can be identified for every
retained item. That does **not** mean every saved response can be judged with a HarmBench
text classifier. No responses were scored or selected for calibration.

| Pinned source route | Before exclusion | Excluded | Retained primary | Evidence for historical use |
|---|---:|---:|---:|---|
| Standard text | 159 | 26 | 133 | No source context required. Saved `text` matches the source behavior. |
| Contextual text | 81 | 1 | 80 | All 80 have a nonempty source context. None contains the whole context in the saved `text`; it is not a separate split field either. |
| Copyright / `hash_check` | 80 | 0 | 80 | All 80 are tagged for the upstream hashing route (40 book, 40 lyrics). These are not standard or missing-context text-judge items. |
| **Total** | **320** | **27** | **293** | All 293 stored primary response IDs match the split in order, without duplicates. |

## How the join was verified

1. Authenticated the existing local `datasets/_cache/harmbench_pinned.csv` against the Git blob ID and size in the [pinned upstream directory](https://github.com/centerforaisafety/HarmBench/tree/8e1604d1171fe8a48d8febecd22f600e462bdcdd/data/behavior_datasets). Only directory metadata was fetched; the 400-row corpus was already local. No reliance on the filename as proof of revision.
2. Matched the saved split manifest to the Qwen `split_build` entry (seq3), recomputed the exclusion-list digest, and checked the primary and validation arm sizes and byte hashes against the manifest and the historical `refusal_eval` receipt. Joined by `BehaviorID`, not normalized text or row position. For every kept primary and validation item, the saved text equaled `Behavior.strip()`, the semantic category matched, and the split source label was consistent.
3. The kept, excluded and validation IDs are disjoint and exhaust the source (293 + 27 + 80). Re-serializing validation rows in saved order, with embedded CRLF converted to LF and CSV records terminated by CRLF, reproduced the pinned validation CSV Git blob **in memory**. Test membership is supported by the complementary ID set and manifest exclusions. The original test CSV byte order was **not** independently reproduced. Neither source nor split was rewritten.
4. Used `Tags`, `FunctionalCategory`, and context presence together. Signals agreed on these rows. The [reference evaluator](https://github.com/centerforaisafety/HarmBench/blob/8e1604d1171fe8a48d8febecd22f600e462bdcdd/evaluate_completions.py#L71-L81) checks `hash_check` **before** classifier dispatch; the [classifier helper](https://github.com/centerforaisafety/HarmBench/blob/8e1604d1171fe8a48d8febecd22f600e462bdcdd/eval_utils.py#L395-L410) selects the contextual template for the `context` tag. This audit counted routes; it did not execute either upstream metric.

## What was recorded versus what is inferred

The primary split has exactly `id`, `text`, `source`, and `category`. The captured historical
gate passes `row['text']` to generation. Its captured renderer builds a single user message
from that string; the fast-session generation helper uses the same renderer. The saved
per-item result has `id`, `response`, and `refusal`, not the rendered input, token IDs, or
an input digest. Its bytes match the earlier inventory snapshot; that comparison does not
retroactively bind it as a receipt output.

For the 80 contextual rows, even allowing CRLF/LF differences and trimming surrounding
whitespace, the **whole source context occurs in zero saved prompt strings**. The stored
inputs and captured code therefore support *behavior-only input*; they do not attest to
the exact tokens seen in each historical call. A response or its label cannot establish
that missing context was supplied. Giving only a later judge the recovered context would
evaluate an answer against information the target is not evidenced to have received.

## Consequence for interpretation

For the proposed per-card harmful-behavior diagnostic on these historical responses,
**133/293 (45.4%) is an upper bound on standard-text coverage**, before any length,
invalid-verdict or execution losses. Under the current evidence, the other 160 must be
accounted for with **two distinct reasons**: target context not supported (80) and
non-classifier reference route (80). Do not let the tool silently treat either as a
standard prompt. No new verdicts or refusal rates were computed. In particular:

- Do not shrink the registered primary denominator, transfer its 11/293 bar to the 133,
  or interpret subgroup agreement as full-arm agreement or accuracy.
- Recovering *source* context does not repair the historical *target* input. A future linked
  run could bind the approved context and rendered target input per ID **before** generation;
  that would be a changed input condition, requiring prospective review and comparable parent
  and candidate inputs, not a correction applied only to the candidate.
- Keep hash-route applicability separate from explicit refusal. Running a copyright matcher
  would measure a different property; it is neither authorized nor a refusal instrument.
- The distinction does not invalidate all 293 saved responses: they remain evidence for
  the inputs actually recorded. No score effect, direction of bias, or candidate result is
  established here. This census covers the primary arm, not SALAD or the safe-prompt arm.

## Reproducibility and limits

Private evidence: `.omp/context-provenance/20261118T070300962207Z/`. It contains pinned
tree metadata, the read-only audit script, per-ID routing records without prompt or response
text, source/input digests and the aggregate summary. Command: isolated workflow Python
`-I -B <private-attempt>/census.py`; Windows/Python 3.11.15. The census ran once at
07:07:58.581Z–07:07:58.623Z (0.047 s as timed by the script, excluding source metadata
retrieval; not a benchmark). No model loading, consultation, Modal call, GPU, gate,
registered artifact write, or change to the non-scoring prototype.
