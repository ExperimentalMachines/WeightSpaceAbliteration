# Provenance

> A claim is only as good as the evidence it resolves to. The evidence must be immutable, or the
> claim must say how to verify it.

This document codifies the rules that make the study's artifacts auditable. Every hash, pin,
receipt and record in this repository exists to satisfy one of these rules, and the code that
enforces them names the rule it enforces.

## The invariant

Every verified claim must resolve to an **immutable evidence anchor**. There are two routes, and
they are not interchangeable:

```text
verified claim
    |
    +-- mutable/local source
    |       -> content digest required (sha256 of committed bytes)
    |
    +-- externally immutable source
            -> immutable revision/pin required (full Git SHA, HF revision, DOI with version)
```

A repository path is mutable. `runs/<id>/splits/manifest.json` can hold different bytes tomorrow
while the ledger entry that cites it is unchanged, so a path alone pins nothing and the entry must
carry a content hash.

An external source pinned to an exact commit or revision is already anchored. Accepted immutable
identifiers include a full Git commit SHA, a Hugging Face model or dataset revision, a DOI with an
explicit version, and an arXiv paper id with version suffix. What is **not** accepted is a moving
target: `blob/main`, `tree/master`, `releases/latest`, short abbreviated revisions, and any URL
whose content can change without changing the URL.

A rule that demanded `sha256` everywhere would be as wrong as one that demanded nothing: it would
add meaningless hashes to sources that are already immutable while proving nothing about the ones
that are not. The distinction is the requirement, not uniformity.

## Content digests are over committed bytes

`.gitattributes` sets `text=auto eol=lf` for every text file in this repository. A file checked out
on Windows has CRLF where the committed blob has LF. Hashing the working-tree bytes would make the
digest a claim about the verifier's operating system rather than about the artifact.

The rule:

* the evidence path must be **tracked by Git**. An untracked path is not part of the research
  record, however stable it looks.
* the digest is computed over the committed blob (`git cat-file blob HEAD:<path>`), or over the
  working-tree bytes only where there is no Git context (unit-test fixtures).
* the `sha256_path` helper in `gdkit.gates` reads the file as bytes; this is correct on platforms
  where the checkout matches the committed blob (i.e. `eol=lf` on all platforms, which
  `.gitattributes` enforces). On a platform where the checkout diverges, `git cat-file` is
  authoritative.

**Enforced by:** `gdkit.gates.sha256_path` for receipt input hashes; `gdkit.ledger` for entry
hashes; `scripts/check_append_only.py` for the append-only rule (uses `git show` for blob
comparison).

## Derived artifacts

A derived artifact is held to the composition of the two routes:

```text
immutable source/input identity
            |
            v
     deterministic transform
            |
            v
       derived identity
```

The study already names these:

| Role | Existing field |
|---|---|
| input identity | `input_hash` on every registered-mode ledger entry |
| derived identity | `output_hash` on every registered-mode ledger entry |
| receipt binding | `receipt_hash` = sha256 of the receipt body |
| gate source identity | `gate_code_hash` = sha256 of the gate function's source |
| direction identity | `result_sha256` in the `direction_derivation` gate result |
| split identity | `manifest.json` carrying per-arm sha256 and exclusion hash |

A derived record must record an immutable input identity and a derived identity, and the ledger's
registered mode enforces this: `Ledger.record()` raises `LedgerError` if either hash is absent.

## Frozen identities must be reproducible

A record asserting an identity — a split manifest hash, a direction digest, a receipt hash — must
be reproducible from the artifacts it names. Either:

* the record names an artifact and the check **re-derives** the digest from committed bytes; or
* the artifact is in `.gitignore` (split JSONL, results), and the record names it alongside a
  reproducible build command (`python harness/build_splits.py --run-id <id>`).

A digest with no reproducible source is decorative. The `split_integrity` gate exists precisely to
catch the case where a manifest claims a hash that the rebuilt arm does not match.

## Reconstructed events

A study event that happened before its record was written is a **reconstructed event**. A ledger
entry written today about a gate that ran yesterday is indistinguishable from one written at the
time unless it says which it is.

Every reconstructed event carries three fields:

| Field | Meaning |
|---|---|
| `event_occurred_at` | when the event actually happened (ISO 8601 UTC) |
| `entry_recorded_at` | when this entry was written (ISO 8601 UTC) |
| `reconstruction_evidence` | the immutable identifier it was reconstructed from |

`recorded_retroactively: true` requires all three, requires that the entry was written strictly
after the event, and requires immutable evidence. An entry whose dates differ without declaring
`recorded_retroactively` is a validation failure: that is exactly the masquerade this prevents.

**Enforced by:** `harness/preflight.py:require_retroactive_dating` on audit.

## Gate non-vacuity

A gate that returns success without examining anything is indistinguishable from one that examined
everything and found nothing wrong.

Every gate reports an **execution census** alongside its result:

