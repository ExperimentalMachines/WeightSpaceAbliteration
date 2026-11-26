#!/usr/bin/env python3
"""Re-generate a frozen sample on this device and compare it with the stored parent outputs.

    python scripts/check_device_equivalence.py --run runs/<id> --arm primary --limit 16

The study compares a candidate against a parent measured on one machine. Moving to another vendor is a
change to the measurement instrument — bf16 attention kernels and BLAS libraries differ — so before any
new number is comparable, the same prompts must produce the same greedy generations. This script reads
an existing arm and its stored responses, regenerates a deterministic sample, and reports how far the
outputs moved. It writes nothing and is not a gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.device import report


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]


def sample(rows: list[dict], limit: int) -> list[dict]:
    """Deterministic, not alphabetical: order by the digest of the item id."""
    return sorted(rows, key=lambda row: hashlib.sha256(str(row["id"]).encode()).hexdigest())[:limit]


def _first_divergence(left: str, right: str) -> int | None:
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return index
    return None if len(left) == len(right) else min(len(left), len(right))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_device_equivalence")
    parser.add_argument("--run", required=True)
    parser.add_argument("--arm", default="primary")
    parser.add_argument("--limit", type=int, default=16)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--max-new-tokens", type=int, default=None)
    parser.add_argument("--min-match", type=float, default=1.0)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    run_dir = Path(args.run)
    cfg = json.loads((run_dir / "harness.json").read_text(encoding="utf-8"))
    split_rows = _rows(run_dir / "splits" / f"{args.arm}.jsonl")
    stored_rows = _rows(run_dir / "results" / f"refusal_{args.arm}.jsonl")
    stored = {row["id"]: row.get("response", "") for row in stored_rows}
    chosen = [row for row in sample(split_rows, args.limit) if row["id"] in stored]
    if not chosen:
        raise SystemExit("no sampled prompt has a stored response; wrong arm or run")

    from harness.gates import _load_model
    from harness.judge_fix import generate_length_sorted

    model, tokenizer = _load_model(
        cfg["model"]["id"], revision=cfg["model"].get("revision"),
        dtype=cfg["model"].get("dtype", "bfloat16"),
    )
    new_tokens = args.max_new_tokens or cfg["model"].get("max_new_tokens", 256)
    regenerated = generate_length_sorted(
        model, tokenizer, [row["text"] for row in chosen],
        max_new_tokens=new_tokens, thinking=cfg["model"].get("thinking", False), batch=args.batch,
    )

    rows, exact = [], 0
    for row, text in zip(chosen, regenerated, strict=True):
        old = stored[row["id"]]
        same = text == old
        exact += same
        rows.append({
            "id": row["id"], "exact": same,
            "first_divergence": _first_divergence(old, text),
            "stored_chars": len(old), "regenerated_chars": len(text),
        })
    rate = exact / len(rows)
    payload = {
        "run": run_dir.name, "arm": args.arm, "device": report()["device"],
        "model": cfg["model"]["id"], "revision": cfg["model"].get("revision"),
        "dtype": cfg["model"].get("dtype", "bfloat16"), "max_new_tokens": new_tokens,
        "batch": args.batch, "sampled": len(rows), "exact_matches": exact,
        "exact_match_rate": round(rate, 4), "min_match": args.min_match,
        "rows": rows,
        "reading": "exact string equality of greedy generations against the stored arm; a miss means the device or library changed the tokens, not that either output is wrong",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if rate >= args.min_match else 2


if __name__ == "__main__":
    raise SystemExit(main())
