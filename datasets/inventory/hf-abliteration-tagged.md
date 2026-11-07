# Abliteration datasets on the HuggingFace Hub — tagged inventory

Every dataset returned by `GET /api/datasets?filter=abliteration&limit=100` (48) and `GET /api/datasets?search=abliteration&limit=100` (27), deduplicated to **70** repos. Revision is the 40-hex `sha` field of `GET https://huggingface.co/api/datasets/<id>`, resolved 2026-11-07 (the `sha` from the listing endpoint matches in every case). Licence is `cardData.license`; `none declared` means the field is absent, not that the repo is unlicensed in law. Row counts come from `datasets-server /info` (`num_examples`, summed over configs and splits) and fall back to the card where the server has no parquet conversion.

Overlap was **measured**, not inferred. Reference sets: AdvBench 520 `goal` strings and the HarmBench 400-row text behaviour CSV, both normalised to lowercase, punctuation stripped, whitespace collapsed, then compared for exact equality. Two regimes: (a) 50 rows pulled from `datasets-server /rows` at offset 0 and offset n/2, for corpora the server serves; (b) the full column, where the data file is under ~500 KB and the server was returning 429. `n` after the slash is the number of rows actually compared. `0/200` therefore means 200 distinct prompts checked and none matched.

Counts: **6 USABLE-EVAL, 5 USABLE-DERIVE, 59 REJECT.** Twenty-two of the 70 repos carry no prompt rows at all (results tables, direction vectors, checkpoints, essays, code); five are byte-identical mirrors of another repo in the list and another five are a second-account copy of five others; two are gated past the point where card or rows can be read, and both are flagged `UNVERIFIED` rather than rejected on merit.

Table, then the same rows as JSON.

