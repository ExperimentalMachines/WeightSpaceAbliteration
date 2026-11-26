# Evidence inventory — 2026-11-17

## Scope and method

The operator authorized a read-only inventory before further execution. No registered run
file, ledger line, receipt, log, frozen pre-registration, or remote file was modified.
No GPU function, deployment, volume commit, upload, or synchronizing pull was invoked.

The inventory used Modal SDK 1.5.5 with Python 3.11.15 and only Volume listing/read APIs.
It captured all current `runs/**` files plus nine explicit source/configuration references.
The completed remote pass ran **2026-11-17T13:29:31Z–13:33:41Z**, taking **249.516 seconds**.
An initial 9.81-second attempt stopped at an absent optional source file because this SDK
raises `modal.exception.NotFoundError`, not `FileNotFoundError`. The existing local snapshot
was retained; only the failed remote stage was resumed after handling that exception.

Private captures, scripts, comparison records, and generated hash manifests are retained
under `.omp/evidence-inventory/20261117T132621Z/`. All 243 files there were confirmed
ignored by Git. A separate local-only backup is stored outside the repository as
`../WeightSpaceAbliteration-local-backups/evidence-inventory-20261117T132621Z.zip`.
Its 242 members were verified against generated SHA-256 digests. The archive is
196,074,107 bytes and contains private research outputs and host metadata; do not publish it.

## Current local and remote state

| Item | Local | Modal workspace |
|---|---:|---:|
| Current files under `runs/` | 95 | 95 |
| Original-run ledger entries | 22 | 22 |
| Qwen-run ledger entries | 29 | 28 |
| Total files captured including source/config references | 104 | 103 |

Of the 95 run files, **94 are byte-identical**. The only difference is the Qwen ledger:
remote bytes are an exact prefix of local bytes. Local seq28 records the owner-approved
controls-passing v2 deviation; that append is absent remotely. Both versions were preserved,
not synchronized or replaced. The original-run ledger is byte-identical on both sides.

The additional source differences are `harness/gates.py`, `scripts/record_host.py`, and
`modal_runner.py`, consistent with the local overwrite-guard changes. The remote harness
listing confirms that `artifact_guard.py`, `artifact_sync.py`, and `gates_optimized.py`
are absent. **The new protections are not deployed remotely.**

All 104 local source-file fingerprints and metadata remained unchanged through capture.
Remote run-listing type/size/mtime remained unchanged, and both remote ledgers had stable
hashes on reread. There were no read failures or nonregular run entries in the completed pass.
These observations describe a read interval, **not an atomic volume snapshot**; metadata
stability does not prove every remote byte was constant throughout the interval.

## Historical evidence coverage

The inventory also examined the earlier local preservation ZIP's previously verified manifest
and reachable Git history, preserving 12 historical Git evidence blobs separately. Original
schema-0 split-integrity receipts remain available in Git/the earlier backup. No historical
receipt was restored over the current working copy.

The Qwen ledger contains **ten** `host_provisioned` entries. Matching `host.json` bytes were
found only for seq27, in local and remote snapshots and the earlier backup manifest. No
matching copy was found for seq16, seq17, or seq19–25: **nine earlier host records**.
Earlier audit prose describing eight earlier missing host snapshots was an undercount;
this corrects the inventory count without changing any ledger entry or measurement.

No separate pre-correction behavioral receipt/log/result versions were found in the checked
stores. Current local/remote equality does not recover versions previously overwritten.
This is not a claim of permanent loss: external backups, filesystem snapshots, unreachable
Git objects, and provider-side historical snapshots were not exhaustively searched.
Hashes cannot reconstruct missing bytes, and hashes computed now cannot retroactively bind
artifacts omitted from the original receipts.

## Measurement artifacts and auditability

| Artifact | Observed coverage | Limit |
|---|---|---|
| Harmful-prompt responses | Primary: 293 rows; large: 15,640 rows. IDs match split IDs in count and order; no duplicates, missing IDs, or unexpected IDs. | Stored `refusal` fields still reflect the previously documented classifier-construct problem; matching IDs do not validate labels. |
| Safe-prompt over-refusal | Aggregate `over_refusal.json` exists. | No per-item safe-prompt generations were found in the inventoried run stores. The aggregate alone cannot support human calibration of those outputs. |
| Activations and directions | NPZ arrays and associated JSON summaries are preserved. | Current preservation does not repair omitted historical output bindings. |
| Capability evaluation | No measurement output found. | The baseline remains incomplete. |
| Receipt-declared inputs/logs | All 167 declared input references match snapshot hashes; all ten schema-1 log references match. | Coverage checks only what receipts declare, not every dependency or executed helper. Ten schema-1 receipts explicitly record `host_check.checked=false`. |

The checks above are artifact-coverage observations, not a claim that the scientific
measurements are validated. In particular, neither data preservation nor judge agreement
establishes that harmfulness-negative output is explicit refusal.

## Private-directory boundary

Remote root metadata showed a pre-existing `.omp` directory. A names/types-only inspection
found two historical files totaling 391,467 bytes. Their contents were not read or removed.
The current `upstream-notes` and `evidence-inventory` directories are not present remotely.
An upload exclusion prevents future copying; it does not remove already uploaded files.

## Next decision

Keep GPU execution held. Do not run the old remote entrypoints or use a forced upload to
resolve the ledger difference. The local guarded uploader deliberately refuses a differing
remote ledger before uploading code.

The next engineering design should separate code deployment from run-artifact synchronization,
provide a verified append-only ledger synchronization path, and address immutable host records
and complete code/input/output provenance. Review that design before deployment or gate changes.
Measurement-construct validation remains a separate prerequisite for new scientific results.
This inventory authorizes none of those subsequent mutations or measurements.

## Engineering lessons

- **Replica agreement is not history preservation.** Two matching current copies can both lack
  an earlier version. Keep immutable attempts/snapshots, not just synchronized paths.
- **A metric is not an auditable dataset.** Per-item inputs, outputs, identities, and measurement
  configuration are needed to diagnose and validate an aggregate.
- **A ledger and artifact store serve different purposes.** The ledger records relationships and
  decisions; the store must retain the actual bytes those relationships name.
- **Integrity is not construct validity.** Correct hashes can preserve an incorrectly defined
  measurement perfectly. Both software provenance and scientific validation are necessary.
