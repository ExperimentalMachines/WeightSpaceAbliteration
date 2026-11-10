from __future__ import annotations

import pytest
import torch

from harness.methods.abliteration import Abliteration

WIDTH, INTER, ATTN_IN, EXPERTS = 3, 4, 5, 3


class Fake:
    """Stands in for a model: apply() only needs state_dict()."""

    def __init__(self, tensors: dict[str, torch.Tensor]) -> None:
        self._tensors = tensors

    def state_dict(self) -> dict[str, torch.Tensor]:
        return self._tensors


def directions() -> torch.Tensor:
    return torch.eye(3)            # blocks 0 and 1 use e1 and e2; index 0 is the embedding output


def attn(layer: int) -> dict[str, torch.Tensor]:
    return {f"model.layers.{layer}.self_attn.o_proj.weight": torch.randn(WIDTH, ATTN_IN)}


def dense(layer: int) -> dict[str, torch.Tensor]:
    return attn(layer) | {f"model.layers.{layer}.mlp.down_proj.weight": torch.randn(WIDTH, INTER)}


def per_expert(layer: int, n: int = EXPERTS) -> dict[str, torch.Tensor]:
    out = attn(layer) | {f"model.layers.{layer}.mlp.gate.weight": torch.randn(n, WIDTH)}
    for e in range(n):
        out[f"model.layers.{layer}.mlp.experts.{e}.down_proj.weight"] = torch.randn(WIDTH, INTER)
    return out


def fused(layer: int, n: int = EXPERTS) -> dict[str, torch.Tensor]:
    return attn(layer) | {f"model.layers.{layer}.mlp.gate.weight": torch.randn(n, WIDTH),
                          f"model.layers.{layer}.mlp.experts.down_proj": torch.randn(n, WIDTH, INTER)}


def model(*layers: dict[str, torch.Tensor]) -> Fake:
    tensors = {"model.embed_tokens.weight": torch.randn(10, WIDTH)}
    for layer in layers:
        tensors.update(layer)
    return Fake(tensors)


# ---- scale ---------------------------------------------------------------------------------------------------------------

def test_scale_changes_the_edit_and_the_manifest_reports_the_value_used():
    torch.manual_seed(1)
    m = model(dense(0), dense(1))
    full, manifest_full = Abliteration().apply(m, directions())
    half, manifest_half = Abliteration(scale=0.5).apply(m, directions())

    assert manifest_full["params"] == {"scale": 1.0} and manifest_half["params"] == {"scale": 0.5}
    name = "model.layers.0.self_attn.o_proj.weight"
    r = directions()[1]
    original = m.state_dict()[name]
    assert not torch.equal(full[name], half[name])                      # the regression: scale used to be inert
    torch.testing.assert_close(r @ full[name], torch.zeros(ATTN_IN), atol=1e-6, rtol=0)
    torch.testing.assert_close(r @ half[name], 0.5 * (r @ original), atol=1e-6, rtol=0)


@pytest.mark.parametrize("bad", [0, 0.0, -0.5, 1.0001, float("nan"), float("inf"), True, "1.0", None])
def test_scale_outside_zero_to_one_is_rejected_instead_of_silently_doing_something_else(bad):
    with pytest.raises(ValueError, match="scale must be"):
        Abliteration(scale=bad)


def test_default_spec_stays_at_full_strength_and_instances_do_not_leak_into_it():
    Abliteration(scale=0.25)
    assert Abliteration.spec.params == {"scale": 1.0}
    assert Abliteration().spec.params == {"scale": 1.0} and Abliteration(scale=0.25).spec.params == {"scale": 0.25}


# ---- expert layouts ------------------------------------------------------------------------------------------------------

