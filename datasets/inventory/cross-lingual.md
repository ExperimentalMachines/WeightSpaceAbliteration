# Cross-lingual / multilingual safety & refusal datasets (held-out generalisation axis)

Motivation: 2505.17306 (*Refusal Direction is Universal Across Safety-Aligned Languages*) shows a refusal
direction extracted in English transfers to 13 other languages, and releases **PolyRefuse** (14 languages,
parallel malicious/harmless prompts translated from English). If abliteration removes the refusal direction
in a real sense, the linear probe must stop separating harmful from harmless **in languages that were never
used to fit the edit**, above null-control and permutation baselines — so this axis needs (a) parallel
prompt sets with a matched harmless class, and (b) multiple independent language sets so one translation
pipeline or one harm taxonomy cannot carry the result.

All revisions verified against the HuggingFace dataset API (`sha`) or `git ls-remote` on 2026-11-07.

| # | dataset | canonical URL | id / host | pinned_revision | size (items / bytes) | license | gated | languages | translated from EN? | category coverage | role in this study | retrieved_at |
|---|---------|---------------|-----------|-----------------|----------------------|---------|-------|-----------|---------------------|-------------------|--------------------|--------------|
| 1 | PolyRefuse | https://github.com/mainlp/Multilingual-Refusal/tree/main/PolyRefuse | `mainlp/Multilingual-Refusal` (GitHub) | `985169df2a0b1ba56a95c65d5f60e228f12be4a1` | 1,771 unique source prompts (871 harmful: 572 test / 260 train / 39 val; 900 harmless: 500 / 200 / 200); ≈24.1k prompt-language instances: test 1,072×14 = 15,008, train+val 699×13 = 9,087 (EN train/val exist only as source prompts in code) | Apache-2.0 | false | ar, de, en, es, fr, it, ja, ko, nl, pl, ru, th, zh, yo (14) | YES — Google Translate from English, with back-translated variants shipped for MT-artifact analysis | 22 pooled harm labels in raw data (e.g. Violence, Non-violent crimes, Hate/harassment/discrimination, Sexual content, Disinformation, cybercrime_intrusion, chemical_biological, illegal goods); binary harmful vs harmless framing | **Primary held-out language axis.** Ships a matched benign class per language, which is exactly what the probe-separation test needs; the paper's own 14-language grid is the reference null | 2026-11-07 |
| 2 | MultiJail | https://huggingface.co/datasets/DAMO-NLP-SG/MultiJail (+ code: https://github.com/DAMO-NLP-SG/multilingual-safety-for-LLMs, `577ac511437e07a256130945ef312a99158a18ad`) | `DAMO-NLP-SG/MultiJail` (HuggingFace datasets) | `93d65c778925d55973b9ff30c7bccc8545494eb6` | 315 prompts × 10 languages = 3,150 instances; 344,347 B original, 194,150 B parquet (single CSV, 13 cols) | MIT | false | en, zh, it, vi, ar, ko, th, bn, sw, jv (10) | YES — 315 English unsafe prompts human-annotated into 9 non-English languages (high/medium/low-resource tiers) | 11 harm types in the paper's annotation; unsafe-jailbreak prompts only (no matched harmless class) | Secondary held-out languages, weighted to low-resource (bn, sw, jv) where a universal direction is most falsifiable | 2026-11-07 |
| 3 | XSafety | https://huggingface.co/datasets/ToxicityPrompts/XSafety | `ToxicityPrompts/XSafety` (HuggingFace datasets) | `5c3f160be50d5d513ba07ed2400b43847cbcc318` | 27,999 rows (≈2,800/lang; ru 2,799); 6,346,841 B dataset, 2,572,020 B download | ODC-By-1.0 | false | en, zh, ja, de, fr, ru, es, ar, hi, bn (10; row values use `sp` for Spanish) | YES — 200 sampled instances per source benchmark, Google Translate then two rounds of professional proofreading with cultural adaptation (per 2310.00905) | 14 safety categories (Physical_Harm, Crimes_And_Illegal_Activities, Privacy_And_Property, Ethics_And_Morality, Mental_Health, Unfairness_And_Discrimination, Insult, Goal_Hijacking, Prompt_Leaking, Reverse_Exposure, Unsafe_Instruction_Topic, Inquiry_With_Unsafe_Opinion, Role_Play_Instruction, commonsense); 29 raw label strings incl. `_n`/truncated variants | Primary breadth axis: 10 languages × 14 categories lets the probe test be run per-category, not just per-language, and it is a different corpus and translation pipeline than PolyRefuse | 2026-11-07 |
| 4 | XSafetyGuard | — (no public artifact found) | — | `UNVERIFIED` | — | — | — | — | — | — | **Excluded.** No dataset or model named XSafetyGuard resolves on HuggingFace (`/api/datasets?search=XSafetyGuard` and `/api/quicksearch` both return 0), and the paper trail points to XSafety + the separate XSGuard/XGuard guard-model line (`Nid4l/X-Guard-Bench`, `af5e9b656b1c6e14a94ca94d6e62c3ab7a469884`, n<1K, English-only). Treat row 3 as the intended dataset | 2026-11-07 |
| 5 | M-ALERT | https://huggingface.co/datasets/felfri/M-ALERT (paper 2412.15035) | `felfri/M-ALERT` (HuggingFace datasets) | `db222285d92571fc7db311e16366f65c5b6e4c86` | 14,763 rows × 5 languages = 73,815 prompt instances; 8,948,798 B dataset, 3,574,795 B download | CC-BY-NC-SA-4.0 | false | en, de, fr, it, es (5) | YES — MT-OPUS-en-X, Google Translate and tower-instruct-mistral-v0.2 candidates, best per-sample chosen by COMET-XXL / MetricX-XXL | 6 coarse / 32 fine categories (crime_injury, crime_theft, hate_religion, weapon_chemical, substance_drug, sex_harrasment, self_harm_suicide, …) | European-language replication with a fine-grained taxonomy; single row = one prompt in all 5 languages, so it is a clean within-item cross-lingual control. The `id` column is an int64 row id, not Indonesian | 2026-11-07 |
| 6 | Aya Red Teaming | https://huggingface.co/datasets/CohereLabs/aya_redteaming (mirror: `walledai/AyaRedTeaming`, `44a009ac4f0cdd854590e6aad22aa8ab5bdca95f`) | `CohereLabs/aya_redteaming` (HuggingFace datasets) | `5a16fee03c19d681b4f3527b6a750e1ed4d434c7` | 7,419 prompts (ar 900, en 987, tl 1,009, fr 813, hi 915, ru 1,007, sr 1,006, es 782); 2,247,594 B (8 jsonl) | Apache-2.0 | false (tag `not-for-all-audiences`) | en, ar, fr, es, hi, ru, sr, tl (8) | **NO** — native authorship by compensated annotators, with explicit `global` vs `local` harm labels; the walledai mirror adds `literal_translation` / `semantic_translation` fields | 9 harm categories (Bullying & Harassment, Discrimination & Injustice, Graphic Material, Harms of Representation Allocation & Quality of Service, Hate Speech, Non-consensual sexual content, Profanity, Self-harm, Violence/threats/incitement) | **Translation-artifact control.** If the probe collapses on translated sets but survives here, the effect is MT style, not language. Also the only set with native-authored low-resource coverage (tl, sr) | 2026-11-07 |
| 7 | PolyGuardPrompts | https://huggingface.co/datasets/ToxicityPrompts/PolyGuardPrompts (paper 2504.04377) | `ToxicityPrompts/PolyGuardPrompts` (HuggingFace datasets) | `c5b466a95b64ff121db4398246b6abb7672696ec` | 29,325 rows = 17 langs × 1,725; 93,846,872 B dataset, 52,852,473 B download | CC-BY-4.0 | false | ar, cs, de, en, es, fr, hi, it, ja, ko, nl, pl, pt, ru, sv, th, zh (17) | YES — prompts built from English safety sources then translated per language (translation pipeline described in §3 of 2504.04377) | prompt_harm_label / response_harm_label + prompt_categories/response_categories, 3-level label incl. refusal | Wide-language benchmark with **harm labels and refusal labels on prompts and responses**, so it can score refusal-rate drops directly instead of relying on a judge | 2026-11-07 |
| 8 | PolyGuardMix | https://huggingface.co/datasets/ToxicityPrompts/PolyGuardMix | `ToxicityPrompts/PolyGuardMix` (HuggingFace datasets) | `5b7d93e9e9a636c6c152df071745e04130a21ff4` | 1,910,372 rows (≈112k/lang); 4,534,873,708 B (8 parquet, ~4.5 GB) | CC-BY-4.0 | false | same 17 as row 7 | YES — translated/curated mix of English safety corpora per language | harm + refusal + category labels on prompt and response, adversarial flag, harm-agreement floats | Training-scale fallback: supply language-matched harmless prompts or a power-sized eval subsample if PolyGuardPrompts per-language n is too small for the permutation null | 2026-11-07 |
| 9 | MSTS | https://huggingface.co/datasets/felfri/MSTS (+ code: https://github.com/paul-rottger/msts-multimodal-safety, `e9ae69e8f1ab87ab2bb2ed7c51e992e0430f12e3`) | `felfri/MSTS` (HuggingFace datasets) | `9630ca3cb6251749ca52fee51e68a21943b23067` | 400 cases × 11 languages = 4,400; 743,772,810 B dataset, 1,615,218,762 B storage | CC-BY-4.0 | false | en, de, ru, zh, hi, es, it, fr, ko, ar, fa (11) | YES — same prompt set rendered per language | 3-level hazard taxonomy (category / subcategory / subsubcategory) with prompt_type strata | Low priority: multimodal (image + text). Text `prompt_text` is usable as an extra 11-language held-out set, but do not pull the 1.6 GB image payload unless the study adds a multimodal arm | 2026-11-07 |
| 10 | SorryBench-202503 multilingual | https://huggingface.co/datasets/tiny-aya-safety/sorry-bench-202503-multilingual | `tiny-aya-safety/sorry-bench-202503-multilingual` (HuggingFace datasets) | `599c7126940d5862fc476f93795d5ab276bdf0cc` | 65,960 rows = 6,596 × 10 languages; 175,736,883 B | MIT | false | en, ar, bn, de, es, fr, hi, ja, ru, zh (10) | YES — 6,596 English SorryBench prompts translated into 9 languages (empty `turns` where translation failed/refused) | 44 harm categories × 21 prompt styles (base, role_play, ascii, morse, …) | Style-confounded stress test: separates "direction removed" from "jailbreak template still works", since each language repeats every style | 2026-11-07 |
| 11 | Multilingual Safety Instructions (iNLP-Lab) | https://huggingface.co/datasets/iNLP-Lab/multilingual-safety | `iNLP-Lab/multilingual-safety` (HuggingFace datasets) | `7b6884a1bb014080c42ab8b0b65bc0bfc9066041` | 1,000 rows/lang × 12 = 12,000 (verified: `en.csv` = 1,000 data rows); 3,263,151 B total | CC-BY-NC-4.0 | false | en, zh, it, bn, ko, th, vi, ar, jv, sw, de, fr (12) | YES — the 1,000 English harmful-prompt/refusal pairs from Safety-Tuned LLaMAs translated with `google/gemini-2.0-flash-001` | harmful instruction + **refusal response** pairs (no fine taxonomy); 12 languages | Refusal-shape reference: the paired refusal completions give a language-matched template for measuring refusal-rate, and it shares MultiJail's low-resource tier (bn, sw, jv) for cross-checking | 2026-11-07 |
| 12 | SafetyPrompts (catalogue) | https://safetyprompts.com/ (paper 2404.05399) | `safetyprompts.com` (web catalogue) | `UNVERIFIED` | catalogue of ~100 datasets; no distributable corpus | n/a | n/a | multilingual subset only by reference | n/a — aggregates other datasets | index of harm categories per listed dataset | **Not usable as a dataset.** It is a review/catalogue with no downloadable prompts; `Paul-Rottger/safetyprompts`, `safetyprompts/safetyprompts` and an `allenai/safety-prompts` all fail to resolve. Its multilingual entries are rows 1–3, 5–11 above | 2026-11-07 |

