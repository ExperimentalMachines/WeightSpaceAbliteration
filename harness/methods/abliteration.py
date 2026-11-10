"""Review-only implementation of the reserved Abliteration method.

This module deliberately has no registration side effect. ``load_method()`` stays closed until
review records a ledger entry; a materializer will call ``Abliteration.apply()`` only after the
study's admission workflow has an approved pre-evaluation transition.

Targets are the residual-writing output projections of every block: the attention ``o_proj`` and
the MLP output, which is ``mlp.down_proj`` in dense blocks, ``mlp.experts.<E>.down_proj`` in blocks
that keep one module per expert, or a single 3-D ``mlp.experts.down_proj`` in blocks that fuse the
experts. Each matrix (each expert slice, for a fused tensor) gets one rank-1 update.
"""
from __future__ import annotations

import dataclasses
import hashlib
import math
import re
from collections.abc import Mapping
from typing import Any, NamedTuple

import torch

from .base import MethodSpec

_ATTN = "self_attn.o_proj"
_DENSE = "mlp.down_proj"
_EXPERT = "mlp.experts.down_proj"
_FUSED = "mlp.experts.down_proj[fused]"
_MLP_FAMILIES = (_DENSE, _EXPERT, _FUSED)

_PATTERNS = (
    (re.compile(r"^model\.layers\.(?P<layer>\d+)\.self_attn\.o_proj\.weight$"), _ATTN),
    (re.compile(r"^model\.layers\.(?P<layer>\d+)\.mlp\.down_proj\.weight$"), _DENSE),
    (re.compile(r"^model\.layers\.(?P<layer>\d+)\.mlp\.experts\.(?P<expert>\d+)\.down_proj\.weight$"), _EXPERT),
    (re.compile(r"^model\.layers\.(?P<layer>\d+)\.mlp\.experts\.down_proj$"), _FUSED),
)
_MIN_DIRECTION_NORM = 1e-12
_UNIT_TOLERANCE = 1e-4


class Target(NamedTuple):
    name: str
    layer: int
    kind: str
    value: torch.Tensor
    expert: int | None


class Abliteration:
    """Remove each block's precomputed refusal direction from residual-writing matrices.

    ``scale`` is the fraction of the direction's component removed: ``W' = W - scale * r (r^T W)``.
    The study runs it at 1.0; any other value is a different candidate and must be declared as such.
    """

    spec = MethodSpec(
        name="abliteration",
        summary="Rank-1 projection of the precomputed refusal direction from all residual writers.",
        targets=(
            "model.layers.*.self_attn.o_proj.weight",
            "model.layers.*.mlp.down_proj.weight",
            "model.layers.*.mlp.experts.*.down_proj.weight",
            "model.layers.*.mlp.experts.down_proj",
        ),
        params={"scale": 1.0},
        requires={"direction": "per_layer_unit"},
        basis=("2406.11717",),
    )

    def __init__(self, scale: float = 1.0) -> None:
        if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not math.isfinite(scale) or not 0.0 < scale <= 1.0:
            raise ValueError(f"scale must be a finite number in (0, 1], got {scale!r}")
        self.scale = float(scale)
        # The instance spec reports the value actually used, so the manifest can never disagree with the weights.
        self.spec = dataclasses.replace(type(self).spec, params={"scale": self.scale})

    def apply(self, model: Any, direction: Any) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
        """Return a candidate state dictionary and an exact manifest without mutating ``model``.

        The derivation gate stores the embedding output at direction index zero. Block ``i`` therefore
        uses vector ``i + 1``. The vectors are validated but never normalized or otherwise transformed.
        """
        vectors = _direction_tensor(direction)
        parent = model.state_dict()
        targets = _targets(parent, vectors.shape)
        candidate = dict(parent)
        direction_cache: dict[tuple[int, str], torch.Tensor] = {}
        changes: list[dict[str, Any]] = []
        update_l2_squared = 0.0

        with torch.no_grad():
            for target in targets:
                original = target.value.detach()
                cache_key = (target.layer, str(original.device))
                vector = direction_cache.get(cache_key)
                if vector is None:
                    vector = vectors[target.layer + 1].to(device=original.device, dtype=torch.float32)
                    direction_cache[cache_key] = vector

                source = original.float()
                edited = (source - self.scale * _projection(vector, source)).to(dtype=original.dtype)
                actual_delta = edited.float() - source
                update_l2_squared += float(torch.sum(actual_delta.square()).item())
                candidate[target.name] = edited
                changes.append(
                    {
                        "name": target.name,
                        "layer": target.layer,
                        "kind": target.kind,
                        "expert": target.expert,
                        "shape": list(original.shape),
                        "direction_index": target.layer + 1,
                        "rank": 1,
                        "weight_l2": float(torch.linalg.vector_norm(source).item()),
                        "update_l2": float(torch.linalg.vector_norm(actual_delta).item()),
                        "relative_update_l2": _relative_norm(actual_delta, source),
                        "elements": original.numel(),
                        "elements_changed": int(torch.count_nonzero(edited != original).item()),
                    }
                )

        elements_changed = sum(change["elements_changed"] for change in changes)
        if not elements_changed:
            raise ValueError("abliteration changed no target elements; refusing to materialize a no-op candidate")
        manifest = {
            "method": self.spec.name,
            "params": dict(self.spec.params),
            "direction": {
                "shape": list(vectors.shape),
                "tensor_sha256": _tensor_sha256(vectors),
                "layer_offset": 1,
                "transformed": False,
            },
            "targets": changes,
            "summary": {
                "matrices_changed": len(changes),
                "elements_in_targets": sum(change["elements"] for change in changes),
                "elements_changed": elements_changed,
                "update_l2": math.sqrt(update_l2_squared),
                "target_kinds": sorted({target.kind for target in targets}),
            },
        }
        return candidate, manifest


