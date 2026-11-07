#!/usr/bin/env python3
"""Semantic duplicate audit: cluster prompts by embedding cosine, not by string.

This is the deep-curation instrument. It answers "how many distinct behaviours are in these two
corpora" and "which items must be excluded so the derivation set and the evaluation set share no
behaviour, only wording".

    python tools/semantic_dedup.py --a advbench --b harmbench --threshold 0.85
    python tools/semantic_dedup.py --calibrate xstest      # false-negative rate on labelled twins

Model and threshold are part of the measurement, so both are written into the record with a sha256.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import urllib.request
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer

SOURCES = {
    "advbench": (
        "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/data/advbench/harmful_behaviors.csv",
        "goal",
    ),
    "harmbench": (
        "https://raw.githubusercontent.com/centerforaisafety/HarmBench/main/data/behavior_datasets/harmbench_behaviors_text_all.csv",
        "Behavior",
    ),
}
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CACHE = Path("datasets/_cache")


def fetch_csv(name: str) -> list[str]:
    url, column = SOURCES[name]
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.csv"
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "semantic-dedup/0.1"})
        path.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    return [row[column].strip() for row in rows if row.get(column)]


def xstest() -> tuple[list[str], list[str]]:
    import time

    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / "xstest_rows.json"
    if cached.exists():
        items = json.loads(cached.read_text(encoding="utf-8"))
    else:
        items = []
        for off in range(0, 450, 100):
            url = (
                "https://datasets-server.huggingface.co/rows?dataset=Paul%2FXSTest"
                f"&config=default&split=train&offset={off}&length=100"
            )
            for attempt in range(4):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "semantic-dedup/0.1"})
                    payload = json.loads(urllib.request.urlopen(req, timeout=40).read())
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    time.sleep(3 * (attempt + 1))
            items += [r["row"] for r in payload["rows"]]
            if len(payload["rows"]) < 100:
                break
        cached.write_text(json.dumps(items), encoding="utf-8")
    safe = [i["prompt"] for i in items if str(i.get("label", "")).lower() == "safe"]
    bad = [i["prompt"] for i in items if str(i.get("label", "")).lower() == "unsafe"]
    return safe, bad


def embed(texts: list[str], batch: int = 64) -> torch.Tensor:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModel.from_pretrained(MODEL).to(device).eval()
    out: list[torch.Tensor] = []
    with torch.no_grad():
        for start in range(0, len(texts), batch):
            chunk = texts[start : start + batch]
            enc = tokenizer(chunk, padding=True, truncation=True, max_length=128, return_tensors="pt").to(device)
            hidden = model(**enc).last_hidden_state
            mask = enc["attention_mask"].unsqueeze(-1).float()
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            out.append(torch.nn.functional.normalize(pooled, dim=-1).cpu())
    return torch.cat(out)


class Union:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def calibrate() -> int:
    safe, bad = xstest()
    with torch.no_grad():
        se = embed(safe)
        be = embed(bad)
        sim = se @ be.T
        best = sim.max(dim=1)
    for thr in (0.60, 0.70, 0.75, 0.80, 0.85, 0.90):
        recall = (best.values >= thr).float().mean().item()
        print(f"threshold {thr:.2f}: twin detected for {recall:.1%} of {len(safe)} safe prompts")
    print("\nSample closest pairs:")
    order = torch.argsort(best.values, descending=True)[:5]
    for i in order.tolist():
        print(f"  {best.values[i].item():.3f}  {safe[i]}")
        print(f"           {bad[best.indices[i].item()]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="semantic_dedup")
    parser.add_argument("--a", default="advbench")
    parser.add_argument("--b", default="harmbench")
    parser.add_argument("--threshold", type=float, default=0.85)
    parser.add_argument("--calibrate", choices=("xstest",), default=None)
    args = parser.parse_args(argv)

    if args.calibrate:
        return calibrate()

    a_items = fetch_csv(args.a)
    b_items = fetch_csv(args.b)
    print(f"{args.a}: {len(a_items)}  {args.b}: {len(b_items)}  model: {MODEL}")

    with torch.no_grad():
        ea = embed(a_items)
        eb = embed(b_items)
        sim = ea @ eb.T

    hits = sim >= args.threshold
    pairs = [
        {"a": a_items[i], "b": b_items[j], "cos": round(sim[i, j].item(), 4)}
        for i, j in hits.nonzero().tolist()
    ]
    pairs.sort(key=lambda p: -p["cos"])

    # Cluster across the union of both corpora so a chain of paraphrases collapses to one behaviour.
    texts = a_items + b_items
    with torch.no_grad():
        e = embed(texts)
        full = e @ e.T
    union = Union(len(texts))
    idx = (full >= args.threshold).nonzero().tolist()
    for i, j in idx:
        if i != j:
            union.union(i, j)
    roots: dict[int, list[int]] = {}
    for i in range(len(texts)):
        roots.setdefault(union.find(i), []).append(i)
    cross = [r for r in roots.values() if any(i < len(a_items) for i in r) and any(i >= len(a_items) for i in r)]

    record = {
        "model": MODEL,
        "threshold": args.threshold,
        "a": args.a,
        "b": args.b,
        "a_count": len(a_items),
        "b_count": len(b_items),
        "cross_corpus_pairs": len(pairs),
        "pairs": pairs,
        "cross_corpus_clusters": len(cross),
        "unique_behaviours": len(roots),
        "excluded_a_items": sorted({p["a"] for p in pairs}),
        "excluded_b_items": sorted({p["b"] for p in pairs}),
    }
    blob = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    digest = hashlib.sha256(blob).hexdigest()
    out = CACHE / f"semantic_{args.a}_{args.b}_{args.threshold}.json"
    out.write_bytes(blob + b"\n")

    print(f"pairs at cos >= {args.threshold}: {len(pairs)}")
    print(f"cross-corpus clusters: {len(cross)}   unique behaviours across both: {len(roots)}")
    for p in pairs[:10]:
        print(f"  {p['cos']:.3f}  {p['a'][:70]}")
        print(f"         {p['b'][:70]}")
    print(f"\nrecord: {out}  sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
