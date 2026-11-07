# Capability measurement stack — harness, version pinning, task datasets

Study role: every capability number that constitutes the "declared cost" side of the ablation claim must be produced by one pinned harness revision over pinned dataset revisions. This file fixes that stack.

Retrieved: 2026-11-07.

## Harness and runtime pins

| item | id | host | canonical URL | pinned_revision | size | license | gated | category coverage | role in study | retrieved_at |
|---|---|---|---|---|---|---|---|---|---|---|
| EleutherAI/lm-evaluation-harness | `EleutherAI/lm-evaluation-harness` | GitHub | https://github.com/EleutherAI/lm-evaluation-harness | `d6de81643928d653435c431bae19945d41d32520` | 1,905 tree entries; ~1.6 MB repo (API-reported tree) | MIT | false | all capability tasks below | single measurement engine for every capability number | 2026-11-07 |
| vllm-project/vllm | `vllm-project/vllm` | GitHub | https://github.com/vllm-project/vllm | `4ba787ec9959e566d3b587a796dff07673324da5` (tag `v0.33.0`) | n/a (package) | Apache-2.0 | false | inference backend | generation backend for loglikelihood + generate_until tasks | 2026-11-07 |
| vllm (PyPI) | `vllm==0.33.0` | PyPI | https://pypi.org/project/vllm/0.33.0/ | `0.33.0` (uploaded 2026-11-02T10:13:42Z; requires-python >=3.11,<3.15) | 3 distribution files | Apache-2.0 | false | — | installed-run pin; equals git tag `v0.33.0` | 2026-11-07 |

Tag cross-check for the harness: `v0.4.13` → `ddd67220430a2470529f25fd5c05a576ca1057a0`; `v0.5.0.dev1` → `b0561c5e015697c6200edae7510f082b1dcc6462`. The pinned commit `d6de8164…` is current `main` (2026-09-14), i.e. it is not any released tag. Record it as a commit pin, not a release pin.

## Task datasets

