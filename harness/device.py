"""Vendor-neutral device identity and the settings a new machine may change.

Every gate already talks to ``torch.cuda``, which ROCm implements, so an MI300X runs the same code
path as an A100. What differs between machines is collectable: the runtime version, the architecture
string, which attention library PyTorch selects, and the batch schedule that actually saturates HBM.
This module collects the first three. It does not guess the fourth — that is measured by
``scripts/benchmark_inference.py`` and recorded with its numbers.

Nothing here is applied to the process. Environment variables that can change GEMM or attention
accumulation order are reported separately from ones that only change launch plumbing, because the
study's claim is a comparison: a faster kernel that shifts the numbers silently is not a win.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

# Documented on the ROCm inference-tuning page and in torch's ROCm flash-attention selector.
# Splitting them by whether they can change arithmetic is the point: only the second group needs
# the cross-device equivalence check before a result produced under it is comparable.
_ARITHMETIC_NEUTRAL = {"HIP_FORCE_DEV_KERNARG": "1"}
_MAY_CHANGE_ARITHMETIC = {
    "TORCH_BLAS_PREFER_HIPBLASLT": "1",
    "PYTORCH_TUNABLEOP_ENABLED": "1",
    "TORCH_ROCM_FA_PREFER_CK": "1",
}


@dataclass(frozen=True)
class Device:
    backend: str            # "rocm" | "cuda" | "cpu"
    index: int
    name: str
    arch: str | None        # gfx942 or sm_80
    memory_gb: float | None
    torch: str
    runtime: str | None     # torch.version.hip or torch.version.cuda
    flash_attention_library: str | None


def detect(index: int = 0) -> Device:
    """Describe the accelerator the process would use, without loading anything onto it."""
    import torch

    hip = getattr(torch.version, "hip", None)
    cuda = getattr(torch.version, "cuda", None)
    if not torch.cuda.is_available():
        return Device("cpu", index, "cpu", None, None, torch.__version__, hip or cuda, None)
    props = torch.cuda.get_device_properties(index)
    arch = getattr(props, "gcnArchName", None) or f"sm_{props.major}{props.minor}"
    library = None
    selector = getattr(torch.backends.cuda, "preferred_rocm_fa_library", None)
    if hip and selector is not None:
        library = str(selector())
    return Device(
        backend="rocm" if hip else "cuda",
        index=index,
        name=props.name,
        arch=arch,
        memory_gb=round(props.total_memory / 2**30, 1),
        torch=torch.__version__,
        runtime=hip or cuda,
        flash_attention_library=library,
    )


def dtypes() -> dict[str, bool]:
    """Which low-precision dtypes this build can run attention in."""
    import torch

    if not torch.cuda.is_available():
        return {"bf16": torch.cuda.is_bf16_supported() if hasattr(torch.cuda, "is_bf16_supported") else False,
                "fp16": False}
    supported = getattr(torch.cuda, "is_bf16_supported", None)
    return {"bf16": bool(supported()) if supported else False, "fp16": True}


def environment_profile(device: Device) -> dict[str, dict[str, str]]:
    """Documented ROCm settings, split by whether they can change arithmetic.

    Values are quoted from the ROCm inference-tuning guide and torch's ROCm flash-attention
    selector; they are recommendations to test, not settings this module applies.
    """
    if device.backend != "rocm":
        return {"arithmetic_neutral": {}, "may_change_arithmetic": {}}
    return {
        "arithmetic_neutral": dict(_ARITHMETIC_NEUTRAL),
        "may_change_arithmetic": dict(_MAY_CHANGE_ARITHMETIC),
    }


def report(index: int = 0) -> dict[str, Any]:
    """Everything a run record needs to say what it executed on."""
    import torch

    device = detect(index)
    return {
        "device": asdict(device),
        "dtypes": dtypes(),
        "sdpa": hasattr(torch.nn.functional, "scaled_dot_product_attention"),
        "attention_backends": sorted(
            name for name in dir(torch.nn.attention) if name.startswith("sdpa")
        ) if hasattr(torch.nn, "attention") else [],
        "environment": environment_profile(device),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="harness.device")
    parser.add_argument("--index", type=int, default=0)
    args = parser.parse_args(argv)
    print(json.dumps(report(args.index), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
