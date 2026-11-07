# Harmful-behaviour / refusal-elicitation batteries

Inventory for the registered study *"can a weight-space edit remove the refusal direction"*. Role tags used below:

- **PRIMARY** — the main safety battery (pre-registered primary endpoint).
- **HELDOUT** — categories or sets reserved from any direction-fitting / probe-training step.
- **PROBE** — supplies matched harmful/harmless pairs for the linear probe and the null-control.
- **CAPCOST** — measures the declared capability cost, not refusal behaviour.
- **JUDGE** — scoring component, not a prompt set.

Revision column: 40-hex commit sha, resolved 2026-11-07. GitHub pins are `HEAD` of the default branch as reported by `git ls-remote https://github.com/<owner>/<repo> HEAD` (identical to `GET /repos/<owner>/<repo>/commits?per_page=1` where the REST API was not rate-limited). HF pins are the `sha` field of `GET https://huggingface.co/api/datasets/<id>`.

| dataset | canonical_url | id | host | pinned_revision | size | license | gated | category_coverage | role | retrieved_at |
|---|---|---|---|---|---|---|---|---|---|---|
| HarmBench (behaviours + eval code) | https://github.com/centerforaisafety/HarmBench | centerforaisafety/HarmBench | GitHub | 8e1604d1171fe8a48d8febecd22f600e462bdcdd | 510 behaviours = 200 standard + 100 copyright + 100 contextual + 110 multimodal. Text-only 400: official split val 80 / test 320 (`harmbench_behaviors_text_val.csv` / `_test.csv`); full split incl. multimodal val 100 / test 410 | MIT | false | 4 functional: standard 200 / copyright 100 / contextual 100 / multimodal 110. 7 semantic labels in the text CSV, with exact counts: copyright 100; cybercrime_intrusion 67; illegal 65; misinformation_disinformation 65; chemical_biological 56; harassment_bullying 25; harmful 22 (paper names them Cybercrime & Unauthorized Intrusion, Chemical & Biological Weapons/Drugs, Copyright Violations, Misinformation & Disinformation, Harassment & Bullying, Illegal Activities, General Harm) | PRIMARY battery + JUDGE harness; test split = HELDOUT | 2026-11-07 |
| HarmBench text-only mirror | https://huggingface.co/datasets/walledai/HarmBench | walledai/HarmBench | HuggingFace datasets | fb6c2afd5a2a943d701d6db3efab87d077e81be5 | 400 rows: standard 200 / contextual 100 / copyright 100 (multimodal 110 absent) | MIT | true (`auto`) | same 7 semantic categories; columns `prompt`, `category` (standard/contextual), `tags` (copyright) | PRIMARY (loader path when GitHub raw is unavailable); multimodal subset must come from the GitHub repo | 2026-11-07 |
| HarmBench classifier | https://huggingface.co/cais/HarmBench-Llama-2-13b-cls | cais/HarmBench-Llama-2-13b-cls | HuggingFace models | bda705349d1144fa618770bea64d99ce54e3835b | 13B-parameter fine-tuned Llama-2 checkpoint (safetensors); no prompt rows | MIT | false | binary harmful/safe classifier over (behaviour, completion) pairs; 4 functional categories used at eval time | JUDGE — ASR scoring for HarmBench-style completions | 2026-11-07 |
| AdvBench | https://github.com/llm-attacks/llm-attacks/tree/main/data/advbench | llm-attacks/llm-attacks | GitHub | 098262edf85f807224e70ecd87b9d83716bf6b73 | 520 harmful behaviours (`harmful_behaviors.csv`) + 574 harmful strings (`harmful_strings.csv`) | MIT | false | flat list, no published taxonomy; the 520 behaviours are the de-facto "harmful instruction" baseline and a subset source for HarmBench standard / JBB / SALAD | PRIMARY baseline + PROBE negatives source | 2026-11-07 |
| AdvBench (HF mirror) | https://huggingface.co/datasets/walledai/AdvBench | walledai/AdvBench | HuggingFace datasets | 9d4730540082fa4017450b65ca1c0e1d8d30446e | 520 rows, columns `prompt`/`target` | MIT | true (`auto`) | flat; no category column | loader path for the 520-behaviour set | 2026-11-07 |
| JailbreakBench JBB-Behaviors | https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors | JailbreakBench/JBB-Behaviors | HuggingFace datasets | 886acc352a31533ffbcf4ef22c744658688086fc | 100 harmful + 100 benign (thematically matched) + 300-row judge-comparison config | MIT | false | 10 OpenAI-policy categories × 10 harmful each: Harassment/Discrimination; Malware/Hacking; Physical harm; Economic harm; Fraud/Deception; Disinformation; Sexual/Adult content; Privacy; Expert advice; Government decision-making | HELDOUT behaviours + benign set for the over-refusal / null-control arm | 2026-11-07 |
| JailbreakBench (code + artifacts) | https://github.com/JailbreakBench/jailbreakbench | JailbreakBench/jailbreakbench | GitHub | 23dbdf6b19650521604456229bc1d9c4156c85c1 | package + loaders; jailbreak strings live in the sibling `JailbreakBench/artifacts` repo | MIT | false | n/a (code) | reproducibility of the JBB leaderboard protocol and its refusal/jailbreak judges | 2026-11-07 |
| StrongREJECT | https://github.com/alexandrasouly/strongreject | alexandrasouly/strongreject | GitHub | f7cad6c17e624e21d8df2278e918ae1dddb4cb56 | 313 forbidden prompts (`strongreject_dataset.csv`) + 60-prompt small subset | MIT for code and custom data; upstream-sourced prompts keep their original licences (AdvBench MIT; DAN MIT; MaliciousInstruct, HarmfulQ, OpenAI system card: no licence) | false | 6 categories with exact counts: Non-violent crimes 59; Violence 54; Disinformation and deception 50; Hate, harassment and discrimination 50; Illegal goods and services 50; Sexual content 50. Sources: custom 221; DAN 35; AdvBench 25; MaliciousInstruct 12; HarmfulQ 11; MasterKey 3; Jailbreaking via Prompt Engineering 3; OpenAI System Card 3 | HELDOUT prompts + graded (0–1) ASR rubric that separates "refused" from "empty jailbreak" | 2026-11-07 |
| StrongREJECT (maintained fork) | https://github.com/dsbowen/strong_reject | dsbowen/strong_reject | GitHub | 7a551d5b440ec7b75d4f6f5bb7c1719965b76b47 | package + paper-replication artefacts; ships the fine-tuned Gemma-2B autograder | MIT | false | same 6 categories | JUDGE — local, offline grader (no OpenAI dependency at scoring time) | 2026-11-07 |
| StrongREJECT (HF mirror) | https://huggingface.co/datasets/walledai/StrongREJECT | walledai/StrongREJECT | HuggingFace datasets | df54272b395ce9e584d2f8140519935425d8549f | 313 rows, columns `prompt`/`category`/`source` | MIT | true (`auto`) | same 6 categories | loader path only | 2026-11-07 |
| SALAD-Bench (Salad-Data) | https://huggingface.co/datasets/OpenSafetyLab/Salad-Data | OpenSafetyLab/Salad-Data | HuggingFace datasets | d21a325e276a99bd69b1fbb8aa51a9f249486b72 | 21,318 base questions + 5,000 attack-enhanced + 300 small attack subset + 200 defense-enhanced + 3,840 MCQ | Apache-2.0 | false | 6 domains: O1 Representation & Toxicity; O2 Misinformation Harms; O3 Socioeconomic Harms; O4 Information & Safety; O5 Malicious Use; O6 Human Autonomy & Integrity — 16 tasks, 65 categories, ≥200 questions per category. Base-set provenance: Finetuned-GPT-3.5 self-instruct 15,433; HH-harmless 4,184; HH-red-team 659; AdvBench 359; Multilingual 230; Do-Not-Answer 189; ToxicChat 129; DAN 93; GPTFuzzer 42 | PRIMARY breadth battery; whole domains (e.g. O3, O4) reserved as HELDOUT | 2026-11-07 |
| SALAD-Bench (code, MD-Judge/MC-Judge) | https://github.com/OpenSafetyLab/SALAD-BENCH | OpenSafetyLab/SALAD-BENCH | GitHub | 575d5369c5355c0ed76e27860a889aa2f3c3e0e5 | eval code + taxonomy; judges are HF models (`OpenSafetyLab/MD-Judge-v0_2-internlm2_7b`) | Apache-2.0 | false | 6/16/65 hierarchy implemented as `1-category`/`2-category`/`3-category` labels | JUDGE + taxonomy reference for domain-level held-out splits | 2026-11-07 |
| HEx-PHI | https://huggingface.co/datasets/LLM-Tuning-Safety/HEx-PHI | LLM-Tuning-Safety/HEx-PHI | HuggingFace datasets | 83128b46334b80cc567bd7a2caf7af11c5b0bab7 | 330 prompts = 11 categories × 30 | custom "hex-phi" agreement (`license: other`), gated behind manual review | true (`auto` + manual approval, affiliation required) | 11 categories: Illegal Activity; Child Abuse Content; Hate/Harass/Violence; Malware; Physical Harm; Economic Harm; Fraud/Deception; Adult Content; Political Campaigning; Privacy Violation; Tailored Financial Advice | PROBE — 30-per-category granularity is the cleanest basis for per-category refusal-probability deltas and for a leave-one-category-out held-out split | 2026-11-07 |
| Do-Not-Answer | https://huggingface.co/datasets/LibrAI/do-not-answer | LibrAI/do-not-answer | HuggingFace datasets | 74e74f2e4507ef256fe536f78a776f4a1ff67955 | 939 instructions | `apache-2.0` in the card frontmatter, but card body states data is CC BY-NC-SA 4.0 and only source files are Apache-2.0 — treat as non-commercial | false | 3-level taxonomy: 5 risk areas → 12 harm types → 61 specific harms (columns `risk_area`, `types_of_harm`, `specific_harms`) | PROBE — low-severity, "should refuse but harmless-adjacent" prompts; the natural stress test for over-refusal after an edit | 2026-11-07 |
| Do-Not-Answer (code) | https://github.com/Libr-AI/do-not-answer | Libr-AI/do-not-answer | GitHub | 460703484df354958a5e1cd7378a38fcb94a2f3e | taxonomy figures + Longformer evaluator (600M) | Apache-2.0 (code) | false | same 5/12/61 hierarchy | JUDGE alternative (cheap refusal/harm classifier) and taxonomy source | 2026-11-07 |
| BeaverTails | https://huggingface.co/datasets/PKU-Alignment/BeaverTails | PKU-Alignment/BeaverTails | HuggingFace datasets | 8401fe609d288129cc684a9b3be6a93e41cfe678 | 333,963 human-labelled QA pairs (330k: 300,567 train / 33,396 test; 30k: 27,186 train / 3,021 test) | CC BY-NC 4.0 | false | 14 harm categories (multi-label): Animal Abuse; Child Abuse; Controversial Topics, Politics; Discrimination, Stereotype, Injustice; Drug Abuse, Weapons, Banned Substance; Financial Crime, Property Crime, Theft; Hate Speech, Offensive Language; Misinformation Regarding ethics, laws, and safety; Non-Violent Unethical Behavior; Privacy Violation; Self-Harm; Sexually Explicit, Adult Content; Shocking, Gruesome Content; Terrorism, Organized Crime | PROBE supply (label noise is real — multi-label, human-annotated) + benign arm from `is_safe=True`; the 3,021-row test split is the practical held-out pool | 2026-11-07 |
| SORRY-Bench | https://huggingface.co/datasets/sorry-bench/sorry-bench-202406 | sorry-bench/sorry-bench-202406 | HuggingFace datasets | b34822276edde97592eda99c0b56d306f8830469 | 450 class-balanced unsafe instructions across 45 fine-grained topics (10 per topic); ~9K additional prompts from 20 linguistic mutations; multilingual release | custom "sorry-bench" licence (`license: other`, `LICENSE` in repo) | true (`auto`, form: name, affiliation, email, country, purpose) | 45 fine-grained unsafe topics (finer than the 10-category policy taxonomies; 10 instructions each). Superseded by `sorry-bench/sorry-bench-202503` (sha `612a4e1f45db…`, same gating) | HELDOUT — fine-grained topic balance is the best available control for "did the edit just move a coarse category boundary" | 2026-11-07 |
| AIR-Bench 2024 | https://huggingface.co/datasets/stanford-crfm/air-bench-2024 | stanford-crfm/air-bench-2024 | HuggingFace datasets | 976d9fbb0f52bce704dcbef5bd7a2652e65f2a21 | 5,694 prompts (`default`); regional configs us 3,921 / china 4,416 / eu_comprehensive 4,134 / eu_mandatory 3,402; 314 judge prompts | CC BY 4.0 | false | 4-tier regulation-grounded taxonomy: 45 medium-level categories → 314 granular risks (columns `cate-idx`, `l2-name`, `l3-name`, `l4-name`). Prompts-per-granular-category counts not published as a table (~18 avg) | HELDOUT — regulation coverage independent of the OpenAI-policy taxonomies that HarmBench/JBB/SALAD partly share | 2026-11-07 |
| AILuminate v1.0 (public demo) | https://github.com/mlcommons/ailuminate | mlcommons/ailuminate | GitHub | 769cc2be9d20c8d4fb26ce53b68865ed41dfb8e2 | 1,200 demo prompts = 10% sample of the 12,000 Public Practice set (full suite 24,000: 12k practice + 12k private) | CC BY 4.0 (data); Apache-2.0 (repo) | false for the demo; full practice/private sets are MLCommons-member-only via request form | 12 hazard categories (14 hazard codes): vcr, src, cse, ssh, iwp (physical) / ipv, dfm, ncr, hte, prv (non-physical) / spc_ele, spc_fin, spc_hlt, sxc_prn (contextual). Fields: Hazard, Persona (normal/unskilled/skilled), Locale | HELDOUT — hazard-balanced grading scale and persona stratification are absent from every other set here | 2026-11-07 |
| WMDP | https://huggingface.co/datasets/cais/wmdp | cais/wmdp | HuggingFace datasets | 7125571f22f032c56415e7980f48d877dd830ff8 | 3,668 MCQ: wmdp-bio 1,273 / wmdp-cyber 1,987 / wmdp-chem 408 | MIT | false | 3 domains only (bio, cyber, chem); 4-choice MCQ, not refusal elicitation | CAPCOST — hazardous-knowledge proxy, the standard cost term in the abliteration / unlearning literature | 2026-11-07 |
| WMDP forget corpora | https://huggingface.co/datasets/cais/wmdp-bio-forget-corpus | cais/wmdp-bio-forget-corpus (also `cais/wmdp-cyber-forget-corpus`) | HuggingFace datasets | 5a786ed1041e56fef2d4ed26c1239f12b73a68eb (cyber: 774cdc4063f21aa0ce8c2aa23c71521c740fd054) | bio corpus: WikiText-style hazardous-text corpus; cyber corpus: same construction | MIT (inherits `cais/wmdp`) | true (`auto`) | domain text only, no labels | CAPCOST support — unlearning-baseline comparator (RMU) that a refusal-direction edit must not be conflated with | 2026-11-07 |
| CyberSecEval (v1 insecure-code) | https://huggingface.co/datasets/walledai/CyberSecEval | walledai/CyberSecEval | HuggingFace datasets | 62dba0bb39c450c375aff453d3396fa8f2338eee | 1,916 cases per config × 2 configs (`autocomplete`, `instruct`); per language: python 351, php 162, javascript 249, rust 204, java 229, cpp 259, c 227, csharp 235 | MIT | false | 8 languages × CWE classes (`cwe_identifier`, `pattern_id`, `rule`, `variant`) — insecure-code generation, not refusal prompts | domain-specific harmful-capability battery (cyber); CAPCOST-adjacent, used as a secondary held-out domain | 2026-11-07 |
| CyberSecEval 2 (PurpleLlama suite) | https://github.com/meta-llama/PurpleLlama/tree/775c64a88c42896611ae224b46b9b5c6baf8b89a/CybersecurityBenchmarks | meta-llama/PurpleLlama | GitHub | 775c64a88c42896611ae224b46b9b5c6baf8b89a (v2-era pin; repo HEAD `f64eebd53003a87d9c2d2a3a712133534c214c8d` is CyberSecEval 4 and has moved the layout) | component files at the pin: `mitre/mitre_benchmark_100_per_category_with_augmentation.json` 4.49 MB (100 prompts per MITRE category, filename states the count); `mitre/mitre_prompts_multilingual_machine_translated.json` 5.72 MB; `frr/frr.json` 420 KB; `frr/frr_multilingual_machine_translated.json` 1.12 MB; `prompt_injection/prompt_injection.json` 193 KB; `prompt_injection/prompt_injection_multilingual_machine_translated.json` 1.04 MB; `interpreter/interpreter.json` 388 KB; `spear_phishing/multiturn_phishing_challenges.json` 1.95 MB; `autocomplete/autocomplete.json` 3.42 MB; `instruct/instruct.json` 3.36 MB | MIT (evals/benchmarks); Llama models under the Llama Community licence | false | 15 prompt-injection attack categories; MITRE ATT&CK tactic/technique grid at 100 prompts per category; interpreter-abuse, spear-phishing and exploitation-capability task families | HELDOUT cyber domain, and the only source here for explicit false-refusal (over-refusal) scoring | 2026-11-07 |
| Tulu-3 HarmBench eval split | https://huggingface.co/datasets/allenai/tulu-3-harmbench-eval | allenai/tulu-3-harmbench-eval | HuggingFace datasets | c8f90e1bf8849be43402450355fcd6bceed60e51 | 320 rows (`test`) — byte-for-byte the HarmBench text test split (`harmbench_behaviors_text_test.csv`): standard 159 / copyright 80 / contextual 81, columns Behavior / FunctionalCategory / SemanticCategory / Tags / ContextString / BehaviorID | ODC-BY | false | same 7 snake_case semantic labels as HarmBench: `illegal`, `misinformation_disinformation`, `cybercrime_intrusion`, `chemical_biological`, `harassment_bullying`, `harmful`, `copyright` | PRIMARY execution path — HF-native HarmBench subset already wired into `allenai/safety-eval`; use for the exact ASR number the comparison papers (Abliteration, Heretic, Obliteratus) report | 2026-11-07 |

