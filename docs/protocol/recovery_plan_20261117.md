# Recovery plan and owner decisions — 2026-11-17

Status: Arjhine selected **A1/B1/C1** on 2026-11-17: local implementation and verification
only; a fresh linked run for future corrected measurements; preserve the historical
remote ledger unchanged. No remote mutation, run creation, GPU execution, artifact reuse,
or scientific protocol change is authorized by these selections.

The local implementation and exercised verification are recorded in
[`local_provenance_contract_20261117.md`](local_provenance_contract_20261117.md).
Remote validation, model-artifact certification, image/dependency review, and scientific
measurement decisions remain outside the completed local checks.

## Objective and boundaries

Make the next measurement auditable without changing the study's goal or manufacturing
upstream bug reports. Preserve all existing evidence and its limitations. The current
state is documented in [the read-only inventory](evidence_inventory_20261117.md).

Three distinct questions must be answered:

1. **Preservation:** do the original bytes still exist?
2. **Execution provenance:** which code, environment, host and inputs produced an output?
3. **Measurement validity:** does that output measure the intended construct?

The proposed next phase addresses the second question while maintaining the first.
It does not by itself establish the third or recover missing historical bytes.

## Proposed implementation sequence

### 1. Separate code releases from research artifacts

Create a code-only release operation with an explicit payload allowlist. It must never
include `runs/`, private notes, credentials, or unrelated working files. Deploy reviewed
source into an immutable release namespace or image, not over mutable live code.

A generated manifest identifies actual source bytes, revision, dependency lock and
resolved runtime/image identity. A Git commit alone does not describe uncommitted edits;
a whole-repository Git archive is not automatically a safe code-only payload. Any
local development snapshot must be labeled as such, not presented as a reviewed release.

A code deployment must not synchronize a ledger, and artifact synchronization must not
implicitly deploy code. Unknown or differing protected evidence stops the operation.

### 2. Unify and preserve host evidence

Replace the conflicting producer/preflight/gdkit host conventions with one enforced
contract for future executions. Keep a new immutable host snapshot for each execution
session, including structured metadata and privately retained raw collector evidence.
The receipt must identify and verify the host that executed its gate.

Old `host_provisioned` records and receipts remain unchanged and interpretable under
their historical contract. New measurements must not silently accept an unchecked host.
A future host record must not replace an earlier snapshot or cause an auditor to mistake
the latest machine for the machine that produced an older result.

### 3. Bind the complete execution through existing receipts

Extend the existing versioned verification/receipt mechanism rather than creating a
parallel evidence system. Explicitly bind the source/helper modules, model/tokenizer
artifacts and revisions, data/configuration, consumed intermediate artifacts, host,
logs and outputs needed for the gate's documented dependency closure.

Remove runtime helper monkeypatching from the measured execution path. Hash actual
persisted output bytes, including NPZ and per-item JSONL. Keep legacy hash conventions
only for historical interpretation; do not normalize old bytes or rewrite old receipts.
Avoid circular receipt/output-manifest hashes.

A receipt's data format version and the verifier's contract version are distinct. A
version label must correspond to enforced checks, not merely a new field. Distinguish
completed, failed, refused, and historical/stale evidence. A later ledger entry can make
an earlier receipt stale for current-head promotion without destroying its historical
meaning.

### 4. Demonstrate the contract locally

Use temporary directories and small artifacts to exercise the real filesystem and
receipt paths. Demonstrate both acceptance of a complete valid attempt and rejection of:

- Changed code/helper, input, host snapshot, or output bytes.
- Missing declared dependencies or required outputs.
- Occupied receipt, final/partial log, or measurement paths.
- Repeated requests, stale writers, and interrupted operations.
- Unchecked hosts and false success after an execution failure.

Intentionally modifying a temporary copy to test our verifier is fault injection, not
evidence of an upstream defect. Record commands, output, timestamps, duration, and
platform limitations. CPU tests do not establish GPU numerical equivalence or throughput.