```text
discovered == checked + blocked + skipped
checked    == passed + failed
```

A counter set that does not add up is itself a failure, because counters that disagree are a symptom
of the same class of bug. A skip without a reason is a failure. A gate declares what its population
is:

| Policy | Meaning |
|---|---|
| `REQUIRED_NONEMPTY` | The inputs exist by construction; discovering none means discovery is broken. |
| `CONDITIONALLY_REQUIRED` | Required only while a stated precondition holds. |
| `OPTIONAL` | May legitimately have no inputs; recorded as a skip with a reason. |

The distinction matters because making every empty population fail would be as wrong as making every
empty population pass. The `split_integrity` gate requires arms because this study declares arms; a
study that declares none is skipped with a reason rather than failed or silently passed.

**Enforced by:** `harness/verification/accounting.py:Census`, checked after every gate in
`harness/gates.py`.

## Verifier contract versions

The contract version is in `harness/verification/__init__.py` and reported by every gate receipt.
Bump it whenever the set of checks, their discovery rules, or their non-vacuity requirements change
such that a PASS means something different.

| Version | What a PASS means |
|---|---|
| v1 (pre-overhaul) | Gate assertions passed. No census, no non-vacuity proof. A gate could exit 0 without validating. |
| v2 | Every required population was examined and passed, with an explicit census. Contract version recorded in every receipt. |

A PASS recorded under v1 is not equivalent to one under v2, and no historical receipt is rewritten
to imply otherwise. Receipts without a `contract_version` field are v1 by absence.

**Enforced by:** `harness/verification/__init__.py:CONTRACT_VERSION`; recorded in every receipt by
`gdkit.gates.run_gate` (via the `contract_version` field added to the receipt body).

## Upstream issue recording

When the study discovers a bug in an upstream dependency — a `transformers` version that produces
different state-dict key names than documented, a `torch` op that returns non-deterministic results
on a specific GPU, a `numpy` broadcast that silently promotes dtype — the study records the issue
and its resolution in the run's ledger and in `docs/upstream_issues/`.

### What the study records internally

Each upstream issue is recorded as a ledger entry with `op: "upstream_issue"` and a companion
Markdown file in `docs/upstream_issues/<SLUG>.md`:

**Ledger entry fields:**

| Field | Description |
|---|---|
| `slug` | Short identifier, e.g. `transformers-qwen35-linear-attn-key-names` |
| `package` | Affected package name and pinned version |
| `severity` | `blocking` (run cannot continue), `degrading` (results affected), `cosmetic` |
| `discovered_at` | ISO 8601 UTC timestamp of discovery |
| `issue_url` | URL of the filed upstream issue, or `null` if not filed |
| `pr_url` | URL of the filed upstream PR, or `null` if not filed |
| `workaround` | Brief description of the applied workaround, or `null` |
| `resolved_upstream` | `true`, `false`, or `null` (unknown) |
| `resolved_version` | Version where the fix was released, or `null` |
| `affected_gates` | List of gate names whose results could be affected |
| `affected_runs` | List of run IDs where the issue was observed |

**Companion Markdown file (`docs/upstream_issues/<SLUG>.md`) must contain:**

1. **Summary.** One paragraph: what broke, what the symptom was, how it was found.
2. **Reproduction.** Minimal script or command that demonstrates the issue on the pinned version.
3. **Impact on study.** Which gates, which runs, which results are affected and how.
4. **Workaround.** Exact code or configuration change applied, with the commit that applied it.
5. **Upstream status.** Link to the issue/PR, current status, and the version where the fix
   landed (if any).
6. **Resolution for this study.** Whether the workaround is permanent (pinned around the bug) or
   temporary (will adopt the fix when the pinned version bumps).

### What the upstream issue filing should contain

When filing an issue or PR upstream, include:

* **Exact versions.** Package version, Python version, OS, GPU model and driver if relevant.
* **Minimal reproducer.** Self-contained script, not a reference to our study.
* **Expected vs actual behaviour.** Concrete values, not "it doesn't work."
* **Pinned checkpoint or dataset.** If the bug is model-specific, the exact revision.
* **No study-internal references.** The upstream issue stands alone; our study is not their problem.

### What never goes upstream

* Unreleased model weights, harmful prompts, or generated text from this study.
* Internal run IDs, ledger entries, or receipt hashes.
* Complaints. A bug report states facts and provides evidence.

**Enforced by:** convention in this document and review. A `blocking` issue without a workaround
recorded in the ledger is a preflight refusal (`require_upstream_clear`).

## Method admission prerequisites

The method review checklist in `harness/methods/README.md` lists nine requirements. Two of them —
compute evidence and tensor-name verification — had no code-enforced gate prior to this overhaul.
They are now enforced:

### Compute evidence

A method may not be admitted (no `method_selected` ledger entry) until a `compute_evidence` entry
exists in the run's ledger, recording:

* GPU model and count
* Wall-clock seconds for one `apply()` call on the registered model
* Peak GPU memory (MB)
* The host fingerprint that matches the run's `host_provisioned` entry

**Enforced by:** `harness/preflight.py:require_compute_evidence`, called by
`harness/gates.py:require_admitted`.

### Tensor inventory

A method may not be admitted until a `tensor_inventory` entry exists in the run's ledger, recording:

* The registered model's state-dict key names as loaded by the pinned `transformers` version
* The shapes and dtypes of every target tensor the method intends to modify
* The `transformers` version and the model revision used for the inventory
* A sha256 of the serialised inventory

**Enforced by:** `harness/preflight.py:require_tensor_inventory`, called by
`harness/gates.py:require_admitted`.

## What this document does not cover

Thresholds, endpoints and decision rules live in the pre-registration. This document does not
restate them, so it cannot become a second place to change them.

The ledger format, the chain integrity check, and the append-only rule are documented in
`runs/README.md` and `docs/protocol/RUN_PROTOCOL.md`. This document states the *provenance model*
those mechanisms serve, not the mechanisms themselves.

## References

This provenance model draws on:

### Pre-registration and study design

* The study's own pre-registration (`.gdkit/project.yaml`, entry 0 of every run's ledger).
* Hofman, Sharma & Watts, "Pre-registration for Predictive Modeling" (arXiv:2311.18807, 2023) —
  adapting pre-registration from social science to ML; discusses templates, pitfalls, benefits.
* Vaccaro, "Preregistration for Experiments with AI Agents" (arXiv:2606.11217, 2026) — extends
  pre-registration to AI agent experiments.

### Provenance and reproducibility infrastructure

* The OpenGrad project's provenance and verification infrastructure, which surfaced the failure
  modes this model prevents (gates passing on empty populations, digests over working-tree bytes
  instead of committed bytes, reconstructed events reading as contemporaneous).
* Samuel et al., "ML Pipelines: Provenance, Reproducibility and FAIR Data Principles"
  (arXiv:2006.12117, 2020) — systematic treatment of provenance tracking in ML pipelines.
* Ojewale et al., "Audit Trails for Accountability in Large Language Models"
  (arXiv:2601.20727, 2026) — append-only audit stores with lightweight emitters for LLM
  accountability; directly relevant to hash-chained ledger design.
* "AuditableLLM: A Hash-Chain-Backed, Compliance-Aware Auditable Framework for LLMs"
  (MDPI Electronics, 2025) — hash-chain audit framework for LLMs; closest existing work
  to our ledger design.
* Pineau et al., "Improving Reproducibility in Machine Learning Research" (JMLR 2021) — the
  reproducibility checklist.
* The ACM artifact review and badging policy (2020 revision) — levels of reproducibility.
* Stodden, McNutt & Bailey, "Enhancing reproducibility for computational methods" (Science, 2016)
  — the case for recording every dependency version.

### Gate-based protocols and staged validation

* "TimeGate: Sustainable Time-Boxed Promotion Gates for Continual ML Adaptation Under Resource
  Constraints" (arXiv:2605.29183, 2026) — quantitative promotion gates with auditable decisions
  for ML pipelines; closest analogue to our gate-based protocol.

### Abliteration lineage

* Arditi et al., "Refusal in Language Models Is Mediated by a Single Direction"
  (arXiv:2406.11717, 2024; NeurIPS 2024) — the abliteration method this study tests.
* Zou et al., "Representation Engineering: A Top-Down Approach to AI Transparency"
  (arXiv:2310.01405, 2023) — upstream RepE framework.
* "The Geometry of Refusal in LLMs: Concept Cones and Representational Independence"
  (arXiv:2502.17420, 2025) — extends refusal geometry beyond single direction.
* Pan et al., "The Hidden Dimensions of LLM Alignment: Multi-Dimensional Analysis of Orthogonal
  Safety Directions" (arXiv:2502.09674, 2025; ICML 2025) — multi-dimensional refusal analysis.

### Software provenance and upstream issue recording

* Dhruv & Dubey, "Managing Software Provenance to Enhance Reproducibility in Computational
  Research" (arXiv:2308.15637, 2023) — lab-notebook model for recording software versions,
  modifications, and execution environments.
* Smith, Katz & Niemeyer, "Software Citation Principles" (PeerJ CS, 2016; FORCE11) — Principle 4
  (Specificity): cite the specific version of software used, including modifications.
* Barker et al., "Introducing the FAIR Principles for Research Software (FAIR4RS Principles)"
  (Scientific Data, 2022) — R1.2 (Provenance): software artifacts must include detailed
  provenance; discovered bugs in dependencies are provenance-critical metadata.
* Hinsen, "Dealing With Software Collapse" (Computing in Science & Engineering, 2019) — upstream
  changes breaking downstream research code; argues for explicit recording of dependency behaviour
  assumptions.