```json
[
  {
    "dataset": "HarmBench",
    "canonical_url": "https://github.com/centerforaisafety/HarmBench",
    "id": "centerforaisafety/HarmBench",
    "host": "GitHub",
    "pinned_revision": "8e1604d1171fe8a48d8febecd22f600e462bdcdd",
    "size": {
      "items": 510,
      "functional_breakdown": {
        "standard": 200,
        "copyright": 100,
        "contextual": 100,
        "multimodal": 110
      },
      "text_only": 400,
      "split": {
        "val": 80,
        "test": 320
      },
      "split_incl_multimodal": {
        "val": 100,
        "test": 410
      }
    },
    "license": "MIT",
    "gated": false,
    "category_coverage": {
      "functional": {
        "standard": 200,
        "copyright": 100,
        "contextual": 100,
        "multimodal": 110
      },
      "semantic_text_set": {
        "copyright": 100,
        "cybercrime_intrusion": 67,
        "illegal": 65,
        "misinformation_disinformation": 65,
        "chemical_biological": 56,
        "harassment_bullying": 25,
        "harmful": 22
      },
      "paper_names": [
        "Cybercrime & Unauthorized Intrusion",
        "Chemical & Biological Weapons/Drugs",
        "Copyright Violations",
        "Misinformation & Disinformation",
        "Harassment & Bullying",
        "Illegal Activities",
        "General Harm"
      ],
      "counts_method": "counted from harmbench_behaviors_text_all.csv at the pinned revision",
      "per_category_counts_published": true
    },
    "role": [
      "PRIMARY",
      "JUDGE_HARNESS",
      "HELDOUT_test_split"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "HarmBench text-only mirror",
    "canonical_url": "https://huggingface.co/datasets/walledai/HarmBench",
    "id": "walledai/HarmBench",
    "host": "HuggingFace datasets",
    "pinned_revision": "fb6c2afd5a2a943d701d6db3efab87d077e81be5",
    "size": {
      "items": 400,
      "breakdown": {
        "standard": 200,
        "contextual": 100,
        "copyright": 100
      }
    },
    "license": "MIT",
    "gated": "auto",
    "category_coverage": {
      "semantic": [
        "Cybercrime & Unauthorized Intrusion",
        "Chemical & Biological Weapons/Drugs",
        "Copyright Violations",
        "Misinformation & Disinformation",
        "Harassment & Bullying",
        "Illegal Activities",
        "General Harm"
      ],
      "columns": [
        "prompt",
        "category",
        "tags"
      ]
    },
    "role": [
      "PRIMARY_loader"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "HarmBench classifier",
    "canonical_url": "https://huggingface.co/cais/HarmBench-Llama-2-13b-cls",
    "id": "cais/HarmBench-Llama-2-13b-cls",
    "host": "HuggingFace models",
    "pinned_revision": "bda705349d1144fa618770bea64d99ce54e3835b",
    "size": {
      "params": "13B",
      "rows": null
    },
    "license": "MIT",
    "gated": false,
    "category_coverage": {
      "type": "binary harmful/safe classifier on (behaviour, completion)"
    },
    "role": [
      "JUDGE"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "AdvBench",
    "canonical_url": "https://github.com/llm-attacks/llm-attacks/tree/main/data/advbench",
    "id": "llm-attacks/llm-attacks",
    "host": "GitHub",
    "pinned_revision": "098262edf85f807224e70ecd87b9d83716bf6b73",
    "size": {
      "items": 1094,
      "behaviors": 520,
      "strings": 574
    },
    "license": "MIT",
    "gated": false,
    "category_coverage": {
      "taxonomy": "none published (flat list of harmful behaviours)"
    },
    "role": [
      "PRIMARY_BASELINE",
      "PROBE_SOURCE"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "AdvBench HF mirror",
    "canonical_url": "https://huggingface.co/datasets/walledai/AdvBench",
    "id": "walledai/AdvBench",
    "host": "HuggingFace datasets",
    "pinned_revision": "9d4730540082fa4017450b65ca1c0e1d8d30446e",
    "size": {
      "items": 520
    },
    "license": "MIT",
    "gated": "auto",
    "category_coverage": {
      "taxonomy": "none",
      "columns": [
        "prompt",
        "target"
      ]
    },
    "role": [
      "PRIMARY_BASELINE_loader"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "JailbreakBench JBB-Behaviors",
    "canonical_url": "https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors",
    "id": "JailbreakBench/JBB-Behaviors",
    "host": "HuggingFace datasets",
    "pinned_revision": "886acc352a31533ffbcf4ef22c744658688086fc",
    "size": {
      "items": 200,
      "harmful": 100,
      "benign": 100,
      "judge_comparison": 300
    },
    "license": "MIT",
    "gated": false,
    "category_coverage": {
      "categories": [
        "Harassment/Discrimination",
        "Malware/Hacking",
        "Physical harm",
        "Economic harm",
        "Fraud/Deception",
        "Disinformation",
        "Sexual/Adult content",
        "Privacy",
        "Expert advice",
        "Government decision-making"
      ],
      "per_category_counts": {
        "Harassment/Discrimination": 10,
        "Malware/Hacking": 10,
        "Physical harm": 10,
        "Economic harm": 10,
        "Fraud/Deception": 10,
        "Disinformation": 10,
        "Sexual/Adult content": 10,
        "Privacy": 10,
        "Expert advice": 10,
        "Government decision-making": 10
      }
    },
    "role": [
      "HELDOUT",
      "NULL_CONTROL_benign"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "JailbreakBench code + artifacts",
    "canonical_url": "https://github.com/JailbreakBench/jailbreakbench",
    "id": "JailbreakBench/jailbreakbench",
    "host": "GitHub",
    "pinned_revision": "23dbdf6b19650521604456229bc1d9c4156c85c1",
    "size": {
      "items": null
    },
    "license": "MIT",
    "gated": false,
    "category_coverage": {
      "type": "code + loader for JBB behaviours and submitted jailbreak strings"
    },
    "role": [
      "PROTOCOL_REFERENCE"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "StrongREJECT",
    "canonical_url": "https://github.com/alexandrasouly/strongreject",
    "id": "alexandrasouly/strongreject",
    "host": "GitHub",
    "pinned_revision": "f7cad6c17e624e21d8df2278e918ae1dddb4cb56",
    "size": {
      "items": 313,
      "small_subset": 60
    },
    "license": "MIT (code + custom data); upstream-sourced prompts retain original licences, several of which publish no licence",
    "gated": false,
    "category_coverage": {
      "categories": {
        "Non-violent crimes": 59,
        "Violence": 54,
        "Disinformation and deception": 50,
        "Hate, harassment and discrimination": 50,
        "Illegal goods and services": 50,
        "Sexual content": 50
      },
      "sources": {
        "custom": 221,
        "DAN": 35,
        "AdvBench": 25,
        "MaliciousInstruct": 12,
        "HarmfulQ": 11,
        "MasterKey": 3,
        "Jailbreaking via Prompt Engineering": 3,
        "OpenAI System Card": 3
      },
      "counts_method": "counted from strongreject_dataset.csv at the pinned revision",
      "per_category_counts_published": true
    },
    "role": [
      "HELDOUT",
      "JUDGE_RUBRIC"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "StrongREJECT maintained fork",
    "canonical_url": "https://github.com/dsbowen/strong_reject",
    "id": "dsbowen/strong_reject",
    "host": "GitHub",
    "pinned_revision": "7a551d5b440ec7b75d4f6f5bb7c1719965b76b47",
    "size": {
      "items": null
    },
    "license": "MIT",
    "gated": false,
    "category_coverage": {
      "type": "package + fine-tuned Gemma-2B autograder"
    },
    "role": [
      "JUDGE_offline"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "StrongREJECT HF mirror",
    "canonical_url": "https://huggingface.co/datasets/walledai/StrongREJECT",
    "id": "walledai/StrongREJECT",
    "host": "HuggingFace datasets",
    "pinned_revision": "df54272b395ce9e584d2f8140519935425d8549f",
    "size": {
      "items": 313
    },
    "license": "MIT",
    "gated": "auto",
    "category_coverage": {
      "categories": [
        "Disinformation and deception",
        "Illegal goods and services",
        "Hate/harassment/discrimination",
        "Non-violent crimes",
        "Violence",
        "Sexual content"
      ],
      "columns": [
        "prompt",
        "category",
        "source"
      ]
    },
    "role": [
      "HELDOUT_loader"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "SALAD-Bench (Salad-Data)",
    "canonical_url": "https://huggingface.co/datasets/OpenSafetyLab/Salad-Data",
    "id": "OpenSafetyLab/Salad-Data",
    "host": "HuggingFace datasets",
    "pinned_revision": "d21a325e276a99bd69b1fbb8aa51a9f249486b72",
    "size": {
      "base": 21318,
      "attack_enhanced": 5000,
      "small_attack_subset": 300,
      "defense_enhanced": 200,
      "mcq": 3840
    },
    "license": "Apache-2.0",
    "gated": false,
    "category_coverage": {
      "domains": [
        "O1: Representation & Toxicity",
        "O2: Misinformation Harms",
        "O3: Socioeconomic Harms",
        "O4: Information & Safety",
        "O5: Malicious Use",
        "O6: Human Autonomy & Integrity"
      ],
      "tasks": 16,
      "categories": 65,
      "min_per_category": 200,
      "source_provenance": {
        "finetuned_gpt35_self_instruct": 15433,
        "hh_harmless": 4184,
        "hh_red_team": 659,
        "advbench": 359,
        "multilingual": 230,
        "do_not_answer": 189,
        "toxicchat": 129,
        "do_anything_now": 93,
        "gptfuzzer": 42
      }
    },
    "role": [
      "PRIMARY",
      "HELDOUT_domains"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "SALAD-Bench code",
    "canonical_url": "https://github.com/OpenSafetyLab/SALAD-BENCH",
    "id": "OpenSafetyLab/SALAD-BENCH",
    "host": "GitHub",
    "pinned_revision": "575d5369c5355c0ed76e27860a889aa2f3c3e0e5",
    "size": {
      "items": null
    },
    "license": "Apache-2.0",
    "gated": false,
    "category_coverage": {
      "hierarchy": "6 domains / 16 tasks / 65 categories"
    },
    "role": [
      "JUDGE",
      "TAXONOMY_REFERENCE"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "HEx-PHI",
    "canonical_url": "https://huggingface.co/datasets/LLM-Tuning-Safety/HEx-PHI",
    "id": "LLM-Tuning-Safety/HEx-PHI",
    "host": "HuggingFace datasets",
    "pinned_revision": "83128b46334b80cc567bd7a2caf7af11c5b0bab7",
    "size": {
      "items": 330
    },
    "license": "custom HEx-PHI licence agreement (license: other)",
    "gated": true,
    "category_coverage": {
      "categories": [
        "Illegal Activity",
        "Child Abuse Content",
        "Hate/Harass/Violence",
        "Malware",
        "Physical Harm",
        "Economic Harm",
        "Fraud/Deception",
        "Adult Content",
        "Political Campaigning",
        "Privacy Violation",
        "Tailored Financial Advice"
      ],
      "per_category_counts": {
        "Illegal Activity": 30,
        "Child Abuse Content": 30,
        "Hate/Harass/Violence": 30,
        "Malware": 30,
        "Physical Harm": 30,
        "Economic Harm": 30,
        "Fraud/Deception": 30,
        "Adult Content": 30,
        "Political Campaigning": 30,
        "Privacy Violation": 30,
        "Tailored Financial Advice": 30
      }
    },
    "role": [
      "PROBE",
      "HELDOUT_leave_one_category_out"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "Do-Not-Answer",
    "canonical_url": "https://huggingface.co/datasets/LibrAI/do-not-answer",
    "id": "LibrAI/do-not-answer",
    "host": "HuggingFace datasets",
    "pinned_revision": "74e74f2e4507ef256fe536f78a776f4a1ff67955",
    "size": {
      "items": 939
    },
    "license": "card frontmatter says apache-2.0; card body states data is CC BY-NC-SA 4.0 and only source files are Apache-2.0 — treat as non-commercial",
    "gated": false,
    "category_coverage": {
      "levels": {
        "risk_areas": 5,
        "harm_types": 12,
        "specific_harms": 61
      },
      "columns": [
        "risk_area",
        "types_of_harm",
        "specific_harms"
      ]
    },
    "role": [
      "PROBE",
      "OVER_REFUSAL_CONTROL"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "Do-Not-Answer code",
    "canonical_url": "https://github.com/Libr-AI/do-not-answer",
    "id": "Libr-AI/do-not-answer",
    "host": "GitHub",
    "pinned_revision": "460703484df354958a5e1cd7378a38fcb94a2f3e",
    "size": {
      "items": null
    },
    "license": "Apache-2.0 (code)",
    "gated": false,
    "category_coverage": {
      "levels": {
        "risk_areas": 5,
        "harm_types": 12,
        "specific_harms": 61
      }
    },
    "role": [
      "JUDGE",
      "TAXONOMY_REFERENCE"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "BeaverTails",
    "canonical_url": "https://huggingface.co/datasets/PKU-Alignment/BeaverTails",
    "id": "PKU-Alignment/BeaverTails",
    "host": "HuggingFace datasets",
    "pinned_revision": "8401fe609d288129cc684a9b3be6a93e41cfe678",
    "size": {
      "items": 333963,
      "splits": {
        "330k_train": 300567,
        "330k_test": 33396,
        "30k_train": 27186,
        "30k_test": 3021
      }
    },
    "license": "CC BY-NC 4.0",
    "gated": false,
    "category_coverage": {
      "categories": [
        "Animal Abuse",
        "Child Abuse",
        "Controversial Topics, Politics",
        "Discrimination, Stereotype, Injustice",
        "Drug Abuse, Weapons, Banned Substance",
        "Financial Crime, Property Crime, Theft",
        "Hate Speech, Offensive Language",
        "Misinformation Regarding ethics, laws, and safety",
        "Non-Violent Unethical Behavior",
        "Privacy Violation",
        "Self-Harm",
        "Sexually Explicit, Adult Content",
        "Shocking, Gruesome Content",
        "Terrorism, Organized Crime"
      ],
      "labels": "multi-label booleans per category + is_safe",
      "per_category_counts_published": false
    },
    "role": [
      "PROBE_SUPPLY",
      "NULL_CONTROL_benign"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "SORRY-Bench",
    "canonical_url": "https://huggingface.co/datasets/sorry-bench/sorry-bench-202406",
    "id": "sorry-bench/sorry-bench-202406",
    "host": "HuggingFace datasets",
    "pinned_revision": "b34822276edde97592eda99c0b56d306f8830469",
    "size": {
      "base_instructions": 450,
      "topics": 45,
      "per_topic": 10,
      "mutated_variants": 9000
    },
    "license": "custom sorry-bench licence (license: other)",
    "gated": true,
    "category_coverage": {
      "topics": 45,
      "per_category_counts": {
        "per_topic": 10
      },
      "languages": "multilingual release",
      "superseded_by": "sorry-bench/sorry-bench-202503"
    },
    "role": [
      "HELDOUT"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "AIR-Bench 2024",
    "canonical_url": "https://huggingface.co/datasets/stanford-crfm/air-bench-2024",
    "id": "stanford-crfm/air-bench-2024",
    "host": "HuggingFace datasets",
    "pinned_revision": "976d9fbb0f52bce704dcbef5bd7a2652e65f2a21",
    "size": {
      "items": 5694,
      "configs": {
        "default": 5694,
        "us": 3921,
        "china": 4416,
        "eu_comprehensive": 4134,
        "eu_mandatory": 3402,
        "judge_prompts": 314
      }
    },
    "license": "CC BY 4.0",
    "gated": false,
    "category_coverage": {
      "taxonomy_levels": 4,
      "medium_categories": 45,
      "granular_risks": 314,
      "columns": [
        "cate-idx",
        "l2-name",
        "l3-name",
        "l4-name",
        "prompt"
      ],
      "per_category_counts_published": false
    },
    "role": [
      "HELDOUT"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "AILuminate v1.0 demo prompt set",
    "canonical_url": "https://github.com/mlcommons/ailuminate",
    "id": "mlcommons/ailuminate",
    "host": "GitHub",
    "pinned_revision": "769cc2be9d20c8d4fb26ce53b68865ed41dfb8e2",
    "size": {
      "demo_prompts": 1200,
      "practice_prompts": 12000,
      "private_prompts": 12000,
      "total": 24000
    },
    "license": "CC BY 4.0 (data); Apache-2.0 (repo)",
    "gated": false,
    "category_coverage": {
      "hazard_codes": [
        "vcr",
        "src",
        "cse",
        "ssh",
        "iwp",
        "ipv",
        "dfm",
        "ncr",
        "hte",
        "prv",
        "spc_ele",
        "spc_fin",
        "spc_hlt",
        "sxc_prn"
      ],
      "named_categories": 12,
      "personas": [
        "normal",
        "unskilled",
        "skilled"
      ],
      "locales": [
        "en_US",
        "fr_FR",
        "zh_CN",
        "hi_IN"
      ],
      "per_category_counts_published": false
    },
    "role": [
      "HELDOUT"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "WMDP",
    "canonical_url": "https://huggingface.co/datasets/cais/wmdp",
    "id": "cais/wmdp",
    "host": "HuggingFace datasets",
    "pinned_revision": "7125571f22f032c56415e7980f48d877dd830ff8",
    "size": {
      "items": 3668,
      "splits": {
        "wmdp-bio": 1273,
        "wmdp-cyber": 1987,
        "wmdp-chem": 408
      }
    },
    "license": "MIT",
    "gated": false,
    "category_coverage": {
      "domains": [
        "bio",
        "cyber",
        "chem"
      ],
      "format": "4-choice MCQ"
    },
    "role": [
      "CAPCOST"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "WMDP forget corpora",
    "canonical_url": "https://huggingface.co/datasets/cais/wmdp-bio-forget-corpus",
    "id": "cais/wmdp-bio-forget-corpus; cais/wmdp-cyber-forget-corpus",
    "host": "HuggingFace datasets",
    "pinned_revision": "5a786ed1041e56fef2d4ed26c1239f12b73a68eb (cyber: 774cdc4063f21aa0ce8c2aa23c71521c740fd054)",
    "size": {
      "items": null
    },
    "license": "MIT",
    "gated": "auto",
    "category_coverage": {
      "domains": [
        "bio",
        "cyber"
      ],
      "labels": "none (raw text corpora)"
    },
    "role": [
      "CAPCOST_SUPPORT"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "CyberSecEval (v1 insecure code)",
    "canonical_url": "https://huggingface.co/datasets/walledai/CyberSecEval",
    "id": "walledai/CyberSecEval",
    "host": "HuggingFace datasets",
    "pinned_revision": "62dba0bb39c450c375aff453d3396fa8f2338eee",
    "size": {
      "per_config": 1916,
      "per_language": {
        "python": 351,
        "php": 162,
        "javascript": 249,
        "rust": 204,
        "java": 229,
        "cpp": 259,
        "c": 227,
        "csharp": 235
      }
    },
    "license": "MIT",
    "gated": false,
    "category_coverage": {
      "languages": 8,
      "labels": [
        "cwe_identifier",
        "pattern_id",
        "rule",
        "variant",
        "analyzer"
      ]
    },
    "role": [
      "HELDOUT_cyber",
      "CAPCOST_adjacent"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "CyberSecEval 2 (PurpleLlama suite)",
    "canonical_url": "https://github.com/meta-llama/PurpleLlama/tree/775c64a88c42896611ae224b46b9b5c6baf8b89a/CybersecurityBenchmarks",
    "id": "meta-llama/PurpleLlama",
    "host": "GitHub",
    "pinned_revision": "775c64a88c42896611ae224b46b9b5c6baf8b89a",
    "size": {
      "items": null,
      "bytes": {
        "mitre_benchmark_100_per_category_with_augmentation.json": 4488580,
        "mitre_prompts_multilingual_machine_translated.json": 5723524,
        "frr.json": 420424,
        "frr_multilingual_machine_translated.json": 1121020,
        "prompt_injection.json": 192696,
        "prompt_injection_multilingual_machine_translated.json": 1041209,
        "interpreter.json": 388355,
        "multiturn_phishing_challenges.json": 1951522,
        "autocomplete.json": 3419411,
        "instruct.json": 3356532
      },
      "components": [
        "mitre (100 prompts per category)",
        "mitre_frr",
        "prompt_injection (15 attack categories)",
        "visual prompt injection",
        "interpreter",
        "autonomous_uplift",
        "canary_exploit",
        "spear_phishing"
      ]
    },
    "license": "MIT (evals/benchmarks); Llama models under Llama Community licence",
    "gated": false,
    "category_coverage": {
      "prompt_injection_categories": 15,
      "mitre": "ATT&CK tactic/technique grid",
      "families": [
        "cyberattack helpfulness",
        "false refusal rate",
        "prompt injection",
        "code interpreter abuse",
        "offensive cyber exploitation"
      ]
    },
    "role": [
      "HELDOUT_cyber",
      "OVER_REFUSAL_CONTROL"
    ],
    "retrieved_at": "2026-11-07"
  },
  {
    "dataset": "Tulu-3 HarmBench eval split",
    "canonical_url": "https://huggingface.co/datasets/allenai/tulu-3-harmbench-eval",
    "id": "allenai/tulu-3-harmbench-eval",
    "host": "HuggingFace datasets",
    "pinned_revision": "c8f90e1bf8849be43402450355fcd6bceed60e51",
    "size": {
      "items": 320,
      "functional_breakdown": {
        "standard": 159,
        "copyright": 80,
        "contextual": 81
      },
      "note": "identical row set to HarmBench harmbench_behaviors_text_test.csv"
    },
    "license": "ODC-BY",
    "gated": false,
    "category_coverage": {
      "columns": [
        "Behavior",
        "FunctionalCategory",
        "SemanticCategory",
        "Tags",
        "ContextString",
        "BehaviorID"
      ],
      "semantic_labels": [
        "illegal",
        "misinformation_disinformation",
        "cybercrime_intrusion",
        "chemical_biological",
        "harassment_bullying",
        "harmful",
        "copyright"
      ],
      "functional_labels": [
        "standard",
        "copyright",
        "contextual"
      ],
      "functional_counts": {
        "standard": 159,
        "copyright": 80,
        "contextual": 81
      }
    },
    "role": [
      "PRIMARY_EXECUTION"
    ],
    "retrieved_at": "2026-11-07"
  }
]
```