| dataset | id | canonical_url | pinned_revision | license | gated | rows | schema | construction | overlap AdvBench | overlap HarmBench | verdict | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen38-27B-abliterated-refusal-eval-fr | GoldfingerCH/qwen38-27B-abliterated-refusal-eval-fr | https://huggingface.co/datasets/GoldfingerCH/qwen38-27B-abliterated-refusal-eval-fr | a79d9c8f5774780225f1f8a012dde0f0e413ca28 | apache-2.0 | false | 626 | id, prompt_sha256, user_en, user_fr, user_safe, user_category, assistant_safe, assistant_category | card documents: user prompts from Guilherme34/uncensor, machine-translated to French (translate-only), Qwen3Guard labels, assistant text dropped, dedup + short-prompt filter | 0/626 | 0/626 | USABLE-EVAL | machine-translation;labels-model-generated |
| engineering-risk-refusal-eval | koldfrontier/engineering-risk-refusal-eval | https://huggingface.co/datasets/koldfrontier/engineering-risk-refusal-eval | 2ca338ee1cd41dcd44ed7796556d491253998d3c | apache-2.0 | false | 50 (11 paired framings, 18 rows) | id, category, subcategory, framing, prompt, refusal_expected, pair_id, note | card documents authoring inside a private DGX lab, paired authorised/unauthorised framings, one known defective row retained for comparability | 0/50 | 0/50 | USABLE-EVAL | single-author;small-n |
| ShrimpMoss_Chinese_Censorship_Abliteration | Nafnlaus/ShrimpMoss_Chinese_Censorship_Abliteration | https://huggingface.co/datasets/Nafnlaus/ShrimpMoss_Chinese_Censorship_Abliteration | 60626961d76ed0a39256120494061bc58510b263 | mit | false | 10,000 bad + 10,000 good, plus 50/125/250/500/1,250/2,500/5,000 slices in 7 formats | prompt / text (fmt-dependent) | card: prompts generated on Mistral NeMo targeting PRC censorship & propaganda topics, EN + Mandarin + Cantonese, paired bad/good sets; ships HarmBench- and StrongREJECT-format CSV renderings (format only, not their content) | 0/125 | 0/125 | USABLE-EVAL | model-generated-prompts;harmbench-format-rendering |
| abliteration-eval | treadon/abliteration-eval | https://huggingface.co/datasets/treadon/abliteration-eval | 3c4296633833a2237be95a1ad9582504841debb1 | apache-2.0 | false | 333 (harmful 200 / over_refusal 83 / multilingual 50); datasets-server /info enumerates only the first two, the 50-row multilingual split ships as a separate parquet | prompt, category, type, note | card documents 200 harmful prompts across 20 categories ×10 and 83 over-refusal prompts across 10 types; generation provenance not stated; blog post is the only trail | 0/200 harmful; 0/83 over_refusal; 0/50 multilingual | 0/200; 0/83; 0/50 | USABLE-EVAL | UNVERIFIED-CONSTRUCTION(provenance);card-schema-mismatch |
| disinhibition-eval | treadon/disinhibition-eval | https://huggingface.co/datasets/treadon/disinhibition-eval | 89a4c3718b79979d0bd236ef9d9c20fba5ef4e81 | apache-2.0 | false | 248 (opinions 120 / factual 42 / explicit_neutral 25 / coherence 28 / edge_cases 33) | prompt, category, type, note | card documents each split's purpose and the disinhibition ablation it measures; no harmful behaviours | 0/50 | 0/50 | USABLE-EVAL | secondary-axis(hedging);UNVERIFIED-CONSTRUCTION(provenance) |
| infosec_harmful_behaviors | zaakirio/infosec_harmful_behaviors | https://huggingface.co/datasets/zaakirio/infosec_harmful_behaviors | 21f231e2c70b4e3fb33e1766c974c513eada4647 | mit | false | 520 (train 400 / test 120) | text | card: generated from data/infosec_harmful.txt in the author's tree; offensive-security prompts, no exploit code | 0/520 | 0/520 | USABLE-EVAL | thin-provenance |
| abliteration-harmful-enriched | Bahushruth/abliteration-harmful-enriched | https://huggingface.co/datasets/Bahushruth/abliteration-harmful-enriched | f29c0b778d3412d5cc7acfc9c6463ce13886212c | apache-2.0 | false | 7,356 (train 5,884 / test 1,472) | text | card documents composition: 6,924 LLM-generated prompts across 33 categories × 10 framings + ~430 from mlabonne/harmful_behaviors (AdvBench); harmful pole only | 520/7356 | 0/7356 | USABLE-DERIVE | advbench-residue |
| harmless-prompts-en-train | chibifire/harmless-prompts-en-train | https://huggingface.co/datasets/chibifire/harmless-prompts-en-train | 128b332feedda5a87586ea0d6a10668896d621fb | apache-2.0 | false | 25,121 (train 22,573 / test 2,548) | text, source | card documents: OASST2 + OASST1 @fdf72ae + Aya English prompter turns, Apache-2.0, length 12-1000 filter, exact dedup, blake2b(text)%10 split | 0/2548 | 0/2548 | USABLE-DERIVE | gold-licence |
| Multilingual-Harmless-Harmful | heretic-org/Multilingual-Harmless-Harmful | https://huggingface.co/datasets/heretic-org/Multilingual-Harmless-Harmful | f4e0aa418ad1f7814a1b64656263e888e79247a9 | cc-by-sa-4.0 | false | 8,320 (416 harmful + 416 harmless × 10 configs) | text, english | card documents translation of heretic-org/Semantic-Harmful + Semantic-Harmless into 10 languages by the uploader; the English harmful split is 50/50 exact AdvBench prompts in sample | 50/50 | 0/50 | USABLE-DERIVE | advbench-derived(behaviours) |
| abliteration-harmful-enriched-categorized | hirundo-io/abliteration-harmful-enriched-categorized | https://huggingface.co/datasets/hirundo-io/abliteration-harmful-enriched-categorized | 6de8d94f685b160b755d047314c5b13af0a7a1d8 | none declared | false | 7,356 (train 5,884 / test 1,472) | text, task_type, framing, domain | re-encoded Bahushruth/abliteration-harmful-enriched parquet with three added label columns; no card body, no licence in cardData | 520/7356 | 0/7356 | USABLE-DERIVE | advbench-residue;no-licence |
| coding_harmless_prompts | zaakirio/coding_harmless_prompts | https://huggingface.co/datasets/zaakirio/coding_harmless_prompts | 0007d89f2ef6116b090f8b81227d7bd2f876df2c | mit | false | 520 (train 400 / test 120) | text | card: generated from data/coding_harmless.txt in the author's infosec-refusal-prompts tree; harmless pole | 0/120 | 0/120 | USABLE-DERIVE | thin-provenance |
| abliteration-eval | 2etatg/abliteration-eval | https://huggingface.co/datasets/2etatg/abliteration-eval | c8d4b3d8f5b2523b8e575edbafea44601c6ccdee | apache-2.0 | false | 333 (harmful 200 / over_refusal 83 / multilingual 50) | prompt, category, type, note | none of its own — byte-identical mirror (5/5 files same git blob oid) of treadon/abliteration-eval, incl. README | 0/200 harmful; 0/83 over_refusal; 0/50 multilingual | 0/200; 0/83; 0/50 | REJECT | duplicate-mirror |
| authorized-cyber-policy-eval | abliterationai/authorized-cyber-policy-eval | https://huggingface.co/datasets/abliterationai/authorized-cyber-policy-eval | c6f631167f9ca90daef924e5f3dad2877acafd02 | apache-2.0 | false | 5 | id, dataset, use_case, surface, scenario, prompt, risk_labels, policy_config, expected, eval, notes | card: gateway policy-routing scenarios (allow/rewrite/escalate), hand-authored | 0/5 | 0/5 | REJECT | too-small;not-refusal-battery |
| fictional-clinical-pii-governance | abliterationai/fictional-clinical-pii-governance | https://huggingface.co/datasets/abliterationai/fictional-clinical-pii-governance | e23e3db02b66f0400e6c1658e21ccbd5c3712dd9 | apache-2.0 | false | 5 | same 11-column policy schema | fictional clinical PII governance scenarios for a policy gateway | 0/5 | 0/5 | REJECT | too-small;not-refusal-battery |
| governed-ai-actions-bench | abliterationai/governed-ai-actions-bench | https://huggingface.co/datasets/abliterationai/governed-ai-actions-bench | 3a55333559b2919e2bd0e2d2478a8337dcd4177d | apache-2.0 | false | 6 | same 11-column policy schema | governed-action routing scenarios | 0/6 | 0/6 | REJECT | too-small;not-refusal-battery |
| synthetic-data-provenance-eval | abliterationai/synthetic-data-provenance-eval | https://huggingface.co/datasets/abliterationai/synthetic-data-provenance-eval | b245e9355a681547eccd7119c291b467cae8d33f | apache-2.0 | false | 5 | same 11-column policy schema | provenance-labelling scenarios | 0/5 | 0/5 | REJECT | too-small;not-refusal-battery |
| trust-safety-action-routing | abliterationai/trust-safety-action-routing | https://huggingface.co/datasets/abliterationai/trust-safety-action-routing | eddbd5cdf2fd71cee0bcecfea87d73ed703a3468 | apache-2.0 | false | 5 | same 11-column policy schema | trust-and-safety routing scenarios | 0/5 | 0/5 | REJECT | too-small;not-refusal-battery |
| authorized-cyber-policy-eval | abliterationaiorg/authorized-cyber-policy-eval | https://huggingface.co/datasets/abliterationaiorg/authorized-cyber-policy-eval | 7091a1b5a88e6b9683590f63b6b2e87e94440f3f | apache-2.0 | false | 5 | same 11-column policy schema | same five scenarios re-uploaded under the second org account | 0/5 | 0/5 | REJECT | duplicate-of-abliterationai |
| fictional-clinical-pii-governance | abliterationaiorg/fictional-clinical-pii-governance | https://huggingface.co/datasets/abliterationaiorg/fictional-clinical-pii-governance | a537c281bd44c2b03e77e83d9a88f897d7bef8ef | apache-2.0 | false | 5 | same | re-upload under second org account | 0/5 | 0/5 | REJECT | duplicate-of-abliterationai |
| governed-ai-actions-bench | abliterationaiorg/governed-ai-actions-bench | https://huggingface.co/datasets/abliterationaiorg/governed-ai-actions-bench | fe7a9fb10c339f17a0cbad1323fb1f6c16cb45ee | apache-2.0 | false | 6 | same | re-upload under second org account | 0/6 | 0/6 | REJECT | duplicate-of-abliterationai |
| synthetic-data-provenance-eval | abliterationaiorg/synthetic-data-provenance-eval | https://huggingface.co/datasets/abliterationaiorg/synthetic-data-provenance-eval | c7ce6155246f3cae9b5ba99b572db403dae53a8f | apache-2.0 | false | 5 | same | re-upload under second org account | 0/5 | 0/5 | REJECT | duplicate-of-abliterationai |
| trust-safety-action-routing | abliterationaiorg/trust-safety-action-routing | https://huggingface.co/datasets/abliterationaiorg/trust-safety-action-routing | 8424023a93af922f7590916025e5c4011f1ad662 | apache-2.0 | false | 5 | same | re-upload under second org account | 0/5 | 0/5 | REJECT | duplicate-of-abliterationai |
| capability-vectors | AlexWortega/capability-vectors | https://huggingface.co/datasets/AlexWortega/capability-vectors | 543e636cadf95891491683837a55620a08143413 | apache-2.0 | false | ~3,500 rows in 10 configs (v2 60/60 … v9 60/60) | prompt (chat-templated trace), source, task_id, reward/reason | card documents: PASS/FAIL trajectories from agent benches (tbench-2, mmlu-pi, claw-eval) on one LoRA base model; rows are full rollout transcripts, not standalone prompts | n/a | n/a | REJECT | model-specific-trajectories |
| arithmetic-abliteration-results | alperiox/arithmetic-abliteration-results | https://huggingface.co/datasets/alperiox/arithmetic-abliteration-results | b883441be983fc1a78336e1f4fcc74d33b413740 | none declared | false | 0 rows; direction_vectors.json (248 KB) + summary.json | n/a (JSON of vectors) | card absent (404); repo holds computed direction vectors only | n/a | n/a | REJECT | no-card;vectors |
| scartissue-tinyaya-abliteration-patches | amugoodbad229/scartissue-tinyaya-abliteration-patches | https://huggingface.co/datasets/amugoodbad229/scartissue-tinyaya-abliteration-patches | 524331aa1e66480e073e35225f5dce4156c6cd16 | none declared | false | 1 row | model, layer, d_model, budget…, patch_format, arms | card: a single patch manifest describing weight-space edits | n/a | n/a | REJECT | model-artifacts |
| scartissue-tinyaya-results | amugoodbad229/scartissue-tinyaya-results | https://huggingface.co/datasets/amugoodbad229/scartissue-tinyaya-results | 44d804df59aed7beb0af4122d4ae38dfa0485f1e | other | false | safety_generations, judge_verdicts 3,864, capability 4,000, frontier 8, patches 5 | judge, arm, prompt, answer, harm, refusal … | card: run outputs — generations, judge verdicts and capability scores for a tiny-aya study | n/a | n/a | REJECT | model-outputs-results |
| scartissue-tinyaya-safety-corpus | amugoodbad229/scartissue-tinyaya-safety-corpus | https://huggingface.co/datasets/amugoodbad229/scartissue-tinyaya-safety-corpus | 45501f117d75af4cdba1fcbee92122fa3d39400c | other | false | 763 (StrongREJECT 313 + XSTest 450) | 18 cols incl. provenance_chain, source_uri, row_index, label, in_scored_evaluation | card documents CuratorKIT rebuild, per-row provenance chain and manifest hashes; content is StrongREJECT + XSTest re-exported (StrongREJECT carries 25 AdvBench prompts upstream) | 25/763 | 0/763 | REJECT | re-export-strongreject/xstest |
| small-mind-probe-sets | arjhinety/small-mind-probe-sets | https://huggingface.co/datasets/arjhinety/small-mind-probe-sets | 917f8ef3ad927d8e87c51e0ce91512aa11477ce4 | cc-by-4.0 | false | 51 probes (h22_judgment 24, emotional_range 27) | probe_id, category, prompt, compliant_shape, good_shape / probe_id, context, emotional_register | card documents GitHub tag study-001 + sha256 pins; LLM-generated, never executed, no scoring script published | 0/51 | 0/51 | REJECT | too-small;UNVERIFIED-scoring |
| FLUX-3-Image-Klein-pup-Uncensored-GGUF-metrics | AtomicChat/FLUX-3-Image-Klein-pup-Uncensored-GGUF-metrics | https://huggingface.co/datasets/AtomicChat/FLUX-3-Image-Klein-pup-Uncensored-GGUF-metrics | 330fbd59f69990537edf6dc97044ea6db969d942 | apache-2.0 | false | no prompt rows; metric tables | n/a | same family: GGUF metric tables | n/a | n/a | REJECT | results-not-prompts |
| FLUX-3-Image-Klein-TE-Uncensored-GGUF-metrics | AtomicChat/FLUX-3-Image-Klein-TE-Uncensored-GGUF-metrics | https://huggingface.co/datasets/AtomicChat/FLUX-3-Image-Klein-TE-Uncensored-GGUF-metrics | 268408a5039270020407d1aea8131139706bda29 | apache-2.0 | false | no prompt rows; metric tables | n/a | card: benchmark metrics for a GGUF bake-off (refusal sweep / MMLU aggregates) | n/a | n/a | REJECT | results-not-prompts |
| Qwen3.8-Flash-Next-Uncensored-GGUF-metrics | AtomicChat/Qwen3.8-Flash-Next-Uncensored-GGUF-metrics | https://huggingface.co/datasets/AtomicChat/Qwen3.8-Flash-Next-Uncensored-GGUF-metrics | a9de1976959d8df97a9a804b2d014a4a02aadfe3 | other | false | no prompt rows; datasets-server 501 (no parquet conversion) | n/a | card: GGUF bake-off metrics, Qwen licence | n/a | n/a | REJECT | results-not-prompts |
| Ternary-Bonsai-2-27B-Uncensored-LoRA-GGUF-metrics | AtomicChat/Ternary-Bonsai-2-27B-Uncensored-LoRA-GGUF-metrics | https://huggingface.co/datasets/AtomicChat/Ternary-Bonsai-2-27B-Uncensored-LoRA-GGUF-metrics | 5c1c1c651a3524aecacb196388a29cb564e4b052 | apache-2.0 | false | 44 runtime_leak / 65 direction_rows / 6 mmlu / 57 mmlu_by_subject / 38 refusal_sweep | pack, config, set, n, refusals, refusal_rate_of_valid … | card: aggregate sweep tables over unnamed internal sets | n/a | n/a | REJECT | results-not-prompts |
| Ternary-Bonsai-2-2B-Uncensored-LoRA-GGUF-metrics | AtomicChat/Ternary-Bonsai-2-2B-Uncensored-LoRA-GGUF-metrics | https://huggingface.co/datasets/AtomicChat/Ternary-Bonsai-2-2B-Uncensored-LoRA-GGUF-metrics | 2b18d839db85dd489fdcf05f29593eadbebd7d08 | apache-2.0 | false | 6 refusal_sweep / 25 direction_rows / 2 mmlu | as above | aggregate sweep tables | n/a | n/a | REJECT | results-not-prompts |
| Ternary-Bonsai-2-4B-Uncensored-LoRA-GGUF-metrics | AtomicChat/Ternary-Bonsai-2-4B-Uncensored-LoRA-GGUF-metrics | https://huggingface.co/datasets/AtomicChat/Ternary-Bonsai-2-4B-Uncensored-LoRA-GGUF-metrics | 24bf8519edc87da2e10f6a25359bc70ddccc3fd0 | apache-2.0 | false | 6 refusal_sweep / 33 direction_rows / 2 mmlu | as above | aggregate sweep tables | n/a | n/a | REJECT | results-not-prompts |
| Ternary-Bonsai-2-9B-Uncensored-LoRA-GGUF-metrics | AtomicChat/Ternary-Bonsai-2-9B-Uncensored-LoRA-GGUF-metrics | https://huggingface.co/datasets/AtomicChat/Ternary-Bonsai-2-9B-Uncensored-LoRA-GGUF-metrics | 21030b8d6086335373001bdf9e45389a149cac36 | apache-2.0 | false | 6 refusal_sweep / 33 direction_rows / 2 mmlu | as above | aggregate sweep tables | n/a | n/a | REJECT | results-not-prompts |
| refusal-geometry-qwen25-3b | bedderautomation/refusal-geometry-qwen25-3b | https://huggingface.co/datasets/bedderautomation/refusal-geometry-qwen25-3b | cecdd6a9f18310343a8dc3903a8e9e16a7e3509d | mit | false | 0 rows; refusal_directions.pt (305 KB), cross_layer_alignment.pt, geometry_results.json | n/a (.pt tensors) | card: OBLITERATUS probing of Qwen2.5-3B — per-layer direction vectors and geometry stats over 512+512 internal pairs | n/a | n/a | REJECT | vectors |
| the-geometry-of-obedience | bedderautomation/the-geometry-of-obedience | https://huggingface.co/datasets/bedderautomation/the-geometry-of-obedience | 2cc8abb5917350c53666cecb797b95c48ca704c1 | mit | false | 0 rows; 6 markdown manuscripts + research notes | n/a | essay/manuscript repo; datasets-server returns 500 (nothing to load) | n/a | n/a | REJECT | no-rows |
| abliterate-refusal | byroneverson/abliterate-refusal | https://huggingface.co/datasets/byroneverson/abliterate-refusal | 7f2934827d9359248d8aae1d664ed9698fd592d5 | none declared | false | 32,331 | prompt, target (bool) | card credits Sumandora/remove-refusals-with-transformers; no licence declared; half the sample is AdvBench verbatim | 25/50 | 0/50 | REJECT | no-licence;advbench-derived |
| Capy-CrackV2 | CapyStudios/Capy-CrackV2 | https://huggingface.co/datasets/CapyStudios/Capy-CrackV2 | 1477ecd2da9828542ba79fb1b9b86a32fa9f68bc | mit | false | ~3,000 claimed; 1.6 MB JSONL | text (request + justification + generated "Master Response") | card is a marketing narrative; rows bundle a request with a generated answer and placeholder code; no eval units, no provenance | n/a | n/a | REJECT | unverified-construction;model-output-mixed |
| harmful-prompts-bench | chibifire/harmful-prompts-bench | https://huggingface.co/datasets/chibifire/harmful-prompts-bench | 579a41537ab6c1f77f20f116b942374590640d65 | mit | false | 520 (train 416 / test 104) | text | card documents: AdvBench via mlabonne/harmful_behaviors @01cead0, dedup on exact text, lexicographic sort, blake2b(text)%5 test split | 520/520 | 0/520 | REJECT | advbench-verbatim |
| abliteration-qwen25-7b-safety-audit | darkengross/abliteration-qwen25-7b-safety-audit | https://huggingface.co/datasets/darkengross/abliteration-qwen25-7b-safety-audit | d88e40ebfdc36eca587dc1e7a42d7e947e173b1e | other | false | 2,641 | goal, category, technique, sample, prompt, baseline_response, abliterated_response, 20 label columns | card: per-prompt paired completions from a base and an abliterated Qwen2.5-7B plus a guard-model label block | 17/96 | 0/96 | REJECT | model-outputs;leakage-risk |
| Comfy_Abliteration_Prompt_Generation_Node | daspin335/Comfy_Abliteration_Prompt_Generation_Node | https://huggingface.co/datasets/daspin335/Comfy_Abliteration_Prompt_Generation_Node | 5cf786a2c395d58fe0140736fb1d9485d77c0ecf | none declared | false | 0 rows; 4 code files | n/a | ComfyUI custom node source (nodes.py), not a dataset | n/a | n/a | REJECT | code-not-dataset |
| Qwen3.6-35B-A3B-heretic-study | DmitryDB/Qwen3.6-35B-A3B-heretic-study | https://huggingface.co/datasets/DmitryDB/Qwen3.6-35B-A3B-heretic-study | b5956886075a609abea3c8a4ab901094a867adde | apache-2.0 | false | no prompt rows (12 label maps over 234 external queries + imatrix + reports) | id → label; matrix summaries | card states explicitly that no prompt or response text is included; queries are AdvBench 104 + ForbiddenQuestions 130 held externally | n/a | n/a | REJECT | no-prompts |
| senbonzakura-dataset | ElementMerc/senbonzakura-dataset | https://huggingface.co/datasets/ElementMerc/senbonzakura-dataset | 11d90d2ca0fc16b7c61a257c075614c1e2a40e1c | cc-by-nc-4.0 | `auto` | unknown — bad_ds 20 KB arrow, bad_eval_ds 360 KB, good_ds 326 KB | inaccessible | gated (auto); README and /rows both return 401 without an accepted token, so neither card nor rows could be read | n/a | n/a | REJECT | UNVERIFIED:gated-401 |
| bonsai-27b-q1-abliteration-benchmark | farbodghasemlu/bonsai-27b-q1-abliteration-benchmark | https://huggingface.co/datasets/farbodghasemlu/bonsai-27b-q1-abliteration-benchmark | 9f0a952c3ca4afac78dff92945c5f5c7516f341e | apache-2.0 | false | 0 rows; lm-eval result JSONs + logs + refusal_eval.py | n/a | card: a 1-bit packing benchmark report (100 prompts, results only) | n/a | n/a | REJECT | results-not-prompts |
| Multilingual-Harmless-Harmful | Heyjab/Multilingual-Harmless-Harmful | https://huggingface.co/datasets/Heyjab/Multilingual-Harmless-Harmful | 67520a76dbfb01df1d677375925196fb500a1fdf | cc-by-sa-4.0 | false | 416 harmful + 416 harmless × 9 languages | text, english | re-upload of heretic-org/Multilingual-Harmless-Harmful minus the japanese config; no method of its own | 50/50 | 0/50 | REJECT | duplicate-of-heretic-org;advbench-derived |
| refinement-abliterated-thinking_heretic | hirundo-io/refinement-abliterated-thinking_heretic | https://huggingface.co/datasets/hirundo-io/refinement-abliterated-thinking_heretic | ea4a9995e330c8e0c395a159d2d378a3666eddb8 | apache-2.0 | false | 416 | prompt, messages, answer | card: seeds from mlabonne/harmful_behaviors (AdvBench), answers generated by an abliterated Qwen3-4B; assistant completion is the payload | n/a | n/a | REJECT | model-outputs;advbench-seeds |
| refinement-abliterated-thinking_heretic_short_answers | hirundo-io/refinement-abliterated-thinking_heretic_short_answers | https://huggingface.co/datasets/hirundo-io/refinement-abliterated-thinking_heretic_short_answers | 8a7018fd6220ee9bcf983d98c4ad28f1f6262234 | apache-2.0 | false | 520 | prompt, answer, messages | same pipeline, short-answer variant | n/a | n/a | REJECT | model-outputs;advbench-seeds |
| refinement-abliterated-vision_heretic__harmful_refusals | hirundo-io/refinement-abliterated-vision_heretic__harmful_refusals | https://huggingface.co/datasets/hirundo-io/refinement-abliterated-vision_heretic__harmful_refusals | 905d76a55647b0ec054616311b28f08839eaca34 | apache-2.0 | false | 520 | prompt, answer, messages | same pipeline, vision-model answers | n/a | n/a | REJECT | model-outputs;advbench-seeds |
| refinement-abliterated-vision_heretic_short_answers | hirundo-io/refinement-abliterated-vision_heretic_short_answers | https://huggingface.co/datasets/hirundo-io/refinement-abliterated-vision_heretic_short_answers | 21760bc8ab6ab40f9b74700b4ec2a6480c3da906 | apache-2.0 | false | 1,974 | prompt, answer, messages | same pipeline | n/a | n/a | REJECT | model-outputs;advbench-seeds |
| refinement-abliterated-vision_heretic_short_answers1 | hirundo-io/refinement-abliterated-vision_heretic_short_answers1 | https://huggingface.co/datasets/hirundo-io/refinement-abliterated-vision_heretic_short_answers1 | 401382792557a955dd4728ac570df34a00747db6 | apache-2.0 | false | 450 | prompt, answer, messages | same pipeline, third variant | n/a | n/a | REJECT | model-outputs;advbench-seeds |
| UncensoredBench | idllresearch/UncensoredBench | https://huggingface.co/datasets/idllresearch/UncensoredBench | 142b4227f676c386677476aa57661237e33904d0 | cc-by-4.0 | false | 6,650 QA over 50 unique prompts | LLM, Type, Question, Answer | card + IMC'26 paper: 50 CatQA prompts answered by 105 uncensored + 28 aligned models; child-abuse items withheld | 0/50 | 0/50 | REJECT | answers-are-model-outputs;prompts-external(catqa) |
| UncensoredLLMList | idllresearch/UncensoredLLMList | https://huggingface.co/datasets/idllresearch/UncensoredLLMList | 34e6e48e5e0f1037b4d14e31e91e3faef299a83a | cc-by-4.0 | false | 22,096 | Identifier, Platform, URL | card: registry of uncensored model repos; no prompts | n/a | n/a | REJECT | no-prompts |
| qwen3.8-27b-refusal-ablation-artifacts | jhk0317/qwen3.8-27b-refusal-ablation-artifacts | https://huggingface.co/datasets/jhk0317/qwen3.8-27b-refusal-ablation-artifacts | cf37178835f77bb78f6d1518a42182f1c43f9901 | apache-2.0 | false | 0 tabular rows; 5 checkpoints, eval/judge/human dirs | n/a | run artefacts (checkpoints, judge outputs) for one ablation sweep | n/a | n/a | REJECT | model-artifacts |
| abliterate-refusal-cn | lenML/abliterate-refusal-cn | https://huggingface.co/datasets/lenML/abliterate-refusal-cn | 31e1a136810bcd550e4a994cd117e8d6ccdff0bd | none declared | false | 32,331 | prompt, prompt_cn, is_harmful | card: local-model translation of byroneverson/abliterate-refusal into Chinese; no licence declared; inherits the AdvBench half | 0/50 (prompt_cn); 25/50 (prompt) | 0/50 | REJECT | no-licence;advbench-derived |
| abliteration_en | Metin/abliteration_en | https://huggingface.co/datasets/Metin/abliteration_en | 6456ffe2a88ed6058872ba50c3995f65fadd1634 | mit | false | 400 (train 256 / test 144) | text | card is frontmatter only (35 bytes, no body): no source, no construction, no split rule | 0/400 | 0/400 | REJECT | UNVERIFIED-CONSTRUCTION |
| abliteration_tr | Metin/abliteration_tr | https://huggingface.co/datasets/Metin/abliteration_tr | 13c0728371288a1e2fe36703a5cc00393d92e962 | mit | false | 400 (train 256 / test 144) + turkish_instructions.csv | text | card is frontmatter only (35 bytes): no body, no method; Turkish sibling of Metin/abliteration_en | 0/256 | 0/256 | REJECT | UNVERIFIED-CONSTRUCTION |
| heretic-completions | noahrossi/heretic-completions | https://huggingface.co/datasets/noahrossi/heretic-completions | 705ea670684d54a764c2725cd95602496ba9bf83 | other | false | 6,768 (4,064 + 2,704) | id, source, split, prompt, completion, label (+ reasoning for gpt-oss) | card: completions from two abliterated models over 9 red-team/over-refusal sources incl. advbench and harmbench | 2/50 | 3/50 | REJECT | model-outputs;harmbench-sourced |
| assistant-axis-abliteration-vectors | pandaman007/assistant-axis-abliteration-vectors | https://huggingface.co/datasets/pandaman007/assistant-axis-abliteration-vectors | d4868a95a3545135f24fe9ce2c0d43bb2a2d873d | none declared | false | 0 rows; activations/, vectors/, scores/, responses/, plots/ | n/a | no README (404); directory tree is model-specific activations and vectors for llama-3.1-8b-abliterated | n/a | n/a | REJECT | vectors;no-card |
| ShrimpMoss_Chinese_Censorship_Abliteration | Quinn67/ShrimpMoss_Chinese_Censorship_Abliteration | https://huggingface.co/datasets/Quinn67/ShrimpMoss_Chinese_Censorship_Abliteration | ba458e94deb0db5e8a5c78071819df4f81d70e72 | mit | false | same 20,000 + slices | same | byte-identical fork of Nafnlaus (50/50 files same blob oid) | 0/125 | 0/125 | REJECT | duplicate-mirror |
| modelatlas-community | RadicalNotionAI/modelatlas-community | https://huggingface.co/datasets/RadicalNotionAI/modelatlas-community | 658e570d970ab492a07220ea2fc0693beac0cc9f | cc-by-4.0 | false | 0 rows (train split empty) | model_id, config, techniques, provenance, intervention_map … | card: model-architecture metadata registry, not prompts | n/a | n/a | REJECT | no-rows |
| derestriction | RevivifAI/derestriction | https://huggingface.co/datasets/RevivifAI/derestriction | 2600f4e7ab6224e61cc77b22a18859b41f3b6372 | mit | false | 111,367 (restrict 12,867 / derestrict 40,791 / allow 57,709) | Prompt, Source, Restriction_Category | card documents assembly from AdvBench, JailbreakBench, Alpaca, MMLU/GSM8K/ARC/MATH/HumanEval and allenai/wildguardmix, with a two-stage harm filter; WildGuardMix is gated under AI2 RUA and is carried into an MIT-licensed repo | 25/50 derestrict; 0/50 allow | 0/50 | REJECT | advbench-derived;licence-conflict(wildguardmix) |
| code-refusal-for-abliteration | scarysnake/code-refusal-for-abliteration | https://huggingface.co/datasets/scarysnake/code-refusal-for-abliteration | a9fc258c4b27b900d73da2e425ca7b913da9918d | cc-by-nc-4.0 | false | 198 | goal, target | card: AdvBench filtered to programming-specific tasks; harmful_behaviors.csv is 198/198 AdvBench rows verbatim | 198/198 | 0/198 | REJECT | advbench-verbatim-subset |
| abliteration-harmful-enriched | spinochenza/abliteration-harmful-enriched | https://huggingface.co/datasets/spinochenza/abliteration-harmful-enriched | 82a74bc4e366c9f26427be34761076f1cceff8f4 | apache-2.0 | false | 7,356 | text | byte-identical copy of Bahushruth/abliteration-harmful-enriched (4/4 files same blob oid, README included) | 520/7356 | 0/7356 | REJECT | duplicate-mirror |
| engineering-risk-refusal-eval | stjibon/engineering-risk-refusal-eval | https://huggingface.co/datasets/stjibon/engineering-risk-refusal-eval | 9f988a69c1aa9abddb9b0ae48bfc15f337c5e3a5 | apache-2.0 | false | 50 + two result files | same schema | byte-identical mirror of koldfrontier (5/5 files same blob oid) | 0/50 | 0/50 | REJECT | duplicate-mirror |
| detailed-vs-vague-pairs-english | strangecreator/detailed-vs-vague-pairs-english | https://huggingface.co/datasets/strangecreator/detailed-vs-vague-pairs-english | 39a6fb3be593892c607cf399659428298e0c3987 | cc-by-4.0 | false | 700 pairs (600 + 100) | detailed_text, vague_text, styles, domain, register, contrast_explanation | card documents 145 domains × 50 vague styles; prose-style pairs, no harm dimension | n/a | n/a | REJECT | not-refusal |
| weightprint | tardellirs/weightprint | https://huggingface.co/datasets/tardellirs/weightprint | e120e08b4580717e97a521b44a49cbe85b6f0cd7 | apache-2.0 | false | 120,976 pairs + 155,769 copies | model_id, parent_id, verdict, tensors_changed … | card: Hub-wide weight-census tables | n/a | n/a | REJECT | no-prompts |
| code-refusal-for-abliteration | timmaythetoolmann/code-refusal-for-abliteration | https://huggingface.co/datasets/timmaythetoolmann/code-refusal-for-abliteration | 09e3ff3edb7d3369fc6281ec8b96be3b728f4751 | cc-by-nc-4.0 | `auto` | 198 (unreadable) | goal, target | gated (auto); README + CSV sizes match scarysnake/code-refusal-for-abliteration exactly (628 B / 31,831 B) | 198/198 | 0/198 | REJECT | UNVERIFIED:gated-401;duplicate-mirror |
| uncensorbench-leaderboard | wisent-ai/uncensorbench-leaderboard | https://huggingface.co/datasets/wisent-ai/uncensorbench-leaderboard | 0eaee36499892ac86cf5ff91c52fb0492dfc681d | mit | false | 0 rows | leaderboard schema (empty) | card: leaderboard table for an external benchmark; prompts live in the uncensorbench package | n/a | n/a | REJECT | no-rows |
| unsafe_qa | XuehangCang/unsafe_qa | https://huggingface.co/datasets/XuehangCang/unsafe_qa | 53e0cbb1068b94912e6a0889261029e587f63dfe | agpl-3.0 | false | 800 | 有害问题, 正确思考, 正确回答, 错误思考, 错误回答 | card names only an unnamed `unsafe_prompt` source for the 800 bilingual questions, then two models' CoT + answers; no upstream id, no filter rule | 26/50 | 0/50 | REJECT | UNVERIFIED-CONSTRUCTION;model-output-mixed |

