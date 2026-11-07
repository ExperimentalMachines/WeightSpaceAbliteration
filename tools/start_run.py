#!/usr/bin/env python3
"""Start a gdkit run: create runs/<run_id>/ and freeze the pre-registration as entry 0.

The freeze is the first ledger entry, written before any data action. It holds the project
answers verbatim plus their sha256. `promote` and `attest` refuse a run whose answers drift
from that entry, and name the changed question.

    python tools/start_run.py --project .gdkit/project.yaml --mode registered
    python tools/start_run.py --run-id 20261107-study001
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from gdkit.interview import load_questions
from gdkit.ledger import Ledger, verify
from gdkit.prereg import answers_digest, freeze_run


def default_run_id() -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-weightspace-abliteration"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="start_run")
    parser.add_argument("--project", default=".gdkit/project.yaml")
    parser.add_argument("--questions", default="interview/questions.yaml")
    parser.add_argument("--mode", default="registered", choices=("explore", "registered"))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--model", default=None, help="model slug appended to the default run id")
    args = parser.parse_args(argv)

    run_id = args.run_id or default_run_id()
    if args.model and not args.run_id:
        run_id = f"{run_id}-{args.model}"
    run_dir = Path(args.runs_dir) / run_id
    if run_dir.exists() and any(run_dir.iterdir()):
        print(f"{run_dir} already has contents; refusing to reuse a run directory", file=sys.stderr)
        return 1
    run_dir.mkdir(parents=True, exist_ok=True)

    ledger_path = run_dir / "ledger.jsonl"
    ledger = Ledger(ledger_path, run_id, args.mode)
    try:
        entry = freeze_run(ledger, args.project, questions_data=load_questions(args.questions))
    except Exception as exc:  # PreregError, InterviewError, yaml errors
        print(f"freeze refused: {exc}", file=sys.stderr)
        return 1

    meta = {"run_id": run_id, "mode": args.mode, "model": args.model,
            "pre_registration": str(Path(args.project).as_posix())}
    (run_dir / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    count = verify(ledger_path)
    print(
        json.dumps(
            {
                "run_id": run_id,
                "run_dir": run_dir.as_posix(),
                "mode": args.mode,
                "ledger_entries": count,
                "entry_hash": entry["entry_hash"],
                "answers_sha256": entry["params"]["answers_sha256"],
                "answers_digest_now": answers_digest(entry["params"]["answers"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
