#!/usr/bin/env python3
"""Verify every run ledger: chain integrity, pre-registration first, no answer drift.

    python scripts/verify_ledger.py
    python scripts/verify_ledger.py --project .gdkit/project.yaml

Exit 0 when every ledger verifies and matches the project file, 1 otherwise. This is the check CI
runs, and the same one a reader can run after cloning.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys

from gdkit.ledger import verify
from gdkit.prereg import check_answers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verify_ledger")
    parser.add_argument("--runs", default="runs/*/ledger.jsonl")
    parser.add_argument("--project", default=".gdkit/project.yaml")
    args = parser.parse_args(argv)

    paths = sorted(glob.glob(args.runs))
    if not paths:
        print(f"no ledgers matched {args.runs}", file=sys.stderr)
        return 1

    failed = False
    for path in paths:
        count = verify(path)
        entries = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
        if entries[0].get("op") != "preregistration":
            print(f"{path}: first entry is {entries[0].get('op')!r}, not 'preregistration'", file=sys.stderr)
            failed = True
        drift = check_answers(entries, args.project)
        lookups = sum(1 for e in entries if e.get("op") == "paper_lookup")
        print(f"{path}: {count} entries, {lookups} paper lookups, drift={drift or 'clean'}")
        if drift:
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