| task (`--tasks`) | task yaml `metadata.version` | dataset id | host | canonical URL | pinned_revision | split used | shot count | items in eval split | license | gated | category coverage | role in study | retrieved_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `mmlu_pro` (group; 14 subject leaves) | 2.0 group / 3.1 leaf | `TIGER-Lab/MMLU-Pro` | HuggingFace datasets | https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro | `b189ec765aa7ed75c8acfea42df31fdae71f97be` | `test` (fewshot from `validation`, 70 rows) | 5 | 12,032 | MIT | false | 14 academic/professional subjects, 4-way MCQ, generate_until | headline knowledge/reasoning capability; primary cost metric | 2026-11-07 |
| `gpqa_diamond_cot_zeroshot` | 2.2 | `Idavidrein/gpqa` (config `gpqa_diamond`) | HuggingFace datasets | https://huggingface.co/datasets/Idavidrein/gpqa | `83022cefff930aea54f654c0b282e74b9eeda5c6` | `train` (only split; equals their validation) | 0 | 198 (card; not server-verifiable while unauthenticated) | CC-BY-4.0 | **true** (`gated: auto`, click-through terms) | graduate-level physics/chemistry/biology, 4-way MCQ, CoT generate_until | hardest science reasoning; leakage-sensitive, gated | 2026-11-07 |
| `bbh` (group `bbh_cot_fewshot`, 27 leaves) | 3.0 group / 4.0 template | `SaylorTwift/bbh` | HuggingFace datasets | https://huggingface.co/datasets/SaylorTwift/bbh | `b5306be6f827cfafbb545ff5a51f96916029b0fd` | `test` | 3 (hard-coded in `fewshot_config.samples`, not sampled from a split) | 6,511 across 27 subtasks | not declared on card | false | 27 BIG-Bench Hard subtasks (logic, arithmetic, tracking, semantics) | multi-step reasoning capability; second-hardest cost metric | 2026-11-07 |
| `musr` → actual ids `leaderboard_musr_murder_mysteries`, `leaderboard_musr_object_placements`, `leaderboard_musr_team_allocation` | 1.0 | `TAUR-Lab/MuSR` | HuggingFace datasets | https://huggingface.co/datasets/TAUR-Lab/MuSR | `7c365b439a222150f317764d4f16ae6c96d7d94a` | `murder_mysteries` (250), `object_placements` (256), `team_allocation` (250) | 0 | 756 | CC-BY-4.0 | false | long-form narrative reasoning, 3 configs, acc_norm | narrative/long-context reasoning; guards against CoT-only capability loss | 2026-11-07 |
| `ifeval` | 4.0 | `google/IFEval` | HuggingFace datasets | https://huggingface.co/datasets/google/IFEval | `966cd89545d6b6acfd7638bc708b98261ca58e84` | `train` (the only split; harness maps it as the eval split) | 0 | 541 prompts / ~833 instructions | Apache-2.0 | false | verifiable instruction following (prompt-level and instruction-level strict/loose) | instruction-following retention; most sensitive to instruction-tuning edits | 2026-11-07 |
| `hellaswag` | 1.0 | `Rowan/hellaswag` | HuggingFace datasets | https://huggingface.co/datasets/Rowan/hellaswag | `218ec52e09a7e7462a5400043bb9a69a41d06b76` | `validation` | 0 | 10,042 | not declared on card | false | commonsense sentence completion, 4-way, acc + acc_norm | standard commonsense anchor; comparability with published abliteration tables | 2026-11-07 |
| `arc_challenge` | 1.0 | `allenai/ai2_arc` (config `ARC-Challenge`) | HuggingFace datasets | https://huggingface.co/datasets/allenai/ai2_arc | `210d026faf9955653af8916fad021475a3f00453` | `test` | 0 | 1,172 | CC-BY-SA-4.0 | false | grade-school science MCQ, acc + acc_norm | science MCQ anchor; low-variance cost check | 2026-11-07 |
| `winogrande` | 1.0 | `allenai/winogrande` (config `winogrande_xl`) | HuggingFace datasets | https://huggingface.co/datasets/allenai/winogrande | `01e74176c63542e6b0bcb004dcdea22d94fb67b5` | `validation` | 0 | 1,267 | not declared on card | false | coreference/commonsense, 2-way | pronoun/commonsense anchor | 2026-11-07 |
| `piqa` | 1.0 | `baber/piqa` | HuggingFace datasets | https://huggingface.co/datasets/baber/piqa | `142f6d7367fd9877f0fb3b5734ea6a545f54cdd1` | `validation` | 0 | 1,838 | not declared on card | false | physical commonsense, 2-way, acc + acc_norm | physical-commonsense anchor | 2026-11-07 |
| `truthfulqa_mc1` | 2.0 | `truthfulqa/truthful_qa` (config `multiple_choice`) | HuggingFace datasets | https://huggingface.co/datasets/truthfulqa/truthful_qa | `741b8276f2d1982aa3d5b832d3ee81ed3b896490` | `validation` | 0 | 817 | Apache-2.0 | false | truthfulness, single-true-answer MC | truthfulness floor; also the closest thing to a refusal-adjacent behavioural probe | 2026-11-07 |
| `truthfulqa_mc2` | 3.0 | `truthfulqa/truthful_qa` (config `multiple_choice`) | HuggingFace datasets | https://huggingface.co/datasets/truthfulqa/truthful_qa | `741b8276f2d1982aa3d5b832d3ee81ed3b896490` | `validation` | 0 | 817 | Apache-2.0 | false | truthfulness, multi-true normalised probability | truthfulness (normalised) — the metric most likely to move if the refusal direction is entangled with hedging | 2026-11-07 |
| `truthfulqa_gen` | 3.0 | `truthfulqa/truthful_qa` (config `generation`) | HuggingFace datasets | https://huggingface.co/datasets/truthfulqa/truthful_qa | `741b8276f2d1982aa3d5b832d3ee81ed3b896490` | `validation` | 0 | 817 | Apache-2.0 | false | generative truthfulness (BLEU/ROUGE max/acc/diff) | generative truthfulness; requires judge-free n-gram scoring | 2026-11-07 |
| `gsm8k` | 3.0 | `openai/gsm8k` (config `main`) | HuggingFace datasets | https://huggingface.co/datasets/openai/gsm8k | `740312add88f781978c0658806c59bc2815b9866` | `test` (fewshot from `train`) | 5 | 1,319 | MIT | false | grade-school math word problems, exact_match via strict-match + flexible-extract | arithmetic reasoning; the task that most reliably breaks under over-aggressive weight edits | 2026-11-07 |