```json
[
  {
    "dataset": "PolyRefuse",
    "url": "https://github.com/mainlp/Multilingual-Refusal/tree/main/PolyRefuse",
    "id": "mainlp/Multilingual-Refusal",
    "host": "GitHub",
    "pinned_revision": "985169df2a0b1ba56a95c65d5f60e228f12be4a1",
    "size_items": 24100,
    "size_detail": "1,771 unique source prompts (871 harmful: 572 test / 260 train / 39 val; 900 harmless: 500 / 200 / 200); test 1,072x14=15,008, train+val 699x13=9,087 prompt-language instances",
    "size_bytes": null,
    "license": "Apache-2.0",
    "gated": false,
    "languages": ["ar","de","en","es","fr","it","ja","ko","nl","pl","ru","th","zh","yo"],
    "translated_from_english": true,
    "translation_method": "Google Translate from English; back-translated variants included",
    "category_coverage": "22 pooled harm labels (Violence, Non-violent crimes, Hate/harassment/discrimination, Sexual content, Disinformation and deception, Illegal goods and services, cybercrime_intrusion, chemical_biological, ...); binary harmful vs harmless",
    "role": "primary held-out language axis with matched harmless class"
  },
  {
    "dataset": "MultiJail",
    "url": "https://huggingface.co/datasets/DAMO-NLP-SG/MultiJail",
    "id": "DAMO-NLP-SG/MultiJail",
    "host": "HuggingFace datasets",
    "pinned_revision": "93d65c778925d55973b9ff30c7bccc8545494eb6",
    "size_items": 3150,
    "size_detail": "315 prompts x 10 languages",
    "size_bytes": 344347,
    "license": "MIT",
    "gated": false,
    "languages": ["en","zh","it","vi","ar","ko","th","bn","sw","jv"],
    "translated_from_english": true,
    "translation_method": "human annotation of 315 English unsafe prompts into 9 non-English languages",
    "category_coverage": "11 harm types; unsafe jailbreak prompts only",
    "role": "secondary held-out languages weighted to low-resource (bn, sw, jv)"
  },
  {
    "dataset": "XSafety",
    "url": "https://huggingface.co/datasets/ToxicityPrompts/XSafety",
    "id": "ToxicityPrompts/XSafety",
    "host": "HuggingFace datasets",
    "pinned_revision": "5c3f160be50d5d513ba07ed2400b43847cbcc318",
    "size_items": 27999,
    "size_detail": "~2,800 per language (ru 2,799)",
    "size_bytes": 6346841,
    "license": "ODC-By-1.0",
    "gated": false,
    "languages": ["en","zh","ja","de","fr","ru","es","ar","hi","bn"],
    "translated_from_english": true,
    "translation_method": "Google Translate + two rounds of professional proofreading with cultural adaptation",
    "category_coverage": "14 safety categories x 10 languages; 29 raw label strings incl. suffixed variants",
    "role": "primary breadth axis: per-category and per-language probe tests"
  },
  {
    "dataset": "XSafetyGuard",
    "url": null,
    "id": null,
    "host": null,
    "pinned_revision": "UNVERIFIED",
    "unverified_reason": "no public artifact by this name; HF dataset search and quicksearch return zero hits; closest real artifacts are ToxicityPrompts/XSafety and the XSGuard/XGuard guard-model line",
    "size_items": null,
    "size_bytes": null,
    "license": null,
    "gated": null,
    "languages": [],
    "translated_from_english": null,
    "category_coverage": null,
    "role": "excluded"
  },
  {
    "dataset": "M-ALERT",
    "url": "https://huggingface.co/datasets/felfri/M-ALERT",
    "id": "felfri/M-ALERT",
    "host": "HuggingFace datasets",
    "pinned_revision": "db222285d92571fc7db311e16366f65c5b6e4c86",
    "size_items": 73815,
    "size_detail": "14,763 rows x 5 language columns (one row = one prompt in all five languages)",
    "size_bytes": 8948798,
    "license": "CC-BY-NC-SA-4.0",
    "gated": false,
    "languages": ["en","de","fr","it","es"],
    "translated_from_english": true,
    "translation_method": "MT-OPUS-en-X, Google Translate, tower-instruct-mistral-v0.2; best per-sample chosen by COMET-XXL / MetricX-XXL",
    "category_coverage": "6 coarse / 32 fine categories (crime_injury, crime_theft, hate_religion, weapon_chemical, substance_drug, sex_harrasment, self_harm_suicide, ...)",
    "role": "European-language replication; within-item cross-lingual control"
  },
  {
    "dataset": "Aya Red Teaming",
    "url": "https://huggingface.co/datasets/CohereLabs/aya_redteaming",
    "id": "CohereLabs/aya_redteaming",
    "host": "HuggingFace datasets",
    "pinned_revision": "5a16fee03c19d681b4f3527b6a750e1ed4d434c7",
    "size_items": 7419,
    "size_detail": "ar 900, en 987, tl 1009, fr 813, hi 915, ru 1007, sr 1006, es 782",
    "size_bytes": 2247594,
    "license": "Apache-2.0",
    "gated": false,
    "gated_note": "content tag not-for-all-audiences; download is ungated",
    "languages": ["en","ar","fr","es","hi","ru","sr","tl"],
    "translated_from_english": false,
    "translation_method": "native authorship by compensated annotators; global vs local harm labels; mirror walledai/AyaRedTeaming adds literal/semantic translation fields",
    "category_coverage": "9 harm categories incl. Non-consensual sexual content, Hate Speech, Self-harm, Violence",
    "role": "translation-artifact control; only natively authored low-resource coverage (tl, sr)"
  },
  {
    "dataset": "PolyGuardPrompts",
    "url": "https://huggingface.co/datasets/ToxicityPrompts/PolyGuardPrompts",
    "id": "ToxicityPrompts/PolyGuardPrompts",
    "host": "HuggingFace datasets",
    "pinned_revision": "c5b466a95b64ff121db4398246b6abb7672696ec",
    "size_items": 29325,
    "size_detail": "17 languages x 1,725",
    "size_bytes": 93846872,
    "license": "CC-BY-4.0",
    "gated": false,
    "languages": ["ar","cs","de","en","es","fr","hi","it","ja","ko","nl","pl","pt","ru","sv","th","zh"],
    "translated_from_english": true,
    "translation_method": "English safety sources translated per language (paper 2504.04377)",
    "category_coverage": "prompt_harm_label / response_harm_label, prompt_categories / response_categories, response_refusal_label",
    "role": "wide-language benchmark with direct refusal labels"
  },
  {
    "dataset": "PolyGuardMix",
    "url": "https://huggingface.co/datasets/ToxicityPrompts/PolyGuardMix",
    "id": "ToxicityPrompts/PolyGuardMix",
    "host": "HuggingFace datasets",
    "pinned_revision": "5b7d93e9e9a636c6c152df071745e04130a21ff4",
    "size_items": 1910372,
    "size_detail": "~112k per language across 17 languages, 8 parquet shards",
    "size_bytes": 4534873708,
    "license": "CC-BY-4.0",
    "gated": false,
    "languages": ["ar","cs","de","en","es","fr","hi","it","ja","ko","nl","pl","pt","ru","sv","th","zh"],
    "translated_from_english": true,
    "translation_method": "translated/curated mix of English safety corpora per language",
    "category_coverage": "harm + refusal + category labels on prompt and response, adversarial flag, agreement scores",
    "role": "training-scale fallback for language-matched harmless class and large permutation subsamples"
  },
  {
    "dataset": "MSTS",
    "url": "https://huggingface.co/datasets/felfri/MSTS",
    "id": "felfri/MSTS",
    "host": "HuggingFace datasets",
    "pinned_revision": "9630ca3cb6251749ca52fee51e68a21943b23067",
    "size_items": 4400,
    "size_detail": "400 cases x 11 languages; multimodal (image + prompt_text)",
    "size_bytes": 743772810,
    "license": "CC-BY-4.0",
    "gated": false,
    "languages": ["en","de","ru","zh","hi","es","it","fr","ko","ar","fa"],
    "translated_from_english": true,
    "translation_method": "same prompt set rendered per language",
    "category_coverage": "category / subcategory / subsubcategory hazard taxonomy with prompt_type strata",
    "role": "low priority; text prompts usable as extra 11-language held-out set"
  },
  {
    "dataset": "SorryBench-202503 multilingual",
    "url": "https://huggingface.co/datasets/tiny-aya-safety/sorry-bench-202503-multilingual",
    "id": "tiny-aya-safety/sorry-bench-202503-multilingual",
    "host": "HuggingFace datasets",
    "pinned_revision": "599c7126940d5862fc476f93795d5ab276bdf0cc",
    "size_items": 65960,
    "size_detail": "6,596 English prompts x 10 languages; empty turns where translation failed",
    "size_bytes": 175736883,
    "license": "MIT",
    "gated": false,
    "languages": ["en","ar","bn","de","es","fr","hi","ja","ru","zh"],
    "translated_from_english": true,
    "translation_method": "translated from SorryBench-202503 English",
    "category_coverage": "44 harm categories x 21 prompt styles (base, role_play, ascii, morse, ...)",
    "role": "style-confounded stress test across languages"
  },
  {
    "dataset": "Multilingual Safety Instructions (iNLP-Lab)",
    "url": "https://huggingface.co/datasets/iNLP-Lab/multilingual-safety",
    "id": "iNLP-Lab/multilingual-safety",
    "host": "HuggingFace datasets",
    "pinned_revision": "7b6884a1bb014080c42ab8b0b65bc0bfc9066041",
    "size_items": 12000,
    "size_detail": "1,000 rows per language x 12 configs (en.csv verified at 1,000 data rows)",
    "size_bytes": 3263151,
    "license": "CC-BY-NC-4.0",
    "gated": false,
    "languages": ["en","zh","it","bn","ko","th","vi","ar","jv","sw","de","fr"],
    "translated_from_english": true,
    "translation_method": "Safety-Tuned LLaMAs 1,000 English harmful-prompt/refusal pairs translated with google/gemini-2.0-flash-001",
    "category_coverage": "harmful instruction + refusal response pairs; no fine taxonomy",
    "role": "language-matched refusal templates; low-resource cross-check with MultiJail"
  },
  {
    "dataset": "SafetyPrompts (catalogue)",
    "url": "https://safetyprompts.com/",
    "id": "safetyprompts.com",
    "host": "web catalogue",
    "pinned_revision": "UNVERIFIED",
    "unverified_reason": "review/catalogue with no distributable prompt corpus; Paul-Rottger/safetyprompts, safetyprompts/safetyprompts and allenai/safety-prompts do not resolve; multilingual entries are the other rows in this table",
    "size_items": null,
    "size_bytes": null,
    "license": null,
    "gated": null,
    "languages": [],
    "translated_from_english": null,
    "category_coverage": "index of harm categories per listed dataset",
    "role": "excluded (not a dataset)"
  }
]
```

