# Fu Index — `obliteratus-full-refusal` (reference column, not an instrument)

- Canonical URL: https://fu.furukama.com/benchmark/?benchmark=obliteratus-full-refusal
- Retrieved: 2026-11-07, rendered through CDP (page is client-side; raw fetch returns no data).
- Aggregator caveat, from the page itself: "Best published score per model. Fu does not re-run evaluations."
- Page footer: data updated 2026-11-06; operator Ben Koehler / furukama.com.
- Benchmark definition (categories, judge, prompt set, threshold): **not published on the page**. Only the ranking is exposed. Treat as `UNVERIFIED` for methodology.
- Direction of the scale: higher score = more refusal on the benchmark's prompt set.

## Scores

| # | Model | Score | Coverage | Model family | Lab | Params | Released |
|---|---|---|---|---|---|---|---|
| 1 | DeepSeek V4.1 Flash 1017 | 81.6% | open | DeepSeek V4.1 | DeepSeek | 552B (16B active) | 2026-10-17 |
| 2 | DeepSeek V4.1 Flash | 4.3% | open | DeepSeek V4.1 | Obliteratus | 552B (16B active) | 2026-10-23 |

## What it means for the study

The published headline for an Obliteratus treatment on this base model is 4.3% residual refusal against
81.6% for the parent. Whatever the denominator is, the reference point is **not zero**. That gives the
study a concrete prior: "full removal" as claimed in public leaderboards currently sits at a residual,
and the pre-registered ceiling should be chosen with that in view rather than from the word "full".

Unusable as a measurement instrument: no judge protocol, no prompt-set revision, no per-category
breakdown, no re-runs. Usable as: a comparison row, and a hypothesis about where the frontier is.
