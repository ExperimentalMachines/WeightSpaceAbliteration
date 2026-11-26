# Local execution-provenance contract — 2026-11-17

## Authority and scope

Arjhine selected A1/B1/C1: local implementation and verification only, a future fresh
linked measurement run, and no historical remote-ledger mutation. This work implements
local execution contract 3; it does not deploy it, initialize the future run, authorize
measurements, reuse old measured outputs, or change scientific thresholds/definitions.
All 96 protected files (current run files and frozen pre-registration) remained unchanged.

This is the A1-phase record. The later
[`dependency target adoption`](dependency_update_20261117.md) replaces the floating
supplementary-install recipe and records its separate local validation; it does not
retroactively expand the checks reported here or certify remote execution.

## Implemented boundaries

- `harness/releases.py` and `scripts/build_release.py`: explicit code-only allowlist,
  deterministic content-addressed manifest, exact Git-revision or explicitly marked
  development snapshots, source verification and non-overwriting publication. The
  builder refuses output destinations inside protected run/preregistration/Git trees.
- `harness/host.py`, `scripts/record_host.py`, and host preflight: immutable canonical
  session files/events compatible with gdkit's same-host check. Raw requested probe
  stdout/stderr bytes are retained privately. New execution refuses unchecked hosts and
  legacy migration; historical verification does not collect the auditor's host.
- `harness/execution.py`: immutable pre-execution manifest, bounded source/callable/constant
  identity, enumerated input hashes, exact output hashes, canonical host binding and
  preserved failure diagnostics through existing gdkit receipts. Harness contract 3 is
  separate from gdkit receipt schema 1; old receipts are not rewritten.
- `scripts/verify_execution.py`: read-only separation of artifact validity, current-ledger
  freshness, and the gate's own `passed` result. Missing release snapshots or incompatible
  execution interpreters yield incomplete identity verification, not a clean pass.
- Gate helpers are statically imported. Runtime patch entrypoints and the obsolete
  `fast_inference.py` patch module were removed. The historical corrected fast-session
  computations remain explicitly labeled legacy/unvalidated for refusal interpretation;
  no numerical-equivalence or speedup claim was made.
- `modal_runner.py`: explicit run/release selection and code-only `upload_release`, replacing
  blind `upload_repo`. Development bundles are refused for upload, and a committed bundle
  still requires explicit review attestation. Source/bootstrap/image-input checks and
  required hardware probes are prepared, but no remote path was executed here.

## Verification evidence

| Check | Observed result | Duration |
|---|---|---:|
| Integrated release, host, execution, preservation, gdkit, append-only and census tests | 298 passed, 20 skipped | pytest: 135.41 s; wrapper: 136.86 s |
| Publication tests with actual Modal SDK and a filesystem volume adapter; no API calls | 11 passed | pytest: 15.09 s; wrapper: 17.703 s |
| Actual local release/host/gate/verifier CLI smoke on a temporary CPU fixture | Passed the lifecycle and negative cases below | command wall time: 7.00 s |
| Protected-file comparison | All 96 hashes and the protected file set unchanged | recorded after verification |

The final integrated test wrapper ran **2026-11-17T15:02:04Z–15:04:20Z**; the publication
wrapper ran **15:02:04Z–15:02:21Z**. All skips required Windows symlink-creation privileges
unavailable on this host. No complete-suite, Linux/Modal-runtime, GPU, or model-inference
validation is claimed.

The CLI smoke built a development release from actual local runtime source, verified the
bundle against that source, recorded a real local CPU host, and ran the existing cheap
`split_integrity` gate on two synthetic fixture rows. It then observed:

1. A complete receipt verifies as valid and current.
2. Repeating the gate refuses occupied evidence and leaves the receipt unchanged.
3. A second immutable host session makes the earlier receipt stale, not corrupt; historical
   verification remains valid, while `--require-current` refuses it.
4. Altering the temporary input causes verification to fail without repairing the receipt.

Only temporary fixture ledgers were executed. They are not registered study runs. Raw test
logs, hashes, smoke commands/output, release snapshots and fixture evidence are retained in
ignored `.omp/local-validation/20261117T144830Z/`.

## Failures found and corrected

Initial integration checks exposed a fixture ledger ID that disagreed with its directory
and obsolete test hooks targeting the removed wrapper. Fixtures were corrected, and the
mocked wiring-only test was removed rather than repinned to a new implementation detail.

The actual CLI smoke then found a real verifier defect: executable identity included
`repr(frozenset(...))`, whose ordering can differ between compilation/import and between
Python hash seeds. Identical source was falsely reported as modified. Constants now use a
canonical representation of unordered values. A subprocess regression verifies execution
and later auditing with different `PYTHONHASHSEED` values. The final reported checks ran
against the corrected implementation.

This illustrates why hashing is only as deterministic as its input representation: a
cryptographic hash does not make an unstable serialization canonical.

## Remaining limits and next approval gate

- Model-consuming gates require IDs and immutable full commit revisions. These remain
  configured artifact references, not a certificate of the bytes in downloaded model caches.
- The existing image recipe still contains supplementary dependency installs outside
  `uv.lock`; image/dependency review is required before deployment. No image rebuild or
  remote environment certification occurred.
- The unvalidated experimental `gates_optimized.py` remains outside the runtime release
  allowlist. A successful local provenance check does not validate that module.
- Host checks cover the declared metadata/probes. Default host collection is CPU/package
  metadata; future GPU wrappers require successful GPU and CUDA/cuDNN probes. Collector
  limitations are recorded, including gdkit's unavailable raw ancillary Git-probe streams.
- Callable checks cover explicit registered Python functions/constants and source bytes;
  they are not OS-level tracing or protection against an adversarial process that controls
  the verifier itself.
- Local locks and adapter tests do not provide distributed Modal compare-and-swap. Historical
  remote artifacts remain unchanged. No remote synchronization is planned under C1.
- Refusal-construct calibration, capability correctness, topic/source controls, population
  checks, and inference performance remain separate work. Valid provenance is not scientific
  validity, and this local verifier is not a promotion authorization.

Next: review this local evidence and the unresolved image/dependency boundary before
considering an isolated CPU-only remote smoke. Any such deployment, new namespace, or
remote writes require a separate owner decision. GPU work remains outside that decision.
