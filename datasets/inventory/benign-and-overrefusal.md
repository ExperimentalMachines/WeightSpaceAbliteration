# Benign prompt sets and over-refusal benchmarks

Study role: these sets supply (a) the harmless arm of refusal-direction derivation, (b) the reference distribution for the KL / capability-drift budget, and (c) the over-refusal endpoints that decide whether an edit removed *refusal* rather than *caution*. Every number below is a pinned revision that was resolved through the host API on the retrieval date, not from a search snippet.

Retrieved: 2026-11-07. No dataset contents were downloaded; row counts come from the HF `datasets-server` size/statistics endpoints, Hugging Face `dataset_info` card data, or the file tree of the pinned git revision.

## Inventory

| id | host | canonical URL | pinned_revision | size | license | gated | category coverage | lex. overlap w/ harm batteries | role in study | retrieved_at |
|---|---|---|---|---|---|---|---|---|---|---|
| `mlabonne/harmless_alpaca` | HuggingFace datasets | https://huggingface.co/datasets/mlabonne/harmless_alpaca | `02c6a92cfcf11bb0c387334f8146d149d65b587f` | 31,323 prompts (train 25,058 / test 6,265); 1,215,139 B parquet, 1,987,533 B in memory; single `text` column, 13–379 chars (mean 59) | none declared on card; derived from `tatsu-lab/alpaca` (CC-BY-NC-4.0) — see Notes | false | open-domain instruction-following; no harm taxonomy | LOW — Alpaca-style tasks, no adversarial framing | primary KL reference set: Heretic's KL scorer defaults to `test[:100]` of this repo; also the `good_prompts` arm (`train[:400]`) for ARA/Abliteration direction derivation | 2026-11-07 |
| `p-e-w/heretic` (KL scorer source) | GitHub | https://github.com/p-e-w/heretic | `ce61e18206990bc1f4c51a6cbecd1bfee4b631bb` | `src/heretic/scorers/kl_divergence.py` , `src/heretic/config.py`, `src/heretic/modifiers/abliteration.py` | AGPL-3.0 | false | — (code pin that fixes the KL dataset, split and column) | — | provenance for the KL evaluator: `[scorer.KLDivergence.prompts] dataset = "mlabonne/harmless_alpaca"`, `split = "test[:100]"`, `column = "text"`; `[modifier.Abliteration.good_prompts]` = `train[:400]`, `bad_prompts` = `mlabonne/harmful_behaviors train[:400]` | 2026-11-07 |
| `mlabonne/harmful_behaviors` | HuggingFace datasets | https://huggingface.co/datasets/mlabonne/harmful_behaviors | `01cead01398926d81f7c52bdb790ee8cf77ebba7` | 520 prompts (train 416 / test 104) | none declared | false | harmful-instruction battery, single `text` column | — (this is the harmful arm) | the bad-prompt counterpart Heretic pairs with `harmless_alpaca train[:400]`; the exact 400/400 pairing is the reference contrast a re-derivation must reproduce | 2026-11-07 |
| `tatsu-lab/alpaca` | HuggingFace datasets | https://huggingface.co/datasets/tatsu-lab/alpaca | `dce01c9b08f87459cf36a430d809084718273017` | 52,002 rows; 24,246,638 B parquet | CC-BY-NC-4.0 | false | open-domain instruction-following, no categories | LOW | upstream of `harmless_alpaca`; larger KL sample if 100 prompts prove too noisy (non-commercial only) | 2026-11-07 |
| `databricks/databricks-dolly-15k` | HuggingFace datasets | https://huggingface.co/datasets/databricks/databricks-dolly-15k | `bdd27f4d94b9c1f951818a7da7fd7aeea5dbff1a` | 15,011 rows; 7,747,823 B parquet | CC-BY-SA-3.0 | false | 8 task types — open_qa 3,742; general_qa 2,191; classification 2,136; closed_qa 1,773; brainstorming 1,766; information_extraction 1,506; summarization 1,188; creative_writing 709 | LOW | secondary KL set for a distribution shift that is *not* a rewrite of the KL set itself (guards against overfitting to 100 Alpaca prompts); share-alike obligation on derivatives | 2026-11-07 |
| `walledai/XSTest` | HuggingFace datasets | https://huggingface.co/datasets/walledai/XSTest | `f1d713187c61b6ae64e602d74f0b3d812cc2e8e8` | 450 prompts (safe 250 / unsafe 200); 16,964 B parquet; columns `id, prompt, type, label, focus, note` | CC-BY-4.0 | **true** (`auto` — accept terms + token) | 18 prompt types × 25, incl. homonyms, figurative_language, definitions, safe_targets, privacy_public/fictional, historical_events, and 9 `contrast_*` pairs | VERY HIGH by construction: same surface tokens as the unsafe counterparts, semantics benign | primary over-refusal endpoint; the 250 `label == "safe"` rows are the paired-contrast test set (benign prompt that *looks* harmful, paired with its `contrast_*` unsafe twin) | 2026-11-07 |
| `Paul/XSTest` (non-gated mirror of the same 450) | HuggingFace datasets | https://huggingface.co/datasets/Paul/XSTest | `f600c994b256f12867dfa5b3eb3d545a3e62f8b5` | 450 prompts, one `train` split; 450 rows / 250 safe + 200 unsafe verified via statistics endpoint | CC-BY-4.0 | false | identical to `walledai/XSTest` | VERY HIGH | drop-in replacement for `walledai/XSTest` when no HF token is available; spot-checked row-for-row on schema (`id, prompt, type, label, focus, note`) | 2026-11-07 |
| `paul-rottger/exaggerated-safety` (canonical XSTest source) | GitHub | https://github.com/paul-rottger/exaggerated-safety | `d7bb5bd738c1fcbc36edd83d5e7d1b71a3e2d84d` | `xstest_prompts.csv`, 38,719 B | none declared in repo (paper: research use; HF mirror is CC-BY-4.0) | false | as XSTest | VERY HIGH | ground truth for the CSV, used to prove the HF mirrors did not mutate prompts | 2026-11-07 |
| `bench-llm/or-bench` — `or-bench-80k` | HuggingFace datasets | https://huggingface.co/datasets/bench-llm/or-bench | `e36d8b80e81837c8a8f264bbb2a49f1b32c7e272` | 80,359 prompts; 5,371,731 B parquet; columns `prompt, category`; 10 categories (harmful 16,083; unethical 12,513; illegal 9,349; privacy 9,146; deception 8,040; violence 6,835; hate 6,160; self-harm 5,094; sexual 3,844; harassment 3,295) | CC-BY-4.0 | false | 10 harm categories, all prompts *seemingly* toxic but benign | VERY HIGH — requests are written to mimic harmful battery items as closely as possible | bulk over-refusal corpus; the "did we over-uncage" control for a large refusal-rate drop. Not a refusal benchmark in isolation — needs rejection-rate scoring | 2026-11-07 |
| `bench-llm/or-bench` — `or-bench-hard-1k` | HuggingFace datasets | https://huggingface.co/datasets/bench-llm/or-bench | `e36d8b80e81837c8a8f264bbb2a49f1b32c7e272` | 1,319 prompts; 82,868 B parquet; same 10 categories (privacy 199, … , violence 66) | CC-BY-4.0 | false | 10 harm categories | VERY HIGH (hard subset: maximally refusable phrasing) | the headline over-refusal number; the subset most likely to move when the refusal direction is removed, so it is the sensitive detector for over-correction | 2026-11-07 |
| `bench-llm/or-bench` — `or-bench-toxic` | HuggingFace datasets | https://huggingface.co/datasets/bench-llm/or-bench | `e36d8b80e81837c8a8f264bbb2a49f1b32c7e272` | 655 prompts; 30,892 B parquet | CC-BY-4.0 | false | 10 harm categories | VERY HIGH, but these are *genuinely* harmful | negative control: a working ablation must leave the refusal rate on this split high. Never merge into the benign arm | 2026-11-07 |
| `InvokerStark/OverKill` — OKTest | GitHub | https://github.com/InvokerStark/OverKill | `9551a7ff7b2cb18d178e64fb5cc95e4684311b3b` | `data/OKTest.csv` 22,289 B (300 prompts, manually inspected) + `data/OKTest_heldout.csv` 3,837 B (50 prompts); same revision also ships `data/xstest_v2_prompts.csv` 39,308 B | none declared — no LICENSE file at the pinned revision (see Notes) | false | word-level harm tokens injected into semantically benign sentences, 4 perturbation regimes in the paper | HIGH at token level, LOW at intent level — this is the discriminating property | lexical-trigger over-refusal probe: separates "the model reacts to a banned token" from "the model reads intent", which is exactly the decomposition the study needs. The 50 held-out items are the clean measurement; the 300 are the paper's headline set | 2026-11-07 |
| `allenai/wildguardmix` | HuggingFace datasets | https://huggingface.co/datasets/allenai/wildguardmix | `d29c47f41c8b51348b5c8e8c81c039b3132b66d1` | 92K labeled examples; `train/wildguard_train.parquet` 53,744,450 B, `test/wildguard_test.parquet` 2,258,878 B; configs `wildguardtrain` / `wildguardtest` | ODC-BY | **true** (`auto`) | vanilla + adversarial prompts across 13 risk categories, each with prompt-harmfulness / response-harmfulness / refusal labels | MEDIUM-HIGH — benign prompts are generated from the same pipelines as the harmful ones | source of a label-defined benign split (`prompt_harmfulness == "unharmful"`) that is *matched in style* to harmful prompts, which is what a direction-derivation control needs; also gives a refused/complied label for calibration | 2026-11-07 |
| `walledai/WildGuardTest` (non-gated 1,725-row test split) | HuggingFace datasets | https://huggingface.co/datasets/walledai/WildGuardTest | `dc2c3d069957e7089865fc328a955a82c4c94b65` | 1,725 rows; 490,550 B parquet | ODC-BY | false | as WildGuardTest | MEDIUM-HIGH | usable benign arm and refusal-rate check without accepting the gated WildGuardMix terms; row count 1,725 verified via size endpoint | 2026-11-07 |
| `Anthropic/hh-rlhf` — `harmless-base` | HuggingFace datasets | https://huggingface.co/datasets/Anthropic/hh-rlhf | `09be8c5bbc57cb3887f3a9732ad6aa7ec602a1fa` | repo total 169,352 rows / 181,576,518 B across the default config (train 160,800 / test 8,552); `harmless-base/train.jsonl.gz` 13,197,306 B, `harmless-base/test.jsonl.gz` 742,801 B | MIT | false | multi-turn preference pairs; harmless tranche is red-team-flavoured dialogue | HIGH — the *prompts* are harmful requests; the `chosen` response is the refusal | **not a benign prompt set.** Use only its `chosen` refusals as a refusal-style reference, or its prompts as a harmful arm. Treating `harmless-base` prompts as the harmless side of a direction would invert the contrast | 2026-11-07 |
| `lmsys/lmsys-chat-1m` | HuggingFace datasets | https://huggingface.co/datasets/lmsys/lmsys-chat-1m | `200748d9d3cddcc9d782887541057aca0b18c5da` | ~1,000,000 conversations; 6 parquet shards; per-turn `openai_moderation` field | LMSYS-Chat-1M research license (custom; no SPDX tag on card) | **true** (`auto`) | real-world user traffic, 25 models, 150+ languages | MEDIUM — organic, uncurated; a benign subset is defined by the moderation field, not by hand | realistic-distribution KL / drift check when the Alpaca-style KL set looks too synthetic; benign subset = turns with all `openai_moderation` categories false | 2026-11-07 |

