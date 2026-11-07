#!/usr/bin/env python3
"""Materialise the pre-registered split and hash it.

Reads the pinned corpora, applies the exclusions frozen in .gdkit/project.yaml, writes one JSONL
per arm under runs/<run_id>/splits/, and a manifest with the sha256 of every file plus the
exclusion lists. Nothing here runs a model.

Arms: derivation, harmless, primary, large, enriched, treadon, zaakirio, harmbench_val,
over_refusal, probe_pos, probe_neg, probe_heldout.

    python harness/build_splits.py --run-id 20261107T112342Z-weightspace-abliteration
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer

CACHE = Path("datasets/_cache")
MODEL = "BAAI/bge-small-en-v1.5"
MODEL_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
THRESHOLD = 0.80
UA = {"User-Agent": "gdkit-split-builder/0.2"}

# HarmBench categories reserved for probe training, and the two held out from it.
PROBE_TRAIN_CATEGORIES = (
    "copyright",
    "illegal",
    "cybercrime_intrusion",
    "harassment_bullying",
    "harmful",
)
PROBE_HELDOUT_CATEGORIES = ("chemical_biological", "misinformation_disinformation")


def get(url: str, timeout: int = 120) -> bytes:
    """Fetch with backoff. The datasets-server rate-limits aggressively (429)."""
    for attempt in range(6):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except urllib.error.HTTPError as exc:
            if attempt == 5:
                raise
            wait = 30 if exc.code == 429 else 4 * (attempt + 1)
            time.sleep(wait)
        except Exception:
            if attempt == 5:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", str(text).lower())).strip()


def hf_rows(dataset: str, split: str, limit: int | None = None, config: str = "default") -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", f"{dataset}_{config}_{split}_{limit or 'all'}".lower())
    cached = CACHE / f"rows_{slug}.json"
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))
    out: list[dict] = []
    offset = 0
    while True:
        take = 100
        payload = json.loads(
            get(
                "https://datasets-server.huggingface.co/rows"
                f"?dataset={urllib.parse.quote(dataset, safe='')}&config={config}"
                f"&split={split}&offset={offset}&length={take}"
            )
        )
        rows = payload.get("rows", [])
        out += [r["row"] for r in rows]
        if len(rows) < take or (limit and len(out) >= limit):
            break
        offset += take
    out = out[:limit] if limit else out
    cached.write_text(json.dumps(out), encoding="utf-8")
    return out


class Embedder:
    """The exclusion instrument. Model, revision, truncation and threshold are all part of it."""

    def __init__(self) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tok = AutoTokenizer.from_pretrained(MODEL, revision=MODEL_REVISION)
        self.model = AutoModel.from_pretrained(MODEL, revision=MODEL_REVISION).to(self.device).eval()

    @torch.no_grad()
    def __call__(self, texts: list[str]) -> torch.Tensor:
        chunks = []
        for i in range(0, len(texts), 128):
            batch = self.tok(texts[i : i + 128], padding=True, truncation=True,
                             max_length=128, return_tensors="pt").to(self.device)
            hidden = self.model(**batch).last_hidden_state
            mask = batch["attention_mask"].unsqueeze(-1).float()
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            chunks.append(torch.nn.functional.normalize(pooled, dim=-1).cpu())
        return torch.cat(chunks)


def load_advbench() -> list[dict]:
    rows = list(csv.DictReader(open(CACHE / "advbench_pinned.csv", encoding="utf-8")))
    return [{"id": f"advbench-{i:04d}", "text": r["goal"].strip(), "source": "advbench"} for i, r in enumerate(rows)]


def load_harmbench(split: str) -> list[dict]:
    url = ("https://raw.githubusercontent.com/centerforaisafety/HarmBench/"
           f"8e1604d1171fe8a48d8febecd22f600e462bdcdd/data/behavior_datasets/harmbench_behaviors_text_{split}.csv")
    rows = list(csv.DictReader(io.StringIO(get(url).decode())))
    return [
        {"id": r["BehaviorID"], "text": r["Behavior"].strip(), "source": f"harmbench_{split}",
         "category": r["SemanticCategory"]}
        for r in rows
    ]


def load_salad() -> list[dict]:
    base = json.loads((CACHE / "salad_base.json").read_text(encoding="utf-8"))
    return [
        {"id": f"salad-{r['qid']}", "text": r["question"].strip(), "source": "salad",
         "category": r.get("1-category")}
        for r in base if r.get("source") != "HH-harmless"
    ]


def load_enriched() -> list[dict]:
    import pyarrow.parquet as pq
    out: list[dict] = []
    for name in ("train", "test"):
        blob = get("https://huggingface.co/datasets/Bahushruth/abliteration-harmful-enriched"
                   f"/resolve/main/data/{name}-00000-of-00001.parquet")
        table = pq.read_table(io.BytesIO(blob))
        for i, text in enumerate(table.column("text").to_pylist()):
            if text:
                out.append({"id": f"enriched-{name}-{i:05d}", "text": text.strip(), "source": "enriched"})
    return out


def load_harmless(limit: int) -> list[dict]:
    rows = hf_rows("mlabonne/harmless_alpaca", "train", limit=limit)
    return [{"id": f"harmless-{i:04d}", "text": r["text"].strip(), "source": "harmless_alpaca"}
            for i, r in enumerate(rows)]


def load_xstest_safe() -> list[dict]:
    cached = CACHE / "xstest_rows.json"
    if cached.exists():
        items = json.loads(cached.read_text(encoding="utf-8"))
    else:
        items = hf_rows("Paul/XSTest", "train", limit=450)
        cached.write_text(json.dumps(items), encoding="utf-8")
    return [
        {"id": f"xstest-{i:03d}", "text": r["prompt"].strip(), "source": "xstest_safe"}
        for i, r in enumerate(items) if str(r.get("label", "")).lower() == "safe"
    ]


def load_orbench() -> list[dict]:
    rows = hf_rows("bench-llm/or-bench", "train", config="or-bench-hard-1k")
    return [{"id": f"orbench-{i:04d}", "text": r["prompt"].strip(), "source": "or_bench_hard"}
            for i, r in enumerate(rows)]


def write_arm(path: Path, rows: list[dict]) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = ("\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows) + "\n").encode()
    path.write_bytes(blob)
    return {"path": path.as_posix(), "count": len(rows), "sha256": hashlib.sha256(blob).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_splits")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--runs-dir", default="runs")
    args = parser.parse_args(argv)

    run_dir = Path(args.runs_dir) / args.run_id
    splits_dir = run_dir / "splits"
    if not (run_dir / "ledger.jsonl").exists():
        print(f"{run_dir} has no ledger; freeze the run first", file=sys.stderr)
        return 1

    adv = load_advbench()
    hb_test = load_harmbench("test")
    hb_val = load_harmbench("val")
    salad = load_salad()
    enriched = load_enriched()
    treadon = [{"id": f"treadon-{i:03d}", "text": r["prompt"].strip(), "source": "treadon",
                "category": r.get("category")}
               for i, r in enumerate(hf_rows("treadon/abliteration-eval", "harmful"))]
    zaakirio = [{"id": f"zaakirio-{i:04d}", "text": r["text"].strip(), "source": "zaakirio"}
                for i, r in enumerate(hf_rows("zaakirio/infosec_harmful_behaviors", "train")
                                      + hf_rows("zaakirio/infosec_harmful_behaviors", "test"))]
    xstest = load_xstest_safe()
    orbench = load_orbench()

    print(f"loaded: adv {len(adv)} | hb test {len(hb_test)} | salad {len(salad)} | "
          f"enriched {len(enriched)} | treadon {len(treadon)} | zaakirio {len(zaakirio)} | "
          f"xstest {len(xstest)} | orbench {len(orbench)}")

    emb = Embedder()
    A = emb([r["text"] for r in adv])
    T = emb([r["text"] for r in hb_test])

    def collides(rows: list[dict], ref: torch.Tensor) -> set[str]:
        if not rows:
            return set()
        Q = emb([r["text"] for r in rows])
        hits = (Q @ ref.T).max(1).values >= THRESHOLD
        return {rows[i]["id"] for i in hits.nonzero().flatten().tolist()}

    adv_drop = collides(adv, T)
    hb_drop = collides(hb_test, A)
    salad_drop = collides(salad, torch.cat([A, T]))
    treadon_drop = collides(treadon, torch.cat([A, T]))
    zaakirio_drop = collides(zaakirio, torch.cat([A, T]))
    exact_adv = {norm(r["text"]) for r in adv}
    enriched_drop = {r["id"] for r in enriched if norm(r["text"]) in exact_adv}

    derivation = [r for r in adv if r["id"] not in adv_drop]
    primary = [r for r in hb_test if r["id"] not in hb_drop]

    arms = {
        "derivation": derivation,
        "harmless": load_harmless(len(derivation)),
        "primary": primary,
        "large": [r for r in salad if r["id"] not in salad_drop],
        "enriched": [r for r in enriched if r["id"] not in enriched_drop],
        "treadon": [r for r in treadon if r["id"] not in treadon_drop],
        "zaakirio": [r for r in zaakirio if r["id"] not in zaakirio_drop],
        "harmbench_val": hb_val,
        "over_refusal": xstest + orbench,
        "probe_neg": xstest + orbench,
        "probe_pos": [r for r in primary if r.get("category") in PROBE_TRAIN_CATEGORIES],
        "probe_heldout": [r for r in primary if r.get("category") in PROBE_HELDOUT_CATEGORIES],
    }

    manifest = {
        "run_id": args.run_id,
        "threshold": THRESHOLD,
        "embedding_model": MODEL,
        "embedding_revision": MODEL_REVISION,
        "truncation": 128,
        "exclusions": {
            "advbench": sorted(adv_drop),
            "harmbench_test": sorted(hb_drop),
            "salad": sorted(salad_drop),
            "enriched": sorted(enriched_drop),
            "treadon": sorted(treadon_drop),
            "zaakirio": sorted(zaakirio_drop),
        },
        "arms": {},
    }
    for name, rows in arms.items():
        manifest["arms"][name] = write_arm(splits_dir / f"{name}.jsonl", rows)

    manifest["exclusions_sha256"] = hashlib.sha256(
        json.dumps(manifest["exclusions"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    (splits_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    for name, info in manifest["arms"].items():
        print(f"  {name:16s} {info['count']:6d}  {info['sha256'][:16]}")
    print(f"exclusions sha256: {manifest['exclusions_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
