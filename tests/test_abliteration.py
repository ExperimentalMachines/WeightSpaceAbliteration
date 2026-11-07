from __future__ import annotations

import pytest
import torch
from torch import nn

from harness.methods.abliteration import Abliteration


class Attention(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.q_proj = nn.Linear(width, width, bias=False)
        self.o_proj = nn.Linear(width, width, bias=False)


class MLP(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.up_proj = nn.Linear(width, width + 1, bias=False)
        self.down_proj = nn.Linear(width + 1, width, bias=False)


class Layer(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.self_attn = Attention(width)
        self.mlp = MLP(width)


class Backbone(nn.Module):
    def __init__(self, width: int, layers: int) -> None:
        super().__init__()
        self.layers = nn.ModuleList(Layer(width) for _ in range(layers))


class TinyQwen(nn.Module):
    def __init__(self, width: int = 3, layers: int = 2) -> None:
        super().__init__()
        self.model = Backbone(width, layers)


def directions() -> torch.Tensor:
    # Index zero represents the embedding output. Blocks 0 and 1 must use e0 and e1, respectively.
    return torch.eye(3)


def target_names(state: dict[str, torch.Tensor]) -> list[str]:
    return sorted(name for name in state if name.endswith(("self_attn.o_proj.weight", "mlp.down_proj.weight")))


def test_projects_each_residual_writer_without_mutating_parent() -> None:
    torch.manual_seed(4)
    model = TinyQwen()
    before = {name: value.detach().clone() for name, value in model.state_dict().items()}

    candidate, manifest = Abliteration().apply(model, {"direction": directions()})

    targets = target_names(before)
    assert len(targets) == 4
    assert manifest["method"] == "abliteration"
    assert manifest["params"] == {"scale": 1.0}
    assert manifest["direction"]["layer_offset"] == 1
    assert manifest["summary"]["matrices_changed"] == len(targets)
    assert manifest["summary"]["elements_changed"] > 0
    assert len(manifest["direction"]["tensor_sha256"]) == 64

    for name, original in before.items():
        torch.testing.assert_close(model.state_dict()[name], original)
        if name not in targets:
            torch.testing.assert_close(candidate[name], original)
            continue
        layer = int(name.split(".")[2])
        vector = directions()[layer + 1]
        residual_component = vector @ candidate[name].float()
        torch.testing.assert_close(residual_component, torch.zeros_like(residual_component), atol=1e-6, rtol=0)
        assert torch.linalg.matrix_rank((candidate[name] - original).float()) == 1
        assert candidate[name].data_ptr() != original.data_ptr()


def test_rejects_incomplete_residual_writer_set_before_editing() -> None:
    model = TinyQwen()
    del model.model.layers[1].mlp.down_proj
    before = {name: value.detach().clone() for name, value in model.state_dict().items()}

    with pytest.raises(ValueError, match="target mismatch"):
        Abliteration().apply(model, directions())

    for name, original in before.items():
        torch.testing.assert_close(model.state_dict()[name], original)


def test_rejects_non_unit_or_near_zero_direction() -> None:
    model = TinyQwen()
    malformed = directions()
    malformed[2].zero_()

    with pytest.raises(ValueError, match="near-zero"):
        Abliteration().apply(model, malformed)

    with pytest.raises(ValueError, match="unit length"):
        Abliteration().apply(model, directions() * 2)


def test_rejects_direction_with_the_wrong_block_count() -> None:
    model = TinyQwen()

    with pytest.raises(ValueError, match="vectors but 2 blocks require 3"):
        Abliteration().apply(model, torch.eye(2, 3))