def _projection(vector: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    """``r (r^T W)`` for a matrix ``[hidden, in]``, or independently for every expert slice of ``[experts, hidden, in]``."""
    if weight.ndim == 2:
        return torch.outer(vector, vector @ weight)
    coefficients = torch.einsum("h,ehi->ei", vector, weight)
    return torch.einsum("h,ei->ehi", vector, coefficients)


def _direction_tensor(direction: Any) -> torch.Tensor:
    """Validate the unmodified per-layer unit vectors supplied by the derivation gate."""
    values = direction["direction"] if isinstance(direction, Mapping) else direction
    tensor = values.detach() if isinstance(values, torch.Tensor) else torch.as_tensor(values)
    if tensor.ndim != 2:
        raise ValueError(f"direction must have shape [hidden_states, hidden_size], got {list(tensor.shape)}")
    if not tensor.shape[0] or not tensor.shape[1]:
        raise ValueError("direction must contain at least one nonempty vector")
    if tensor.is_complex():
        raise ValueError("direction must be real-valued")
    tensor = tensor.to(dtype=torch.float32)
    if not torch.isfinite(tensor).all():
        raise ValueError("direction contains non-finite values")
    norms = torch.linalg.vector_norm(tensor, dim=1)
    if torch.any(norms <= _MIN_DIRECTION_NORM):
        raise ValueError("direction contains a near-zero vector")
    if not torch.allclose(norms, torch.ones_like(norms), atol=_UNIT_TOLERANCE, rtol=_UNIT_TOLERANCE):
        raise ValueError("direction vectors must be unit length exactly as emitted by direction_derivation")
    return tensor


def _targets(state: Mapping[str, torch.Tensor], direction_shape: torch.Size) -> list[Target]:
    """Discover a complete, contiguous set of supported residual writers or fail closed.

    Every block must have an attention ``o_proj`` and exactly one MLP-output family (dense, per-expert or fused).
    Blocks may differ from each other (a model with some dense and some expert blocks is accepted), but a block
    that mixes families, lacks either side, or has gaps in its expert indices is rejected.
    """
    found: dict[int, dict[str, list[Target]]] = {}
    for name, value in state.items():
        for pattern, kind in _PATTERNS:
            match = pattern.fullmatch(name)
            if match:
                break
        else:
            continue
        if not isinstance(value, torch.Tensor):
            raise ValueError(f"target {name!r} must be a torch tensor")
        rank = 3 if kind == _FUSED else 2
        if value.ndim != rank:
            raise ValueError(f"target {name!r} must be a rank-{rank} torch tensor")
        if not value.is_floating_point():
            raise ValueError(f"target {name!r} must have floating-point values")
        width = value.shape[1] if kind == _FUSED else value.shape[0]
        if width != direction_shape[1]:
            raise ValueError(f"target {name!r} writes {width} features but direction width is {direction_shape[1]}")
        layer = int(match["layer"])
        expert = int(match["expert"]) if kind == _EXPERT else None
        found.setdefault(layer, {}).setdefault(kind, []).append(Target(name, layer, kind, value, expert))

    if not found:
        raise ValueError("no supported residual-writing targets found")
    layers = sorted(found)
    if layers != list(range(len(layers))):
        raise ValueError(f"target layers must be contiguous from zero, found {layers}")
    if direction_shape[0] != len(layers) + 1:
        raise ValueError(
            f"direction has {direction_shape[0]} vectors but {len(layers)} blocks require {len(layers) + 1}"
        )

    targets: list[Target] = []
    for layer in layers:
        kinds = found[layer]
        families = [kind for kind in _MLP_FAMILIES if kind in kinds]
        missing = ([] if _ATTN in kinds else [_ATTN]) + ([] if families else ["mlp.down_proj or mlp.experts.*.down_proj"])
        if missing or len(families) > 1:
            raise ValueError(f"layer {layer} target mismatch; missing={missing}, unexpected={families[1:]}")
        experts = sorted(t.expert for t in kinds.get(_EXPERT, []))
        if experts != list(range(len(experts))):
            raise ValueError(f"layer {layer} expert indices must be contiguous from zero, found {experts}")
        targets += kinds[_ATTN]
        targets += sorted(kinds[families[0]], key=lambda t: -1 if t.expert is None else t.expert)
    return targets


def _relative_norm(delta: torch.Tensor, weight: torch.Tensor) -> float:
    denominator = torch.linalg.vector_norm(weight).clamp_min(torch.finfo(weight.dtype).eps)
    return float((torch.linalg.vector_norm(delta) / denominator).item())


def _tensor_sha256(tensor: torch.Tensor) -> str:
    canonical = tensor.detach().cpu().contiguous().numpy().tobytes()
    return hashlib.sha256(canonical).hexdigest()
