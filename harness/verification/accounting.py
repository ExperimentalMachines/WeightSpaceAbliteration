"""Execution census for gates: proof that a gate examined what it claims to have examined.

A gate that returns success without examining anything is indistinguishable from one that examined
everything and found nothing wrong. The census makes the distinction visible.

    from harness.verification.accounting import Census, PopulationPolicy

    census = Census("split_integrity", PopulationPolicy.REQUIRED_NONEMPTY)
    for arm in arms:
        census.discover(arm)
        if check_arm(arm):
            census.check_pass(arm)
        else:
            census.check_fail(arm, reason="hash mismatch")
    census.validate()  # raises CensusError if invariants are broken

See ``docs/PROVENANCE.md`` § Gate non-vacuity.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class PopulationPolicy(enum.Enum):
    """What a gate expects its input population to look like."""

    REQUIRED_NONEMPTY = "REQUIRED_NONEMPTY"
    CONDITIONALLY_REQUIRED = "CONDITIONALLY_REQUIRED"
    OPTIONAL = "OPTIONAL"


class CensusError(ValueError):
    """A census invariant is broken. This is a gate failure, not a data failure."""


@dataclass
class Census:
    """Tracks what a gate discovered, checked, and skipped.

    Invariants enforced by ``validate()``:
    - ``discovered == checked + blocked + skipped``
    - ``checked == passed + failed``
    - If policy is ``REQUIRED_NONEMPTY``, ``discovered > 0``
    - Every skip has a reason
    - Every failure has a reason
    - Every blocked item has a reason
    """

    gate: str
    policy: PopulationPolicy
    precondition_met: bool = True

    _discovered: list[str] = field(default_factory=list, repr=False)
    _passed: list[str] = field(default_factory=list, repr=False)
    _failed: list[tuple[str, str]] = field(default_factory=list, repr=False)
    _skipped: list[tuple[str, str]] = field(default_factory=list, repr=False)
    _blocked: list[tuple[str, str]] = field(default_factory=list, repr=False)

    def discover(self, item: str) -> None:
        """Register an input artifact as discovered."""
        self._discovered.append(item)

    def check_pass(self, item: str) -> None:
        """Record that ``item`` was checked and passed."""
        self._passed.append(item)

    def check_fail(self, item: str, reason: str) -> None:
        """Record that ``item`` was checked and failed."""
        if not reason:
            raise CensusError(f"census failure without a reason: {item!r}")
        self._failed.append((item, reason))

    def skip(self, item: str, reason: str) -> None:
        """Record that ``item`` was skipped with an explicit reason."""
        if not reason:
            raise CensusError(f"census skip without a reason: {item!r}")
        self._skipped.append((item, reason))

    def block(self, item: str, reason: str) -> None:
        """Record that ``item`` is blocked (e.g. upstream gate has not run)."""
        if not reason:
            raise CensusError(f"census block without a reason: {item!r}")
        self._blocked.append((item, reason))

    @property
    def discovered(self) -> int:
        return len(self._discovered)

    @property
    def checked(self) -> int:
        return len(self._passed) + len(self._failed)

    @property
    def passed(self) -> int:
        return len(self._passed)

    @property
    def failed(self) -> int:
        return len(self._failed)

    @property
    def skipped(self) -> int:
        return len(self._skipped)

    @property
    def blocked(self) -> int:
        return len(self._blocked)

    def validate(self) -> None:
        """Raise ``CensusError`` if the census invariants are broken."""
        errors: list[str] = []

        # Arithmetic invariant: discovered == checked + blocked + skipped
        if self.discovered != self.checked + self.blocked + self.skipped:
            errors.append(
                f"discovered ({self.discovered}) != "
                f"checked ({self.checked}) + blocked ({self.blocked}) + skipped ({self.skipped})"
            )

        # checked == passed + failed
        if self.checked != self.passed + self.failed:
            errors.append(
                f"checked ({self.checked}) != passed ({self.passed}) + failed ({self.failed})"
            )

        # Population policy
        if self.policy == PopulationPolicy.REQUIRED_NONEMPTY and self.discovered == 0:
            errors.append(
                f"gate {self.gate!r} requires a nonempty population but discovered 0 items"
            )
        if (
            self.policy == PopulationPolicy.CONDITIONALLY_REQUIRED
            and self.precondition_met
            and self.discovered == 0
        ):
            errors.append(
                f"gate {self.gate!r} precondition is met but discovered 0 items"
            )

        if errors:
            raise CensusError(
                f"census invariant violated for gate {self.gate!r}: " + "; ".join(errors)
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialise the census for inclusion in a gate receipt."""
        return {
            "gate": self.gate,
            "policy": self.policy.value,
            "precondition_met": self.precondition_met,
            "discovered": self.discovered,
            "checked": self.checked,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "blocked": self.blocked,
            "failures": [{"item": item, "reason": reason} for item, reason in self._failed],
            "skips": [{"item": item, "reason": reason} for item, reason in self._skipped],
            "blocks": [{"item": item, "reason": reason} for item, reason in self._blocked],
        }

    def __repr__(self) -> str:
        return (
            f"Census(gate={self.gate!r}, policy={self.policy.value}, "
            f"discovered={self.discovered}, checked={self.checked}, "
            f"passed={self.passed}, failed={self.failed}, "
            f"skipped={self.skipped}, blocked={self.blocked})"
        )