## Notes

- **Licences that gate reuse.** M-ALERT is CC-BY-NC-SA-4.0 and iNLP-Lab is CC-BY-NC-4.0 — fine for a research write-up, not for a redistributed artefact. PolyRefuse is Apache-2.0, MultiJail MIT, XSafety ODC-By (attribution only), PolyGuard* / MSTS CC-BY-4.0, Aya Apache-2.0, SorryBench-multilingual MIT.
- **Access.** No dataset here requires auth: `gated=false` on every HuggingFace row (checked via `/api/datasets/<id>`). Aya carries the `not-for-all-audiences` content tag but downloads without a token.
- **Size caveats.** M-ALERT's row count (14,763) is the number of prompts, not prompt-language pairs; multiply by 5 for instances. PolyGuardMix is 4.5 GB — subsample by `language` rather than cloning. MSTS is 1.6 GB of images; only `prompt_text` matters for a text-only arm. XSafety's `ru` block is one row short of 2,800 and its Spanish rows are labelled `sp`, so join on that literal value.
- **Translation provenance matters for the claim.** PolyRefuse, XSafety, MultiJail, M-ALERT, PolyGuard*, MSTS, SorryBench-multilingual and iNLP-Lab are English-source translations, so a probe collapse on them can be an MT-register artefact. Aya Red Teaming is natively authored and is the control that rules that out; run the held-out test on Aya first, then on the translated sets.
- **Matched benign class.** Only PolyRefuse ships harmless prompts per language out of the box. If the separation test needs benign text for the other sets, M-ALERT (all 5 columns are harmful) and MultiJail (harmful only) cannot supply it — use PolyRefuse's harmless split translated, or PolyGuardMix's negative samples.
- **Mirrors.** `walledai/AyaRedTeaming` (`44a009ac4f0cdd854590e6aad22aa8ab5bdca95f`) is a re-upload of Aya with extra translation columns and per-language splits; `walledai/MultiJail` (`df5dc9e51087aae978e3992e61da2e28e58dcb0b`) is a parquet mirror of MultiJail, 315 rows per language. `Kamyar-zeinalipour/M-ALERT` (`3edf183acf0a7172c1ea63b1952d6e1e89e65d50`) is a 1,000-row sample only — do not mistake it for the full benchmark.
- **Excluded.** `thu-coai/Safety-Prompts` (`559ab9f24ce4621e3f839ef05e1075b6c4f125ee`) is Chinese/English only and not a 5+ language parallel set; XSafetyGuard and SafetyPrompts have no verifiable public artifact (see rows 4 and 12).
