from __future__ import annotations

import pytest
import torch

from harness.methods.abliteration import Abliteration

WIDTH, INTER, ATTN_IN, EXPERTS = 3, 4, 5, 2


class Fake:
    def __init__(self, tensors: dict[str, torch.Tensor]) -> None:
        self._tensors = tensors

    def state_dict(self) -> dict[str, torch.Tensor]:
        return self._tensors


def directions() -> torch.Tensor:
    return torch.eye(3)


def linear(layer: int) -> dict[str, torch.Tensor]:
    return {f"model.layers.{layer}.linear_attn.out_proj.weight": torch.randn(WIDTH, ATTN_IN)}


def full(layer: int) -> dict[str, torch.Tensor]:
    return {f"model.layers.{layer}.self_attn.o_proj.weight": torch.randn(WIDTH, ATTN_IN)}


def mlp(layer: int) -> dict[str, torch.Tensor]:
    return {f"model.layers.{layer}.mlp.down_proj.weight": torch.randn(WIDTH, INTER)}


def fused(layer: int) -> dict[str, torch.Tensor]:
    return {f"model.layers.{layer}.mlp.experts.down_proj": torch.randn(EXPERTS, WIDTH, INTER)}


def model(*parts: dict[str, torch.Tensor]) -> Fake:
    tensors = {"model.embed_tokens.weight": torch.randn(10, WIDTH)}
    for part in parts:
        tensors.update(part)
    return Fake(tensors)


def test_qwen35_style_hybrid_blocks_are_projected():
    """Block 0 is linear attention, block 1 full attention: the layout of Qwen3.5-0.8B (18 of 24 blocks are linear). This used to raise."""
    torch.manual_seed(1)
    m = model(linear(0), mlp(0), full(1), mlp(1))
    candidate, manifest = Abliteration().apply(m, directions())

    for layer, name in ((0, "model.layers.0.linear_attn.out_proj.weight"), (1, "model.layers.1.self_attn.o_proj.weight")):
        torch.testing.assert_close(directions()[layer + 1] @ candidate[name], torch.zeros(ATTN_IN), atol=1e-6, rtol=0)
        assert not torch.equal(candidate[name], m.state_dict()[name])
    assert {t["kind"] for t in manifest["targets"]} == {"linear_attn.out_proj", "self_attn.o_proj", "mlp.down_proj"}
    assert manifest["summary"]["matrices_changed"] == 4
    assert torch.equal(candidate["model.embed_tokens.weight"], m.state_dict()["model.embed_tokens.weight"])


def test_linear_attention_with_expert_blocks_and_scale():
    torch.manual_seed(2)
    m = model(linear(0), fused(0), full(1), fused(1))
    half, manifest = Abliteration(scale=0.5).apply(m, directions())
    name, r = "model.layers.0.linear_attn.out_proj.weight", directions()[1]
    torch.testing.assert_close(r @ half[name], 0.5 * (r @ m.state_dict()[name]), atol=1e-6, rtol=0)
    assert manifest["params"] == {"scale": 0.5}


def test_a_block_with_both_attention_writers_is_rejected():
    both = linear(0) | full(0) | mlp(0)
    with pytest.raises(ValueError, match="target mismatch") as info:
        Abliteration().apply(model(both, full(1), mlp(1)), directions())
    assert "unexpected" in str(info.value)


def test_a_block_with_no_attention_writer_still_fails_closed():
    with pytest.raises(ValueError, match="target mismatch") as info:
        Abliteration().apply(model(mlp(0), full(1), mlp(1)), directions())
    assert "linear_attn.out_proj" in str(info.value)                     # the message names both accepted families


def test_linear_attention_weight_of_the_wrong_width_is_rejected():
    bad = {"model.layers.0.linear_attn.out_proj.weight": torch.randn(4, ATTN_IN)}      # hidden width 4, direction width 3
    with pytest.raises(ValueError, match="writes 4 features"):
        Abliteration().apply(model(bad, mlp(0), full(1), mlp(1)), directions())