## Paired harmful/harmless contrast — what can actually carry it

| pair | harmless side | harmful side | verdict |
|---|---|---|---|
| Heretic default (reproduce-first) | `mlabonne/harmless_alpaca` `train[:400]` | `mlabonne/harmful_behaviors` `train[:400]` | **Suitable.** This is the exact pairing in `src/heretic/config.py + src/heretic/modifiers/abliteration.py` at `ce61e18`; any re-derivation must match it or declare the deviation. Both arms are single-turn, single-column, equal length. |
| XSTest intrinsic pairs | 250 `label == "safe"` rows | their `contrast_*` twins (the 200 `unsafe` rows) | **Suitable and uniquely valuable** — the only pair here where the surface form is held near-constant and only intent differs, which is what makes a null-control comparison meaningful. |
| OR-Bench | `or-bench-80k` / `or-bench-hard-1k` | `or-bench-toxic` | **Suitable for rate comparison, not for direction fitting.** Categories are shared, so per-category refusal deltas are comparable; but the 655 toxic items were not written as lexical twins of the 80K items. |
| WildGuardMix | `prompt_harmfulness == "unharmful"` rows | `prompt_harmfulness == "harmful"` rows | **Suitable**, style-matched by construction. Requires the gated accept or the `walledai/WildGuardTest` mirror for the test half. |
| OKTest | 300 / 50 benign prompts with injected harm tokens | a harm battery | **Not a pair.** Its counterpart is the *same sentence without the injected token*, which the paper builds itself; use it as an over-refusal endpoint, not as a direction arm. |
| HH-RLHF `harmless-base` | — | its own prompts | **Not usable as a benign arm.** The prompts are harmful; only the `chosen` completions are refusals. |
| Alpaca / Dolly / LMSYS | these sets | — | **KL only.** No category structure to pair against a harm battery, and pairing them against one would confound "harmless" with "different topic and different length". |

