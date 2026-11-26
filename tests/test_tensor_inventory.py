from __future__ import annotations

import pytest
import torch

from scripts.record_tensor_inventory import build_inventory

HIDDEN, INTER = 3, 4


def state(blocks: int = 2) -> dict[str, torch.Tensor]:
    tensors = {"model.embed_tokens.weight": torch.zeros(7, HIDDEN, dtype=torch.bfloat16)}
    for layer in range(blocks):
        writer = "self_attn.o_proj" if layer == 0 else "linear_attn.out_proj"
        tensors[f"model.layers.{layer}.{writer}.weight"] = torch.zeros(HIDDEN, HIDDEN, dtype=torch.bfloat16)
        tensors[f"model.layers.{layer}.mlp.down_proj.weight"] = torch.zeros(HIDDEN, INTER, dtype=torch.bfloat16)
    return tensors


def inventory(blocks: int = 2, declared: int | None = None) -> dict:
    return build_inventory(
        state(blocks), (blocks + 1, HIDDEN),
        model="Qwen/Qwen3.5-0.8B", revision="2fc06364",
        transformers_version="5.22.2", torch_version="2.15.0",
        declared_blocks=blocks if declared is None else declared,
    )


def test_hybrid_blocks_are_enumerated_in_order():
    built = inventory()
    assert [row["name"] for row in built["tensors"]] == [
        "model.layers.0.self_attn.o_proj.weight",
        "model.layers.0.mlp.down_proj.weight",
        "model.layers.1.linear_attn.out_proj.weight",
        "model.layers.1.mlp.down_proj.weight",
    ]
    assert built["blocks"] == 2
    assert built["kinds"] == {"linear_attn.out_proj": 1, "mlp.down_proj": 2, "self_attn.o_proj": 1}
    assert built["tensors"][0]["shape"] == [HIDDEN, HIDDEN]
    assert built["tensors"][0]["dtype"] == "bfloat16"


def test_edited_fraction_counts_only_targets():
    built = inventory()
    edited = 2 * (HIDDEN * HIDDEN + HIDDEN * INTER)
    assert built["edited_parameters"] == edited
    assert built["state_dict_parameters"] == edited + 7 * HIDDEN
    assert built["edited_fraction"] == pytest.approx(edited / (edited + 7 * HIDDEN))


def test_excluded_writers_record_what_exists_and_not_what_is_merely_omitted():
    built = inventory()
    excluded = built["excluded_writers"]
    assert excluded["embedding"]["count"] == 1
    assert excluded["embedding"]["names"] == ["model.embed_tokens.weight"]
    assert excluded["embedding"]["shapes"]["model.embed_tokens.weight"] == [7, HIDDEN]
    assert excluded["positional"]["count"] == 0
    assert excluded["biases"]["count"] == 0


def test_bias_and_tied_embedding_flag_are_recorded_when_present():
    tensors = state()
    tensors["model.layers.0.self_attn.q_proj.bias"] = torch.zeros(HIDDEN, dtype=torch.bfloat16)
    built = build_inventory(
        tensors, (3, HIDDEN), model="m", revision=None,
        transformers_version="5.22.2", torch_version="2.15.0", declared_blocks=2,
        tied_word_embeddings=True,
    )
    assert built["excluded_writers"]["biases"]["count"] == 1
    assert built["excluded_writers"]["biases"]["names"] == ["model.layers.0.self_attn.q_proj.bias"]
    assert built["tied_word_embeddings"] is True


def test_declared_block_mismatch_is_refused():
    with pytest.raises(ValueError, match="declares 3 blocks"):
        inventory(blocks=2, declared=3)


def test_block_without_mlp_writer_is_refused():
    tensors = state()
    del tensors["model.layers.1.mlp.down_proj.weight"]
    with pytest.raises(ValueError, match="layer 1 target mismatch"):
        build_inventory(
            tensors, (3, HIDDEN), model="m", revision=None,
            transformers_version="5.22.2", torch_version="2.15.0", declared_blocks=2,
        )
