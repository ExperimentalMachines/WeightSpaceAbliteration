#!/usr/bin/env python3
"""Replay selected pwc lookups into a run's ledger, so provenance is recorded, not typed.

Each call becomes one ``op = "paper_lookup"`` ledger entry carrying the request sha256, the
response sha256, the pwc version, the paper identity fields and the volatile fields with the
call time. The raw JSON response is written under ``<run>/paper_lookups/NNNN.json``.

    python tools/record_lookups.py --run-id 20261107T101500Z-weightspace-abliteration \
        --queries datasets/pwc_queries.json

Query file: a JSON list of argument lists, without ``--json`` (gdkit appends it):

    [["search", "refusal direction activation", "--limit", "8"],
     ["paper", "info", "2406.11717"]]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gdkit.ledger import Ledger
from gdkit.pwc_lookup import lookup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="record_lookups")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--queries", required=True)
    args = parser.parse_args(argv)

    run_dir = Path(args.runs_dir) / args.run_id
    ledger_path = run_dir / "ledger.jsonl"
    if not ledger_path.exists():
        raise SystemExit(f"{ledger_path} does not exist; start the run first")

    ledger = Ledger(ledger_path, args.run_id, "registered")
    queries = json.loads(Path(args.queries).read_text(encoding="utf-8"))
    for query in queries:
        params = lookup(ledger, run_dir, list(query))
        titles = [paper.get("title") for paper in params.get("papers", [])]
        print(json.dumps({"status": params.get("status"), "args": query,
                          "papers": len(titles), "first": titles[0] if titles else None}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