```json
[
 {
  "id": "GoldfingerCH/qwen38-27B-abliterated-refusal-eval-fr",
  "canonical_url": "https://huggingface.co/datasets/GoldfingerCH/qwen38-27B-abliterated-refusal-eval-fr",
  "pinned_revision": "a79d9c8f5774780225f1f8a012dde0f0e413ca28",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "626",
  "schema": "id, prompt_sha256, user_en, user_fr, user_safe, user_category, assistant_safe, assistant_category",
  "construction": "card documents: user prompts from Guilherme34/uncensor, machine-translated to French (translate-only), Qwen3Guard labels, assistant text dropped, dedup + short-prompt filter",
  "overlap_advbench": "0/626",
  "overlap_harmbench": "0/626",
  "overlap_basis": "full parquet, user_en",
  "verdict": "USABLE-EVAL",
  "flags": "machine-translation;labels-model-generated",
  "downloads": 36
 },
 {
  "id": "koldfrontier/engineering-risk-refusal-eval",
  "canonical_url": "https://huggingface.co/datasets/koldfrontier/engineering-risk-refusal-eval",
  "pinned_revision": "2ca338ee1cd41dcd44ed7796556d491253998d3c",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "50 (11 paired framings, 18 rows)",
  "schema": "id, category, subcategory, framing, prompt, refusal_expected, pair_id, note",
  "construction": "card documents authoring inside a private DGX lab, paired authorised/unauthorised framings, one known defective row retained for comparability",
  "overlap_advbench": "0/50",
  "overlap_harmbench": "0/50",
  "overlap_basis": "full JSONL (all 50 prompts)",
  "verdict": "USABLE-EVAL",
  "flags": "single-author;small-n",
  "downloads": 99
 },
 {
  "id": "Nafnlaus/ShrimpMoss_Chinese_Censorship_Abliteration",
  "canonical_url": "https://huggingface.co/datasets/Nafnlaus/ShrimpMoss_Chinese_Censorship_Abliteration",
  "pinned_revision": "60626961d76ed0a39256120494061bc58510b263",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "10,000 bad + 10,000 good, plus 50/125/250/500/1,250/2,500/5,000 slices in 7 formats",
  "schema": "prompt / text (fmt-dependent)",
  "construction": "card: prompts generated on Mistral NeMo targeting PRC censorship & propaganda topics, EN + Mandarin + Cantonese, paired bad/good sets; ships HarmBench- and StrongREJECT-format CSV renderings (format only, not their content)",
  "overlap_advbench": "0/125",
  "overlap_harmbench": "0/125",
  "overlap_basis": "full 125-row published slice (china_bad_125)",
  "verdict": "USABLE-EVAL",
  "flags": "model-generated-prompts;harmbench-format-rendering",
  "downloads": 439
 },
 {
  "id": "treadon/abliteration-eval",
  "canonical_url": "https://huggingface.co/datasets/treadon/abliteration-eval",
  "pinned_revision": "3c4296633833a2237be95a1ad9582504841debb1",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "333 (harmful 200 / over_refusal 83 / multilingual 50); datasets-server /info enumerates only the first two, the 50-row multilingual split ships as a separate parquet",
  "schema": "prompt, category, type, note",
  "construction": "card documents 200 harmful prompts across 20 categories ×10 and 83 over-refusal prompts across 10 types; generation provenance not stated; blog post is the only trail",
  "overlap_advbench": "0/200 harmful; 0/83 over_refusal; 0/50 multilingual",
  "overlap_harmbench": "0/200; 0/83; 0/50",
  "overlap_basis": "full parquet, all three splits",
  "verdict": "USABLE-EVAL",
  "flags": "UNVERIFIED-CONSTRUCTION(provenance);card-schema-mismatch",
  "downloads": 123
 },
 {
  "id": "treadon/disinhibition-eval",
  "canonical_url": "https://huggingface.co/datasets/treadon/disinhibition-eval",
  "pinned_revision": "89a4c3718b79979d0bd236ef9d9c20fba5ef4e81",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "248 (opinions 120 / factual 42 / explicit_neutral 25 / coherence 28 / edge_cases 33)",
  "schema": "prompt, category, type, note",
  "construction": "card documents each split's purpose and the disinhibition ablation it measures; no harmful behaviours",
  "overlap_advbench": "0/50",
  "overlap_harmbench": "0/50",
  "overlap_basis": "50-row sample, opinions split",
  "verdict": "USABLE-EVAL",
  "flags": "secondary-axis(hedging);UNVERIFIED-CONSTRUCTION(provenance)",
  "downloads": 33
 },
 {
  "id": "zaakirio/infosec_harmful_behaviors",
  "canonical_url": "https://huggingface.co/datasets/zaakirio/infosec_harmful_behaviors",
  "pinned_revision": "21f231e2c70b4e3fb33e1766c974c513eada4647",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "520 (train 400 / test 120)",
  "schema": "text",
  "construction": "card: generated from data/infosec_harmful.txt in the author's tree; offensive-security prompts, no exploit code",
  "overlap_advbench": "0/520",
  "overlap_harmbench": "0/520",
  "overlap_basis": "full CSV, train+test",
  "verdict": "USABLE-EVAL",
  "flags": "thin-provenance",
  "downloads": 43
 },
 {
  "id": "Bahushruth/abliteration-harmful-enriched",
  "canonical_url": "https://huggingface.co/datasets/Bahushruth/abliteration-harmful-enriched",
  "pinned_revision": "f29c0b778d3412d5cc7acfc9c6463ce13886212c",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "7,356 (train 5,884 / test 1,472)",
  "schema": "text",
  "construction": "card documents composition: 6,924 LLM-generated prompts across 33 categories × 10 framings + ~430 from mlabonne/harmful_behaviors (AdvBench); harmful pole only",
  "overlap_advbench": "520/7356",
  "overlap_harmbench": "0/7356",
  "overlap_basis": "full column, train+test parquet",
  "verdict": "USABLE-DERIVE",
  "flags": "advbench-residue",
  "downloads": 177
 },
 {
  "id": "chibifire/harmless-prompts-en-train",
  "canonical_url": "https://huggingface.co/datasets/chibifire/harmless-prompts-en-train",
  "pinned_revision": "128b332feedda5a87586ea0d6a10668896d621fb",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "25,121 (train 22,573 / test 2,548)",
  "schema": "text, source",
  "construction": "card documents: OASST2 + OASST1 @fdf72ae + Aya English prompter turns, Apache-2.0, length 12-1000 filter, exact dedup, blake2b(text)%10 split",
  "overlap_advbench": "0/2548",
  "overlap_harmbench": "0/2548",
  "overlap_basis": "full parquet, test split",
  "verdict": "USABLE-DERIVE",
  "flags": "gold-licence",
  "downloads": 38
 },
 {
  "id": "heretic-org/Multilingual-Harmless-Harmful",
  "canonical_url": "https://huggingface.co/datasets/heretic-org/Multilingual-Harmless-Harmful",
  "pinned_revision": "f4e0aa418ad1f7814a1b64656263e888e79247a9",
  "license": "cc-by-sa-4.0",
  "gated_raw": false,
  "gated": false,
  "rows": "8,320 (416 harmful + 416 harmless × 10 configs)",
  "schema": "text, english",
  "construction": "card documents translation of heretic-org/Semantic-Harmful + Semantic-Harmless into 10 languages by the uploader; the English harmful split is 50/50 exact AdvBench prompts in sample",
  "overlap_advbench": "50/50",
  "overlap_harmbench": "0/50",
  "overlap_basis": "50-row sample (offset 0 + 208), text",
  "verdict": "USABLE-DERIVE",
  "flags": "advbench-derived(behaviours)",
  "downloads": 465
 },
 {
  "id": "hirundo-io/abliteration-harmful-enriched-categorized",
  "canonical_url": "https://huggingface.co/datasets/hirundo-io/abliteration-harmful-enriched-categorized",
  "pinned_revision": "6de8d94f685b160b755d047314c5b13af0a7a1d8",
  "license": "none declared",
  "gated_raw": false,
  "gated": false,
  "rows": "7,356 (train 5,884 / test 1,472)",
  "schema": "text, task_type, framing, domain",
  "construction": "re-encoded Bahushruth/abliteration-harmful-enriched parquet with three added label columns; no card body, no licence in cardData",
  "overlap_advbench": "520/7356",
  "overlap_harmbench": "0/7356",
  "overlap_basis": "full column, train+test parquet; identical files to Bahushruth/abliteration-harmful-enriched",
  "verdict": "USABLE-DERIVE",
  "flags": "advbench-residue;no-licence",
  "downloads": 9
 },
 {
  "id": "zaakirio/coding_harmless_prompts",
  "canonical_url": "https://huggingface.co/datasets/zaakirio/coding_harmless_prompts",
  "pinned_revision": "0007d89f2ef6116b090f8b81227d7bd2f876df2c",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "520 (train 400 / test 120)",
  "schema": "text",
  "construction": "card: generated from data/coding_harmless.txt in the author's infosec-refusal-prompts tree; harmless pole",
  "overlap_advbench": "0/120",
  "overlap_harmbench": "0/120",
  "overlap_basis": "full CSV, test split",
  "verdict": "USABLE-DERIVE",
  "flags": "thin-provenance",
  "downloads": 22
 },
 {
  "id": "2etatg/abliteration-eval",
  "canonical_url": "https://huggingface.co/datasets/2etatg/abliteration-eval",
  "pinned_revision": "c8d4b3d8f5b2523b8e575edbafea44601c6ccdee",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "333 (harmful 200 / over_refusal 83 / multilingual 50)",
  "schema": "prompt, category, type, note",
  "construction": "none of its own — byte-identical mirror (5/5 files same git blob oid) of treadon/abliteration-eval, incl. README",
  "overlap_advbench": "0/200 harmful; 0/83 over_refusal; 0/50 multilingual",
  "overlap_harmbench": "0/200; 0/83; 0/50",
  "overlap_basis": "full parquet, all three splits; identical files to treadon/abliteration-eval",
  "verdict": "REJECT",
  "flags": "duplicate-mirror",
  "downloads": 23
 },
 {
  "id": "abliterationai/authorized-cyber-policy-eval",
  "canonical_url": "https://huggingface.co/datasets/abliterationai/authorized-cyber-policy-eval",
  "pinned_revision": "c6f631167f9ca90daef924e5f3dad2877acafd02",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "5",
  "schema": "id, dataset, use_case, surface, scenario, prompt, risk_labels, policy_config, expected, eval, notes",
  "construction": "card: gateway policy-routing scenarios (allow/rewrite/escalate), hand-authored",
  "overlap_advbench": "0/5",
  "overlap_harmbench": "0/5",
  "overlap_basis": "full JSONL, 5/5 prompt rows",
  "verdict": "REJECT",
  "flags": "too-small;not-refusal-battery",
  "downloads": 37
 },
 {
  "id": "abliterationai/fictional-clinical-pii-governance",
  "canonical_url": "https://huggingface.co/datasets/abliterationai/fictional-clinical-pii-governance",
  "pinned_revision": "e23e3db02b66f0400e6c1658e21ccbd5c3712dd9",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "5",
  "schema": "same 11-column policy schema",
  "construction": "fictional clinical PII governance scenarios for a policy gateway",
  "overlap_advbench": "0/5",
  "overlap_harmbench": "0/5",
  "overlap_basis": "full JSONL, 5/5 prompt rows",
  "verdict": "REJECT",
  "flags": "too-small;not-refusal-battery",
  "downloads": 33
 },
 {
  "id": "abliterationai/governed-ai-actions-bench",
  "canonical_url": "https://huggingface.co/datasets/abliterationai/governed-ai-actions-bench",
  "pinned_revision": "3a55333559b2919e2bd0e2d2478a8337dcd4177d",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "6",
  "schema": "same 11-column policy schema",
  "construction": "governed-action routing scenarios",
  "overlap_advbench": "0/6",
  "overlap_harmbench": "0/6",
  "overlap_basis": "full JSONL, 6/6 prompt rows",
  "verdict": "REJECT",
  "flags": "too-small;not-refusal-battery",
  "downloads": 38
 },
 {
  "id": "abliterationai/synthetic-data-provenance-eval",
  "canonical_url": "https://huggingface.co/datasets/abliterationai/synthetic-data-provenance-eval",
  "pinned_revision": "b245e9355a681547eccd7119c291b467cae8d33f",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "5",
  "schema": "same 11-column policy schema",
  "construction": "provenance-labelling scenarios",
  "overlap_advbench": "0/5",
  "overlap_harmbench": "0/5",
  "overlap_basis": "full JSONL, 5/5 prompt rows",
  "verdict": "REJECT",
  "flags": "too-small;not-refusal-battery",
  "downloads": 54
 },
 {
  "id": "abliterationai/trust-safety-action-routing",
  "canonical_url": "https://huggingface.co/datasets/abliterationai/trust-safety-action-routing",
  "pinned_revision": "eddbd5cdf2fd71cee0bcecfea87d73ed703a3468",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "5",
  "schema": "same 11-column policy schema",
  "construction": "trust-and-safety routing scenarios",
  "overlap_advbench": "0/5",
  "overlap_harmbench": "0/5",
  "overlap_basis": "full JSONL, 5/5 prompt rows",
  "verdict": "REJECT",
  "flags": "too-small;not-refusal-battery",
  "downloads": 26
 },
 {
  "id": "abliterationaiorg/authorized-cyber-policy-eval",
  "canonical_url": "https://huggingface.co/datasets/abliterationaiorg/authorized-cyber-policy-eval",
  "pinned_revision": "7091a1b5a88e6b9683590f63b6b2e87e94440f3f",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "5",
  "schema": "same 11-column policy schema",
  "construction": "same five scenarios re-uploaded under the second org account",
  "overlap_advbench": "0/5",
  "overlap_harmbench": "0/5",
  "overlap_basis": "full JSONL; byte-identical to abliterationai/authorized-cyber-policy-eval",
  "verdict": "REJECT",
  "flags": "duplicate-of-abliterationai",
  "downloads": 46
 },
 {
  "id": "abliterationaiorg/fictional-clinical-pii-governance",
  "canonical_url": "https://huggingface.co/datasets/abliterationaiorg/fictional-clinical-pii-governance",
  "pinned_revision": "a537c281bd44c2b03e77e83d9a88f897d7bef8ef",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "5",
  "schema": "same",
  "construction": "re-upload under second org account",
  "overlap_advbench": "0/5",
  "overlap_harmbench": "0/5",
  "overlap_basis": "full JSONL; byte-identical to abliterationai/fictional-clinical-pii-governance",
  "verdict": "REJECT",
  "flags": "duplicate-of-abliterationai",
  "downloads": 32
 },
 {
  "id": "abliterationaiorg/governed-ai-actions-bench",
  "canonical_url": "https://huggingface.co/datasets/abliterationaiorg/governed-ai-actions-bench",
  "pinned_revision": "fe7a9fb10c339f17a0cbad1323fb1f6c16cb45ee",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "6",
  "schema": "same",
  "construction": "re-upload under second org account",
  "overlap_advbench": "0/6",
  "overlap_harmbench": "0/6",
  "overlap_basis": "full JSONL; byte-identical to abliterationai/governed-ai-actions-bench",
  "verdict": "REJECT",
  "flags": "duplicate-of-abliterationai",
  "downloads": 30
 },
 {
  "id": "abliterationaiorg/synthetic-data-provenance-eval",
  "canonical_url": "https://huggingface.co/datasets/abliterationaiorg/synthetic-data-provenance-eval",
  "pinned_revision": "c7ce6155246f3cae9b5ba99b572db403dae53a8f",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "5",
  "schema": "same",
  "construction": "re-upload under second org account",
  "overlap_advbench": "0/5",
  "overlap_harmbench": "0/5",
  "overlap_basis": "full JSONL; byte-identical to abliterationai/synthetic-data-provenance-eval",
  "verdict": "REJECT",
  "flags": "duplicate-of-abliterationai",
  "downloads": 38
 },
 {
  "id": "abliterationaiorg/trust-safety-action-routing",
  "canonical_url": "https://huggingface.co/datasets/abliterationaiorg/trust-safety-action-routing",
  "pinned_revision": "8424023a93af922f7590916025e5c4011f1ad662",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "5",
  "schema": "same",
  "construction": "re-upload under second org account",
  "overlap_advbench": "0/5",
  "overlap_harmbench": "0/5",
  "overlap_basis": "full JSONL; byte-identical to abliterationai/trust-safety-action-routing",
  "verdict": "REJECT",
  "flags": "duplicate-of-abliterationai",
  "downloads": 21
 },
 {
  "id": "AlexWortega/capability-vectors",
  "canonical_url": "https://huggingface.co/datasets/AlexWortega/capability-vectors",
  "pinned_revision": "543e636cadf95891491683837a55620a08143413",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "~3,500 rows in 10 configs (v2 60/60 … v9 60/60)",
  "schema": "prompt (chat-templated trace), source, task_id, reward/reason",
  "construction": "card documents: PASS/FAIL trajectories from agent benches (tbench-2, mmlu-pi, claw-eval) on one LoRA base model; rows are full rollout transcripts, not standalone prompts",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "`prompt` holds a rendered multi-turn agent trace, not a standalone instruction",
  "verdict": "REJECT",
  "flags": "model-specific-trajectories",
  "downloads": 88
 },
 {
  "id": "alperiox/arithmetic-abliteration-results",
  "canonical_url": "https://huggingface.co/datasets/alperiox/arithmetic-abliteration-results",
  "pinned_revision": "b883441be983fc1a78336e1f4fcc74d33b413740",
  "license": "none declared",
  "gated_raw": false,
  "gated": false,
  "rows": "0 rows; direction_vectors.json (248 KB) + summary.json",
  "schema": "n/a (JSON of vectors)",
  "construction": "card absent (404); repo holds computed direction vectors only",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — direction vectors",
  "verdict": "REJECT",
  "flags": "no-card;vectors",
  "downloads": 19
 },
 {
  "id": "amugoodbad229/scartissue-tinyaya-abliteration-patches",
  "canonical_url": "https://huggingface.co/datasets/amugoodbad229/scartissue-tinyaya-abliteration-patches",
  "pinned_revision": "524331aa1e66480e073e35225f5dce4156c6cd16",
  "license": "none declared",
  "gated_raw": false,
  "gated": false,
  "rows": "1 row",
  "schema": "model, layer, d_model, budget…, patch_format, arms",
  "construction": "card: a single patch manifest describing weight-space edits",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — patch manifest",
  "verdict": "REJECT",
  "flags": "model-artifacts",
  "downloads": 53
 },
 {
  "id": "amugoodbad229/scartissue-tinyaya-results",
  "canonical_url": "https://huggingface.co/datasets/amugoodbad229/scartissue-tinyaya-results",
  "pinned_revision": "44d804df59aed7beb0af4122d4ae38dfa0485f1e",
  "license": "other",
  "gated_raw": false,
  "gated": false,
  "rows": "safety_generations, judge_verdicts 3,864, capability 4,000, frontier 8, patches 5",
  "schema": "judge, arm, prompt, answer, harm, refusal …",
  "construction": "card: run outputs — generations, judge verdicts and capability scores for a tiny-aya study",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "prompts are run outputs keyed to corpus ids; not a prompt corpus",
  "verdict": "REJECT",
  "flags": "model-outputs-results",
  "downloads": 136
 },
 {
  "id": "amugoodbad229/scartissue-tinyaya-safety-corpus",
  "canonical_url": "https://huggingface.co/datasets/amugoodbad229/scartissue-tinyaya-safety-corpus",
  "pinned_revision": "45501f117d75af4cdba1fcbee92122fa3d39400c",
  "license": "other",
  "gated_raw": false,
  "gated": false,
  "rows": "763 (StrongREJECT 313 + XSTest 450)",
  "schema": "18 cols incl. provenance_chain, source_uri, row_index, label, in_scored_evaluation",
  "construction": "card documents CuratorKIT rebuild, per-row provenance chain and manifest hashes; content is StrongREJECT + XSTest re-exported (StrongREJECT carries 25 AdvBench prompts upstream)",
  "overlap_advbench": "25/763",
  "overlap_harmbench": "0/763",
  "overlap_basis": "full parquet (25 = the AdvBench rows inside StrongREJECT)",
  "verdict": "REJECT",
  "flags": "re-export-strongreject/xstest",
  "downloads": 83
 },
 {
  "id": "arjhinety/small-mind-probe-sets",
  "canonical_url": "https://huggingface.co/datasets/arjhinety/small-mind-probe-sets",
  "pinned_revision": "917f8ef3ad927d8e87c51e0ce91512aa11477ce4",
  "license": "cc-by-4.0",
  "gated_raw": false,
  "gated": false,
  "rows": "51 probes (h22_judgment 24, emotional_range 27)",
  "schema": "probe_id, category, prompt, compliant_shape, good_shape / probe_id, context, emotional_register",
  "construction": "card documents GitHub tag study-001 + sha256 pins; LLM-generated, never executed, no scoring script published",
  "overlap_advbench": "0/51",
  "overlap_harmbench": "0/51",
  "overlap_basis": "full JSONL, both probe sets",
  "verdict": "REJECT",
  "flags": "too-small;UNVERIFIED-scoring",
  "downloads": 16
 },
 {
  "id": "AtomicChat/FLUX-3-Image-Klein-pup-Uncensored-GGUF-metrics",
  "canonical_url": "https://huggingface.co/datasets/AtomicChat/FLUX-3-Image-Klein-pup-Uncensored-GGUF-metrics",
  "pinned_revision": "330fbd59f69990537edf6dc97044ea6db969d942",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "no prompt rows; metric tables",
  "schema": "n/a",
  "construction": "same family: GGUF metric tables",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — metric table",
  "verdict": "REJECT",
  "flags": "results-not-prompts",
  "downloads": 76
 },
 {
  "id": "AtomicChat/FLUX-3-Image-Klein-TE-Uncensored-GGUF-metrics",
  "canonical_url": "https://huggingface.co/datasets/AtomicChat/FLUX-3-Image-Klein-TE-Uncensored-GGUF-metrics",
  "pinned_revision": "268408a5039270020407d1aea8131139706bda29",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "no prompt rows; metric tables",
  "schema": "n/a",
  "construction": "card: benchmark metrics for a GGUF bake-off (refusal sweep / MMLU aggregates)",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — metric table",
  "verdict": "REJECT",
  "flags": "results-not-prompts",
  "downloads": 68
 },
 {
  "id": "AtomicChat/Qwen3.8-Flash-Next-Uncensored-GGUF-metrics",
  "canonical_url": "https://huggingface.co/datasets/AtomicChat/Qwen3.8-Flash-Next-Uncensored-GGUF-metrics",
  "pinned_revision": "a9de1976959d8df97a9a804b2d014a4a02aadfe3",
  "license": "other",
  "gated_raw": false,
  "gated": false,
  "rows": "no prompt rows; datasets-server 501 (no parquet conversion)",
  "schema": "n/a",
  "construction": "card: GGUF bake-off metrics, Qwen licence",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — metric table",
  "verdict": "REJECT",
  "flags": "results-not-prompts",
  "downloads": 494
 },
 {
  "id": "AtomicChat/Ternary-Bonsai-2-27B-Uncensored-LoRA-GGUF-metrics",
  "canonical_url": "https://huggingface.co/datasets/AtomicChat/Ternary-Bonsai-2-27B-Uncensored-LoRA-GGUF-metrics",
  "pinned_revision": "5c1c1c651a3524aecacb196388a29cb564e4b052",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "44 runtime_leak / 65 direction_rows / 6 mmlu / 57 mmlu_by_subject / 38 refusal_sweep",
  "schema": "pack, config, set, n, refusals, refusal_rate_of_valid …",
  "construction": "card: aggregate sweep tables over unnamed internal sets",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — sweep aggregates",
  "verdict": "REJECT",
  "flags": "results-not-prompts",
  "downloads": 126
 },
 {
  "id": "AtomicChat/Ternary-Bonsai-2-2B-Uncensored-LoRA-GGUF-metrics",
  "canonical_url": "https://huggingface.co/datasets/AtomicChat/Ternary-Bonsai-2-2B-Uncensored-LoRA-GGUF-metrics",
  "pinned_revision": "2b18d839db85dd489fdcf05f29593eadbebd7d08",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "6 refusal_sweep / 25 direction_rows / 2 mmlu",
  "schema": "as above",
  "construction": "aggregate sweep tables",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — sweep aggregates",
  "verdict": "REJECT",
  "flags": "results-not-prompts",
  "downloads": 104
 },
 {
  "id": "AtomicChat/Ternary-Bonsai-2-4B-Uncensored-LoRA-GGUF-metrics",
  "canonical_url": "https://huggingface.co/datasets/AtomicChat/Ternary-Bonsai-2-4B-Uncensored-LoRA-GGUF-metrics",
  "pinned_revision": "24bf8519edc87da2e10f6a25359bc70ddccc3fd0",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "6 refusal_sweep / 33 direction_rows / 2 mmlu",
  "schema": "as above",
  "construction": "aggregate sweep tables",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — sweep aggregates",
  "verdict": "REJECT",
  "flags": "results-not-prompts",
  "downloads": 96
 },
 {
  "id": "AtomicChat/Ternary-Bonsai-2-9B-Uncensored-LoRA-GGUF-metrics",
  "canonical_url": "https://huggingface.co/datasets/AtomicChat/Ternary-Bonsai-2-9B-Uncensored-LoRA-GGUF-metrics",
  "pinned_revision": "21030b8d6086335373001bdf9e45389a149cac36",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "6 refusal_sweep / 33 direction_rows / 2 mmlu",
  "schema": "as above",
  "construction": "aggregate sweep tables",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — sweep aggregates",
  "verdict": "REJECT",
  "flags": "results-not-prompts",
  "downloads": 101
 },
 {
  "id": "bedderautomation/refusal-geometry-qwen25-3b",
  "canonical_url": "https://huggingface.co/datasets/bedderautomation/refusal-geometry-qwen25-3b",
  "pinned_revision": "cecdd6a9f18310343a8dc3903a8e9e16a7e3509d",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "0 rows; refusal_directions.pt (305 KB), cross_layer_alignment.pt, geometry_results.json",
  "schema": "n/a (.pt tensors)",
  "construction": "card: OBLITERATUS probing of Qwen2.5-3B — per-layer direction vectors and geometry stats over 512+512 internal pairs",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — .pt direction tensors",
  "verdict": "REJECT",
  "flags": "vectors",
  "downloads": 152
 },
 {
  "id": "bedderautomation/the-geometry-of-obedience",
  "canonical_url": "https://huggingface.co/datasets/bedderautomation/the-geometry-of-obedience",
  "pinned_revision": "2cc8abb5917350c53666cecb797b95c48ca704c1",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "0 rows; 6 markdown manuscripts + research notes",
  "schema": "n/a",
  "construction": "essay/manuscript repo; datasets-server returns 500 (nothing to load)",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no rows",
  "verdict": "REJECT",
  "flags": "no-rows",
  "downloads": 170
 },
 {
  "id": "byroneverson/abliterate-refusal",
  "canonical_url": "https://huggingface.co/datasets/byroneverson/abliterate-refusal",
  "pinned_revision": "7f2934827d9359248d8aae1d664ed9698fd592d5",
  "license": "none declared",
  "gated_raw": false,
  "gated": false,
  "rows": "32,331",
  "schema": "prompt, target (bool)",
  "construction": "card credits Sumandora/remove-refusals-with-transformers; no licence declared; half the sample is AdvBench verbatim",
  "overlap_advbench": "25/50",
  "overlap_harmbench": "0/50",
  "overlap_basis": "50-row sample (offset 0 + 16165)",
  "verdict": "REJECT",
  "flags": "no-licence;advbench-derived",
  "downloads": 108
 },
 {
  "id": "CapyStudios/Capy-CrackV2",
  "canonical_url": "https://huggingface.co/datasets/CapyStudios/Capy-CrackV2",
  "pinned_revision": "1477ecd2da9828542ba79fb1b9b86a32fa9f68bc",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "~3,000 claimed; 1.6 MB JSONL",
  "schema": "text (request + justification + generated \"Master Response\")",
  "construction": "card is a marketing narrative; rows bundle a request with a generated answer and placeholder code; no eval units, no provenance",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "one `text` blob per row (request + justification + generated answer); no standalone prompt column",
  "verdict": "REJECT",
  "flags": "unverified-construction;model-output-mixed",
  "downloads": 34
 },
 {
  "id": "chibifire/harmful-prompts-bench",
  "canonical_url": "https://huggingface.co/datasets/chibifire/harmful-prompts-bench",
  "pinned_revision": "579a41537ab6c1f77f20f116b942374590640d65",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "520 (train 416 / test 104)",
  "schema": "text",
  "construction": "card documents: AdvBench via mlabonne/harmful_behaviors @01cead0, dedup on exact text, lexicographic sort, blake2b(text)%5 test split",
  "overlap_advbench": "520/520",
  "overlap_harmbench": "0/520",
  "overlap_basis": "full parquet, train+test",
  "verdict": "REJECT",
  "flags": "advbench-verbatim",
  "downloads": 63
 },
 {
  "id": "darkengross/abliteration-qwen25-7b-safety-audit",
  "canonical_url": "https://huggingface.co/datasets/darkengross/abliteration-qwen25-7b-safety-audit",
  "pinned_revision": "d88e40ebfdc36eca587dc1e7a42d7e947e173b1e",
  "license": "other",
  "gated_raw": false,
  "gated": false,
  "rows": "2,641",
  "schema": "goal, category, technique, sample, prompt, baseline_response, abliterated_response, 20 label columns",
  "construction": "card: per-prompt paired completions from a base and an abliterated Qwen2.5-7B plus a guard-model label block",
  "overlap_advbench": "17/96",
  "overlap_harmbench": "0/96",
  "overlap_basis": "96 rows parsed from an 800 KB range read of a 21 MB JSONL",
  "verdict": "REJECT",
  "flags": "model-outputs;leakage-risk",
  "downloads": 30
 },
 {
  "id": "daspin335/Comfy_Abliteration_Prompt_Generation_Node",
  "canonical_url": "https://huggingface.co/datasets/daspin335/Comfy_Abliteration_Prompt_Generation_Node",
  "pinned_revision": "5cf786a2c395d58fe0140736fb1d9485d77c0ecf",
  "license": "none declared",
  "gated_raw": false,
  "gated": false,
  "rows": "0 rows; 4 code files",
  "schema": "n/a",
  "construction": "ComfyUI custom node source (nodes.py), not a dataset",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no rows — code repo",
  "verdict": "REJECT",
  "flags": "code-not-dataset",
  "downloads": 10
 },
 {
  "id": "DmitryDB/Qwen3.6-35B-A3B-heretic-study",
  "canonical_url": "https://huggingface.co/datasets/DmitryDB/Qwen3.6-35B-A3B-heretic-study",
  "pinned_revision": "b5956886075a609abea3c8a4ab901094a867adde",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "no prompt rows (12 label maps over 234 external queries + imatrix + reports)",
  "schema": "id → label; matrix summaries",
  "construction": "card states explicitly that no prompt or response text is included; queries are AdvBench 104 + ForbiddenQuestions 130 held externally",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column by design",
  "verdict": "REJECT",
  "flags": "no-prompts",
  "downloads": 92
 },
 {
  "id": "ElementMerc/senbonzakura-dataset",
  "canonical_url": "https://huggingface.co/datasets/ElementMerc/senbonzakura-dataset",
  "pinned_revision": "11d90d2ca0fc16b7c61a257c075614c1e2a40e1c",
  "license": "cc-by-nc-4.0",
  "gated_raw": "auto",
  "gated": true,
  "rows": "unknown — bad_ds 20 KB arrow, bad_eval_ds 360 KB, good_ds 326 KB",
  "schema": "inaccessible",
  "construction": "gated (auto); README and /rows both return 401 without an accepted token, so neither card nor rows could be read",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "not a prompt corpus",
  "verdict": "REJECT",
  "flags": "UNVERIFIED:gated-401",
  "downloads": 13
 },
 {
  "id": "farbodghasemlu/bonsai-27b-q1-abliteration-benchmark",
  "canonical_url": "https://huggingface.co/datasets/farbodghasemlu/bonsai-27b-q1-abliteration-benchmark",
  "pinned_revision": "9f0a952c3ca4afac78dff92945c5f5c7516f341e",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "0 rows; lm-eval result JSONs + logs + refusal_eval.py",
  "schema": "n/a",
  "construction": "card: a 1-bit packing benchmark report (100 prompts, results only)",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — result JSON/logs",
  "verdict": "REJECT",
  "flags": "results-not-prompts",
  "downloads": 37
 },
 {
  "id": "Heyjab/Multilingual-Harmless-Harmful",
  "canonical_url": "https://huggingface.co/datasets/Heyjab/Multilingual-Harmless-Harmful",
  "pinned_revision": "67520a76dbfb01df1d677375925196fb500a1fdf",
  "license": "cc-by-sa-4.0",
  "gated_raw": false,
  "gated": false,
  "rows": "416 harmful + 416 harmless × 9 languages",
  "schema": "text, english",
  "construction": "re-upload of heretic-org/Multilingual-Harmless-Harmful minus the japanese config; no method of its own",
  "overlap_advbench": "50/50",
  "overlap_harmbench": "0/50",
  "overlap_basis": "50-row sample (offset 0 + 208), text; identical files to heretic-org/Multilingual-Harmless-Harmful",
  "verdict": "REJECT",
  "flags": "duplicate-of-heretic-org;advbench-derived",
  "downloads": 170
 },
 {
  "id": "hirundo-io/refinement-abliterated-thinking_heretic",
  "canonical_url": "https://huggingface.co/datasets/hirundo-io/refinement-abliterated-thinking_heretic",
  "pinned_revision": "ea4a9995e330c8e0c395a159d2d378a3666eddb8",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "416",
  "schema": "prompt, messages, answer",
  "construction": "card: seeds from mlabonne/harmful_behaviors (AdvBench), answers generated by an abliterated Qwen3-4B; assistant completion is the payload",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "not a prompt corpus",
  "verdict": "REJECT",
  "flags": "model-outputs;advbench-seeds",
  "downloads": 29
 },
 {
  "id": "hirundo-io/refinement-abliterated-thinking_heretic_short_answers",
  "canonical_url": "https://huggingface.co/datasets/hirundo-io/refinement-abliterated-thinking_heretic_short_answers",
  "pinned_revision": "8a7018fd6220ee9bcf983d98c4ad28f1f6262234",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "520",
  "schema": "prompt, answer, messages",
  "construction": "same pipeline, short-answer variant",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "not a prompt corpus",
  "verdict": "REJECT",
  "flags": "model-outputs;advbench-seeds",
  "downloads": 13
 },
 {
  "id": "hirundo-io/refinement-abliterated-vision_heretic__harmful_refusals",
  "canonical_url": "https://huggingface.co/datasets/hirundo-io/refinement-abliterated-vision_heretic__harmful_refusals",
  "pinned_revision": "905d76a55647b0ec054616311b28f08839eaca34",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "520",
  "schema": "prompt, answer, messages",
  "construction": "same pipeline, vision-model answers",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "not a prompt corpus",
  "verdict": "REJECT",
  "flags": "model-outputs;advbench-seeds",
  "downloads": 26
 },
 {
  "id": "hirundo-io/refinement-abliterated-vision_heretic_short_answers",
  "canonical_url": "https://huggingface.co/datasets/hirundo-io/refinement-abliterated-vision_heretic_short_answers",
  "pinned_revision": "21760bc8ab6ab40f9b74700b4ec2a6480c3da906",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "1,974",
  "schema": "prompt, answer, messages",
  "construction": "same pipeline",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "not a prompt corpus",
  "verdict": "REJECT",
  "flags": "model-outputs;advbench-seeds",
  "downloads": 22
 },
 {
  "id": "hirundo-io/refinement-abliterated-vision_heretic_short_answers1",
  "canonical_url": "https://huggingface.co/datasets/hirundo-io/refinement-abliterated-vision_heretic_short_answers1",
  "pinned_revision": "401382792557a955dd4728ac570df34a00747db6",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "450",
  "schema": "prompt, answer, messages",
  "construction": "same pipeline, third variant",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "not a prompt corpus",
  "verdict": "REJECT",
  "flags": "model-outputs;advbench-seeds",
  "downloads": 16
 },
 {
  "id": "idllresearch/UncensoredBench",
  "canonical_url": "https://huggingface.co/datasets/idllresearch/UncensoredBench",
  "pinned_revision": "142b4227f676c386677476aa57661237e33904d0",
  "license": "cc-by-4.0",
  "gated_raw": false,
  "gated": false,
  "rows": "6,650 QA over 50 unique prompts",
  "schema": "LLM, Type, Question, Answer",
  "construction": "card + IMC'26 paper: 50 CatQA prompts answered by 105 uncensored + 28 aligned models; child-abuse items withheld",
  "overlap_advbench": "0/50",
  "overlap_harmbench": "0/50",
  "overlap_basis": "50-row sample, Question column",
  "verdict": "REJECT",
  "flags": "answers-are-model-outputs;prompts-external(catqa)",
  "downloads": 55
 },
 {
  "id": "idllresearch/UncensoredLLMList",
  "canonical_url": "https://huggingface.co/datasets/idllresearch/UncensoredLLMList",
  "pinned_revision": "34e6e48e5e0f1037b4d14e31e91e3faef299a83a",
  "license": "cc-by-4.0",
  "gated_raw": false,
  "gated": false,
  "rows": "22,096",
  "schema": "Identifier, Platform, URL",
  "construction": "card: registry of uncensored model repos; no prompts",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — model registry",
  "verdict": "REJECT",
  "flags": "no-prompts",
  "downloads": 38
 },
 {
  "id": "jhk0317/qwen3.8-27b-refusal-ablation-artifacts",
  "canonical_url": "https://huggingface.co/datasets/jhk0317/qwen3.8-27b-refusal-ablation-artifacts",
  "pinned_revision": "cf37178835f77bb78f6d1518a42182f1c43f9901",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "0 tabular rows; 5 checkpoints, eval/judge/human dirs",
  "schema": "n/a",
  "construction": "run artefacts (checkpoints, judge outputs) for one ablation sweep",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — checkpoints and judge output",
  "verdict": "REJECT",
  "flags": "model-artifacts",
  "downloads": 184
 },
 {
  "id": "lenML/abliterate-refusal-cn",
  "canonical_url": "https://huggingface.co/datasets/lenML/abliterate-refusal-cn",
  "pinned_revision": "31e1a136810bcd550e4a994cd117e8d6ccdff0bd",
  "license": "none declared",
  "gated_raw": false,
  "gated": false,
  "rows": "32,331",
  "schema": "prompt, prompt_cn, is_harmful",
  "construction": "card: local-model translation of byroneverson/abliterate-refusal into Chinese; no licence declared; inherits the AdvBench half",
  "overlap_advbench": "0/50 (prompt_cn); 25/50 (prompt)",
  "overlap_harmbench": "0/50",
  "overlap_basis": "50-row samples, both columns",
  "verdict": "REJECT",
  "flags": "no-licence;advbench-derived",
  "downloads": 36
 },
 {
  "id": "Metin/abliteration_en",
  "canonical_url": "https://huggingface.co/datasets/Metin/abliteration_en",
  "pinned_revision": "6456ffe2a88ed6058872ba50c3995f65fadd1634",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "400 (train 256 / test 144)",
  "schema": "text",
  "construction": "card is frontmatter only (35 bytes, no body): no source, no construction, no split rule",
  "overlap_advbench": "0/400",
  "overlap_harmbench": "0/400",
  "overlap_basis": "full CSV, train+test",
  "verdict": "REJECT",
  "flags": "UNVERIFIED-CONSTRUCTION",
  "downloads": 22
 },
 {
  "id": "Metin/abliteration_tr",
  "canonical_url": "https://huggingface.co/datasets/Metin/abliteration_tr",
  "pinned_revision": "13c0728371288a1e2fe36703a5cc00393d92e962",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "400 (train 256 / test 144) + turkish_instructions.csv",
  "schema": "text",
  "construction": "card is frontmatter only (35 bytes): no body, no method; Turkish sibling of Metin/abliteration_en",
  "overlap_advbench": "0/256",
  "overlap_harmbench": "0/256",
  "overlap_basis": "full CSV, train split",
  "verdict": "REJECT",
  "flags": "UNVERIFIED-CONSTRUCTION",
  "downloads": 47
 },
 {
  "id": "noahrossi/heretic-completions",
  "canonical_url": "https://huggingface.co/datasets/noahrossi/heretic-completions",
  "pinned_revision": "705ea670684d54a764c2725cd95602496ba9bf83",
  "license": "other",
  "gated_raw": false,
  "gated": false,
  "rows": "6,768 (4,064 + 2,704)",
  "schema": "id, source, split, prompt, completion, label (+ reasoning for gpt-oss)",
  "construction": "card: completions from two abliterated models over 9 red-team/over-refusal sources incl. advbench and harmbench",
  "overlap_advbench": "2/50",
  "overlap_harmbench": "3/50",
  "overlap_basis": "50-row sample, gemma-abliterated prompts",
  "verdict": "REJECT",
  "flags": "model-outputs;harmbench-sourced",
  "downloads": 26
 },
 {
  "id": "pandaman007/assistant-axis-abliteration-vectors",
  "canonical_url": "https://huggingface.co/datasets/pandaman007/assistant-axis-abliteration-vectors",
  "pinned_revision": "d4868a95a3545135f24fe9ce2c0d43bb2a2d873d",
  "license": "none declared",
  "gated_raw": false,
  "gated": false,
  "rows": "0 rows; activations/, vectors/, scores/, responses/, plots/",
  "schema": "n/a",
  "construction": "no README (404); directory tree is model-specific activations and vectors for llama-3.1-8b-abliterated",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — activations/vectors",
  "verdict": "REJECT",
  "flags": "vectors;no-card",
  "downloads": 419
 },
 {
  "id": "Quinn67/ShrimpMoss_Chinese_Censorship_Abliteration",
  "canonical_url": "https://huggingface.co/datasets/Quinn67/ShrimpMoss_Chinese_Censorship_Abliteration",
  "pinned_revision": "ba458e94deb0db5e8a5c78071819df4f81d70e72",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "same 20,000 + slices",
  "schema": "same",
  "construction": "byte-identical fork of Nafnlaus (50/50 files same blob oid)",
  "overlap_advbench": "0/125",
  "overlap_harmbench": "0/125",
  "overlap_basis": "full 125-row published slice (china_bad_125); identical files to Nafnlaus/ShrimpMoss_Chinese_Censorship_Abliteration",
  "verdict": "REJECT",
  "flags": "duplicate-mirror",
  "downloads": 258
 },
 {
  "id": "RadicalNotionAI/modelatlas-community",
  "canonical_url": "https://huggingface.co/datasets/RadicalNotionAI/modelatlas-community",
  "pinned_revision": "658e570d970ab492a07220ea2fc0693beac0cc9f",
  "license": "cc-by-4.0",
  "gated_raw": false,
  "gated": false,
  "rows": "0 rows (train split empty)",
  "schema": "model_id, config, techniques, provenance, intervention_map …",
  "construction": "card: model-architecture metadata registry, not prompts",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "zero rows",
  "verdict": "REJECT",
  "flags": "no-rows",
  "downloads": 25
 },
 {
  "id": "RevivifAI/derestriction",
  "canonical_url": "https://huggingface.co/datasets/RevivifAI/derestriction",
  "pinned_revision": "2600f4e7ab6224e61cc77b22a18859b41f3b6372",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "111,367 (restrict 12,867 / derestrict 40,791 / allow 57,709)",
  "schema": "Prompt, Source, Restriction_Category",
  "construction": "card documents assembly from AdvBench, JailbreakBench, Alpaca, MMLU/GSM8K/ARC/MATH/HumanEval and allenai/wildguardmix, with a two-stage harm filter; WildGuardMix is gated under AI2 RUA and is carried into an MIT-licensed repo",
  "overlap_advbench": "25/50 derestrict; 0/50 allow",
  "overlap_harmbench": "0/50",
  "overlap_basis": "50-row samples, derestrict + allow",
  "verdict": "REJECT",
  "flags": "advbench-derived;licence-conflict(wildguardmix)",
  "downloads": 41
 },
 {
  "id": "scarysnake/code-refusal-for-abliteration",
  "canonical_url": "https://huggingface.co/datasets/scarysnake/code-refusal-for-abliteration",
  "pinned_revision": "a9fc258c4b27b900d73da2e425ca7b913da9918d",
  "license": "cc-by-nc-4.0",
  "gated_raw": false,
  "gated": false,
  "rows": "198",
  "schema": "goal, target",
  "construction": "card: AdvBench filtered to programming-specific tasks; harmful_behaviors.csv is 198/198 AdvBench rows verbatim",
  "overlap_advbench": "198/198",
  "overlap_harmbench": "0/198",
  "overlap_basis": "full CSV",
  "verdict": "REJECT",
  "flags": "advbench-verbatim-subset",
  "downloads": 24
 },
 {
  "id": "spinochenza/abliteration-harmful-enriched",
  "canonical_url": "https://huggingface.co/datasets/spinochenza/abliteration-harmful-enriched",
  "pinned_revision": "82a74bc4e366c9f26427be34761076f1cceff8f4",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "7,356",
  "schema": "text",
  "construction": "byte-identical copy of Bahushruth/abliteration-harmful-enriched (4/4 files same blob oid, README included)",
  "overlap_advbench": "520/7356",
  "overlap_harmbench": "0/7356",
  "overlap_basis": "full column, train+test parquet; identical files to Bahushruth/abliteration-harmful-enriched",
  "verdict": "REJECT",
  "flags": "duplicate-mirror",
  "downloads": 36
 },
 {
  "id": "stjibon/engineering-risk-refusal-eval",
  "canonical_url": "https://huggingface.co/datasets/stjibon/engineering-risk-refusal-eval",
  "pinned_revision": "9f988a69c1aa9abddb9b0ae48bfc15f337c5e3a5",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "50 + two result files",
  "schema": "same schema",
  "construction": "byte-identical mirror of koldfrontier (5/5 files same blob oid)",
  "overlap_advbench": "0/50",
  "overlap_harmbench": "0/50",
  "overlap_basis": "full JSONL (all 50 prompts); identical files to koldfrontier/engineering-risk-refusal-eval",
  "verdict": "REJECT",
  "flags": "duplicate-mirror",
  "downloads": 52
 },
 {
  "id": "strangecreator/detailed-vs-vague-pairs-english",
  "canonical_url": "https://huggingface.co/datasets/strangecreator/detailed-vs-vague-pairs-english",
  "pinned_revision": "39a6fb3be593892c607cf399659428298e0c3987",
  "license": "cc-by-4.0",
  "gated_raw": false,
  "gated": false,
  "rows": "700 pairs (600 + 100)",
  "schema": "detailed_text, vague_text, styles, domain, register, contrast_explanation",
  "construction": "card documents 145 domains × 50 vague styles; prose-style pairs, no harm dimension",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "not a prompt corpus",
  "verdict": "REJECT",
  "flags": "not-refusal",
  "downloads": 159
 },
 {
  "id": "tardellirs/weightprint",
  "canonical_url": "https://huggingface.co/datasets/tardellirs/weightprint",
  "pinned_revision": "e120e08b4580717e97a521b44a49cbe85b6f0cd7",
  "license": "apache-2.0",
  "gated_raw": false,
  "gated": false,
  "rows": "120,976 pairs + 155,769 copies",
  "schema": "model_id, parent_id, verdict, tensors_changed …",
  "construction": "card: Hub-wide weight-census tables",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "no prompt column — model census",
  "verdict": "REJECT",
  "flags": "no-prompts",
  "downloads": 103
 },
 {
  "id": "timmaythetoolmann/code-refusal-for-abliteration",
  "canonical_url": "https://huggingface.co/datasets/timmaythetoolmann/code-refusal-for-abliteration",
  "pinned_revision": "09e3ff3edb7d3369fc6281ec8b96be3b728f4751",
  "license": "cc-by-nc-4.0",
  "gated_raw": "auto",
  "gated": true,
  "rows": "198 (unreadable)",
  "schema": "goal, target",
  "construction": "gated (auto); README + CSV sizes match scarysnake/code-refusal-for-abliteration exactly (628 B / 31,831 B)",
  "overlap_advbench": "198/198",
  "overlap_harmbench": "0/198",
  "overlap_basis": "full CSV; identical files to scarysnake/code-refusal-for-abliteration",
  "verdict": "REJECT",
  "flags": "UNVERIFIED:gated-401;duplicate-mirror",
  "downloads": 6
 },
 {
  "id": "wisent-ai/uncensorbench-leaderboard",
  "canonical_url": "https://huggingface.co/datasets/wisent-ai/uncensorbench-leaderboard",
  "pinned_revision": "0eaee36499892ac86cf5ff91c52fb0492dfc681d",
  "license": "mit",
  "gated_raw": false,
  "gated": false,
  "rows": "0 rows",
  "schema": "leaderboard schema (empty)",
  "construction": "card: leaderboard table for an external benchmark; prompts live in the uncensorbench package",
  "overlap_advbench": "n/a",
  "overlap_harmbench": "n/a",
  "overlap_basis": "zero rows",
  "verdict": "REJECT",
  "flags": "no-rows",
  "downloads": 19
 },
 {
  "id": "XuehangCang/unsafe_qa",
  "canonical_url": "https://huggingface.co/datasets/XuehangCang/unsafe_qa",
  "pinned_revision": "53e0cbb1068b94912e6a0889261029e587f63dfe",
  "license": "agpl-3.0",
  "gated_raw": false,
  "gated": false,
  "rows": "800",
  "schema": "有害问题, 正确思考, 正确回答, 错误思考, 错误回答",
  "construction": "card names only an unnamed `unsafe_prompt` source for the 800 bilingual questions, then two models' CoT + answers; no upstream id, no filter rule",
  "overlap_advbench": "26/50",
  "overlap_harmbench": "0/50",
  "overlap_basis": "50-row sample (offset 0 + 700)",
  "verdict": "REJECT",
  "flags": "UNVERIFIED-CONSTRUCTION;model-output-mixed",
  "downloads": 35
 }
]
```

