# `tools/`

**Audience:** someone reproducing a provenance claim, or re-running an audit before extending the study.

These are utilities that make claims checkable. None of them is needed to run a gate; all of them are
needed to justify why a gate's inputs are what they are.

| tool | what it proves | writes |
|---|---|---|
| `start_run.py` | the pre-registration was written before any data action | `runs/<run_id>/ledger.jsonl` entry 0 |
| `record_lookups.py` | each cited paper was retrieved, when, and what came back | `paper_lookup` ledger entries + `paper_lookups/NNNN.json` |
| `verify_datasets.py` | every dataset revision in the inventory still resolves to the recorded sha | `datasets/inventory/_verified.json`, `_manifest.json` |
| `inventory_resources.py` | which files are locally present at the configured model revisions and in NLTK's unpacked English `punkt_tab` directory | JSON to stdout only |
| `leakage_audit.py` | two corpora share no exact-normalised prompt, and how much n-gram overlap they have | `datasets/_cache/leakage_*.json` |
| `semantic_dedup.py` | how many distinct behaviours two corpora contain once paraphrases are collapsed | `datasets/_cache/semantic_*.json` |

## Non-scoring judge contract

`judge_contract.py` is an off-run Python API for the
[prospective text-judge contract](../docs/protocol/judge_spec_draft_20261118.md).
It is not a registry entry, classifier, release artifact, or refusal instrument.

- `local_judge(role, cache)` checks the four pinned local tokenizer/config files for
  `judge` (Llama) or `judge_alt` (Mistral) and loads only the tokenizer in a temporary cache.
  `judge_card_templates.json` contains the pinned cards' literal strings, source URLs,
  and tool-derived hashes. No model-loading or generation API is called.
- `prepare(item)` returns the exact template identity and full token IDs, or an explicit
  abstention. `Route` describes a caller-verified source-to-item join; it is **not proof**
  that a dataset revision was retrieved or that a historical target saw the context.
  A missing response is `not_obtained`; a present but empty response is still data.
- `parse_supplied(prepared, sequence)` checks the input prefix and parses only the
  supplied continuation. `None` denotes no call/output; an empty continuation on a
  returned sequence is an invalid output, not a negative verdict.
- `summarize(plan, rows, role)` and `agreement(plan, primary, alternate)` require one
  explicit row per planned ID, including abstentions. The caller supplies the independently
  fixed plan: do not construct it by filtering returned judgments. Binary agreement and
  κ are conditional on pairs with two valid labels. Nothing here writes a study receipt.

### WildGuard development profile (no inference)

`wildguard_dev_profile_v1.json` freezes the candidate configuration for
`refusal_development_cases.json` only. `wildguard_dev_contract.py` checks local
profile bindings, formats a supplied pair, checks its length budget, and parses
a supplied token sequence or raw verdict record. It has no model loader, download
or scoring entrypoint and is not part of the registered gate release. Exercise the
contract with `python -m pytest -q tests/test_wildguard_dev_contract.py`.

### Primary routing fixture (offline)

From the repository root in the pinned workflow environment:

```sh
python -B -m tools.check_primary_routing_fixture --inventory <trusted-local-resource-inventory.json>
```

The inventory is produced by `inventory_resources.py`; use one containing the pinned
Qwen snapshot. Qwen and both judges' verified tokenizer assets must already exist in
the configured local Hub cache. The command stages only tokenizer/config files in
temporary directories. It accepts no real arm, study responses, or GPU options.

The JSON output contains the three harmless fixture items, one common input plan,
two simulated batch captures and the text-judge preparations. Continuations are supplied
test data, not model predictions. An ID/response swap after capture must fail; an item
with a hash route must still have a captured target answer but no text-judge input.
This checks linkage to the supplied boundary record, not the honesty of a real generation
producer. It does not read a registered split or prove what an earlier target saw.

## Offline resource comparison

Use the dependency-validation Python environment. Run `python tools/inventory_resources.py
--config <harness.json>` and save stdout in a new, private UTF-8 manifest. To check a second
cache, pass `--compare <manifest.json>`, optionally `--hf-cache <hub-root>` and
`--punkt-english <directory>`. No Hub client requests, NLTK downloads, model loads, or run
writes are needed. Comparison returns 0 for a match, 1 for drift, and 2 on an inventory error.
A match can describe two equally **partial** caches. Inspect `missing_standard_inputs` and
`missing_tables`; even empty lists are not a loader test or proof of upstream authenticity.

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