## How versions are actually pinned

- **Repo pin is the real pin.** `metadata.version` in a task yaml is *not* a dataset revision. `TaskConfig` reads it into `Task.VERSION` (`lm_eval/api/task.py:646-647`) and prints it in results; it participates in the few-shot request cache key alongside task name, `num_fewshot`, world size, chat-template flags and tokenizer name. Two runs with the same task name but different yaml `version` can therefore silently differ in prompt/scoring while producing identical-looking result JSON. Cite the yaml version in the paper's appendix, but reproducibility comes from `d6de8164…`.
- **Dataset revisions are not pinned by the harness by itself.** `load_dataset` is called with `dataset_path` and `dataset_name` only; no `revision` is passed in any of the yamls above. To make the run reproducible, pass the sha explicitly per task, e.g. `--model_args ...,tokenizer=...` plus a yaml override with `dataset_kwargs: {revision: <40-hex>}`, or pre-populate the HF cache from a pinned snapshot (`huggingface-cli download <id> --revision <sha>`) and run offline (`HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1`). Without one of these, "pinned" is a claim about the day the run happened, not a claim about the data.
- **Task selection** is by `--tasks a,b,c`. Groups resolve to their leaves: `mmlu_pro` → `mmlu_pro_{biology,business,chemistry,computer_science,economics,engineering,health,history,law,math,other,philosophy,physics,psychology}`; `bbh` → 27 `bbh_cot_fewshot_*` leaves; `musr` is not a group name at this revision — the group is `leaderboard_musr` (leaves `leaderboard_musr_murder_mysteries`, `leaderboard_musr_object_placements`, `leaderboard_musr_team_allocation`). Running `--tasks musr` fails at this commit.
- **Shot counts** above are the values in the yaml at `d6de8164…` (`num_fewshot` defaults to 0 per `docs/task_guide.md:48`). A global `--num_fewshot N` overrides every task and silently changes comparability — if the Abliteration comparison table used different shots, reproduce that table with its own override set rather than mixing overrides and yaml defaults in one run.
- **Filter-dependent tasks.** MMLU-Pro scores through the `custom-extract` regex `answer is \(?([ABCDEFGHIJ])\)?`; BBH through `get-answer` (`(?<=the answer is )(.*)(?=.)`); GSM8K reports both `strict-match` and `flexible-extract`; GPQA reports `strict-match` and `flexible-extract`. Report which filter is quoted, not just the task name.
- **vLLM pinning.** Runtime is `vllm==0.33.0` (tag `v0.33.0` → `4ba787ec…`, PyPI upload 2026-11-02). Pin it three ways for a paper artifact: the pip pin, the container digest (`vllm/vllm-openai:v0.33.0`), and `--model vllm` with explicit `vllm_args` (gpu_memory_utilization, max_model_len, dtype, enforce_eager). Version drift in vLLM changes loglikelihood numerics (batching/kernel selection), so the vLLM pin belongs in the same table as the harness pin. Note `VLLM_WORKER_MULTIPROC_METHOD=spawn` is required on Windows hosts but the study's Linux/GPU host should record whichever it used.

## Notes