## Lexical-similarity tiers (drives which baseline a prompt set can falsify)

- **Near-twin (XSTest safe/contrast, OR-Bench-80K, or-bench-hard-1k):** a linear probe with no semantic content can separate these from harmful prompts only via intent. If the probe still separates post-edit, the edit left a lexical trigger behind rather than a refusal direction. This is the tier that makes the permutation baseline informative.
- **Style-matched (WildGuardMix benign, OKTest with injected tokens):** separable in part by banned-token presence. Report the OKTest number separately from XSTest so token-level and intent-level over-refusal are not averaged together.
- **Open-domain (harmless_alpaca, alpaca, dolly-15k, LMSYS benign):** trivially separable from any harm battery on topic alone. Any probe trained with these as the negative class and a harm battery as the positive class will report high AUROC for reasons that have nothing to do with refusal — **never use them as the harmless arm of the probe**.

## Notes

- `mlabonne/harmless_alpaca` declares no license on its card. It is a filtered derivative of `tatsu-lab/alpaca` (CC-BY-NC-4.0), which makes the non-commercial term travel with it in practice. This affects redistribution of any artifact derived from it, not local measurement. `mlabonne/harmful_behaviors` likewise declares no license.
- `tatsu-lab/alpaca` is CC-BY-NC-4.0: non-commercial only. `databricks/databricks-dolly-15k` is CC-BY-SA-3.0: share-alike propagates to derived prompt sets, so do not fold Dolly prompts into a redistributed mixed benchmark without attribution and the same license.
- OKTest has **no LICENSE file** at the pinned revision `9551a7ff…`; the paper describes research use. Treat as all-rights-reserved for redistribution purposes and keep it a local measurement set.
- `walledai/XSTest`, `allenai/wildguardmix` and `lmsys/lmsys-chat-1m` are `gated: auto` — an HF token with accepted terms is required, and an unauthenticated `resolve/` request returns HTTP 401 (verified). Use `Paul/XSTest` and `walledai/WildGuardTest` when the run must stay tokenless; both were row-counted through the public API.
- `lmsys/lmsys-chat-1m` ships under a custom LMSYS research license, not a SPDX license; commercial use is excluded and the card forbids re-identification. Its benign subset is defined per-turn by `openai_moderation`, so the subset size is a function of the moderation threshold and must be frozen before any comparison — do not let it vary between the baseline and the ablated model.
- Sample-size caveat for the KL term: Heretic's default is **100 prompts** (`harmless_alpaca test[:100]`). At that size the KL estimate carries visible run-to-run variance; if the declared capability cost is stated to two decimals, pre-register a larger fixed prefix (e.g. `test[:500]`, revision-pinned, prefix-stable) rather than resampling.
- Split stability: every split expression above is a *prefix* of a revision-pinned split, so the same rows are selected on every run. Random sampling with an unset seed would break comparability between baseline, edited model, and the null/permutation controls.
- Row counts for the HH-RLHF `harmless-base` tranche are not exposed by the dataset viewer (`harmless_base` is not a viewer config); the 169,352-row figure is the aggregate across the repo's default config and is what the API verifies. The per-tranche figure should be taken at load time, not quoted.

