#!/usr/bin/env python3
"""Record the execution environment and bind it to the run's ledger.

Run this once on the host, before any gate. It writes `runs/<id>/host.json` with what actually
executed — GPUs, driver, CUDA, library versions — and records a `host_provisioned` entry whose
input hash covers the raw tool output and whose output hash covers the structured record.

Nothing here is typed by hand. A version list a person writes down is unverifiable the moment it is
written; `nvidia-smi` output read by a machine is not.

    python scripts/record_host.py --run runs/<id>
    python scripts/record_host.py --run runs/<id> --dry-run     # print, write nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

PACKAGES = (
    "torch",
    "transformers",
    "numpy",
    "pyarrow",
    "pyyaml",
    "lm-eval",
    "gdkit",
    "accelerate",
    "sentence-transformers",
    "datasets",
    "vllm",
)


def run(command: list[str], timeout: int = 30) -> dict:
    """Run a command and return its result, or an explicit reason why it did not run."""
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return {"command": command, "available": False, "reason": "not found"}
    except subprocess.TimeoutExpired:
        return {"command": command, "available": False, "reason": "timed out"}
    return {
        "command": command,
        "available": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip()[:2000],
    }


def package_versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in PACKAGES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def torch_record() -> dict:
    try:
        import torch
    except Exception as exc:  # torch is optional at record time
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
    record: dict = {
        "available": True,
        "version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "cuda_available": torch.cuda.is_available(),
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "matmul_precision": getattr(torch, "get_float32_matmul_precision", lambda: None)(),
    }
    if torch.cuda.is_available():
        devices = []
        for index in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(index)
            devices.append(
                {
                    "index": index,
                    "name": props.name,
                    "total_memory_bytes": props.total_memory,
                    "compute_capability": f"{props.major}.{props.minor}",
                    "multi_processor_count": props.multi_processor_count,
                }
            )
        record["devices"] = devices
        record["current_device"] = torch.cuda.current_device()
    return record


def git_commit() -> str | None:
    try:
        proc = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        return proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def collect() -> tuple[dict, dict]:
    """Return (structured record, raw text used as the input hash)."""
    smi = run([
        "nvidia-smi",
        "--query-gpu=index,name,uuid,driver_version,memory.total,compute_cap",
        "--format=csv,noheader",
    ])
    smi_full = run(["nvidia-smi"])
    nvcc = run(["nvcc", "--version"])
    raw_parts = [
        f"python {sys.version}",
        f"platform {platform.platform()}",
        f"executable {sys.executable}",
        json.dumps(package_versions(), sort_keys=True),
        smi.get("stdout", ""),
        smi_full.get("stdout", ""),
        nvcc.get("stdout", ""),
    ]
    raw = "\n---\n".join(part for part in raw_parts if part)

    structured = {
        "recorded_utc": None,  # filled by caller
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "platform": platform.platform(),
            "cpu_count": None,
        },
        "packages": package_versions(),
        "torch": torch_record(),
        "nvidia_smi": smi,
        "nvidia_smi_full": smi_full,
        "nvcc": nvcc,
        "repo_commit": git_commit(),
        "tools_present": {tool: shutil.which(tool) for tool in ("nvidia-smi", "nvcc", "git")},
    }
    try:
        import os

        structured["platform"]["cpu_count"] = os.cpu_count()
    except Exception:
        pass
    return structured, raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="record_host")
    parser.add_argument("--run", required=True, help="run directory, e.g. runs/<id>")
    parser.add_argument("--dry-run", action="store_true", help="print the record, write nothing")
    args = parser.parse_args(argv)

    structured, raw = collect()
    import datetime

    structured["recorded_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    blob = json.dumps(structured, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    if args.dry_run:
        print(blob)
        print(f"--- raw input sha256: {hashlib.sha256(raw.encode()).hexdigest()}")
        print(f"--- record sha256:    {hashlib.sha256(blob.encode()).hexdigest()}")
        return 0

    run_dir = Path(args.run)
    if not (run_dir / "ledger.jsonl").exists():
        print(f"{run_dir} has no ledger; freeze the run first", file=sys.stderr)
        return 1

    out = run_dir / "host.json"
    out.write_text(blob, encoding="utf-8")

    from gdkit.ledger import Ledger
    from harness.preflight import host_fingerprint

    run_id = run_dir.name
    ledger = Ledger(run_dir / "ledger.jsonl", run_id, "registered")
    entry = ledger.record(
        "host_provisioned",
        rows_before=0,
        rows_after=0,
        params={
            "file": out.name,
            "gpus": [d["name"] for d in structured["torch"].get("devices", [])],
            "torch": structured["packages"].get("torch"),
            "transformers": structured["packages"].get("transformers"),
            "cuda": structured["torch"].get("cuda_version"),
            "driver": (structured["nvidia_smi"].get("stdout", "").split(", ")[3]
                       if structured["nvidia_smi"].get("stdout") else None),
            "record_sha256": hashlib.sha256(blob.encode()).hexdigest(),
            "fingerprint": host_fingerprint(),
        },
        input_hash=hashlib.sha256(raw.encode()).hexdigest(),
        output_hash=hashlib.sha256(blob.encode()).hexdigest(),
    )
    print(json.dumps({"entry": entry["seq"], "entry_hash": entry["entry_hash"], "file": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
