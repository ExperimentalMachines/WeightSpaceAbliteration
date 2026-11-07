"""Review-only implementation of the reserved Abliteration method.

This module deliberately has no registration side effect. ``load_method()`` stays closed until
review records a ledger entry; a materializer will call ``Abliteration.apply()`` only after the
study's admission workflow has an approved pre-evaluation transition.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Mapping
from typing import Any

import torch

from .base import MethodSpec

_TARGET_PATTERN = re.compile(
    r"^model\.layers\.(?P<layer>\d+)\.(?P<kind>self_attn\.o_proj|mlp\.down_proj)\.weight$"
)
_TARGET_KINDS = frozenset({"self_attn.o_proj", "mlp.down_proj"})
_MIN_DIRECTION_NORM = 1e-12
_UNIT_TOLERANCE = 1e-4


class Abliteration:
    """Remove each block's precomputed refusal direction from residual-writing matrices."""

    spec = MethodSpec(
        name="abliteration",
        summary="Rank-1 projection of the precomputed refusal direction from all residual writers.",
        targets=(
            "model.layers.*.self_attn.o_proj.weight",
            "model.layers.*.mlp.down_proj.weight",
        ),
        params={"scale": 1.0},
        requires={"direction": "per_layer_unit"},
        basis=("2406.11717",),
    )

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
            for name, layer, kind, weight in targets:
                cache_key = (layer, str(weight.device))
                vector = direction_cache.get(cache_key)
                if vector is None:
                    vector = vectors[layer + 1].to(device=weight.device, dtype=torch.float32)
                    direction_cache[cache_key] = vector

                original = weight.detach()
                source = original.float()
                delta = torch.outer(vector, vector @ source)
                edited = (source - delta).to(dtype=original.dtype)
                actual_delta = edited.float() - source
                update_l2_squared += float(torch.sum(actual_delta.square()).item())
                update_l2 = float(torch.linalg.vector_norm(actual_delta).item())
                changed = int(torch.count_nonzero(edited != original).item())
                candidate[name] = edited
                changes.append(
                    {
                        "name": name,
                        "layer": layer,
                        "kind": kind,
                        "shape": list(original.shape),
                        "direction_index": layer + 1,
                        "rank": 1,
                        "weight_l2": float(torch.linalg.vector_norm(source).item()),
                        "update_l2": update_l2,
                        "relative_update_l2": _relative_norm(actual_delta, source),
                        "elements": original.numel(),
                        "elements_changed": changed,
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
                "target_kinds": sorted(_TARGET_KINDS),
            },
        }
        return candidate, manifest


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


def _targets(
    state: Mapping[str, torch.Tensor], direction_shape: torch.Size,
) -> list[tuple[str, int, str, torch.Tensor]]:
    """Discover a complete, contiguous set of supported residual writers or fail closed."""
    per_layer: dict[int, dict[str, tuple[str, torch.Tensor]]] = {}
    for name, value in state.items():
        match = _TARGET_PATTERN.fullmatch(name)
        if not match:
            continue
        if not isinstance(value, torch.Tensor) or value.ndim != 2:
            raise ValueError(f"target {name!r} must be a rank-2 torch tensor")
        if not value.is_floating_point():
            raise ValueError(f"target {name!r} must have floating-point values")
        layer = int(match["layer"])
        kind = match["kind"]
        if value.shape[0] != direction_shape[1]:
            raise ValueError(
                f"target {name!r} writes {value.shape[0]} features but direction width is {direction_shape[1]}"
            )
        per_layer.setdefault(layer, {})[kind] = (name, value)

    if not per_layer:
        raise ValueError("no supported residual-writing targets found")
    layers = sorted(per_layer)
    if layers != list(range(len(layers))):
        raise ValueError(f"target layers must be contiguous from zero, found {layers}")
    if direction_shape[0] != len(layers) + 1:
        raise ValueError(
            f"direction has {direction_shape[0]} vectors but {len(layers)} blocks require {len(layers) + 1}"
        )

    targets: list[tuple[str, int, str, torch.Tensor]] = []
    for layer in layers:
        found = set(per_layer[layer])
        if found != _TARGET_KINDS:
            missing = sorted(_TARGET_KINDS - found)
            extra = sorted(found - _TARGET_KINDS)
            raise ValueError(f"layer {layer} target mismatch; missing={missing}, unexpected={extra}")
        for kind in sorted(_TARGET_KINDS):
            name, value = per_layer[layer][kind]
            targets.append((name, layer, kind, value))
    return targets


def _relative_norm(delta: torch.Tensor, weight: torch.Tensor) -> float:
    denominator = torch.linalg.vector_norm(weight).clamp_min(torch.finfo(weight.dtype).eps)
    return float((torch.linalg.vector_norm(delta) / denominator).item())


def _tensor_sha256(tensor: torch.Tensor) -> str:
    canonical = tensor.detach().cpu().contiguous().numpy().tobytes()
    return hashlib.sha256(canonical).hexdigest()