## Candidates worth adding

Ranked by how much they widen the behaviour space per unit of leakage risk. Sizes are rows, overlap is exact-normalised measured against AdvBench (520) and HarmBench text (400).

### 1. `treadon/abliteration-eval` — 333 rows, 0/200 AdvBench, 0/200 HarmBench
200 harmful prompts in a 20-category × 10 grid plus 83 benign over-refusal prompts across 10 trigger-word types, and a 50-row multilingual split (ES/FR/DE/HI/JA) that ships as its own parquet but is missing from both the card's `dataset_info` and the `/rows` split list. Every split measured at exact-zero against both references — the only set here whose harmful arm is both this large and completely clear of the two existing batteries. What it adds: 200 disjoint behaviours, a matched benign arm, and a second language axis in one repo. **Risk:** the card documents composition but never states how the prompts were produced — `UNVERIFIED-CONSTRUCTION` until the author's blog trail is read; exact-match zero does not exclude semantic paraphrase of AdvBench items, so run the study's 0.8 semantic screen before pooling.

### 2. `koldfrontier/engineering-risk-refusal-eval` — 50 rows, 0/50, 0/50
Reverse-engineering, pen-testing, AV/EDR evasion and malware-triage prompts, 18 of them forming 11 authorised/unauthorised pairs around the same technical ask. This is the only set in the sweep that measures *judgement* rather than keyword reaction, and the behaviour space (licence bypass, unpacking, dongle patching, C2 persistence) is absent from both AdvBench and HarmBench. **Risk:** single author, n=50, one row documented as defective and deliberately retained; treat the pair-discrimination metric as the endpoint, not a raw refusal rate.