def test_per_expert_layout_projects_every_expert_and_leaves_router_and_embedding_alone():
    torch.manual_seed(2)
    m = model(per_expert(0), per_expert(1))
    candidate, manifest = Abliteration().apply(m, directions())

    for layer in (0, 1):
        r = directions()[layer + 1]
        for e in range(EXPERTS):
            weight = candidate[f"model.layers.{layer}.mlp.experts.{e}.down_proj.weight"]
            torch.testing.assert_close(r @ weight, torch.zeros(INTER), atol=1e-6, rtol=0)
        gate = f"model.layers.{layer}.mlp.gate.weight"
        assert torch.equal(candidate[gate], m.state_dict()[gate])
    assert torch.equal(candidate["model.embed_tokens.weight"], m.state_dict()["model.embed_tokens.weight"])
    assert manifest["summary"]["matrices_changed"] == 2 * (1 + EXPERTS)
    assert {t["kind"] for t in manifest["targets"]} == {"self_attn.o_proj", "mlp.experts.down_proj"}
    assert sorted(t["expert"] for t in manifest["targets"] if t["layer"] == 1 and t["expert"] is not None) == [0, 1, 2]


def test_fused_layout_projects_each_expert_slice_with_one_rank_one_update_each():
    torch.manual_seed(3)
    m = model(fused(0), fused(1))
    before = {k: v.clone() for k, v in m.state_dict().items()}
    candidate, manifest = Abliteration().apply(m, directions())

    name, r = "model.layers.0.mlp.experts.down_proj", directions()[1]
    torch.testing.assert_close(torch.einsum("h,ehi->ei", r, candidate[name]), torch.zeros(EXPERTS, INTER), atol=1e-6, rtol=0)
    delta = candidate[name] - before[name]
    assert all(torch.linalg.matrix_rank(delta[e]) == 1 for e in range(EXPERTS))
    assert all(torch.equal(m.state_dict()[k], v) for k, v in before.items())          # parent never mutated
    assert {t["kind"] for t in manifest["targets"]} == {"self_attn.o_proj", "mlp.experts.down_proj[fused]"}
    assert manifest["summary"]["matrices_changed"] == 2 * 2                          # one attention matrix and one fused tensor per block


def test_scale_applies_to_expert_tensors_too():
    torch.manual_seed(4)
    m = model(fused(0), fused(1))
    half, _ = Abliteration(scale=0.5).apply(m, directions())
    name, r = "model.layers.1.mlp.experts.down_proj", directions()[2]
    torch.testing.assert_close(torch.einsum("h,ehi->ei", r, half[name]), 0.5 * torch.einsum("h,ehi->ei", r, m.state_dict()[name]), atol=1e-6, rtol=0)


def test_blocks_may_differ_in_family_but_not_within_a_block():
    torch.manual_seed(5)
    Abliteration().apply(model(dense(0), fused(1)), directions())                    # dense block then expert block: accepted
    both = dense(0) | {"model.layers.0.mlp.experts.0.down_proj.weight": torch.randn(WIDTH, INTER)}
    with pytest.raises(ValueError, match="target mismatch"):
        Abliteration().apply(model(both, dense(1)), directions())


@pytest.mark.parametrize(
    ("layers", "message"),
    [
        ((attn(0), per_expert(1)), "target mismatch"),                                        # block 0 has no MLP output at all
        ((per_expert(0), {k: v for k, v in per_expert(1).items() if "o_proj" not in k}), "target mismatch"),   # block 1 has no attention output
    ],
)
def test_incomplete_expert_models_fail_closed(layers, message):
    with pytest.raises(ValueError, match=message):
        Abliteration().apply(model(*layers), directions())


def test_expert_index_gaps_and_wrong_fused_axis_fail_closed():
    gap = per_expert(0)
    del gap["model.layers.0.mlp.experts.1.down_proj.weight"]                              # experts 0 and 2 remain
    with pytest.raises(ValueError, match="contiguous"):
        Abliteration().apply(model(gap, per_expert(1)), directions())
    wrong_axis = fused(0) | {"model.layers.0.mlp.experts.down_proj": torch.randn(EXPERTS, INTER, WIDTH)}   # hidden axis last
    with pytest.raises(ValueError, match="writes 4 features"):
        Abliteration().apply(model(wrong_axis, fused(1)), directions())
