# `tools/`

**Audience:** someone reproducing a provenance claim, or re-running an audit before extending the study.

These are utilities that make claims checkable. None of them is needed to run a gate; all of them are
needed to justify why a gate's inputs are what they are.

| tool | what it proves | writes |
|---|---|---|
| `start_run.py` | the pre-registration was written before any data action | `runs/<run_id>/ledger.jsonl` entry 0 |
| `record_lookups.py` | each cited paper was retrieved, when, and what came back | `paper_lookup` ledger entries + `paper_lookups/NNNN.json` |
| `verify_datasets.py` | every dataset revision in the inventory still resolves to the recorded sha | `datasets/inventory/_verified.json`, `_manifest.json` |
| `leakage_audit.py` | two corpora share no exact-normalised prompt, and how much n-gram overlap they have | `datasets/_cache/leakage_*.json` |
| `semantic_dedup.py` | how many distinct behaviours two corpora contain once paraphrases are collapsed | `datasets/_cache/semantic_*.json` |

## Notes that cost time to learn

`verify_datasets.py` falls back to `git ls-remote` when the GitHub API rate-limits, because five
parallel audits exhaust sixty unauthenticated requests in minutes. A row that names more than one
dataset is reported `MULTI` rather than guessed at.

String measures are a blunt instrument on short prompts. On XSTest's labelled twin pairs, five-gram
Jaccard at 0.50 detects about five percent of true twins, because a one-word substitution destroys most
five-grams in an eight-word prompt. That is why the split uses embeddings and why `leakage_audit.py`
says "approximate" out loud.

The embedding model, its revision, the truncation length and the threshold are all part of the
measurement. Changing any of them changes which items are excluded, which changes the denominator.
Pin them.