### 3. `zaakirio/infosec_harmful_behaviors` — 520 rows, 0/520, 0/520
400 train / 120 test offensive-security instructions, built as the harmful pole of a matched pair with `zaakirio/coding_harmless_prompts` (0/120 overlap, also clean). Adds an infosec domain at a size that actually moves an estimate. **Risk:** provenance is a single line — "generated from `data/infosec_harmful.txt`" in a tree that is not linked from the card — so the construction is thin; the rows look model-authored with no dedup statement.

### 4. `Nafnlaus/ShrimpMoss_Chinese_Censorship_Abliteration` — 10,000 bad + 10,000 good (7 slice sizes), 0/125, 0/125
Chinese-government censorship and propaganda prompts in English, Mandarin and Cantonese, paired with a topically matched "good" set. The refusal axis it probes is a political-censorship axis, not a harm axis, which is exactly why it does not collide with either battery. **Risk:** prompts were generated on Mistral NeMo; only the 125-row slice was verified (the 10k files were not pulled); the repo ships `.harmbench.csv` and `.strongreject.csv` renderings that are format conversions, not those benchmarks, and a careless loader could mistake one for the other. `Quinn67/…` is a byte-identical fork — cite Nafnlaus only.

### 5. `GoldfingerCH/qwen38-27B-abliterated-refusal-eval-fr` — 626 rows, 0/626, 0/626
French translations of the user turns from `Guilherme34/uncensor`, with the assistant text removed and a `prompt_sha256` per row. Full-set zero against both references. What it adds is language variance, not behaviour variance — the underlying asks are the same English set — so it belongs in a cross-lingual arm, not in the pooled English denominator. **Risk:** machine translation (translate-only pass), Qwen3Guard labels rather than human labels, and the upstream `uncensor` provenance is one hop deep.

