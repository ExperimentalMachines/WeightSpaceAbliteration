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
* **Observed use case.** What study operation encountered the failure, the relevant configuration,
  and the measured impact. Say when a finding came only from source inspection or automated analysis.
* **Text diagnostics.** Complete traceback, relevant stdout/stderr, exact launch command and config.
  Logs support the report; they do not replace a runnable reproducer.
* **Validation.** Exact commands, versions/commits, and before/after results; identify checks not run.

### Upstream evidence requirements

Checked against official GitHub guides and templates on 2026-11-17 using Firecrawl.
These are submission requirements, not changes to this study's protocol. Recheck the current
target templates before filing; do not upgrade the registered environment to satisfy them.

| Project | Evidence requested by its guide/template |
|---|---|
| [TRL guide](https://github.com/huggingface/trl/blob/bf38f3358474e384917fe7f620621c9e45604d96/CONTRIBUTING.md) and [bug form](https://github.com/huggingface/trl/blob/main/.github/ISSUE_TEMPLATE/bug-report.yml) | Actual training workload, configuration and practical cost; explicitly identify analysis-only discoveries. Short self-contained reproducer (guide requests under 30 seconds), complete text traceback, and `trl env` output. The form rejects screenshots as substitutes for code/errors. |
| [Transformers guide](https://github.com/huggingface/transformers/blob/a8d43b20622149fab30762129c59a2b1ba829364/CONTRIBUTING.md) and [bug form](https://github.com/huggingface/transformers/blob/a8d43b20622149fab30762129c59a2b1ba829364/.github/ISSUE_TEMPLATE/bug-report.yml) | Runnable reproducer on latest release or `main`, using a published checkpoint, default config, or documented workflow; `transformers env`, relevant Trainer/TRL/PEFT/DeepSpeed configs, expected behavior and textual error/traceback. Long traces belong in a collapsible details block. A standalone bug-fix PR needs a script failing on `main` and passing with the fix. |
| [Accelerate guide](https://github.com/huggingface/accelerate/blob/ad419b8669d34b41304ee50a37346e12164f7882/CONTRIBUTING.md) and [bug form](https://github.com/huggingface/accelerate/blob/main/.github/ISSUE_TEMPLATE/bug-report.yml) | Actual workflow and impact; minimal runnable code, launch command/config, full text traceback, hardware and device/machine counts. Capture `accelerate env`, or `accelerate env --config_file path/to/config.yaml` for the configuration actually used. Check latest release or `main` separately. |
| [PyTorch bug form](https://github.com/pytorch/pytorch/blob/8ab9c868e14a239ab4588917f35efa5bb8f72d16/.github/ISSUE_TEMPLATE/bug-report.yml) | Minimal self-contained example without downloadable artifacts, observed versus expected results, full traceback, and output from its linked `torch/utils/collect_env.py` script. Inspect downloaded scripts before executing. If possible, check the latest nightly separately. Numerical/reproducibility reports must explain why the discrepancy is not an expected documented limitation. |

Public model/checkpoint references are appropriate for the Hugging Face workflows above;
PyTorch's general bug form instead asks for a reproduction without downloaded artifacts.
Do not impose one project's reproduction format on all dependencies.

For performance fixes, Transformers and Accelerate request before/after measurements on a
representative workload with hardware/configuration, not only an isolated microbenchmark.
Retain measurement commands and outputs privately; publish the relevant results and limitations.
Latest/main/nightly checks are separate off-run work and still require any existing execution
approval. If unavailable, say so rather than implying the current release was tested.

Submission procedures also differ: TRL's current guide requires first-time contributors to
obtain an assigned issue before a PR; Transformers permits qualifying issue-linked or
evidence-backed standalone PRs and does not assign issues. PyTorch's
[PR lifecycle](https://github.com/pytorch/pytorch/blob/main/CONTRIBUTING.md#pr-lifecycle)
requires an actionable issue or the applicable maintainer approval/access.
Do not submit automatically based on a locally documented finding.

Follow each project's disclosure and review rules. TRL's
[PR template](https://github.com/huggingface/trl/blob/e8bf8d05991468a99e34026155b835e4f68e2a88/.github/PULL_REQUEST_TEMPLATE.md)
asks for the level of AI involvement; its guide declines fully AI-generated first-time PRs.
PyTorch's [AI policy](https://github.com/pytorch/pytorch/blob/main/AI_POLICY.md) requires
AI-generated material to be disclosed and clearly separated, with human commentary, and
does not accept fully autonomous contributions. Accelerate requires an actual use case,
exact validation commands/results and unrun-test limitations; its guide limits authored
PR descriptions to 250 words and directs longer logs/reproducers/benchmarks to links.

### Public research record versus private working evidence

The study's goal and trustworthy results take priority. These records support reproducible
research and transparent handling of dependency failures. Reporting a genuine encountered
bug may benefit upstream, but generating reports or PRs is not a study deliverable.

Do not divert study work into speculative bug hunting or construct invalid inputs,
unsupported configurations, or artificial internal states just to manufacture a failure.
A minimal reproducer is a reduction of an observed study failure: keep its causal conditions
and verify that the same failure remains. Small models or synthetic data may simplify a
real case; a different exception created by the reduction is not evidence of the original
bug. Record unsuccessful reductions and uncertainty honestly.

Useful public findings are broader than bug reports. Maintain informative research docs
for model quirks, compatibility requirements, environment constraints, failed approaches,
negative results, and operational lessons. Classify expected behavior, local integration
errors, and suspected dependency defects separately; do not imply every surprise is upstream's
fault. Include setup/evidence, interpretation and uncertainty, mitigation, and scope limits.
Clearly distinguish smoke checks or rough timings from validated benchmark results.
The operator's [model-quirks example](https://github.com/arjhinety/small-mind-companion/blob/2e7c393cb9f82e11f3dc0082800896a66c997d60/docs/model_quirks.md)
illustrates this documentation style; its findings are not evidence about this study's models.

| Location | Appropriate content |
|---|---|
| Public study docs and required ledger records | Confirmed observations, explicitly qualified hypotheses, affected methods/results, severity, workaround and resolution, concise verification evidence, and material limitations. Keep required run links inside study records, not in upstream bug reports. |
| Public upstream report or PR | Relevant actual use case, sanitized minimal reproducer, required environment/configuration, complete relevant textual error/traceback, expected/actual behavior, and exercised validation. Link longer sanitized evidence when the project requests it. |
| Local `.omp/upstream-notes/` | Exploratory notes, captured references, drafts, full stdout/stderr, environment dumps, and diagnostic artifacts not suitable for publication. This path is gitignored and excluded from Modal uploads; never force-add it. |

Private storage is not permission to hide adverse results, misstate discovery provenance,
omit required AI disclosures, or replace mandatory run records with unpublished notes.
Do not publish speculative contribution lists or private correspondence. Preserve raw
evidence privately and publish labeled sanitized derivatives where needed, without altering
immutable originals. Gitignore prevents ordinary staging, not access or data loss; retain
private backups and keep credentials out of all captures.


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