```json
[
  {
    "id": "mlabonne/harmless_alpaca",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/mlabonne/harmless_alpaca",
    "pinned_revision": "02c6a92cfcf11bb0c387334f8146d149d65b587f",
    "size": "31323 prompts (train 25058 / test 6265); 1215139 B parquet; 1987533 B in memory",
    "license": "none declared on card; derivative of tatsu-lab/alpaca (CC-BY-NC-4.0)",
    "gated": false,
    "category_coverage": "open-domain instruction-following; no harm taxonomy",
    "lexical_similarity_to_harm_batteries": "LOW",
    "role": "primary KL reference set; Heretic KL scorer default split test[:100]; good_prompts arm train[:400] for direction derivation",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "p-e-w/heretic",
    "host": "GitHub",
    "canonical_url": "https://github.com/p-e-w/heretic",
    "pinned_revision": "ce61e18206990bc1f4c51a6cbecd1bfee4b631bb",
    "size": "code pin: src/heretic/scorers/kl_divergence.py + src/heretic/config.py + src/heretic/modifiers/abliteration.py",
    "license": "AGPL-3.0",
    "gated": false,
    "category_coverage": "n/a",
    "lexical_similarity_to_harm_batteries": "n/a",
    "role": "provenance for KL evaluator dataset/split/column and for the good_prompts/bad_prompts pairing",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "mlabonne/harmful_behaviors",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/mlabonne/harmful_behaviors",
    "pinned_revision": "01cead01398926d81f7c52bdb790ee8cf77ebba7",
    "size": "520 prompts (train 416 / test 104)",
    "license": "none declared",
    "gated": false,
    "category_coverage": "harmful-instruction battery",
    "lexical_similarity_to_harm_batteries": "is the harmful arm",
    "role": "bad_prompts counterpart to harmless_alpaca train[:400] in Heretic config",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "tatsu-lab/alpaca",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/tatsu-lab/alpaca",
    "pinned_revision": "dce01c9b08f87459cf36a430d809084718273017",
    "size": "52002 rows; 24246638 B parquet",
    "license": "CC-BY-NC-4.0",
    "gated": false,
    "category_coverage": "open-domain instruction-following",
    "lexical_similarity_to_harm_batteries": "LOW",
    "role": "upstream of harmless_alpaca; larger KL sample (non-commercial only)",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "databricks/databricks-dolly-15k",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/databricks/databricks-dolly-15k",
    "pinned_revision": "bdd27f4d94b9c1f951818a7da7fd7aeea5dbff1a",
    "size": "15011 rows; 7747823 B parquet",
    "license": "CC-BY-SA-3.0",
    "gated": false,
    "category_coverage": "open_qa 3742, general_qa 2191, classification 2136, closed_qa 1773, brainstorming 1766, information_extraction 1506, summarization 1188, creative_writing 709",
    "lexical_similarity_to_harm_batteries": "LOW",
    "role": "secondary distribution-shift KL set, independent of the Alpaca prompt family",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "walledai/XSTest",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/walledai/XSTest",
    "pinned_revision": "f1d713187c61b6ae64e602d74f0b3d812cc2e8e8",
    "size": "450 prompts (safe 250 / unsafe 200); 16964 B parquet",
    "license": "CC-BY-4.0",
    "gated": true,
    "category_coverage": "18 types x 25 incl. homonyms, figurative_language, definitions, safe_targets, privacy_public/fictional, historical_events, 9 contrast_* pairs",
    "lexical_similarity_to_harm_batteries": "VERY HIGH",
    "role": "primary over-refusal endpoint; 250 safe rows are the paired-contrast test set",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "Paul/XSTest",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/Paul/XSTest",
    "pinned_revision": "f600c994b256f12867dfa5b3eb3d545a3e62f8b5",
    "size": "450 prompts, single train split",
    "license": "CC-BY-4.0",
    "gated": false,
    "category_coverage": "identical to walledai/XSTest (250 safe / 200 unsafe)",
    "lexical_similarity_to_harm_batteries": "VERY HIGH",
    "role": "tokenless drop-in for walledai/XSTest",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "paul-rottger/exaggerated-safety",
    "host": "GitHub",
    "canonical_url": "https://github.com/paul-rottger/exaggerated-safety",
    "pinned_revision": "d7bb5bd738c1fcbc36edd83d5e7d1b71a3e2d84d",
    "size": "xstest_prompts.csv, 38719 B",
    "license": "none declared in repo (HF mirror CC-BY-4.0)",
    "gated": false,
    "category_coverage": "as XSTest",
    "lexical_similarity_to_harm_batteries": "VERY HIGH",
    "role": "canonical CSV, used to prove HF mirrors are unmutated",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "bench-llm/or-bench#or-bench-80k",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/bench-llm/or-bench",
    "pinned_revision": "e36d8b80e81837c8a8f264bbb2a49f1b32c7e272",
    "size": "80359 prompts; 5371731 B parquet",
    "license": "CC-BY-4.0",
    "gated": false,
    "category_coverage": "10 categories: harmful 16083, unethical 12513, illegal 9349, privacy 9146, deception 8040, violence 6835, hate 6160, self-harm 5094, sexual 3844, harassment 3295",
    "lexical_similarity_to_harm_batteries": "VERY HIGH",
    "role": "bulk over-refusal corpus and over-uncaging control",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "bench-llm/or-bench#or-bench-hard-1k",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/bench-llm/or-bench",
    "pinned_revision": "e36d8b80e81837c8a8f264bbb2a49f1b32c7e272",
    "size": "1319 prompts; 82868 B parquet",
    "license": "CC-BY-4.0",
    "gated": false,
    "category_coverage": "same 10 categories, hard subset (privacy 199 ... violence 66)",
    "lexical_similarity_to_harm_batteries": "VERY HIGH",
    "role": "headline over-refusal number; sensitive detector for over-correction",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "bench-llm/or-bench#or-bench-toxic",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/bench-llm/or-bench",
    "pinned_revision": "e36d8b80e81837c8a8f264bbb2a49f1b32c7e272",
    "size": "655 prompts; 30892 B parquet",
    "license": "CC-BY-4.0",
    "gated": false,
    "category_coverage": "10 harm categories, genuinely harmful",
    "lexical_similarity_to_harm_batteries": "VERY HIGH (truly harmful)",
    "role": "negative control: refusal rate must stay high; never part of the benign arm",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "InvokerStark/OverKill",
    "host": "GitHub",
    "canonical_url": "https://github.com/InvokerStark/OverKill",
    "pinned_revision": "9551a7ff7b2cb18d178e64fb5cc95e4684311b3b",
    "size": "data/OKTest.csv 22289 B (300 prompts); data/OKTest_heldout.csv 3837 B (50 prompts); also data/xstest_v2_prompts.csv 39308 B",
    "license": "none declared (no LICENSE file at this revision)",
    "gated": false,
    "category_coverage": "word-level harm tokens injected into semantically benign sentences, 4 perturbation regimes",
    "lexical_similarity_to_harm_batteries": "HIGH token-level, LOW intent-level",
    "role": "lexical-trigger over-refusal probe; separates token reaction from intent reading",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "allenai/wildguardmix",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/allenai/wildguardmix",
    "pinned_revision": "d29c47f41c8b51348b5c8e8c81c039b3132b66d1",
    "size": "92K labeled examples; train parquet 53744450 B; test parquet 2258878 B",
    "license": "ODC-BY",
    "gated": true,
    "category_coverage": "13 risk categories, vanilla + adversarial, with prompt-harmfulness / response-harmfulness / refusal labels",
    "lexical_similarity_to_harm_batteries": "MEDIUM-HIGH (style-matched)",
    "role": "label-defined benign split for style-matched direction control; refusal/compliance calibration",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "walledai/WildGuardTest",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/walledai/WildGuardTest",
    "pinned_revision": "dc2c3d069957e7089865fc328a955a82c4c94b65",
    "size": "1725 rows; 490550 B parquet",
    "license": "ODC-BY",
    "gated": false,
    "category_coverage": "as WildGuardTest",
    "lexical_similarity_to_harm_batteries": "MEDIUM-HIGH",
    "role": "tokenless benign arm and refusal-rate check",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "Anthropic/hh-rlhf#harmless-base",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/Anthropic/hh-rlhf",
    "pinned_revision": "09be8c5bbc57cb3887f3a9732ad6aa7ec602a1fa",
    "size": "repo aggregate 169352 rows / 181576518 B (default config train 160800 / test 8552); harmless-base train.jsonl.gz 13197306 B, test.jsonl.gz 742801 B",
    "license": "MIT",
    "gated": false,
    "category_coverage": "multi-turn preference pairs; harmless tranche is red-team-flavoured",
    "lexical_similarity_to_harm_batteries": "HIGH (prompts ARE harmful)",
    "role": "NOT a benign prompt set; use chosen refusals as refusal-style reference or prompts as harmful arm",
    "retrieved_at": "2026-11-07"
  },
  {
    "id": "lmsys/lmsys-chat-1m",
    "host": "HuggingFace datasets",
    "canonical_url": "https://huggingface.co/datasets/lmsys/lmsys-chat-1m",
    "pinned_revision": "200748d9d3cddcc9d782887541057aca0b18c5da",
    "size": "~1000000 conversations; 6 parquet shards",
    "license": "LMSYS-Chat-1M research license (custom, no SPDX tag)",
    "gated": true,
    "category_coverage": "real-world user traffic, 25 models, 150+ languages",
    "lexical_similarity_to_harm_batteries": "MEDIUM",
    "role": "realistic-distribution KL/drift check; benign subset = turns with all openai_moderation categories false",
    "retrieved_at": "2026-11-07"
  }
]
```