### 6. `treadon/disinhibition-eval` — 248 rows, 0/50, 0/50 (opinions split sampled)
120 contentious questions plus 42 factual, 25 explicit-neutral, 28 coherence and 33 edge-case controls. Not a harmful battery and should never be counted as one: it measures hedging versus commitment. It is the cleanest available null-control for the study's actual question — whether the edit removed caution or removed judgement — and its `explicit_neutral` split tests whether the ablation overruns an explicit user instruction. **Risk:** different construct, author-built, provenance unstated; only the opinions split was sampled.

**What pooling buys.** The 313-row HarmBench test gives a paired difference (McNemar) standard error of roughly `sqrt(p_d/313)`; at a 10% discordance rate that is ±3.5 points at 95%, so 0.5 points is not resolvable by any amount of care, only by n. Adding candidates 1–3 (+770 English harmful behaviours) takes the same statistic to ±2.2 points. Reaching ±0.5 needs on the order of 15,000 paired prompts at that discordance rate, which no dataset in this sweep supplies — the fix is a paired per-prompt design and a stratified subset, not a bigger pile.

## Rejected wholesale

**No prompt content — results, vectors, checkpoints, code, essays (20)**
- `AtomicChat/FLUX-3-Image-Klein-TE-Uncensored-GGUF-metrics`, `…-pup-…`, `AtomicChat/Qwen3.8-Flash-Next-Uncensored-GGUF-metrics`, `AtomicChat/Ternary-Bonsai-2-{2B,4B,9B,27B}-Uncensored-LoRA-GGUF-metrics` — aggregate refusal-sweep and MMLU tables over unnamed internal sets; no prompts to evaluate.
- `alperiox/arithmetic-abliteration-results` — `direction_vectors.json` only, no card.
- `amugoodbad229/scartissue-tinyaya-abliteration-patches` — one-row patch manifest describing weight edits.
- `bedderautomation/refusal-geometry-qwen25-3b` — `refusal_directions.pt` and layer-geometry JSON for Qwen2.5-3B.
- `bedderautomation/the-geometry-of-obedience` — six markdown manuscripts; nothing to load.
- `pandaman007/assistant-axis-abliteration-vectors` — activations, vectors and scores for one abliterated Llama; no README at all.
- `jhk0317/qwen3.8-27b-refusal-ablation-artifacts` — five checkpoints plus judge output directories.
- `daspin335/Comfy_Abliteration_Prompt_Generation_Node` — a ComfyUI node, `nodes.py`, not a dataset.
- `farbodghasemlu/bonsai-27b-q1-abliteration-benchmark` — lm-eval JSON and logs from a 100-prompt 1-bit packing test.
- `RadicalNotionAI/modelatlas-community` — zero rows; model-architecture registry schema.
- `tardellirs/weightprint` — Hub-wide weight census, 276k model rows, no prompts.
- `idllresearch/UncensoredLLMList` — 22,096 model registry rows.
- `wisent-ai/uncensorbench-leaderboard` — zero rows; the leaderboard table for an external benchmark.
- `DmitryDB/Qwen3.6-35B-A3B-heretic-study` — id→label maps over 234 external queries; the card states no prompt text is included.
- `AlexWortega/capability-vectors` — chat-templated agent rollout transcripts for one base model, not standalone refusal prompts.

