# `datasets/`

**Audience:** someone who wants to rebuild the split, or to check why a particular corpus was admitted
or rejected.

Two kinds of content live here, and only one of them is committed:

- `inventory/` — **committed.** Every dataset considered, with canonical URL, verified 40-hex revision,
  licence, gated flag, size, and the measurement behind its verdict. No prompt text.
- `_cache/` — **ignored.** Fetched rows, used to build the split. Never published.

## Pinned sources

| role | dataset | revision | licence |
|---|---|---|---|
| derivation | AdvBench (`llm-attacks`) | `098262edf85f807224e70ecd87b9d83716bf6b73` | MIT |
| primary endpoint | HarmBench text test | `8e1604d1171fe8a48d8febecd22f600e462bdcdd` | MIT |
| large replication | `OpenSafetyLab/Salad-Data` | `d21a325e276a99bd69b1fbb8aa51a9f249486b72` | Apache-2.0 |
| secondary | `treadon/abliteration-eval` | see inventory | see inventory |
| secondary | `zaakirio/infosec_harmful_behaviors` | see inventory | see inventory |
| secondary | `Bahushruth/abliteration-harmful-enriched` | `f29c0b778d3412d5cc7acfc9c6463ce13886212c` | Apache-2.0, construction undocumented |
| benign / KL | `mlabonne/harmless_alpaca` | `02c6a92cfcf11bb0c387334f8146d149d65b587f` | none declared; CC BY-NC inherited — never redistributed |

## Building

```bash
python harness/build_splits.py --run-id <run_id>
```

Fetches the sources, applies the exclusions recorded in the split manifest, and writes one JSONL per
arm plus `splits/manifest.json`. The manifest carries a sha256 per file and a hash over the exclusion
lists, so a rebuild either matches or explains itself.

## Why exclusions, not just deduplication

The evaluation set and the derivation set must not share behaviours. Exact-normalised matching finds
copies; it does not find paraphrases. The split therefore drops any item whose embedding cosine to the
other arm is at least 0.80, using `sentence-transformers/all-MiniLM-L6-v2`.

That rule is not decorative. It removed 522 of Salad-Data's 17,134 harmful questions — including 145
the dataset card does not declare as AdvBench-derived — and 14 of treadon's 200 that exact matching had
scored at zero.

## Inventory index

| file | covers |
|---|---|
| `harmful-behaviour-batteries.md` | HarmBench, JBB, AdvBench, StrongREJECT, SALAD, HEx-PHI, AIR-Bench, and the rest |
| `benign-and-overrefusal.md` | XSTest, OR-Bench, Alpaca, Heretic's exact KL and contrast settings |
| `mechanistic-corpora.md` | the derivation corpora behind Arditi, Heretic, Geometry of Refusal, COSMIC, SOM |
| `capability-suites.md` | the pinned harness revision and every task dataset |
| `cross-lingual.md` | PolyRefuse, MultiJail, XSafety, M-ALERT, Aya |
| `hf-abliteration-tagged.md` | the 70 Hub datasets tagged `abliteration` |
| `abliteration-org.md` | the abliteration.org Evaluate-stage catalogue |
| `fu-index-obliteratus-full-refusal.md` | the public reference row, with its caveats |
