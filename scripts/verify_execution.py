#!/usr/bin/env python3
"""Read-only execution audit; never repairs receipts or collects the auditor's host."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Support direct script execution without requiring an editable installation.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.execution import verify_execution


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True, help="absolute path or path relative to --run")
    parser.add_argument("--release", type=Path, help="available immutable archived release snapshot")
    parser.add_argument("--source", type=Path, help="optionally compare current local source to --release")
    parser.add_argument("--require-current", action="store_true", help="also refuse a valid but stale receipt")
    args = parser.parse_args(argv)
    if args.source is not None and args.release is None:
        parser.error("--source requires --release")
    receipt = args.receipt if args.receipt.is_absolute() else args.run / args.receipt
    report = verify_execution(args.run, receipt, release_dir=args.release, source_root=args.source)
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["validity"] == "valid" and (not args.require_current or report["currentness"] == "current") else 1


if __name__ == "__main__":
    raise SystemExit(main())
