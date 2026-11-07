"""Method interface for weight-space editing. No method is implemented here on purpose.

Nothing in this file edits weights. It defines the contract a method must satisfy so a reviewer can
inspect one method in isolation, run it against the frozen split, and only then let it be recorded in
the ledger as the method this run used.

A method is frozen by being named in a ledger entry, not by being merged. Until that entry exists,
`load_method()` refuses every name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class MethodSpec:
    """What a method declares about itself before it touches a tensor."""

    name: str
    summary: str
    #: tensors the method intends to modify, as dotted parameter names or a glob the reviewer accepts
    targets: tuple[str, ...]
    #: free parameters and their defaults, e.g. {"scale": 1.0, "layers": "all"}
    params: dict[str, Any] = field(default_factory=dict)
    #: what the method needs from the direction gate, e.g. {"direction": "per_layer_unit"}
    requires: dict[str, str] = field(default_factory=dict)
    #: literature this method reproduces, as arXiv ids; empty means the method is novel
    basis: tuple[str, ...] = ()


@runtime_checkable
class Method(Protocol):
    """A weight-space edit.

    `apply` receives the parent model already loaded and the direction produced by the
    `direction_derivation` gate, and returns a new state dict plus a manifest of what changed.
    It must not write to disk; the caller saves the checkpoint and records the manifest.
    """

    spec: MethodSpec

    def apply(self, model: Any, direction: Any) -> tuple[dict[str, Any], dict[str, Any]]: ...


KNOWN = ("abliteration", "heretic_style", "obliteratus_style")


def load_method(name: str) -> Method:
    """Refuse until a method is implemented and reviewed.

    The three names the study compares are reserved. None is implemented, and this function is the
    single place that decides whether one may run, so the decision is reviewable in one file.
    """
    if name in KNOWN:
        raise NotImplementedError(
            f"{name!r} is reserved but not implemented. A method is admitted only after review; "
            "see harness/methods/README.md for the checklist and the ledger entry that freezes it."
        )
    raise KeyError(f"unknown method {name!r}; reserved names are {', '.join(KNOWN)}")


def registry() -> dict[str, MethodSpec | None]:
    """The three reserved slots, all empty. A reviewer fills one by implementing it."""
    return {name: None for name in KNOWN}
