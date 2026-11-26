# Resumption review — proposed next step

Status update: the overwrite guard was subsequently approved and implemented locally;
see `EXECUTION_LOG.md`, "Approved overwrite guard implemented locally". Other recovery
and validation recommendations remain proposals. No GPU execution or protocol amendment
is authorized here.

## Evidence and review record

Both requested consultants completed successfully: `fable` and `gemini-4-argon`.
Complete outputs, stderr, invocation timestamps, and the identical prompt are beside
this file. Model aliases are requested identifiers; these records do not independently
prove a particular resolved backend model version. PWC metadata/abstract lookups,
raw response hashes, and verification scope are in `paper_lookups/lookup_manifest.json`.
These are off-run research records, not newly appended registered paper-ledger entries.

A verified local-only ZIP preserves 41 current metadata/code/receipt/log files and the
committed split-integrity receipt separately. It is outside the repository in
`WeightSpaceAbliteration-local-backups/resume-audit-20261117T121241131518Z.zip`.
This is not a complete backup of datasets or all raw results, nor proof of recovery
of historical overwritten artifacts. Original run files have not been modified.

## Agreement supported by code inspection

1. Hold further measurements. Preserve evidence and validate the refusal construct first.
2. HarmBench-positive and explicit refusal are distinct. The current complement cannot
   establish 81.6% explicit refusal or 61.3% over-refusal. High kappa does not repair this.
3. The optimized module has an invalid import and retained caller model references.
   It is unvalidated and must not be deployed as ready.
4. Capability fixes must cover revisions, seeds, prompt policy, paths, fresh outputs,
   required task/metric coverage, and rejection of empty results.
5. CPU/synthetic off-run repairs and tests may precede any new GPU validation, with
   owner approval. Construct validation requires human labels, not merely unit tests.
6. A fresh measurement namespace after validation is the conservative proposal. Existing
   run bytes must remain intact; a deviation does not authorize receipt/log overwrites.

## Corrections and limits to consultant advice

- Reject restoring tracked run files to HEAD, even when proposed by Argon. Preserve
  separate copies; do not erase a version of the evidence to make git look clean.
- Fable's claim that no denominator deviation exists is incomplete: the original run
  records the split rebuild at seq16 and rate-based decision at seq17 (primary 293,
  max11; large 15640, max594). The Qwen run's seq3 records the rebuilt counts. Whether
  all cross-run links meet protocol is a separate audit question; the decision is not absent.
- A rounded 81.6% matching a quoted prior is not evidence of manipulation or circularity.
- Missing earlier behavioral receipts locally is not proof that no backups exist.
  Remote/recovery inventories are still pending; do not label bytes unrecoverable yet.
- Saved over-refusal per-item generations appear absent. Do not promise human calibration
  can use those generations until their existence is verified. Sampling/rubric approval
  must precede selecting the required 200 examples; do not select based on judge outcomes.
- No automatic operational stop was demonstrated in earlier runs. Completion flags and
  a narrative rule are not an enforced 60–95% validity check. That check remains unresolved
  until actual refusal is measured.
- Probe AUC remains a recorded separability measurement. Source-aliasing, geometric
  effects, selection, and instrument validity limit any causal refusal-erasure claim.
  Keep controls v2 unchanged while reviewing; do not weaken it to obtain a pass.

## Local checks

- Ledger verification passed (22 and 29 entries, clean answer drift).
- Staged append-only check passed; it does not include the changed unstaged receipt.
- Present receipt self-hashes and schema-1 log hashes verified.
- Result JSON digests checked match bytes without the trailing LF, not actual file
  bytes. This existing convention is documented in `receipt_integrity.json`; no hashes
  or files were rewritten to disguise it.
- Existing `pytest -q tests` ran for 300 seconds and timed out after reaching 87%
  and four additional passing-test dots. No displayed failure, but the suite is NOT
  certified passed. The optimized module is not covered by that test result.

## Recommendation for owner

Preserve and inventory first; fix synchronization so it cannot overwrite evidence;
validate the classification/refusal distinction and human-calibration procedure;
prepare/test capability and inference code off-run. Only then approve a separate GPU
validation and decide a fresh registered measurement namespace. No retirement,
restoration, reclassification, new run, or expensive rerun has been executed here.

## Sources checked independently (metadata/abstract only)

- [HarmBench](https://arxiv.org/abs/2402.04249): red-teaming evaluation framework.
- [XSTest](https://arxiv.org/abs/2308.01263): exaggerated safety behavior on safe prompts.
- [OR-Bench](https://arxiv.org/abs/2405.20947): over-refusal measurement.
- [Probing Classifiers](https://arxiv.org/abs/2102.12452): methodological limitations.
- [Amnesic Probing](https://arxiv.org/abs/2006.00995): limits of behavioral inference from probing.
- [Harmfulness and Refusal Separately](https://arxiv.org/abs/2507.11878): distinct concepts.

These citations support the distinctions, not arbitrary numerical cutoffs or promised speedups.
