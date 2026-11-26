#!/usr/bin/env python3
"""Measure the batch schedule a new device actually sustains, before any gate runs.

    python scripts/benchmark_inference.py --model Qwen/Qwen3.5-0.8B \
        --revision 2fc06364 --mode generate --batches 1,8,16,32,64,128

Runs on CPU as well as an accelerator, so the plumbing can be checked before the machine arrives.
Prompts are synthetic tokens drawn from a fixed seed: no split arm, no study prompt and no stored
response is read. The output is a measurement, not a claim — the timer starts after a warm-up and
the report states repeats, batch, sequence lengths and the memory counter that produced each row.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.device import report


def _prompts(tokenizer, count: int, length: int, *, seed: int = 1234) -> list[str]:
    import torch

    generator = torch.Generator().manual_seed(seed)
    ids = torch.randint(100, len(tokenizer), (count, length), generator=generator)
    return [tokenizer.decode(row.tolist(), skip_special_tokens=True) for row in ids]


def _sync() -> None:
    import torch

    if torch.cuda.is_available():
        torch.cuda.synchronize()


def _peak_mb() -> float | None:
    import torch

    if not torch.cuda.is_available():
        return None
    return round(torch.cuda.max_memory_allocated() / 2**20, 1)


def _reset_peak() -> None:
    import torch

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def measure_generate(model, tokenizer, *, batch: int, prompt_tokens: int, new_tokens: int, repeats: int) -> dict:
    import torch

    texts = _prompts(tokenizer, batch, prompt_tokens)
    enc = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=prompt_tokens)
    enc = {key: value.to(model.device) for key, value in enc.items()}
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    times, produced = [], 0
    for run in range(repeats + 1):
        _reset_peak()
        _sync()
        start = time.perf_counter()
        with torch.inference_mode():
            out = model.generate(**enc, max_new_tokens=new_tokens, do_sample=False, pad_token_id=pad)
        _sync()
        elapsed = time.perf_counter() - start
        produced = int((out != pad).sum().item()) - int(enc["input_ids"].numel())
        if run:                      # the first pass is the warm-up and is not timed
            times.append(elapsed)
        del out
    best = min(times)
    return {
        "batch": batch, "prompt_tokens": prompt_tokens, "new_tokens": new_tokens,
        "repeats": repeats, "seconds_best": round(best, 3), "seconds_median": round(statistics.median(times), 3),
        "generated_tokens": produced, "tokens_per_second": round(produced / best, 1),
        "peak_memory_mb": _peak_mb(),
    }


def measure_forward(model, tokenizer, *, batch: int, prompt_tokens: int, repeats: int) -> dict:
    import torch

    texts = _prompts(tokenizer, batch, prompt_tokens)
    enc = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=prompt_tokens)
    enc = {key: value.to(model.device) for key, value in enc.items()}
    times = []
    for run in range(repeats + 1):
        _reset_peak()
        _sync()
        start = time.perf_counter()
        with torch.inference_mode():
            model(**enc, logits_to_keep=1)
        _sync()
        elapsed = time.perf_counter() - start
        if run:
            times.append(elapsed)
    best = min(times)
    return {
        "batch": batch, "prompt_tokens": prompt_tokens, "repeats": repeats,
        "seconds_best": round(best, 3), "sequences_per_second": round(batch / best, 1),
        "peak_memory_mb": _peak_mb(),
    }


def recommend(rows: list[dict], key: str) -> int | None:
    """Smallest batch within 2% of the best measured throughput.

    A larger batch that buys nothing is memory reserved for no reason, and on a shared device memory
    is the thing that limits a rerun.
    """
    if not rows:
        return None
    best = max(row[key] for row in rows)
    for row in sorted(rows, key=lambda item: item["batch"]):
        if row[key] >= 0.98 * best:
            return row["batch"]
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="benchmark_inference")
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--dtype", default="bfloat16")
    parser.add_argument("--mode", choices=("generate", "forward"), default="generate")
    parser.add_argument("--batches", default="1,8,16,32,64,128")
    parser.add_argument("--prompt-tokens", type=int, default=256)
    parser.add_argument("--new-tokens", type=int, default=64)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--attn", default="sdpa")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    kwargs = {"revision": args.revision, "attn_implementation": args.attn}
    dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16, "float32": torch.float32}[args.dtype]
    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype, **kwargs).eval()
    if torch.cuda.is_available():
        model = model.to("cuda")

    measure = measure_generate if args.mode == "generate" else measure_forward
    rows = []
    for batch in (int(value) for value in args.batches.split(",")):
        row = measure(
            model, tokenizer, batch=batch, prompt_tokens=args.prompt_tokens,
            repeats=args.repeats, **({"new_tokens": args.new_tokens} if args.mode == "generate" else {}),
        )
        rows.append(row)
        print(json.dumps({**row, "mode": args.mode}), flush=True)

    key = "tokens_per_second" if args.mode == "generate" else "sequences_per_second"
    payload = {
        "device": report()["device"],
        "dtypes": report()["dtypes"],
        "model": args.model, "revision": args.revision, "dtype": args.dtype,
        "attn_implementation": args.attn, "mode": args.mode,
        "rows": rows, "metric": key, "recommended_batch": recommend(rows, key),
        "method": "one warm-up pass, then the stated repeats; best wall time; generated tokens counted from the output tensor",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
