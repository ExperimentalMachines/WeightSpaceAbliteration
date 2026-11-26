"""Verification infrastructure for the weight-space abliteration study.

This package holds the census accounting module and the contract version. The contract version
is reported by every gate receipt and determines what "PASS" means.

Bump ``CONTRACT_VERSION`` whenever the set of checks, their discovery rules, or their non-vacuity
requirements change such that a PASS means something different. A PASS recorded under an earlier
version is not equivalent to one under the current version, and no historical receipt is rewritten.

See ``docs/PROVENANCE.md`` § Verifier contract versions.
"""

# v1 (implicit): gate assertions only; no census, no non-vacuity proof.
# v2: census accounting was introduced, but was not wired into every gate. A
#     historical version number alone is not proof of population completeness.
# v3: local release/source, canonical host, immutable execution manifest, bounded
#     callable bindings, declared input/output closure and gdkit log binding.
#     This does not repair historical measurement semantics or certify promotion.
CONTRACT_VERSION = 3
