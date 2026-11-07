#!/usr/bin/env python3
"""Leakage audit between two prompt corpora: exact-normalised overlap and n-gram near-duplicates.

Normalisation catches one leakage channel (surface duplication). This tool measures that channel
exactly and the near-duplicate channel approximately, and prints both so a pre-registration can
declare a threshold instead of an assurance.

    python tools/leakage_audit.py --a advbench --b harmbench
    python tools/leakage_audit.py --a advbench --b harmbench --threshold 0.7 --top 15

Everything is deterministic: same inputs, same thresholds, same output. The exclusion list it emits
should be hashed into the run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

SOURCES = {
    "advbench": (
        "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/data/advbench/harmful_behaviors.csv",
        "goal",
        "csv",
    ),
    "harmbench": (
        "https://raw.githubusercontent.com/centerforaisafety/HarmBench/main/data/behavior_datasets/harmbench_behaviors_text_all.csv",
        "Behavior",
        "csv",
    ),
}
CACHE = Path("datasets/_cache")


def fetch(name: str) -> list[str]:
    url, column, _ = SOURCES[name]
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.csv"
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "leakage-audit/0.1"})
        path.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    return [row[column].strip() for row in rows if row.get(column)]


def normalise(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def shingles(text: str, n: int = 5) -> set[str]:
    tokens = normalise(text).split()
    if len(tokens) < n:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="leakage_audit")
    parser.add_argument("--a", default="advbench")
    parser.add_argument("--b", default="harmbench")
    parser.add_argument("--threshold", type=float, default=0.8)
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args(argv)

    a_items = fetch(args.a)
    b_items = fetch(args.b)
    print(f"{args.a}: {len(a_items)} prompts   {args.b}: {len(b_items)} prompts")

    a_norm = {normalise(x) for x in a_items}
    b_norm = {normalise(x) for x in b_items}
    exact = a_norm & b_norm
    print(f"exact-normalised overlap: {len(exact)} ({len(exact)/max(1,len(a_norm)):.1%} of {args.a})")

    sh_a = [(x, shingles(x)) for x in a_items]
    pairs: list[tuple[float, str, str]] = []
    for xa, sa in sh_a:
        for xb in b_items:
            sim = jaccard(sa, shingles(xb))
            if sim >= args.threshold:
                pairs.append((sim, xa, xb))
    pairs.sort(reverse=True)

    print(f"near-duplicates at Jaccard >= {args.threshold:.2f}: {len(pairs)} pair(s)")
    for sim, xa, xb in pairs[: args.top]:
        print(f"  {sim:.3f}  {args.a}: {xa[:80]}")
        print(f"         {args.b}: {xb[:80]}")

    record = {
        "a": args.a,
        "b": args.b,
        "a_count": len(a_items),
        "b_count": len(b_items),
        "threshold": args.threshold,
        "exact_overlap": sorted(exact),
        "exact_overlap_count": len(exact),
        "near_duplicate_count": len(pairs),
        "near_duplicates": [{"sim": round(s, 4), "a": xa, "b": xb} for s, xa, xb in pairs],
    }
    blob = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    digest = hashlib.sha256(blob).hexdigest()
    out = CACHE / f"leakage_{args.a}_{args.b}_{args.threshold}.json"
    out.write_bytes(blob + b"\n")
    print(f"\nrecord: {out}  sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