- **GPQA Diamond is gated.** HF API reports `"gated": "auto"` on `Idavidrein/gpqa` with `extra_gated_prompt` requiring acceptance of a no-leakage term; the datasets-server `/size` endpoint returns "does not exist, or is not accessible without authentication" for the anonymous caller. The sha `83022cef…` is public metadata and is verified; the 198-item count is from the dataset card and cannot be API-verified without an authenticated token. Any replication must record that a token with granted access was present, because a missing token fails the task rather than degrading it.
- No other task on this list is gated. All twelve remaining dataset ids resolved anonymously with `"gated": false` and `"private": false`.
- `baber/piqa` is a mirror, not the canonical `ybisk/piqa` (`2e8ac2dffd59bac8c3c6714948f4c551a0848bb0`). The harness switched to `baber/piqa` because the canonical repo lacks a usable `validation` split; `baber/piqa` has train 16,113 / validation 1,838 / test 3,084. It declares no license and no card metadata, which is a provenance weakness to disclose: the underlying PiQA is `ybisk/piqa`, license `unknown`. If licensing matters for redistribution, cite `ybisk/piqa` as the source and `baber/piqa` as the loading artifact.
- `google/IFEval` exposes a single split named `train`; the yaml sets `test_split: train`. That is a naming artifact of the upstream release, not an evaluation-on-training-data error — the 541 prompts are the evaluation set.
- `SaylorTwift/bbh` card lists 28 configs; `default` (250 rows) duplicates `date_understanding` and is never referenced by any harness leaf. The 27 referenced subtasks total 6,511 items. Smallest subtask `penguins_in_a_table` (146), and `causal_judgement` (187) / `snarks` (178) are the noisy ones — per-subtask variance should be reported, not only the group mean.
- `TIGER-Lab/MMLU-Pro` validation split is 70 rows, the few-shot source for 5-shot; it is far too small to serve as a dev set for tuning, so no held-out tuning on MMLU-Pro is possible.
- TruthfulQA MC1 and MC2 share one dataset revision and config; MC2 differs only by `process_results` (normalised probability over all true answers) and carries its own yaml version (3.0 vs 2.0). Reporting both is cheap and separates "picks a true answer" from "ranks true answers highly".
- HellaSwag, WinoGrande, PiQA and both TruthfulQA MC tasks declare no `license` field in card metadata. Treat them as research-use, and record the upstream repo licence separately if the artifact is redistributed.
- Harness revision `d6de8164…` is `main` as of 2026-09-14, i.e. newer than tag `v0.5.0.dev1`. It carries the `datasets>=4.0` compatibility shim at `lm_eval/api/task.py:856-858`; pairing it with `datasets<4` or with the 3.x line changes `dataset_kwargs` handling. Pin `datasets` too (the repo's own unit job resolved `datasets==5.0.1` in the commit message for `d6de8164`).

```json
[
  {
    "item": "EleutherAI/lm-evaluation-harness",
    "dataset_id": "EleutherAI/lm-evaluation-harness",
    "host": "GitHub",
    "url": "https://github.com/EleutherAI/lm-evaluation-harness",
    "pinned_revision": "d6de81643928d653435c431bae19945d41d32520",
    "size": "1905 tree entries",
    "license": "MIT",
    "gated": false,
    "category_coverage": "all capability tasks",
    "role": "measurement engine for every capability number",
    "retrieved_at": "2026-11-07"
  },
  {
    "item": "vllm-project/vllm",
    "dataset_id": "vllm-project/vllm",
    "host": "GitHub",
    "url": "https://github.com/vllm-project/vllm",
    "pinned_revision": "4ba787ec9959e566d3b587a796dff07673324da5",
    "size": "n/a (package, tag v0.33.0)",
    "license": "Apache-2.0",
    "gated": false,
    "category_coverage": "inference backend",
    "role": "generation/loglikelihood backend",
    "retrieved_at": "2026-11-07"
  },
  {
    "item": "vllm (PyPI)",
    "dataset_id": "vllm",
    "host": "PyPI",
    "url": "https://pypi.org/project/vllm/0.33.0/",
    "pinned_revision": "0.33.0",
    "size": "3 distribution files",
    "license": "Apache-2.0",
    "gated": false,
    "category_coverage": "inference backend",
    "role": "installed-run pin matching git tag v0.33.0 (uploaded 2026-11-02T10:13:42Z)",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "mmlu_pro",
    "task_yaml_version": "2.0 group / 3.1 leaf",
    "dataset_id": "TIGER-Lab/MMLU-Pro",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro",
    "pinned_revision": "b189ec765aa7ed75c8acfea42df31fdae71f97be",
    "split": "test",
    "fewshot_split": "validation",
    "num_fewshot": 5,
    "items_eval_split": 12032,
    "license": "MIT",
    "gated": false,
    "category_coverage": "14 academic/professional subjects, 4-way MCQ",
    "role": "headline knowledge/reasoning capability; primary cost metric",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "gpqa_diamond_cot_zeroshot",
    "task_yaml_version": "2.2",
    "dataset_id": "Idavidrein/gpqa",
    "dataset_config": "gpqa_diamond",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/Idavidrein/gpqa",
    "pinned_revision": "83022cefff930aea54f654c0b282e74b9eeda5c6",
    "split": "train",
    "fewshot_split": "train",
    "num_fewshot": 0,
    "items_eval_split": 198,
    "items_source": "dataset card; not datasets-server verifiable while unauthenticated",
    "license": "CC-BY-4.0",
    "gated": true,
    "gated_detail": "gated: auto; click-through no-leakage terms; token with granted access required",
    "category_coverage": "graduate-level physics/chemistry/biology, 4-way MCQ, CoT",
    "role": "hardest science reasoning; leakage-sensitive",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "bbh (group bbh_cot_fewshot, 27 leaves)",
    "task_yaml_version": "3.0 group / 4.0 template",
    "dataset_id": "SaylorTwift/bbh",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/SaylorTwift/bbh",
    "pinned_revision": "b5306be6f827cfafbb545ff5a51f96916029b0fd",
    "split": "test",
    "fewshot_split": null,
    "num_fewshot": 3,
    "fewshot_config": "3 hard-coded exemplars per leaf in fewshot_config.samples",
    "items_eval_split": 6511,
    "license": "not declared on card",
    "gated": false,
    "category_coverage": "27 BIG-Bench Hard subtasks: logic, arithmetic, tracking, semantics",
    "role": "multi-step reasoning capability; second-hardest cost metric",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "leaderboard_musr (murder_mysteries, object_placements, team_allocation)",
    "task_yaml_version": "1.0",
    "dataset_id": "TAUR-Lab/MuSR",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/TAUR-Lab/MuSR",
    "pinned_revision": "7c365b439a222150f317764d4f16ae6c96d7d94a",
    "split": "murder_mysteries (250) / object_placements (256) / team_allocation (250)",
    "num_fewshot": 0,
    "items_eval_split": 756,
    "license": "CC-BY-4.0",
    "gated": false,
    "category_coverage": "long-form narrative reasoning, 3 configs, acc_norm",
    "role": "narrative/long-context reasoning; guards against CoT-only capability loss",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "ifeval",
    "task_yaml_version": "4.0",
    "dataset_id": "google/IFEval",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/google/IFEval",
    "pinned_revision": "966cd89545d6b6acfd7638bc708b98261ca58e84",
    "split": "train",
    "num_fewshot": 0,
    "items_eval_split": 541,
    "license": "Apache-2.0",
    "gated": false,
    "category_coverage": "verifiable instruction following, prompt-level and instruction-level strict/loose",
    "role": "instruction-following retention; most sensitive to instruction-tuning edits",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "hellaswag",
    "task_yaml_version": "1.0",
    "dataset_id": "Rowan/hellaswag",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/Rowan/hellaswag",
    "pinned_revision": "218ec52e09a7e7462a5400043bb9a69a41d06b76",
    "split": "validation",
    "num_fewshot": 0,
    "items_eval_split": 10042,
    "license": "not declared on card",
    "gated": false,
    "category_coverage": "commonsense sentence completion, 4-way, acc + acc_norm",
    "role": "standard commonsense anchor; comparability with published abliteration tables",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "arc_challenge",
    "task_yaml_version": "1.0",
    "dataset_id": "allenai/ai2_arc",
    "dataset_config": "ARC-Challenge",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/allenai/ai2_arc",
    "pinned_revision": "210d026faf9955653af8916fad021475a3f00453",
    "split": "test",
    "num_fewshot": 0,
    "items_eval_split": 1172,
    "license": "CC-BY-SA-4.0",
    "gated": false,
    "category_coverage": "grade-school science MCQ, acc + acc_norm",
    "role": "science MCQ anchor; low-variance cost check",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "winogrande",
    "task_yaml_version": "1.0",
    "dataset_id": "allenai/winogrande",
    "dataset_config": "winogrande_xl",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/allenai/winogrande",
    "pinned_revision": "01e74176c63542e6b0bcb004dcdea22d94fb67b5",
    "split": "validation",
    "num_fewshot": 0,
    "items_eval_split": 1267,
    "license": "not declared on card",
    "gated": false,
    "category_coverage": "coreference/commonsense, 2-way",
    "role": "pronoun/commonsense anchor",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "piqa",
    "task_yaml_version": "1.0",
    "dataset_id": "baber/piqa",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/baber/piqa",
    "pinned_revision": "142f6d7367fd9877f0fb3b5734ea6a545f54cdd1",
    "split": "validation",
    "num_fewshot": 0,
    "items_eval_split": 1838,
    "license": "not declared on card",
    "gated": false,
    "category_coverage": "physical commonsense, 2-way, acc + acc_norm",
    "role": "physical-commonsense anchor",
    "upstream": "ybisk/piqa @ 2e8ac2dffd59bac8c3c6714948f4c551a0848bb0 (license unknown)",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "truthfulqa_mc1",
    "task_yaml_version": "2.0",
    "dataset_id": "truthfulqa/truthful_qa",
    "dataset_config": "multiple_choice",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/truthfulqa/truthful_qa",
    "pinned_revision": "741b8276f2d1982aa3d5b832d3ee81ed3b896490",
    "split": "validation",
    "num_fewshot": 0,
    "items_eval_split": 817,
    "license": "Apache-2.0",
    "gated": false,
    "category_coverage": "truthfulness, single-true-answer MC",
    "role": "truthfulness floor",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "truthfulqa_mc2",
    "task_yaml_version": "3.0",
    "dataset_id": "truthfulqa/truthful_qa",
    "dataset_config": "multiple_choice",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/truthfulqa/truthful_qa",
    "pinned_revision": "741b8276f2d1982aa3d5b832d3ee81ed3b896490",
    "split": "validation",
    "num_fewshot": 0,
    "items_eval_split": 817,
    "license": "Apache-2.0",
    "gated": false,
    "category_coverage": "truthfulness, multi-true normalised probability",
    "role": "truthfulness (normalised); most likely to move if refusal direction is entangled with hedging",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "truthfulqa_gen",
    "task_yaml_version": "3.0",
    "dataset_id": "truthfulqa/truthful_qa",
    "dataset_config": "generation",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/truthfulqa/truthful_qa",
    "pinned_revision": "741b8276f2d1982aa3d5b832d3ee81ed3b896490",
    "split": "validation",
    "num_fewshot": 0,
    "items_eval_split": 817,
    "license": "Apache-2.0",
    "gated": false,
    "category_coverage": "generative truthfulness (BLEU/ROUGE max/acc/diff)",
    "role": "generative truthfulness; judge-free n-gram scoring",
    "retrieved_at": "2026-11-07"
  },
  {
    "task": "gsm8k",
    "task_yaml_version": "3.0",
    "dataset_id": "openai/gsm8k",
    "dataset_config": "main",
    "host": "HuggingFace datasets",
    "url": "https://huggingface.co/datasets/openai/gsm8k",
    "pinned_revision": "740312add88f781978c0658806c59bc2815b9866",
    "split": "test",
    "fewshot_split": "train",
    "num_fewshot": 5,
    "items_eval_split": 1319,
    "license": "MIT",
    "gated": false,
    "category_coverage": "grade-school math word problems, exact_match (strict-match + flexible-extract)",
    "role": "arithmetic reasoning; most likely to break under over-aggressive weight edits",
    "retrieved_at": "2026-11-07"
  }
]
```