**Duplicates, mirrors and forks (8)**
- `2etatg/abliteration-eval` — 5/5 files identical to `treadon/abliteration-eval`, README included.
- `Quinn67/ShrimpMoss_Chinese_Censorship_Abliteration` — 50/50 files identical to the Nafnlaus repo.
- `stjibon/engineering-risk-refusal-eval` — 5/5 files identical to `koldfrontier/…`.
- `spinochenza/abliteration-harmful-enriched` — 4/4 files identical to `Bahushruth/…`.
- `timmaythetoolmann/code-refusal-for-abliteration` — gated fork; README and CSV byte sizes match `scarysnake/…` exactly.
- `Heyjab/Multilingual-Harmless-Harmful` — re-upload of the heretic-org set minus the Japanese config; the harmful pole inherits the same AdvBench prompts.
- `abliterationaiorg/{authorized-cyber-policy-eval, fictional-clinical-pii-governance, governed-ai-actions-bench, synthetic-data-provenance-eval, trust-safety-action-routing}` — the five `abliterationai/*` repos re-uploaded under a second org account, 5–6 rows each.

**Prompt sets that duplicate AdvBench or HarmBench (6)**
- `chibifire/harmful-prompts-bench` — 520/520 rows are AdvBench verbatim; it is a documented, well-built AdvBench loader and could replace the existing 520 source, but it adds nothing to an evaluation set.
- `scarysnake/code-refusal-for-abliteration` — 198 AdvBench rows filtered to programming tasks, 198/198 exact.
- `byroneverson/abliterate-refusal` — 32,331 rows, 25/50 sampled AdvBench, and no licence declared anywhere on the card.
- `lenML/abliterate-refusal-cn` — Chinese translation of the above, 25/50 of its English column is AdvBench, no licence declared.
- `hirundo-io/refinement-abliterated-*` (5 repos) — seeds from `mlabonne/harmful_behaviors` (AdvBench) with abliterated-model completions as the payload; the completion is the row, not the prompt.
- `noahrossi/heretic-completions` — completions over nine sources including `advbench` and `harmbench`; 2/50 and 3/50 sampled, i.e. the prompts are recycled from the very sets we are trying to grow away from.