### 5. Review before any remote validation

Existing Modal smoke functions request a GPU. A genuinely CPU-only smoke requires a
new explicit entrypoint and a disposable namespace, with no access to write historical
runs. Remote writes and possible CPU charges are not implied by local tests.

Modal's local filesystem locks and last-write-wins volume semantics do not provide
distributed compare-and-swap. A delay, lease-file convention, or final reread cannot
guarantee exclusion of a late writer. Any future in-place ledger append requires reliable
exclusive writer control; if that cannot be established, refuse. Do not replace an entire
ledger file and call it append-only synchronization.

## Owner choices

### A. Scope of the next engineering phase

- **Local implementation and verification only (recommended):** return with evidence
  before requesting deployment permission. No remote mutation or GPU execution.
- **Local implementation, then conditional isolated CPU smoke:** permits the new disposable
  remote smoke only after the documented local acceptance checks pass. Fewer approval stops,
  but grants limited remote-write/CPU-spend authority in advance. Historical runs and GPUs
  remain excluded.

### B. Organization of future corrected measurements

- **Fresh linked registered run (recommended):** preserve the old runs, freeze the same
  pre-registration, and explicitly carry lineage and known post-baseline amendments.
  New host evidence precedes the first measured gate. A new directory does not turn a
  post-baseline amendment into a pre-data decision.
- **Versioned attempts within the existing run:** retain one run ID, but migrate attempt
  discovery, receipt selection, attestation and promotion semantics. More implementation
  and audit complexity; no attempt may overwrite another.

This is a design choice only. It does not authorize creating the run, reusing old
measurement outputs, retiring historical findings, or starting measurements.

### C. Historical remote ledger policy

- **Leave the remote historical copy unchanged (recommended with a fresh run):** retain
  the documented 28-entry replica and the complete 29-entry local/snapshotted history.
  It is not an active execution target. The extra local entry is not assumed committed.
- **Plan a later one-time append of the already-approved seq28:** pursue only after safe
  exclusive access and append behavior are established and remote mutation is authorized.
  Refuse if those conditions cannot be proved. This adds no new decision text and cannot
  repair host/provenance gaps or make old receipts current.

## Scientific decisions deferred

After engineering verification, separately review explicit-refusal definitions, human
calibration and sampling, per-item safe-prompt recording, capability seeds/revisions/
prompt-policy/result coverage, and controls-v2 topic/source implementation. Preserve the
approved thresholds. Establish correctness before rolling out inference optimizations.
Any GPU validation needs an explicit workload, cost ceiling and stop conditions; none is
approved here. Matching hashes alone do not authorize reuse of old measured artifacts.

## Review and evidence

Independent Fable and Argon recommendations and the requested Claude Opus 4.6
reconciliation completed successfully. Requested identifiers, returned metadata, prompts,
outputs and generated hashes are retained in gitignored local review records. The
recommendation was A1/B1/C1. The owner subsequently selected those options; the authority
and exclusions are recorded at the top of this document.

Raw reviewer output is not an authority for facts. Corrections include a reviewer-invented
run ID, stale kappa values, an unjustified permanent-loss claim, and unsafe check/write/lease
suggestions. The corrected-invocation kappa is 0.816, but agreement still does not establish
human-ground-truth accuracy. Exact schema numbers and implementation details will be settled
against the existing contract, not copied uncritically from reviewer proposals.

Methodological support, verified through `pwc paper info` metadata/abstracts only:

- [An Experience Report on Machine Learning Reproducibility](https://arxiv.org/abs/2107.00821v2): reproducibility requires explicit engineering processes.
- [Datasheets for Datasets](https://arxiv.org/abs/1803.09010v8): document collection, composition and intended use.

These papers do not validate the proposed filesystem protocol. Modal behavior follows
its [Volume API documentation](https://modal.com/docs/reference/modal.Volume) and the
observed implementation; scientific interpretation requires separate evidence.
