# Security policy

## Reporting

Report a vulnerability privately to the maintainer through GitHub's security advisory feature on this
repository. Do not open a public issue for anything that could be exploited before it is fixed.

Expect an acknowledgement within seven days and a decision within thirty.

## Scope

Two distinct classes of issue matter here.

**Ordinary software defects** — code execution, path traversal in the fetchers, credential leakage in
logs, dependency compromise. Standard handling.

**Dual-use research artifacts** — anything that would make the ablated models easier to misuse than
they already are. This study produces models whose refusal behaviour is degraded by design. A report
that a released checkpoint lacks the guardrails described in the pre-registration's `intended_use` is
in scope and will be treated as a defect, not as a research result.

## What this repository deliberately does not do

- It does not redistribute evaluation corpora. It publishes identifiers, revisions and hashes, and
  fetches rows at build time.
- It does not release ablated weights as part of the repository. Any release is a separate, controlled
  decision recorded in the run's ledger.
- It does not accept contributions that add prompt corpora to git.

## Supported versions

The study is pre-1.0 and the run in `runs/` is immutable. Fixes ship as new commits; the frozen
pre-registration and its ledger are never rewritten.