**Model output rather than prompts (4)**
- `XuehangCang/unsafe_qa` — 800 bilingual questions each paired with two models' chain-of-thought and answers; the `unsafe_prompt` upstream is unnamed, so construction is unverifiable even though 26/50 sample rows are AdvBench.
- `amugoodbad229/scartissue-tinyaya-results` — generations, 3,864 judge verdicts and capability scores.
- `CapyStudios/Capy-CrackV2` — one `text` blob per row holding request, justification and a generated "Master Response" with placeholder code; an SFT augmentation set with no eval units and no provenance beyond a marketing narrative.
- `darkengross/abliteration-qwen25-7b-safety-audit` — 2,641 rows of paired base/abliterated completions with guard-model labels; 17/96 sampled rows are AdvBench, and the completions make it a leakage hazard rather than a clean prompt set.

**Too small, wrong construct, or unverifiable (11)**
- `arjhinety/small-mind-probe-sets` — 51 LLM-generated probes, never run, no scoring script published; cannot move a 0.5-point estimate.
- `strangecreator/detailed-vs-vague-pairs-english` — 700 prose-style pairs, 145 domains, no harm dimension at all.
- `idllresearch/UncensoredBench` — 6,650 QA pairs over 50 CatQA prompts; the prompts are CatQA's and the value is the 133 models' answers.
- `amugoodbad229/scartissue-tinyaya-safety-corpus` — meticulous row-level provenance for a re-export of StrongREJECT (313) + XSTest (450); 25/763 rows are AdvBench, which is exactly StrongREJECT's known AdvBench content, and neither source is new.
- `RevivifAI/derestriction` — 111,367 prompts, 25/50 sampled AdvBench in `derestrict`; also carries gated `allenai/wildguardmix` content into an MIT repo.
- `Bahushruth/abliteration-harmful-enriched` and `hirundo-io/abliteration-harmful-enriched-categorized` — usable as a direction-fitting harmful pole (see USABLE-DERIVE), not as eval: 520/7,356 rows are AdvBench verbatim and the rest are LLM-generated.
- `ElementMerc/senbonzakura-dataset` — gated; README and rows both 401. `UNVERIFIED`, not rejected on merit.
- `Metin/abliteration_en`, `Metin/abliteration_tr` — cards are frontmatter only (35 bytes). Overlap is clean (0/400, 0/256), but with no stated source or split rule they are `UNVERIFIED-CONSTRUCTION`.

## Addendum — semantic re-audit of `Bahushruth/abliteration-harmful-enriched` (2026-11-07)

The verdict `REJECT` in the table above was based on exact-normalised overlap alone (520/7,356 rows
matching AdvBench). That was too blunt: exact matching cannot distinguish a copy from a paraphrase farm,
and it cannot distinguish either from genuinely new behaviours. Re-audited with embeddings.

- Revision: `f29c0b778d3412d5cc7acfc9c6463ce13886212c`, apache-2.0, ungated, `text` column only.
- Rows: 7,356 (train 5,884 / test 1,472). Unique exact-normalised: **7,323** — 33 internal duplicates.
- Semantic distance to AdvBench, 300-row test sample, all-MiniLM-L6-v2 cosine:
  median **0.452**, p90 **0.576**, fraction ≥ 0.80 **0.0%**, ≥ 0.90 **0.0%**.
- Semantic distance to HarmBench test: median **0.377**, p90 **0.482**, fraction ≥ 0.80 **0.0%**.
- Domain terms (share of unique rows): drugs 10.5%, finance 10.2%, cyber 10.2%, weapons 6.1%,
  violence 5.8%, bio 2.1%.
- Framing: **14.7%** of rows carry a roleplay or research wrapper ("in my novel", "screenplay",
  "research paper", "hypothetical"). That is a style shift to declare, not a disqualifier.
- Length: median 131 chars, max 275.

**Revised verdict: `USABLE-EVAL` with conditions.** It is not AdvBench-derived beyond the 520 exact
matches, and it supplies roughly 6,800 new English behaviours. Conditions: (1) drop the 520 AdvBench
matches by exact hash; (2) mark `UNVERIFIED-CONSTRUCTION` — the card documents no method; (3) report the
roleplay-framed 14.7% as its own slice, since framing changes refusal rates; (4) do not let its row count
dominate a pooled rate — report it as a pre-registered arm, weighted by corpus rather than by row.
