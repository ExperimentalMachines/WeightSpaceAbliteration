#!/usr/bin/env python3
"""Append an immutable canonical host session without replacing historical evidence.

    python scripts/record_host.py --run runs/<fresh-linked-id>
    python scripts/record_host.py --run <temporary-run> --probe "python --version"

No torch/GPU library is imported. Add explicit probe commands when appropriate;
full records and exact probe streams are private files below hosts/. The default
records installed package metadata and CPU/Python/platform identity only.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gdkit.host import HostError, host_summary
from gdkit.ledger import LedgerError
from harness.artifact_guard import ArtifactConflict
from harness.host import collect_session_host, record_session_host

PACKAGES = (
    "torch", "transformers", "numpy", "pyarrow", "pyyaml", "lm-eval", "gdkit",
    "accelerate", "sentence-transformers", "datasets", "vllm", "tiktoken", "sentencepiece", "protobuf",
)

# Only the tool that exists on this machine is recorded, so an absent vendor never fails
# --require-probes. AMD and NVIDIA queries are kept side by side: the study is vendor-neutral,
# and which of these ran is itself part of the host record.
VENDOR_PROBES = {
    "nvidia-smi": ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
    "amd-smi": ["amd-smi", "static", "--asic", "--bus", "--board", "--json"],
    "rocm-smi": ["rocm-smi", "--showproductname", "--showdriverversion", "--json"],
}


def _vendor_probes() -> list[list[str]]:
    """GPU tooling that is actually installed; recorded, not assumed."""
    import shutil

    return [list(command) for tool, command in VENDOR_PROBES.items() if shutil.which(tool)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="record_host")
    parser.add_argument("--run", required=True, help="fresh linked run directory (never migrates a legacy run)")
    parser.add_argument("--package", action="append", default=[], help="additional package metadata to record")
    parser.add_argument("--probe", action="append", default=[], help="quoted command, parsed without a shell")
    parser.add_argument("--require-probes", action="store_true", help="refuse if no probe or any probe fails")
    parser.add_argument("--dry-run", action="store_true", help="collect and print only the public summary; write nothing")
    args = parser.parse_args(argv)
    try:
        probes = [*_vendor_probes(), *(shlex.split(command) for command in args.probe)]
        packages = [*PACKAGES, *args.package]
        if args.dry_run:
            full, _ = collect_session_host(packages=packages, probes=probes)
            if args.require_probes and (not probes or any(not probe["available"] for probe in full["probes"])):
                raise ArtifactConflict("required host probes are missing or failed")
            result = {"dry_run": True, "summary": host_summary(full), "limitations": full["collector_limitations"]}
        else:
            result = record_session_host(
                Path(args.run), packages=packages, probes=probes, require_probes=args.require_probes,
            )
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0
    except (ArtifactConflict, LedgerError, HostError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
