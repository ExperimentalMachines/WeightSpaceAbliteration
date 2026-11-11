"""Tests for the execution census accounting module.

Every gate must report a census that adds up. These tests verify the invariants
that ``Census.validate()`` enforces, ensuring a gate cannot silently pass on an
empty population or produce inconsistent counters.
"""

from __future__ import annotations

import pytest

from harness.verification.accounting import Census, CensusError, PopulationPolicy


# -------------------------------------------------------------------------- arithmetic invariants


def test_valid_census_all_pass() -> None:
    c = Census("test_gate", PopulationPolicy.REQUIRED_NONEMPTY)
    c.discover("a")
    c.discover("b")
    c.check_pass("a")
    c.check_pass("b")
    c.validate()
    assert c.discovered == 2
    assert c.checked == 2
    assert c.passed == 2
    assert c.failed == 0
    assert c.skipped == 0
    assert c.blocked == 0


def test_valid_census_mixed() -> None:
    c = Census("test_gate", PopulationPolicy.REQUIRED_NONEMPTY)
    c.discover("a")
    c.discover("b")
    c.discover("c")
    c.discover("d")
    c.check_pass("a")
    c.check_fail("b", reason="hash mismatch")
    c.skip("c", reason="arm not yet built")
    c.block("d", reason="upstream gate has not run")
    c.validate()
    assert c.discovered == 4
    assert c.checked == 2
    assert c.passed == 1
    assert c.failed == 1
    assert c.skipped == 1
    assert c.blocked == 1


def test_arithmetic_invariant_violation() -> None:
    c = Census("test_gate", PopulationPolicy.OPTIONAL)
    c.discover("a")
    c.discover("b")
    c.check_pass("a")
    # b is discovered but neither checked, skipped, nor blocked
    with pytest.raises(CensusError, match="discovered.*!=.*checked.*blocked.*skipped"):
        c.validate()


def test_checked_invariant_violation() -> None:
    c = Census("test_gate", PopulationPolicy.OPTIONAL)
    c.discover("a")
    # manually corrupt: add to passed AND failed (should never happen via API,
    # but the invariant catches programming errors in the gate itself)
    c._passed.append("a")
    c._failed.append(("a", "double-counted"))
    # discovered=1, checked=2 (passed=1 + failed=1), but checked > discovered
    with pytest.raises(CensusError, match="discovered.*!=.*checked"):
        c.validate()


# -------------------------------------------------------------------------- population policies


def test_required_nonempty_rejects_zero_discovered() -> None:
    c = Census("split_integrity", PopulationPolicy.REQUIRED_NONEMPTY)
    with pytest.raises(CensusError, match="requires a nonempty population"):
        c.validate()


def test_conditionally_required_rejects_when_precondition_met() -> None:
    c = Census("refusal_eval", PopulationPolicy.CONDITIONALLY_REQUIRED, precondition_met=True)
    with pytest.raises(CensusError, match="precondition is met but discovered 0"):
        c.validate()


def test_conditionally_required_allows_when_precondition_not_met() -> None:
    c = Census("refusal_eval", PopulationPolicy.CONDITIONALLY_REQUIRED, precondition_met=False)
    c.validate()  # no items, but precondition not met — that is allowed


def test_optional_allows_zero_discovered() -> None:
    c = Census("optional_check", PopulationPolicy.OPTIONAL)
    c.validate()  # empty population is fine for optional gates


# -------------------------------------------------------------------------- reason enforcement


def test_skip_without_reason_raises() -> None:
    c = Census("test_gate", PopulationPolicy.OPTIONAL)
    c.discover("a")
    with pytest.raises(CensusError, match="skip without a reason"):
        c.skip("a", reason="")


def test_fail_without_reason_raises() -> None:
    c = Census("test_gate", PopulationPolicy.OPTIONAL)
    c.discover("a")
    with pytest.raises(CensusError, match="failure without a reason"):
        c.check_fail("a", reason="")


def test_block_without_reason_raises() -> None:
    c = Census("test_gate", PopulationPolicy.OPTIONAL)
    c.discover("a")
    with pytest.raises(CensusError, match="block without a reason"):
        c.block("a", reason="")


# -------------------------------------------------------------------------- serialisation


def test_to_dict_roundtrip() -> None:
    c = Census("split_integrity", PopulationPolicy.REQUIRED_NONEMPTY)
    c.discover("primary.jsonl")
    c.discover("large.jsonl")
    c.discover("derivation.jsonl")
    c.check_pass("primary.jsonl")
    c.check_fail("large.jsonl", reason="sha256 mismatch")
    c.skip("derivation.jsonl", reason="derivation arm is not checked by this gate")
    c.validate()

    d = c.to_dict()
    assert d["gate"] == "split_integrity"
    assert d["policy"] == "REQUIRED_NONEMPTY"
    assert d["discovered"] == 3
    assert d["checked"] == 2
    assert d["passed"] == 1
    assert d["failed"] == 1
    assert d["skipped"] == 1
    assert d["blocked"] == 0
    assert len(d["failures"]) == 1
    assert d["failures"][0]["item"] == "large.jsonl"
    assert d["failures"][0]["reason"] == "sha256 mismatch"
    assert len(d["skips"]) == 1
    assert d["skips"][0]["reason"] == "derivation arm is not checked by this gate"


def test_repr() -> None:
    c = Census("g", PopulationPolicy.OPTIONAL)
    r = repr(c)
    assert "gate='g'" in r
    assert "OPTIONAL" in r
    assert "discovered=0" in r
