# AMD MI300X preparation

The gates use `torch.cuda`, which ROCm implements. No code change needed to load the model,
generate or judge. What changes is the runtime underneath and the numbers it produces.

## On arrival: verification order

```
python -m harness.device                             # 1. confirm ROCm, gfx942, bf16
python scripts/record_host.py --run runs/<id> --dry-run  # 2. check amd-smi probe works
python scripts/benchmark_inference.py \
    --model Qwen/Qwen3.5-0.8B --revision 2fc06364 \
    --mode generate --batches 1,8,16,32,64,128,256 \
    --out benchmark_generate.json                    # 3. measure; don't guess
python scripts/benchmark_inference.py \
    --model cais/HarmBench-Llama-2-13b-cls \
    --revision bda705349d --mode forward \
    --batches 1,8,16,32,64,128,256 \
    --prompt-tokens 512 --out benchmark_judge.json   # 4. judge forward throughput
python scripts/check_device_equivalence.py \
    --run runs/20261110T135200Z-weightspace-abliteration-qwen3.5-0.8b \
    --arm primary --limit 32                         # 5. greedy output drift vs stored parent
python scripts/record_host.py --run runs/<id>        # 6. record only after verification
```

If the equivalence check reports mismatches, record the rate and the first-divergence offsets
in `EXECUTION_LOG.md` before running any gate. Drift is evidence, not a blocker: the protocol
compares parent vs candidate on the same device, so within-run consistency is what matters. But
the existing parent numbers were measured on A100 — if they must be reused, the drift is part of
the error budget.

## Environment variables

`harness/device.py` splits ROCm settings into two groups:

| Group | Variables | Rule |
|---|---|---|
| Arithmetic-neutral | `HIP_FORCE_DEV_KERNARG=1` | Expected not to change FP results; reduces kernel launch overhead. Set before all runs. |
| May change arithmetic | `TORCH_BLAS_PREFER_HIPBLASLT=1`, `PYTORCH_TUNABLEOP_ENABLED=1`, `TORCH_ROCM_FA_PREFER_CK=1` | Selects a different GEMM library or attention kernel; can change bf16 accumulation order. Enable one at a time, re-run the equivalence check, and record which are active in the host session. |

**Do not use TunableOp offline tuning on study prompts.** TunableOp selects GEMM algorithms based
on observed matrix shapes; the shapes come from the prompt lengths. Tune on the synthetic prompts
the benchmark script generates, not on a split arm.

Sources: [ROCm MI300X workload optimization](https://rocm.docs.amd.com/en/docs-6.3.1/how-to/rocm-for-ai/inference-optimization/workload.html),
[torch.backends.cuda.preferred_rocm_fa_library](https://github.com/pytorch/pytorch/blob/main/torch/backends/cuda/__init__.py),
[vLLM on MI300X](https://vllm.ai/blog/2024-10-23-vllm-serving-amd).

## Attention backend

PyTorch on ROCm defaults to AOTriton for flash attention inside SDPA. CK (Composable Kernel)
is available via `TORCH_ROCM_FA_PREFER_CK=1` or:

```python
torch.backends.cuda.preferred_rocm_fa_library("ck")
```

The choice is recorded by `python -m harness.device`. Neither is guaranteed to match the A100's
cuDNN flash attention path exactly; the equivalence check measures the gap.

A known issue (PyTorch #156012) reported bf16 context-parallelism numerical inaccuracy on MI300X
with AOTriton. Context parallelism is not used here, but the report is evidence that the bf16
attention code path has had accuracy bugs on this hardware. Record the torch+ROCm version and the
attention library in every host session.

## Install

The repo pins `torch==2.15.0` via `uv.lock`. ROCm builds use a different wheel index:

```
# Check whether a ROCm 6.x wheel exists for the pinned version
pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/rocm6.4
```

If the pinned version has no ROCm wheel, install the nearest available build and record the
resolved version in the host session and `EXECUTION_LOG.md`. It is not a deviation unless a gate
receipt already exists that was produced under the pinned version on this run.

## What must be recorded

| When | What | Where |
|---|---|---|
| Before any gate | `scripts/record_host.py` with `amd-smi static --json` probe | `host_provisioned` / `host` ledger entry |
| Before any gate | `python -m harness.device` output | `EXECUTION_LOG.md` |
| Before any gate | `scripts/benchmark_inference.py` JSON | private benchmark artifact |
| Before any gate | `scripts/check_device_equivalence.py` output | `EXECUTION_LOG.md` |
| If env vars enabled | Which ones and their values | host session params |

## What not to do

- Do not use vLLM for gate runs. The registered generation path is HF `model.generate`, and
  vLLM's KV-cache paging and speculative decoding change the token sequence. Use vLLM only for
  exploratory throughput measurement outside the registered run.
- Do not rewrite stored parent results to "fix" cross-device drift. Record the drift; rerun
  the parent on this device if the comparison requires it.
- Do not benchmark on split arms. The benchmark script generates synthetic tokens for a reason.
