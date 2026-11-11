# Upstream issue recording

**Audience:** anyone who discovers a bug in a dependency during a run, or who needs to audit how
the study handled one.

When this study discovers a bug in an upstream dependency — `transformers` loading different
state-dict key names than documented, `torch` producing non-deterministic output on a specific
GPU, `numpy` silently promoting a dtype — the bug and its resolution become part of the research
record. A result that depends on an unrecorded workaround is a result whose provenance is broken.

## Why this matters

A workaround changes the code path. If the workaround is not recorded:

* a reproduction attempt on a version where the bug is fixed will run different code and may
  produce different numbers;
* a reproduction attempt on the same buggy version without the workaround will fail for a reason
  the paper does not explain;
* a reviewer cannot distinguish a real effect from an artifact of the workaround.

Recording the issue is the minimum cost that prevents all three.

## Lifecycle

```
discover ──► record in ledger ──► file companion .md ──► file upstream (optional)
                                                              │
                                          ┌───────────────────┘
                                          v
                              track resolution ──► update status entry
```

Each upstream issue produces **two artifacts**:

1. A ledger entry (`op: "upstream_issue"`) that binds the issue to the run.
2. A companion Markdown file in this directory (`<SLUG>.md`) with the full narrative.

Status changes (fix merged, version bumped, workaround removed) are **new ledger entries**
referencing the original slug, not edits to the original entry. The append-only rule applies.

## Ledger entry schema

```json
{
  "op": "upstream_issue",
  "params": {
    "slug": "transformers-qwen35-linear-attn-key-names",
    "package": "transformers==4.44.2",
    "severity": "blocking",
    "discovered_at": "2026-11-10T14:23:00Z",
    "issue_url": "https://github.com/huggingface/transformers/issues/NNNNN",
    "pr_url": null,
    "workaround": "Accept both self_attn.o_proj and linear_attn.out_proj as attention writers",
    "workaround_commit": "196b6f2d674daa058e3b5e409e4c18fbd3114edb",
    "resolved_upstream": false,
    "resolved_version": null,
    "affected_gates": ["direction_derivation", "refusal_eval"],
    "affected_runs": ["20261110T135200Z-weightspace-abliteration-qwen3.5-0.8b"],
    "status": "workaround-in-place"
  }
}
```

The full JSON schema is in [`schema.json`](schema.json).

### Severity levels

| Level | Meaning |
|---|---|
| `blocking` | The run cannot continue without a workaround. |
| `degrading` | Results are affected but the run can complete; the effect must be quantified. |
| `cosmetic` | Output formatting or logging is wrong; no numerical effect. |

### Status values

| Status | Meaning |
|---|---|
| `open` | Bug discovered, no workaround yet. Run is blocked if severity is `blocking`. |
| `workaround-in-place` | Workaround applied in this study; bug still open upstream. |
| `fix-merged` | Upstream fix merged; study still on workaround (pinned version). |
| `adopted` | Study has bumped to the fixed version and removed the workaround. |
| `wont-fix` | Upstream declined the fix; workaround is permanent. |

## Companion Markdown file

Each `<SLUG>.md` in this directory must contain:

### 1. Summary

One paragraph: what broke, what the symptom was, how it was found.

### 2. Reproduction

Minimal script or command that demonstrates the issue on the pinned version. Must be
self-contained — no references to internal run artifacts.

### 3. Impact on study

Which gates, which runs, which results are affected and how. Be specific: "the
`direction_derivation` gate on the Qwen3.5-0.8B run produced a direction tensor with 6 layers
instead of 24 because 18 linear-attention blocks were silently skipped."

### 4. Workaround

Exact code or configuration change applied. Reference the commit SHA that applied it.

### 5. Upstream status

Link to the issue/PR. Current status. Version where the fix landed, if any.

### 6. Resolution for this study

Whether the workaround is permanent (pinned around the bug) or temporary (will adopt the fix
when the pinned version bumps). If permanent, state why the fix was not adopted.

## Filing upstream

When filing an issue or PR upstream, include:

* **Exact versions.** Package version, Python version, OS, GPU model and driver if relevant.
* **Minimal reproducer.** Self-contained script. Not a reference to this study.
* **Expected vs actual behaviour.** Concrete values, not "it doesn't work."
* **Pinned checkpoint or dataset.** If the bug is model-specific, the exact revision.

### What never goes upstream

* Unreleased model weights, harmful prompts, or generated text from this study.
* Internal run IDs, ledger entries, or receipt hashes.
* Complaints. A bug report states facts and provides evidence.

## Enforcement

A `blocking` upstream issue without a workaround recorded in the ledger is a preflight refusal:

```
ProtocolViolation[upstream-clear]: blocking upstream issue has no recorded workaround
  detail: transformers-qwen35-linear-attn-key-names (blocking, status=open)
  run:    runs/20261110T135200Z-weightspace-abliteration-qwen3.5-0.8b
  remedy: apply a workaround and record it, or downgrade severity if the assessment changed
```

**Enforced by:** `harness/preflight.py:require_upstream_clear`.

## References

* Dhruv & Dubey, "Managing Software Provenance to Enhance Reproducibility in Computational
  Research" (arXiv:2308.15637, 2023).
* Smith, Katz & Niemeyer, "Software Citation Principles" (PeerJ CS, 2016; FORCE11).
* Barker et al., "Introducing the FAIR Principles for Research Software" (Scientific Data, 2022).
* Hinsen, "Dealing With Software Collapse" (Computing in Science & Engineering, 2019).
* See also: [`docs/PROVENANCE.md`](../PROVENANCE.md) § Upstream issue recording.
