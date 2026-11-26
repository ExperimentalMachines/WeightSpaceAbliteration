#!/usr/bin/env python3
"""Record the state-dict inventory the method's target list is checked against.

    python scripts/record_tensor_inventory.py --run runs/<id>

Loads the registered checkpoint with the pinned `transformers`, enumerates the residual-writing
targets the abliteration method would modify, and appends a `tensor_inventory` ledger entry.
Nothing is written to the weights and no gate is run. The inventory file is hashed as stored
bytes, so it is listed `-text` in `.gitattributes`.

This is the CPU half of admission: it needs the registered checkpoint on disk, not a GPU.
`compute_evidence` needs the GPU and is recorded separately, by the materializer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.gates import config
from harness.methods.abliteration import _targets
from harness.host import run_write_lock


def _excluded_writers(state: dict) -> dict:
    """Inventory the residual writers the method deliberately does not edit.

    The method document declares three omissions from arXiv:2406.11717 §4.1: the embedding matrix,
    positional embeddings and output biases. Recording whether they exist turns that declaration into
    checkable evidence — an absent tensor and a skipped tensor look identical from the target list.
    """
    embeddings, positional, biases = [], [], []
    for name, value in state.items():
        if name.endswith("embed_tokens.weight") or name.endswith("wte.weight"):
            embeddings.append(name)
        elif name.endswith("embed_positions.weight") or name.endswith("wpe.weight"):
            positional.append(name)
        elif name.endswith(".bias"):
            biases.append(name)
    def describe(names: list[str]) -> dict:
        return {
            "count": len(names),
            "names": sorted(names),
            "shapes": {name: list(state[name].shape) for name in sorted(names)},
        }
    return {"embedding": describe(embeddings), "positional": describe(positional), "biases": describe(biases)}


def build_inventory(
    state: dict, direction_shape, *, model: str, revision: str | None,
    transformers_version: str, torch_version: str, declared_blocks: int | None = None,
    tied_word_embeddings: bool | None = None,
) -> dict:
    """Enumerate the method's targets in a real state dict and describe them.

    Fails (raises) rather than returning a partial list when a block is unsupported, when the
    target count disagrees with the model's declared block count, or when a target's width does
    not match the direction. The inventory is the evidence that the method can run on this model.
    """
    targets = _targets(state, direction_shape)
    blocks = sorted({target.layer for target in targets})
    if declared_blocks is not None and len(blocks) != declared_blocks:
        raise ValueError(
            f"model declares {declared_blocks} blocks but {len(blocks)} carry a supported residual writer"
        )
    rows = []
    for target in targets:
        tensor = target.value
        rows.append({
            "name": target.name,
            "shape": list(tensor.shape),
            "dtype": str(tensor.dtype).removeprefix("torch."),
            "layer": target.layer,
            "kind": target.kind,
            "expert": target.expert,
        })
    edited = sum(int(tensor.numel()) for tensor in (state[row["name"]] for row in rows))
    total = sum(int(value.numel()) for value in state.values() if hasattr(value, "numel"))
    kinds: dict[str, int] = {}
    for row in rows:
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
    return {
        "model": model,
        "revision": revision,
        "transformers": transformers_version,
        "torch": torch_version,
        "direction_shape": list(direction_shape),
        "blocks": len(blocks),
        "tensor_count": len(rows),
        "kinds": dict(sorted(kinds.items())),
        "edited_parameters": edited,
        "state_dict_parameters": total,
        "edited_fraction": edited / total if total else None,
        "tied_word_embeddings": tied_word_embeddings,
        "excluded_writers": _excluded_writers(state),
        "tensors": rows,
    }


def _measurement_digest(inventory: dict) -> str:
    """Digest of what was measured, independent of when it was recorded."""
    payload = json.dumps(
        {key: inventory[key] for key in ("model", "revision", "direction_shape", "tensors", "excluded_writers")},
        sort_keys=True, ensure_ascii=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def record(run_dir: Path, inventory: dict) -> dict:
    """Write the inventory byte-exact and append the ledger entry that binds it."""
    from gdkit.ledger import Ledger

    run_dir = Path(run_dir)
    path = run_dir / "tensor_inventory.json"
    if path.exists():
        raise FileExistsError(f"{path} already exists; a recorded inventory is not replaced")
    blob = (json.dumps(inventory, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    path.write_bytes(blob)
    digest = hashlib.sha256(blob).hexdigest()
    params = {
        "path": path.name,
        "sha256": digest,
        "model": inventory["model"],
        "revision": inventory["revision"],
        "transformers": inventory["transformers"],
        "torch": inventory["torch"],
        "blocks": inventory["blocks"],
        "tensor_count": inventory["tensor_count"],
        "kinds": inventory["kinds"],
        "edited_parameters": inventory["edited_parameters"],
        "edited_fraction": inventory["edited_fraction"],
        "tied_word_embeddings": inventory["tied_word_embeddings"],
        "excluded_writers": {key: inventory["excluded_writers"][key]["count"]
                             for key in ("embedding", "positional", "biases")},
    }
    with run_write_lock(run_dir):
        ledger = Ledger(run_dir / "ledger.jsonl", run_dir.name, "registered")
        ledger.ensure_current()
        entry = ledger.record_event(
            "tensor_inventory", params=params,
            input_hash=_measurement_digest(inventory), output_hash=digest,
        )
    return {**params, "event_seq": entry["seq"], "event_hash": entry["entry_hash"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="record_tensor_inventory")
    parser.add_argument("--run", required=True)
    parser.add_argument("--dry-run", action="store_true", help="print the inventory, append nothing")
    args = parser.parse_args(argv)

    import torch
    import transformers
    from transformers import AutoModelForCausalLM

    run_dir = Path(args.run)
    cfg = config(run_dir)
    model_id = cfg["model"]["id"]
    revision = cfg["model"].get("revision")
    model = AutoModelForCausalLM.from_pretrained(
        model_id, revision=revision, dtype=torch.bfloat16, low_cpu_mem_usage=True,
    )
    state = model.state_dict()
    direction_path = run_dir / "results" / "direction.npz"
    if direction_path.exists():
        import numpy as np
        direction_shape = np.load(direction_path)["direction"].shape
    else:
        direction_shape = (len(model.model.layers) + 1, model.config.hidden_size)
    inventory = build_inventory(
        state, direction_shape,
        model=model_id, revision=revision,
        transformers_version=transformers.__version__, torch_version=torch.__version__,
        declared_blocks=len(model.model.layers),
        tied_word_embeddings=bool(getattr(model.config, "tie_word_embeddings", False)),
    )
    if args.dry_run:
        print(json.dumps(inventory, indent=2, ensure_ascii=True))
        return 0
    print(json.dumps(record(run_dir, inventory), indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