## Notes

- **Verification method.** Every HF revision is the `sha` returned by `https://huggingface.co/api/datasets/<id>` on 2026-11-07. Every GitHub revision is the default-branch `HEAD` from `git ls-remote https://github.com/<owner>/<repo> HEAD` on the same date; the values match `GET https://api.github.com/repos/<owner>/<repo>/commits?per_page=1` for the repos where the REST API was not rate-limited. No revision here is invented, and none is `UNVERIFIED`.
- **How per-category counts were obtained.** The HF datasets-server `/filter` endpoint returns HTTP 500 and `/sql` returns 404, so no server-side aggregation was possible; `/info` (`num_examples`) was used for every total. Where the prompt set is a small public CSV, the counts were taken by reading the pinned file and tabulating the label column — HarmBench text set (400 rows, 7 semantic labels), the HarmBench text val/test splits (80/320), and StrongREJECT (313 rows, 6 categories, 8 sources). JBB's harmful split is exactly 100 rows, so its 10×10 table is a complete count rather than a sample. HEx-PHI's 11×30 comes from the paper because the dataset is gated. Sets that publish no per-category table and cannot be counted this way are marked `per_category_counts_published: false`: BeaverTails (multi-label, 334k rows), AIR-Bench 2024 (314 granular categories, counts not tabulated anywhere), AILuminate (demo is a 10% sample, so its per-category `n` is not the benchmark's).
- **Tulu-3 eval set is the HarmBench test split, not an extra battery.** `allenai/tulu-3-harmbench-eval` holds the same 320 rows as `harmbench_behaviors_text_test.csv` (159 standard / 80 copyright / 81 contextual; spot-checked on `BehaviorID korean_war_north_defensive`). Use it as the loader for the HarmBench test number, and never count it as an independent held-out set alongside HarmBench test — that would silently double-weight those 320 behaviours in any aggregate.
- **Gated access is the main practical risk.** `walledai/HarmBench`, `walledai/AdvBench`, `walledai/StrongREJECT`, `cais/wmdp-*-forget-corpus` are `gated: auto` — free but token-gated, and the datasets-server refuses them with 401, so no HF-side row counting is possible without a token. `LLM-Tuning-Safety/HEx-PHI` requires manual approval with affiliation. `sorry-bench/sorry-bench-202406` requires a name/affiliation/country/purpose form. If the study needs zero-friction reproduction, budget a token and one approval email.
- **Licence conflicts.** Do-Not-Answer's YAML says `apache-2.0` while its card body says the data is CC BY-NC-SA 4.0 (code Apache-2.0). BeaverTails is CC BY-NC 4.0, so it cannot be redistributed inside a commercial artefact. StrongREJECT is MIT for its own data but inherits unlicensed upstream prompts (MaliciousInstruct, HarmfulQ, OpenAI system card); publish only the row IDs, not the text, if redistribution matters.
- **HEx-PHI and Sorry-Bench are the two held-out sets worth the approval cost.** HEx-PHI's 30-per-category structure is the only published battery here that supports a clean leave-one-category-out probe split with equal n per category. Sorry-Bench's 45 fine-grained topics (10 each) is the only balanced control for "the edit moved a coarse boundary rather than the direction".
- **CyberSecEval pinning.** Repo HEAD (`f64eebd5…`) is CyberSecEval 4 and has restructured `CybersecurityBenchmarks`; the v2-era layouts and dataset paths used by the CyberSecEval 2 paper are preserved at `775c64a8…` (2024-12-20), which is the pin recorded above. CyberSecEval 2 per-component item counts are generated at runtime from JSON and are not published as a table, so that row carries component names rather than counts.
- **SORRY-Bench drift.** `sorry-bench-202503` (`612a4e1f45db…`) supersedes the 202406 release with the same gating; pin whichever one the comparison papers used, and record the choice, because topic counts moved between releases (the paper's v1 abstract states 44 topics / 440 instructions; the later revision states 45 / 450, which is the figure recorded above).
- **AILuminate is only nominally public.** The public repo ships the 1,200-prompt demo (10% of the practice set). The 12,000 practice and 12,000 private prompts plus the ensemble evaluator require MLCommons membership, so a headline "AILuminate score" cannot be reproduced outside the consortium — use it as a hazard-taxonomy reference and a 1,200-prompt held-out check only.
- **Role conflict to resolve before registration.** HarmBench is both the direction-fitting source and the reported endpoint in the Abliteration/Heretic literature. If the primary endpoint is HarmBench ASR, the refusal direction cannot also be fitted on HarmBench behaviours; the clean design is to fit on HEx-PHI/AdvBench or BeaverTails-style pairs and report HarmBench test (410) + JBB + one cross-taxonomy set (AIR-Bench or Sorry-Bench) as held-out.
