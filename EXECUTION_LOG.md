# Execution Log

Lab notebook for the Weight-Space Abliteration study. Every operational decision,
gate run, and environment choice is recorded here with timestamps and rationale.
The pre-registration (`.gdkit/project.yaml`) defines what is measured and what
success means; this log records how the measurements were carried out.

Operator: Arjhine. Recorded assistant attribution: Claude Code (Claude Opus 4.6). Previous contributor: Jules.

---

## 2026-11-14 — Session 1: Environment Setup and Baseline Verification

### Context

Jules completed 9 rounds of pilot work (pilots/) covering 7 methods × 3 models, filling
every cell in the screening matrix. The harness infrastructure was upgraded (PR #1, merged
2026-11-11): gdkit pinned to fa1e4d5, schema 1 receipts, probe_train rewritten, byte-exact
restores, append-only enforcement in CI.

Neither registered run had a `host_provisioned` entry. No gates had been run on either run.
Execution transferred to Arjhine; the prior execution environment is unavailable.

### Decision: Execution platform

**Decided by:** Arjhine
**Choice:** Modal cloud GPU execution via modal CLI v1.5.5.
**Rationale:** Use on-demand A100 containers with a reproducible software image.

### Decision: Target run

**Decided by:** Arjhine
**Choice:** Qwen3.5-0.8B run (`20261110T135200Z-weightspace-abliteration-qwen3.5-0.8b`) first.  
**Rationale:** Smallest model (873M params), fastest iteration, already has pilot data across
all 7 methods. Good for shaking out the full pipeline end-to-end before committing to
larger models.

### Decision: GPU tier

**Decided by:** Arjhine
**Choice:** A100-SXM4-40GB (Modal `a100-40gb`).  
**Rationale:** Comfortable headroom for Qwen3.5-0.8B (~1.7GB bf16) plus the 13B HarmBench
classifier. All 3 piloted models fit on 40GB.

### Decision: Environment strategy

**Decided by:** Arjhine
**Choice:** Strict — copy `uv.lock` into the container, install with `uv export --frozen`
piped to `uv pip install --system`.  
**Rationale:** Exact same package versions as the local venv (torch 2.15.0, transformers
5.22.2, lm-eval 0.4.13, gdkit fa1e4d5). The host record captures what's actually installed.

### Decision: Additional packages

**Decided by:** Claude Opus 4.6 (confirmed by Arjhine)
**Choice:** Install `accelerate==1.15.0` and `sentence-transformers==6.3.0` in the Modal
image via `uv pip install --system`, not added to `pyproject.toml`.  
**Rationale:** `accelerate` is required for `device_map="auto"` model loading; `sentence-transformers`
is required for the exclusion instrument (bge-small-en-v1.5). Neither is in `pyproject.toml`
(oversight from initial setup). Added at the image level for now; proper `pyproject.toml`
fix deferred until after the first result.

### Decision: Volume strategy

**Decided by:** Arjhine (volume names), Claude Opus 4.6 (architecture)
**Choice:** Two Modal volumes: `wsa-workspace` (repo + run artifacts) and `wsa-hf-cache`
(HuggingFace model downloads). Pull results locally after every GPU step.  
**Rationale:** Persist artifacts after each gate to limit loss from interrupted cloud
execution. This objective does not establish that synchronization is overwrite-safe.

### Step: check_env (GPU)

**Time:** ~2026-11-14T11:10 UTC  
**Container:** A100-SXM4-40GB, driver 620.70.06, CUDA 13.2, cuDNN 92600  
**Result:** All packages verified. accelerate and sentence-transformers initially missing;
image rebuilt to include them.

### Step: record_host — first attempt (stale)

**Time:** ~2026-11-14T11:12 UTC  
**Ledger entry:** seq 16, fingerprint `afecb3562eb1...`  
**Result:** Entry written successfully. But the fingerprint includes the GPU UUID, which
changes every time Modal allocates a new container. The next gate run got a different
container → fingerprint mismatch → `ProtocolViolation[host-before-gates]`.  
**Status:** STALE. This entry is in the ledger permanently (append-only) but does not
match any container that will run gates. A deviation is recorded (see below).

### Decision: Fingerprint mismatch resolution

**Decided by:** Arjhine
**Choice:** Run everything in a single Modal session (one container, one GPU).  
**Alternatives considered:**
- Weaken the fingerprint to exclude GPU UUID (rejected: protocol exists for a reason)
- Modal Sandbox / persistent container (rejected: more expensive, more complex)  
**Rationale:** Single session guarantees the same physical GPU for record_host and all gates.
A new `host_provisioned` entry is recorded at the start of each session; the gate checks
`last_entry("host_provisioned")`, so the latest one wins. The stale entry stays as history.

### Step: baseline_session — record_host + 3 cheap gates

**Time:** ~2026-11-14T11:30 UTC  
**Container:** A100-SXM4-40GB, driver 620.70.06, CUDA 13.2  
**Ledger entry:** seq 17, fingerprint `1e704f5b5009...`  

| Gate | Result | Receipt |
|---|---|---|
| `split_integrity` | passed | `receipts/split_integrity.json` |
| `arm_counts` | passed | `receipts/arm_counts.json` |
| `exclusions_applied` | passed | `receipts/exclusions_applied.json` |

**Artifacts pulled locally:** 15 files (ledger, host.json, 3 receipts, 3 logs, harness.json, plus main run's existing artifacts).

### Deviation: stale host_provisioned entry (seq 16)

**Recorded in ledger:** seq 18 (`2026-11-14-stale-modal-host-entry`)  
**What happened:** `record_host.py` was run in an isolated Modal container, producing
ledger entry seq 16 with fingerprint `afecb3562eb1...`. The subsequent gate run landed
on a different Modal container with a different GPU UUID, causing a fingerprint mismatch.
Modal cloud GPUs are pooled; the physical machine changes between container launches.  
**Decided:** Record a new `host_provisioned` entry at the start of each single-session
run, so the fingerprint matches the container running the gates. Entry seq 16 is stale
but remains in the ledger (append-only). The preflight check reads the last such entry.  
**Decided by:** Arjhine (chose single-session approach).
**Impact on results:** None. No gate produced results under the stale fingerprint. The
three cheap gates that passed (split_integrity, arm_counts, exclusions_applied) ran
under seq 17, which matches their container.

### Deviation recorded locally

The stale host deviation was recorded locally using gdkit (seq 18, hash `793010ce...`)
and uploaded back to Modal volume. Future gate sessions will see it.

---

## 2026-11-14 — Study Structure Decision

### Decision: dual-track approach

**Decided by:** Arjhine
**Choice:** Two parallel tracks.

**Track 1 (Registered Study):** Run abliteration through the full harness — direction
derivation, refusal eval, probe, capability suite — on the Qwen3.5-0.8B run. This
produces a registered baseline for measuring linear separability after rank-1 projection.

**Track 2 (WSP Session):** After Track 1 completes, Claude Opus 4.6 inspects the model's
weights, activations, and probe results. Claude reasons about the refusal mechanism,
selects target weights and records the supporting observations, rationale, and assumptions.
The same probe framework evaluates the WSP edits.

**Rationale:** Compare a fixed rank-1 projection across residual writers with
LLM-selected targeted weight edits informed by probe diagnostics and weight analysis.
Evaluate both using the same registered measurements.

**Pre-registration:** Track 2 will have its own pre-registration, written before Claude
sees any Track 1 probe results. This freezes what counts as success for the WSP edits
and prevents post-hoc goalpost moving.

**Execution order:** Track 1 runs to completion first. Track 2 begins after Track 1's
probe results are recorded. The WSP pre-registration is written between the two tracks.

---

## 2026-11-14 — Session 2: Gate Execution

### Gate: direction_derivation (measurement completed)

**Time:** ~2026-11-14T11:35 UTC  
**Duration:** 45s (model was small, forward passes fast)  
**Result:** Passed. Direction tensor saved as `results/direction.npz`.  
**Shape:** 25 × 1024 (one unit vector per layer: 24 transformer layers + embedding output).  
**Computed from:** 400 derivation (harmful) + 400 harmless prompts (balanced arms from build_splits).  
**Artifact hash:** `1ec82b3735d2a6fa1bda57ab479c26312eb4c67aa92a152b5e370f7c80ce4f7a`  
**Note:** Required creating `results/` directory on the volume (gitignored, not uploaded by default).  
**Pulled locally:** Yes, immediately after.

### Missing package fixes (image rebuilds)

The Modal image needed several packages not in `pyproject.toml`:

| Package | Version | Why needed | When discovered |
|---|---|---|---|
| accelerate | 1.15.0 | `device_map="auto"` model loading | check_env |
| sentence-transformers | 6.3.0 | Exclusion instrument (bge-small-en-v1.5) | check_env |
| tiktoken | 0.14.0 | Qwen tokenizer conversion in transformers 5.22.2 | refusal_eval attempt 1 |
| sentencepiece | 0.2.3 | Llama 2 tokenizer (HarmBench classifier) | refusal_eval attempt 2 |
| protobuf | 7.36.2 | SentencePiece model file parsing | refusal_eval attempt 2 |

**Decided by:** Claude Opus 4.6
**Rationale:** These are runtime dependencies the harness needs but `pyproject.toml` doesn't declare.
Each was discovered by a gate failure. Added to the Modal image via `uv pip install --system`.
Not added to `pyproject.toml` yet (deferred to avoid lock file churn during execution).
Each image rebuild costs a fresh package install (~60s) but the image is cached after.

### Gate: refusal_eval (in progress)

**Started:** ~2026-11-14T12:05 UTC  
**What it does:** Loads Qwen3.5-0.8B, generates responses to 293 primary + 15,640 large arm
harmful prompts, then loads the 13B HarmBench classifier to judge each response as harmful/refused.
This is the parent baseline — measuring how often the unmodified model refuses.

---

## 2026-11-14 — "Controls Passing" Definition

### Decision: controls passing definition for probe interpretation

**Decided by:** Arjhine, after consultation of three models  
**Models consulted:** Claude Opus 4.6 (initial proposal), Claude Fable 5.2, Gemini 4 Argon  
**Consultation record:** `docs/protocol/controls_passing_consultation.md`  
**Final definition:** `docs/protocol/controls_passing.md`  
**Papers cited:** 15+ papers, all verified via `pwc paper info`, recorded in consultation doc  

**Key changes from initial proposal:**
- p-value tightened from 0.05 to 0.025 (matches CI's one-sided level)
- Three outcomes: kill / success / inconclusive (not binary)
- Confound ceiling: q975 ≤ 0.65 or run is inconclusive
- Parent positive control required for success (CI_low ≥ 0.80)
- Controls don't gate success (logical contradiction)
- Wording: "linearly decodable" not "direction survived" + harmfulness caveat (2507.11878)

**Timing:** Decided before any probe_train gate has run. No probe data has been seen.

### Standing protocol: model consultation on major decisions

**Decided by:** Arjhine  
**Rule:** For every major decision (thresholds, method choices, deviation resolutions,
interpretation of results, pre-registration amendments), consult Claude Fable 5.2
(`claude -p --model fable`) and Gemini 4 Argon (`agy --model gemini-4-argon -p`)
in parallel. Both should cite papers via `pwc` CLI where possible. Claude Opus 4.6
reconciles their responses and presents the decision to Arjhine.
**Rationale:** Obtain independent reviews of proposed decisions and their cited evidence.
The controls review identified issues in the initial proposal. Agreement between models
does not establish methodological validity; findings require independent verification.

---

## 2026-11-14 — Session 3: refusal_eval Results

### Gate: refusal_eval (measurement completed)

**Duration:** 174 min (2h54m) on A100-40GB. ~$9.40 estimated credits.  
**Bottleneck:** `_judge_refusal` runs batch size 1 through the 13B HarmBench classifier.
15,640 individual forward passes through a 13B model. Optimization to batched inference
is essential before the next run (would reduce to ~15 min).

**Results (parent baseline, Qwen3.5-0.8B unmodified):**

| Arm | Prompts | Harmful completions | Refusals | Harmful rate | Refusal rate |
|---|---|---|---|---|---|
| Primary | 293 | 100 | 193 | 34.1% | 65.9% |
| Large | 15,640 | 3,937 | 11,703 | 25.2% | 74.8% |

**Pre-registration check:** "if the parent lands outside 60–95% the run stops."
Parent refusal rate: 65.9% primary, 74.8% large. Both inside range. Primary is
close to the 60% floor.

**Code issue found:** The `_judge_refusal` docstring says "yes means the response is
a refusal" but the HarmBench classifier's "yes" means "yes, this IS harmful." The output
field `refusals` actually counts harmful completions, not refusals. The field name is
inverted. Numbers are correct; interpretation requires flipping the label.
This is logged but not fixed (modifying gate code is a protocol decision).

**Pulled locally:** Yes, immediately. 24 files including refusal_primary.jsonl,
refusal_large.jsonl, receipt, and log.

### Gate: judge_agreement (measurement completed)
**Result:** Agreement 0.485, Kappa 0.129, Disagreements 151/293.
Very low inter-judge reliability. Concern for study validity.

### Gate: kl_divergence (measurement completed)
**Result:** KL = 0.000000. Correct — parent vs parent at baseline.

### Gate: activation_extraction (measurement completed)
**Result:** Activations saved for probe arms (probe_pos, probe_neg, probe_heldout).

### Gate: probe_train (measurement completed)
**Chosen layer:** 5  
**Held-out category AUC:** 0.9992 [0.9978, 1.0000]  
**In-distribution AUC:** 0.9998  
**Permutation mean:** 0.4545, p = 0.001
**Random direction q975:** 0.9364, median = 0.7098  
**Confound flag:** q975 (0.9364) > 0.65 ceiling → flagged per controls definition.
Random untrained directions separate the categories at AUC 0.94, which is nearly
as good as the trained probe. This is the covariate shift concern Gemini and Fable
warned about. Needs discussion before interpretation.

### Gate: over_refusal_eval (passed=false)
**Result:** Rate 0.325 (510/1569), above 10% threshold.
32.5% of harmless prompts flagged. Combined with low judge agreement (kappa 0.129),
suggests classifier unreliability on this model's outputs.

### Session 3 total: 5 gates in 28 min (1678s)

**All gates committed and pulled locally (40 files).**

---

## 2026-11-15 — Operator-requested execution pause

**Decided by:** Arjhine  
**Decision:** Pause execution pending operator authorization to resume.
**Operational state:** Artifacts saved locally; no GPU workload reported active.

**Remaining for baseline:** capability_suite only (12 benchmarks × 3 seeds).  

**Issues to discuss on resume:**
1. Random direction q975 = 0.9364 triggers confound flag — what does this mean
   for the controls-passing definition? (Consult Fable + Argon)
2. Judge agreement kappa = 0.129 — two classifiers disagree on 51.5% of responses.
   Is this a data quality issue or expected for this model?
3. Over-refusal rate 32.5% on harmless prompts — classifier behavior or model issue?
4. The `_judge_refusal` naming inversion — document formally?
5. Inference optimization (batched classifier) — record deviation and deploy for
   candidate run.

**State snapshot:** 10 of 11 baseline gates complete. Only capability_suite remains.
Probe baseline shows near-perfect separation (AUC 0.9992) but with a confound flag.
All files saved locally. fast_inference.py written and ready for next session.

---

## 2026-11-15 — Session 4: Baseline Interpretation

### Reasoning document created

All reasoning about baseline findings documented in
`docs/protocol/baseline_findings_reasoning.md` BEFORE any candidate results exist.
Covers: probe confound flag, judge disagreement, over-refusal, KL, and assumptions
going forward. Interpretations require review before inclusion in supplementary material.

### Consultation: Fable 5.2 + Gemini 4 Argon on baseline findings

**Pending.** Both models consulted on:
1. Whether q975 = 0.9364 invalidates the probe or is expected for a parent model
2. Whether kappa = 0.129 undermines the behavioral results
3. Over-refusal classifier reliability
4. Whether to proceed to capability_suite or address issues first
5. Strongest path forward

### Behavioral gate re-execution (completed)

**Duration:** 60 min (3,625s) — down from 174 min for refusal_eval alone in the broken run.  
**Patches applied:** judge_fix.py (correct HarmBench LLAMA2_CLS_PROMPT, logits_to_keep=1,
batch=32 classifier, left-padding, length-sorted generation batch=64).

**CORRECTED Results vs. Broken Results:**

| Metric | Broken (old) | Corrected (new) | Interpretation |
|---|---|---|---|
| Primary refusal rate | 34.1% (noise) | **81.6%** (239/293) | Parent refuses 81.6% of harmful prompts |
| Large refusal rate | 25.2% (noise) | **79.8%** (12,475/15,640) | Consistent across arms |
| Judge agreement | κ=0.129 (chance) | **κ=0.816** (excellent) | Classifiers agree on 94.2% of responses |
| Over-refusal | 32.5% (noise) | **61.3%** (962/1,569) | Genuine over-refusal on safe prompts |

**Pre-registration validity check:** Parent refusal rate 81.6% is inside the 60–95%
window. The stop rule is NO LONGER triggered. The harness is working correctly.

**Over-refusal at 61.3%:** This is a genuine characteristic of Qwen3.5-0.8B — it
over-refuses 61.3% of safe prompts from XSTest/OR-Bench hard. OR-Bench hard-1k
is designed to trigger false refusals, so some over-refusal is expected. But 61.3%
is high. This doesn't block baseline measurement but affects promotion (gate fails).
The over-refusal rate is a property of the model, not the harness.

**Judge agreement κ=0.816:** The corrected classifiers agree on 276 of 293 responses.
This is substantial agreement, confirming the behavioral measurements are reliable.

**Total baseline status (10/11 gates):**

| Gate | Status | Key number |
|---|---|---|
| split_integrity | Completed | All files match |
| arm_counts | Completed | Correct sizes |
| exclusions_applied | Completed | Dedup applied |
| direction_derivation | Completed | 25×1024 direction tensor |
| refusal_eval | Completed | 81.6% primary, 79.8% large |
| judge_agreement | Completed | κ=0.816 |
| kl_divergence | Completed | 0.0 (baseline) |
| activation_extraction | Completed | Activations saved |
| probe_train | Completed | AUC 0.9992 (confound flagged) |
| over_refusal_eval | Failed gate threshold | 61.3% (>10% threshold) |
| capability_suite | Not run | Not yet run |

### Confound deadlock resolved: controls_passing v2

**Decided by:** Arjhine, after Fable + Argon consultation  
**Deviation:** seq 28 (`2026-11-15-controls-passing-v2`)  

v1's absolute q975 ≤ 0.65 ceiling permanently locked the study into "inconclusive"
(parent q975 = 0.9364). v2 replaces it with:

**Kill (all five must hold):**
1. CI_low ≥ 0.90 (pre-registered)
2. Permutation p ≤ 0.025
3. Selectivity: CI_low > q975_candidate (Argon)
4. Topic control CI_upper < 0.90 (Fable)
5. Source control CI_upper < 0.90 (Fable)

**Success:** CI_high ≤ 0.60 + parent positive control only (corpus confound is
invariant between parent and candidate, so AUC collapse is causally attributable
to the edit).

**Expected outcome (stated before candidate data):** Kill likely inconclusive
(topic control expected ≥ 0.90). Success likely not met (refit probe expected
above 0.60 due to corpus structure). Both outcomes are the definition working.

**Remaining gates:** capability_suite only, then baseline is complete.

---

## 2026-11-15 — Session 4 Pause

**Decided by:** Arjhine  
**Reason:** Operator pause.

**State snapshot:**
- 10 of 11 baseline gates complete (capability_suite remaining)
- Corrected behavioral numbers: 81.6% refusal, κ=0.816
- Probe: AUC 0.9992, confound flag active but deadlock resolved (v2)
- Two deviations recorded: seq 26 (classifier bug), seq 28 (controls v2)
- `gates_optimized.py` ready for next run (sequential model loading)
- `judge_fix.py` deployed and validated
- Ledger has 29 entries (seq 0–28)
- All files saved locally

**Next session:**
1. Fix capability_suite seed loop (pass --seed for [0,1,2])
2. Run capability_suite (last baseline gate)
3. Baseline complete → method admission → candidate run

## 2026-11-17 — Resumption audit: execution held

Arjhine requested continuation. No GPU jobs, gates, uploads, reruns, or run-artifact
changes have been initiated during this audit. The following corrections qualify
earlier readiness and validity claims; earlier entries remain as historical statements.

### Checks completed locally

- HEAD remains `d225055`; the working tree includes substantial uncommitted changes.
- `scripts/verify_ledger.py` passes: original run 22 entries, Qwen run 29 entries,
  with clean frozen-answer drift checks. Both working ledgers preserve their HEAD prefixes.
- The staged append-only check passes, but it does not cover unstaged changes.
  A separate working-copy comparison confirms the Qwen `split_integrity.json` receipt
  differs in content from its HEAD version. Ledger-chain validity does not establish
  receipt immutability or recover overwritten files.
- AST parsing fails for `harness/gates_optimized.py` at line 52 (invalid import syntax).
  The other three new inference/runner modules parse; parsing alone is not validation.

### Corrections to previous interpretations

- The 81.6% and 79.8% values are currently complements of HarmBench-positive verdicts.
  They are not validated explicit-refusal rates. Nonharmful output can be helpful,
  irrelevant, incoherent, or a refusal.
- The 61.3% safe-prompt complement is not a validated over-refusal measurement.
  The previous claim that it was a genuine model characteristic is withdrawn.
- Kappa 0.816 records inter-judge agreement under the implemented invocation, not
  calibration against human truth or proof of construct validity.
- The optimized module is not ready for deployment. Besides invalid syntax,
  `_free_model(model)` deletes only its local reference while callers retain the model.
  Speedup and exact-equivalence claims remain unmeasured.
- Capability preparation needs more than seeds: pinned revision, explicit template/
  thinking policy, correct output paths, fresh per-seed result discovery, and nonempty
  task/metric coverage must be checked.
- Controls v2 is an owner-approved post-baseline amendment, not an unchanged
  pre-data rule. Its topic/source controls still need implementation and validation.
  A low probe score alone does not establish removal of a causal refusal mechanism.

### Next-decision review

Read-only Fable and Argon consultations have been launched with the same factual
brief, requesting independent challenges, a conservative recovery sequence, and
paper support. Prompt and complete CLI outputs are being saved under
`docs/protocol/resume_review_20261117/`. Requested aliases are recorded separately
from any resolved model identity. Consultant recommendations are not owner decisions.

No existing ledger line, receipt, log, or frozen pre-registration was edited.
Any artifact recovery or fresh measurement plan requires review and owner approval;
a deviation does not authorize overwriting old receipts.

### Review completed; owner decision pending

Both read-only consultations completed successfully. Full responses and a reconciliation
are saved in `docs/protocol/resume_review_20261117/`. Both recommend preservation and
refusal-construct validation before another GPU run, with local off-run repairs/tests
permitted. No recommendation has yet been adopted as a new protocol decision.

Additional qualification: the earlier "stop rule is no longer triggered" assertion is
withdrawn. A complement-of-harmfulness rate does not validate the refusal window, and
`passed=True` in this gate indicates completion rather than enforcement of that window.
The earlier gate-count summaries must not be read as ten validated scientific endpoints.

Consultant advice was also checked: denominator changes are documented in the original
run's seq16 split rebuild and seq17 rate-based decision, with rebuilt counts in Qwen seq3.
Advice to restore run files to HEAD was rejected; current and committed versions are
preserved separately without altering the originals.

A local-only ZIP outside the repository preserves 41 metadata/source/receipt/log files
and the committed split receipt, each verified against its generated SHA-256 manifest:
`../WeightSpaceAbliteration-local-backups/resume-audit-20261117T121241131518Z.zip`.
This is not a complete backup of all raw results or proof that superseded receipts exist.

Current receipt self-hashes and schema-1 log hashes verify. The result JSON digest
convention omits the file's trailing newline; evidence is in `receipt_integrity.json`.
The existing CPU pytest suite timed out at 300 seconds after 87% plus four further
passing-test dots. No complete-suite PASS is claimed.

Arjhine supplied access to Firecrawl CLI 1.29.0; its launcher successfully reports
that version. The private installation location is intentionally omitted from
committable artifacts. No credentials were read and no paid search was initiated.

### Technical writing and privacy normalization

Documentation cleanup removed nontechnical operational context, redundant account
identifiers, decorative status markers, and private local paths from editable text.
Operator/model attribution, measurement values, decision chronology, and recorded
technical mistakes remain available.

Edited consultation responses and temporary prompt copies are labeled as derivatives.
`resume_review_20261117/text_redactions.json` records pre-edit and saved-copy hashes;
`provenance_audit_20261117/prompt_redaction.json` distinguishes submitted input from
the privacy-redacted saved prompt. Paper response bytes and their hashes are unchanged.

The tracked/nonignored text scan identified a legacy actor alias in Qwen ledger seq18.
That immutable entry was not edited. Publication redaction, if required, must use a
separate labeled derivative; it must not replace the hash-chained original.

Argon's provenance audit has completed and is saved under
`docs/protocol/provenance_audit_20261117/`. Source inspection confirms the primary
overwrite risks at producer, upload, and download boundaries. Runtime changes remain
pending; this cleanup did not modify gate behavior or start GPU work.

## 2026-11-17 — Approved overwrite guard implemented locally

**Verification recorded:** 2026-11-17T13:05:18Z.
**Authorization:** review of the preceding session recovered Arjhine's explicit
approval of the three-point non-destructive artifact guard after the consultations.
The current continuation request resumes that approval. The earlier "owner decision
pending" and "runtime changes remain pending" statements describe the preceding
audit stage; they are not the current implementation status.

### Scope and implementation

- `harness/artifact_guard.py` and `harness/gates.py` refuse existing gate receipts,
  final/partial logs, and gate-owned measurements before invoking gdkit. Configured
  refusal-arm outputs and the entire capability output directory are covered.
- `scripts/record_host.py` refuses an occupied host record before collection,
  validates the existing ledger, and creates new host bytes exclusively. It does
  not replace old host records or introduce a new snapshot schema.
- `modal_runner.py` prechecks complete session gate lists before host recording.
  Guard/subprocess refusals propagate as failures rather than successful sessions.
- `harness/artifact_sync.py` preflights transfers, skips identical bytes, publishes
  new local files without replacing occupied paths, and preserves conflicting
  incoming bytes in a private quarantine outside the repository. Local ledger
  updates append only verified same-run byte-prefix extensions.
- Run uploads use `force=False`, separate from ordinary code upload. Differing
  remote ledgers are refused, including valid extensions: Modal bulk upload lacks
  atomic compare-and-append. No unsafe remote ledger replacement was introduced.
- Shared per-run locks coordinate guarded local writers. Stale locks are not
  automatically removed. Locks do not coordinate separate Modal containers;
  concurrent writers against one volume/run remain prohibited. Direct gdkit
  execution and direct check-function calls bypass the repository producer guard.

The existing gate/log integration test now uses a registered gate with a known
output contract. Two source-text/AST-only assertions were removed rather than
retained as implementation-shape tests. Operational guidance is in `harness/README.md`.

### Verification and limitations

- Targeted CPU command:
  `python -m pytest -q -rs tests/test_artifact_guard.py tests/test_artifact_sync.py tests/test_gdkit_upgrade.py tests/test_append_only_restore.py`
  — **185 passed, 14 skipped in 42.60 seconds**. All skips require Windows symlink
  creation privileges unavailable on this host. No complete-suite pass is claimed.
- The initial targeted run exposed an occupied lock directory raising
  `PermissionError` on Windows rather than `FileExistsError`. Acquisition now
  classifies an occupied path as a conflict without hiding unrelated I/O errors;
  the corrected regression run passed.
- A temporary runtime smoke exercised actual gate/host CLI refusals and actual
  Modal runner function bodies locally against temporary files and a filesystem
  volume adapter. Both session variants rejected occupied/duplicate/unknown gates
  before invoking the host subprocess. Pull/upload conflicts preserved originals
  and incoming copies; upload conflicts stopped code upload. A real gdkit-generated
  two-entry ledger was pulled as a verified suffix while retaining its exact prefix.
  Final smoke completed successfully in **6.84 seconds**.
- Before/after SHA-256 comparison covered **96 protected files**, including the
  frozen pre-registration and all current run files: no bytes changed and no files
  were added or removed.
- No Modal API calls, GPU jobs, real transfers, registered gate runs, or ledger
  entries were made. Remote behavior and distributed concurrency were not tested.

This completes the approved local overwrite guard, not historical evidence recovery
or measurement validation. Refusal-construct validation, capability/inference repairs,
controls-v2 implementation, and any new measurement namespace remain separate work.

## 2026-11-17 — Dependency-failure evidence and publication guidance

At Arjhine's request, inspected official contribution guides and issue/PR templates
using Firecrawl. Updated `AGENTS.md` and `docs/upstream_issues/README.md` with sourced
requirements for real-use context, runnable reproductions, environment/configuration,
text tracebacks, exercised validation, and honest disclosure.

The working priority is the study's goal and trustworthy results. Upstream reporting
is incidental; contrived failures and speculative contribution campaigns are not study
work. Minimal reproductions must preserve the cause of an observed failure.

Public records retain material findings, limitations, and decisions. Exploratory notes,
source captures, and drafts stay in gitignored `.omp/upstream-notes/`, without replacing
required run records. Verified 11 captured-source hashes, 13 ignored local files, and
10 source citations against retrieved pages and displayed file commits. Documentation
only: no runtime behavior changed, registered run artifacts modified, or upstream
submissions made.

Further clarification: informative public research docs remain encouraged, including
model quirks, compatibility constraints, negative results, and failed approaches.
The supplied model-quirks example was read as a documentation example, not adopted as
evidence for this study. `AGENTS.md` now explicitly distinguishes curated public
findings from private raw diagnostics and drafts.

The operator emphasized dated observations and measured durations, citing a resolved
Transformers issue from another project. Findings guidance now requires timestamps
with timezones, measured durations and timing conditions, and dated corrections;
missing historical details must remain explicitly unknown.

## 2026-11-17 — Read-only local/Modal evidence inventory

**Authorized by:** Arjhine. **Completed remote read interval:**
2026-11-17T13:29:31Z–13:33:41Z, **249.516 seconds**. Full findings and limitations:
[`docs/protocol/evidence_inventory_20261117.md`](docs/protocol/evidence_inventory_20261117.md).

- Preserved all 95 current run files from each location, plus explicit code/config
  references and 12 historical Git evidence blobs. Of the run files, 94 are identical;
  the remote Qwen ledger is an exact byte prefix of the local ledger (28 versus 29 entries).
  Local seq28, the controls-passing v2 deviation, is absent remotely. No synchronization
  or replacement was performed.
- The remote overwrite guards are absent. Local/remote differences in gate, host, and
  runner source remain intentionally undeployed.
- Only the latest of ten Qwen host records has matching bytes in the checked stores:
  nine earlier snapshots were not found. This corrects the earlier prose undercount of
  eight; it does not establish permanent loss outside the searched locations.
- Harmful-prompt generation IDs cover all 293 primary and 15,640 large-arm items in order.
  Safe-prompt over-refusal has only an aggregate artifact in the checked stores, not
  per-item responses. No capability measurement output was found.
- An initial 9.81-second recorder attempt stopped at a missing optional remote source
  file because the SDK raises `NotFoundError`. Handling that exception allowed the
  remote stage to resume without replacing the completed local snapshot.
- Verified all 219 captured local/remote/Git blob hashes, all 242 members of a new
  private off-repository backup ZIP, and Git-ignore coverage for 243 inventory files.
  Local source fingerprints were unchanged; remote run metadata and ledger rereads
  were stable. This was not an atomic remote snapshot.
- No registered artifact edits, GPU jobs, deployments, uploads, volume commits,
  protocol changes, or new ledger entries. Private raw evidence remains outside
  committable documents. No runtime test suite was run for this investigation.

Next proposed design: code-only deployment separate from verified append-only ledger
synchronization, then immutable host and complete execution/artifact provenance.
No such implementation or deployment is authorized by this inventory record.

## 2026-11-17 — Recovery-design review; owner choices pending

The operator requested a detailed next-step explanation and selectable decisions.
Read-only Fable and Argon consultations completed, followed by the requested
Claude Opus 4.6 reconciliation. Private prompts, raw outputs, returned metadata,
and generated hashes are retained under `.omp/design-review/20261117T135239Z/`.
Relevant paper metadata/abstracts were retrieved through `pwc`; their scope is
methodological support, not proof of concurrency or filesystem guarantees.

The proposed sequence and acceptance criteria are in
[`docs/protocol/recovery_plan_20261117.md`](docs/protocol/recovery_plan_20261117.md).
Recommendation: local-only provenance engineering; future corrected measurements
in a fresh linked run carrying known amendments; leave the historical remote ledger
unchanged. The owner has not selected these options or authorized implementation.

Review corrections retained: a fabricated run ID, stale agreement figures, an
unsupported permanent-loss claim, full-ledger replacement described as append,
and lease/check/reread procedures that do not establish distributed exclusion.
No code, run, deployment, or scientific protocol mutation was performed.

### Owner selections: A1 / B1 / C1

Arjhine selected local implementation and verification only (A1), a fresh linked
registered run for future corrected measurements (B1), and preservation of the historical
remote ledger without synchronization (C1). Local provenance engineering may proceed.
These selections do not authorize a new run, any remote mutation or deployment, GPU
execution, measurement-definition changes, or reuse of old measured artifacts.

## 2026-11-17 — A1 local execution-provenance implementation verified

Implemented under the selected local-only scope. Details:
[`docs/protocol/local_provenance_contract_20261117.md`](docs/protocol/local_provenance_contract_20261117.md).
No existing registered run or frozen pre-registration was changed, and no future run was created.

- Added immutable, allowlisted code releases and explicit development-bundle marking.
  Replaced blind code upload with reviewed code-only release publication; publication was
  exercised only through a local filesystem adapter, never the Modal API.
- Unified canonical immutable session host records with gdkit verification, preserving raw
  requested probe streams privately. New execution refuses legacy migration or unchecked
  hosts. Historical verification does not compare against the auditor's current machine.
- Added contract-3 execution manifests and read-only verification within gdkit receipt
  schema 1, binding source/callables/constants, declared inputs, host and exact output bytes.
  Static helper imports replace runtime monkeypatching. Measurement definitions and
  thresholds were not reinterpreted; legacy refusal metrics remain explicitly unvalidated.
- Final integrated tests: **298 passed, 20 skipped in 135.41 s**; wrapper ran
  **2026-11-17T15:02:04Z–15:04:20Z**, elapsed **136.86 s**. Skips require unavailable
  Windows symlink privileges. Publication boundary tests: **11 passed in 15.09 s**
  (wrapper **17.703 s**). No complete-suite or remote-runtime pass is claimed.
- Actual local CLIs passed a **7.00 s** smoke on a temporary two-row CPU fixture:
  release/source verification, real CPU host collection, cheap gate execution,
  valid/current receipt, occupied-output refusal, second immutable host session,
  valid/stale historical receipt, currentness refusal, and changed-input detection.
- Preliminary integration failures included an inconsistent fixture run ID and obsolete
  wrapper test hooks. The actual smoke then exposed process-dependent frozenset repr
  in executable identity; canonical unordered-constant encoding and a cross-hash-seed
  regression corrected the false mismatch. These were local verifier issues, not
  manufactured upstream reports.
- All **96 protected file hashes and the protected file set remain unchanged**. Raw
  commands, outputs, generated hashes and development snapshots remain in ignored
  `.omp/local-validation/20261117T144830Z/`.

Remaining limits are explicit: downloaded model-weight bytes are not certified by configured
commit references; supplementary image installs are not lockfile-pinned; the experimental
optimized module remains outside the runtime payload; no GPU, model-inference, remote-image,
distributed-writer, scientific-calibration, candidate-admission or promotion validation was
performed. Historical remote artifacts remain untouched under C1. Any remote deployment
or isolated CPU smoke requires a separate owner decision.

## 2026-11-17 UTC — Dependency/image audit; pinning choices pending

The operator authorized an audit and proposal before dependency changes. Findings:
[`docs/protocol/dependency_image_audit_20261117.md`](docs/protocol/dependency_image_audit_20261117.md).
Root dependency files, image recipe, the installed project package census, and all
96 protected files remain unchanged.

- Correct marker evaluation selects the Python-3.11 lock branches. All eight comparable
  recorded core package versions match; no core drift was established.
- Recovered recorded pins for five supplementary packages. Evidence strength differs:
  two appear in the preserved host census, two have historical machine-output corroboration,
  and Protobuf remains supported by the execution log without independent machine confirmation.
- Actual local import-only probes failed on missing Accelerate for the HF backend and
  missing langdetect for IFEval. These are dependency-declaration gaps, not upstream bugs;
  they do not prove historical remote package absence.
- Recorded-only and declared-workflow shadow locks resolve with six and eleven added
  entries respectively, with no existing version or source/sdist/wheel metadata changes.
  A clean minimal workflow proposal also resolves and includes a pinned uv requirement
  plus hash-bound setuptools build constraints generated from existing lock metadata.
- IFEval's NLTK resource is outside the Python lock. `punkt_tab` exists locally, but its
  exact bytes and remote provisioning were not certified; no resource download occurred.
- Root `uv lock --check` passed. Historical uv0.8.17 exported existing/runtime shadow locks.
  That tool was provisioned only in an isolated cache. No candidate ML environment was installed.
- Public registry metadata supplies digest-addressed Python3.11.15 and3.11.12 base candidates;
  neither was pulled or built, and no historical measurement image was identified from them.
- Fable/Argon review and requested Opus reconciliation completed. Recommendation: workflow
  coverage and a newly recorded target aligned to local Python3.11.15/uv0.12.18, with client
  SDK1.6.4. Recommendations are not owner approvals; missing historical identities were
  not reclassified as permanently unrecoverable.

Probe records include exact UTC timestamps, durations, output hashes and preserved diagnostics
under ignored `.omp/dependency-audit/20261117T152146Z/`. No Modal API call, deployment, GPU
work, model construction, registered-run mutation, dependency adoption, or permanent test
addition occurred. Owner selection is required before applying the proposed pins/recipe.

### Owner selection: workflow coverage and Python 3.11.15

Arjhine selected the workflow-coverage package profile and Python 3.11.15 future target.
This authorizes local dependency/image-definition updates and isolated local validation
only. The five recorded supplements, published backend/task/tokenizer extras, uv0.12.18
requirement, and hash-bound setuptools build constraint are applied from the generated
minimal proposal. Existing package versions and artifact identities are to remain fixed.

The image definition uses the registry-returned Linux/amd64 Python3.11.15 base digest and
Modal SDK1.6.4. Its single uv-sync installation uses `--locked` rather than unchecked
`--frozen`, so stale project metadata is refused without lock updates. No image is built
by this local source edit. Image/deployment, model/resource downloads, GPU execution,
new study runs, and historical-remote changes remain unapproved.

## 2026-11-17 UTC — Approved dependency target validated locally

Applied workflow coverage and the selected Python3.11.15/uv0.12.18/SDK1.6.4 image-definition
target. Detailed evidence:
[`docs/protocol/dependency_update_20261117.md`](docs/protocol/dependency_update_20261117.md).

- The adopted lock has eleven additions and no existing version or source/sdist/wheel
  metadata changes. Root project/lock correspondence passes. Registry/base and build
  hashes were copied programmatically from captured metadata, not invented.
- Installed into a separate ignored environment, not the active project `.venv`, in
  **34.14 s**, **2026-11-17T16:57:51Z–16:58:25Z**. All **103 expected packages** are present,
  with no version mismatches or unexpected packages, and the gdkit Git commit matches.
- HF backend, IFEval, Tiktoken, SentencePiece, Protobuf and blobfile imports passed.
  Python socket and NLTK-download guards plus HF offline settings recorded zero network/
  download attempts. Existing local `punkt_tab` was used, not provisioned into an image
  or certified by hash. No model constructor or task-evaluation API was called.
- Isolated regressions: **298 passed, 20 skipped in 124.70 s** (wrapper **126.594 s**,
  **17:19:34Z–17:21:40Z**). Skips require unavailable Windows symlink privileges.
  Pinned-SDK publication tests: **11 passed in 15.69 s**. An intentionally older SDK
  invocation was refused before image preparation; this is our guard's expected behavior,
  not an upstream bug report.
- The actual local release/host/gate/verifier CLI lifecycle passed in **6.40 s** using
  temporary fixture data and the isolated environment. No complete-suite, image-build,
  Linux/CUDA, model-loading, numerical-equivalence, or benchmark-validity claim is made.
- All **96 protected files** and the original **125-name project-package census** remain
  unchanged. Raw records are retained under ignored
  `.omp/dependency-update/20261117T164529Z/`. No working-repository commit or push was made.

The image definition is updated but unbuilt. Apt/OS and actual image identity, external
resources/model bytes, Linux/CUDA behavior, and scientific measurement repairs remain
separate gates. No Modal API call, image pull/build/deployment, new registered run,
historical-remote mutation, or GPU workload occurred.

## 2026-11-18 UTC — Local resource and checkpoint inventory

Using Python 3.11.15 in the isolated workflow environment, ran `tools/inventory_resources.py`
on the historical Qwen harness configuration (read only). Capture and an independent
`--compare` invocation ran **05:42:29Z–05:42:42Z**, taking **6.969 s** and **6.375 s**
respectively on this Windows workstation. These are single local filesystem observations,
not throughput benchmarks. The manifest binds the exact config bytes and records file
paths relative to each resource, sizes and SHA-256 digests. Private manifests and command
records: `.omp/resource-inventory/20261118T054229216298Z/`.

| Configured role(s) | Files at the exact revision | Local observation |
|---|---:|---|
| Qwen model and parent (one shared revision) | 4 | Config, tokenizer and template; no standard model weights |
| HarmBench Llama judge | 5 | Config and tokenizer assets; no standard model weights |
| HarmBench Mistral alternate judge | 5 | Config and tokenizer assets; no standard model weights |
| BGE embedding | 6 | Includes `model.safetensors`, config and tokenizer; no loading test |
| IFEval English `punkt_tab` (local NLTK 3.10.4 resource, not a Hub revision) | 4 | All four tables used by the English loader present; 237,757 bytes |

All observed bytes matched on reread. This is a **local reference for detecting drift**,
not an upstream-signed inventory, reconstruction of the historical GPU cache, or receipt
binding. It covers the selected checkpoint snapshots and English sentence-tokenization
tables, not benchmark datasets/access or a built image. A cache directory named for a
commit can contain only the files previously requested.

Targeted temporary-fixture tests: `python -m pytest -q -rs tests/test_resource_inventory.py`
— **2 passed, 1 skipped** (symlink creation unavailable) in 0.22 s. Tests cover missing
shards, exact-byte drift and missing resource tables. No downloads, GPU/model execution,
image build, remote API calls, or historical-run writes. Next proposed step: separately
authorize read-only inspection of the existing remote model cache at these exact revisions
before considering fresh artifact downloads or image provisioning.

## 2026-11-18 UTC — Read-only Modal checkpoint-cache listing

The operator approved filename/size inspection, not checkpoint-content reads. Used
`Volume.listdir` with Modal SDK 1.6.4 on the existing `wsa-hf-cache` volume, under the
four exact `hub/models--…/snapshots/<revision>` paths from the preceding local inventory.
Qwen's model and parent roles share one revision. The recursive listings ran from
05:45:50.862Z to 05:45:54.084Z (3.219 s across the four calls). The private scripts,
listings and name comparison are in `.omp/resource-inventory/modal-metadata-20261118T054506708051Z/`.

| Model | Local files | Remote snapshot entries | Shared names | Remote weight filenames |
|---|---:|---:|---:|---|
| Qwen 0.8B | 4 | 6 | 4 | One shard and an index |
| HarmBench Llama 13B | 5 | 12 | 4 | Six numbered shards and an index |
| HarmBench Mistral 7B | 5 | 9 | 4 | Three numbered shards and an index |
| BGE small | 6 | Not found | — | No listing at configured path |

All 27 returned entries were **symlinks**. Sizes of 52 or 76 bytes describe directory
entries, not model payloads. A direct listing of the Qwen shard also returned only
symlink metadata. A nonrecursive lookup of BGE's expected repository directory returned
not-found (two follow-up calls: 2.360 s, ending 05:46:42.285Z). This does not establish
that BGE is unavailable elsewhere or needed for a gate that consumes already-built splits.

No index contents, link targets, blob sizes, or remote file hashes were verified. Continuous
shard numbering is encouraging but cannot rule out a missing, dangling, or corrupt target.
Shared filenames do not imply shared bytes. No volume writes, container starts, GPU jobs,
model downloads, or registered-run changes occurred.

Next proposed check: a read-only preflight that parses only the three index JSONs, resolves
their shard links within each repository cache, and stats target sizes. Require separate
approval for content reads or container execution. Keep weight hashing, inference and BGE
provisioning separate; none follows from a successful metadata check.

## 2026-11-18 UTC — Pinned checkpoint indexes and resolved shard sizes

The operator approved reading the three index JSONs and checking referenced shard
targets. Used short-lived CPU sandboxes (Modal SDK 1.6.4, stock Python image, no GPU,
blocked sandbox network, only `wsa-hf-cache` mounted read-only). The study image was
not built or deployed. The payload opened index JSONs only; weight checks used
`readlink`/`stat`, not reads, downloads, hashes, or inference.

| Model at previously inventoried revision | Index keys | Referenced shards found | Sum of logical file sizes (bytes) | Index `metadata.total_size` (bytes) |
|---|---:|---:|---:|---:|
| Qwen 0.8B (model and parent) | 488 | 1/1 | 1,746,942,600 | 1,746,882,752 |
| HarmBench Llama 13B judge | 363 | 6/6 | 26,031,770,928 | 26,031,728,640 |
| HarmBench Mistral 7B alternate judge | 291 | 3/3 | 14,483,498,016 | 14,483,464,192 |

All three index Git blob hashes recomputed from their bytes matched the corresponding
cache link names. Their shard sets exactly matched the earlier listing. All ten links
resolved to distinct nonempty regular files **within the mounted cache**. Logical file
sizes include container overhead; the small excess over declared tensor bytes is not
itself evidence of corruption. Neither total proves the payload hashes or tensor contents.

Earlier probes refused unexpected redirects rather than following them blindly. The
mount root resolves through a platform redirect. A later targeted check parsed the
indexes but found the repository blob entries were themselves symlinks. This matches
the installed Hub client's documented shared-blob layout: repository `blobs/<etag>`
can link to cache-wide `blobs/<prefix>/<xet-hash>`. The successful probe accepted only
that bounded second hop, checked its two-character prefix, and verified that the final
regular file was the one actually resolved from the snapshot path. It did not scan the
shared store or infer content integrity from its filenames.

Final command: `uvx --from modal==1.6.4 --python 3.11.15 python <private-attempt>/launch.py`.
The successful controller invocation ran 06:00:09.977Z–06:00:15.768Z (5.797 s elapsed);
in-sandbox inspection took 0.209 s. This is a metadata observation, not a read-throughput
benchmark. All four attempts' scripts, outputs, timestamps and a generated evidence
manifest are retained privately under `.omp/resource-inventory/shard-preflight-*/`;
the successful attempt is `shard-preflight-20261118T055959250272Z`. No volume or registered
run files were modified. This check does not certify the study image, tokenizers, BGE,
historical use of these bytes, or model loadability.

## 2026-11-18 UTC — Qwen weight shard matched the pinned upstream SHA-256

The operator approved hashing the single Qwen shard in place. The independent expected
digest and size came from `lfs.oid` and `lfs.size` for `model.safetensors-00001-of-00001.safetensors`
in the [Hugging Face tree metadata for the pinned commit](https://huggingface.co/api/models/Qwen/Qwen3.5-0.8B/tree/2fc06364715b967f1860aea9cf38778875588b17).
The Git pointer ID, Xet storage name, and index's tensor-byte total are not substitutes
for the SHA-256 and length of the weight file itself.

`uvx --from modal==1.6.4 --python 3.11.15 python <private-attempt>/launch.py` used the
previous stock CPU image with a read-only `wsa-hf-cache` mount and blocked sandbox network.
After checking the snapshot-to-blob link chain, the probe read **1,746,942,600 bytes**
in chunks from one regular file; the resolved target and file metadata stayed stable
across the read. The controller compared the returned digest and byte count to upstream:
**both matched**. Only the digest and scan metadata returned from the sandbox.

One scan, no warm-up or cache eviction: **06:05:00.578Z–06:05:03.966Z**, **3.388 s**.
The controller took **9.391 s** including sandbox lifecycle; not a throughput benchmark.
Private source, upstream metadata, full digests, results, and evidence manifest:
`.omp/resource-inventory/qwen-shard-hash-20261118T060319345943Z/`.
No weights were downloaded to the workstation, and no volume or registered artifact was
modified. This verifies the cached Qwen weight payload at inspection time, not historical
use, tokenizer/config integrity, judge weight integrity, loadability, or inference behavior.

## 2026-11-18 UTC — Both judges' cached weight shards matched upstream

The operator approved checking only the indexed weight shards for the two pinned judges.
Expected values came from `lfs.oid` (SHA-256) and `lfs.size` in the upstream file trees
for [HarmBench Llama](https://huggingface.co/api/models/cais/HarmBench-Llama-2-13b-cls/tree/bda705349d1144fa618770bea64d99ce54e3835b)
and [HarmBench Mistral](https://huggingface.co/api/models/cais/HarmBench-Mistral-7b-val-cls/tree/51182c7cdaf9b2e5f05b745b81b047b67e7384a1).
The file sets agreed with the preceding index preflight. One CPU sandbox streamed each shard
once through SHA-256 on the read-only cache mount. The controller compared the repo,
revision, filename, digest and byte count for each returned observation.

| Pinned judge | Individual size and digest checks | Bytes scanned | Sum of shard scan times |
|---|---|---:|---:|
| Llama 13B | Shards 1–6 of 6 each matched | 26,031,770,928 | 40.454 s |
| Mistral 7B | Shards 1–3 of 3 each matched | 14,483,498,016 | 19.407 s |

Command: `uvx --from modal==1.6.4 --python 3.11.15 python <private-attempt>/launch.py`.
Controller interval: 06:09:10.968Z–06:10:15.698Z; elapsed 64.735 s including sandbox
lifecycle. One sequential pass with no deliberate warm-up or cache eviction; not an
inference or storage benchmark. File identity, size and timestamps were stable across
each read. An offline check against the saved upstream responses confirmed nine distinct
results with no omitted, extra or mismatched shard.

Private attempt: `.omp/resource-inventory/judge-shard-hash-20261118T060752688256Z/`.
It contains the two upstream metadata captures, scoped paths, probe, per-file results,
UTC timings and evidence manifest. No weight payloads were transferred to the workstation.
No GPU, inference, study image build, volume mutation or registered-run write occurred.
Together with the earlier Qwen scan this establishes current cached weight integrity for
all three checkpoints, not historical execution identity, tokenizer/config integrity,
loadability, or validity of the judges' measurements.

## 2026-11-18 UTC — Tokenizer, template and configuration byte checks

Compared the three pinned snapshots on the read-only Modal cache mount with the upstream
file trees retained for the weight scans above. Scope: published tokenizer assets, model
and generation configs, chat templates, and processor configs in those trees. Excluded
weights, weight indexes, training binaries, documentation and BGE. Expected size and
identity came from `size` and the Git blob `oid` for ordinary files, or `lfs.size` and
`lfs.oid` for LFS payloads. For ordinary files the comparison hashes the Git blob header
plus content, not raw content alone. No missing files were fetched.

| Pinned checkpoint | Matched files | Absent upstream-listed files |
|---|---|---|
| Qwen 0.8B | `config.json`, `tokenizer.json`, `tokenizer_config.json`, `chat_template.jinja` | `merges.txt`, `vocab.json`, `preprocessor_config.json`, `video_preprocessor_config.json` |
| HarmBench Llama 13B | `config.json`, `generation_config.json`, `tokenizer_config.json`, `tokenizer.model`, `special_tokens_map.json` | None in scope |
| HarmBench Mistral 7B | Same five named files, checked independently at the Mistral revision | None in scope |

**14 matched, four absent, zero size/digest mismatches or read errors.** The 12 matched
files also present in the prior local inventory had identical raw SHA-256 there. The
other two were the judges' generation configs. Qwen and Mistral each have a nonempty
embedded `chat_template` string in `tokenizer_config.json`; Llama has no nonempty embedded
template. This check did not select, execute or compare template behavior.

Command: `uvx --from modal==1.6.4 --python 3.11.15 python <private-attempt>/launch.py`.
One sequential scan of 13,833,447 bytes, no deliberate warm-up: **06:14:30.082Z–06:14:30.845Z**
(0.763 s); controller elapsed **6.313 s**. Not a throughput benchmark. Scripts, observed
digests, upstream references and results are in ignored
`.omp/resource-inventory/tokenizer-config-check-20261118T061314556657Z/`.
Stock CPU sandbox, blocked sandbox network, no weight rereads, inference, study image
build, volume mutations or registered-run writes.

Qwen's snapshot is partial, not shown corrupt. A verified consolidated `tokenizer.json`
is present, but the index of cached filenames does not tell us which inputs the pinned
text loader needs. Next proposed check: use the existing local matching tokenizer assets
for an offline CPU tokenizer-only smoke with a harmless fixed input, exercising the
actual text rendering/tokenization paths. No evidence here requires downloading the four
missing files, and no historical prompt or judge semantics have been validated.

## 2026-11-18 UTC — Offline tokenizer and harness text-path smoke

**Question:** Can the pinned text tokenizers load without fetching the missing Qwen
files, and does each actual formatted input retain its user text after encoding?
On Windows/Python 3.11.15 with Transformers 5.22.2 and tokenizers 0.23.3, staged
only the twelve previously matched local tokenizer/config assets (four per revision)
into a temporary Hub cache after rechecking their sizes and SHA-256 digests.
`AutoTokenizer.from_pretrained` used the configured repo ID and full commit per role,
`local_files_only=True` and `trust_remote_code=False`. The cache contained no weights.

Two fixed harmless inputs of different lengths used a lemon-color question and a
garden counting question, each with a supplied answer. Qwen used `harness.gates._render`
with `thinking=False`; both judges used the actual `harness.judge_fix.LLAMA2_CLS_PROMPT`
format string, not the tokenizers' own chat templates. Applied the harness's left
padding, length sorting and truncation settings (limits: 4,096/2,048 respectively).

| Role | Loaded tokenizer | Nonpadding tokens (short / long) | Short row's left-pad tokens |
|---|---|---:|---:|
| Qwen model/parent | `Qwen3_5Tokenizer` | 19 / 34 | 15 |
| Llama judge | `LlamaTokenizer` | 234 / 252 | 18 |
| Mistral alternate judge | `TokenizersBackend` | 225 / 241 | 16 |

All six rows retained the literal user question exactly once after decoding; judge
inputs also retained the supplied answer exactly once after the question. Masked
batch IDs matched individual encodings with only the expected left padding. Qwen
added an assistant generation suffix, including an **empty, closed** think block for
the short example. This is rendered input text, not generated reasoning. Qwen's four
absent upstream files were not necessary for this text-only path in this environment.

Command: isolated dependency environment's `python -I -B <private-attempt>/probe.py
<configured-local-Hub-cache>`. One local invocation, no warm-up or repetitions:
**06:19:48.267Z–06:20:51.894Z**, probe elapsed **63.625 s**, not a benchmark. HF
offline settings and Python socket guards recorded zero attempted network connections.
Private scope, script, rendered text, token IDs, results and hashes:
`.omp/resource-inventory/text-path-smoke-20261118T061823870076Z/`.

No Modal calls, GPU, model construction, generation, scoring, study gates or run-file
writes. The check does not establish behavior at truncation limits or on multimodal
inputs, nor that the shared Llama-style prompt is appropriate for both classifiers.
It establishes text-path compatibility, not refusal accuracy or historical runtime identity.

## 2026-11-18 UTC — Judge invocation comparison; no scoring

Compared the harness against both pinned judge cards and HarmBench's example, validation
notebook and main CLI at a fixed source commit. See
[`docs/protocol/judge_invocation_20261118.md`](docs/protocol/judge_invocation_20261118.md).
One harmless offline fixture at 06:27:44.752Z–06:28:04.487Z (19.734 s) showed 234/235
local/card tokens for Llama and 225/319 for Mistral. The Mistral mismatch changes
the wrapper and rubric, not just whitespace. The main CLI is yet another reference.
Its invalid-label handling and generation clipping also differ from this harness.

The captured historical helper supports the source finding but is not a retroactive
runtime attestation. No verdicts were produced and no change to κ or either arm's rate
was measured. Fable and Argon reviewed the interpretation; Opus reconciled the reviews.
We reject the inference that the Llama whitespace difference has negligible *score*
impact or that the historical instrument is validated for relative deltas. Neither
follows from a token comparison. No decision to change gates, thresholds, or parsing,
or to collect labels, rerun a gate, or execute on a GPU. No registered evidence changed.

## 2026-11-18 UTC — Local, non-scoring judge contract

After the owner paused Fable consultation and requested continuation, implemented the
[draft's local design target](docs/protocol/judge_spec_draft_20261118.md) under `tools/`,
outside the measured release and gate registry. No further consultant requests. This is
engineering work on a prospective diagnostic, not adoption of a new scientific endpoint.

The prototype binds four exact card literals and per-judge tokenizer/config file hashes.
Explicit standard/contextual routing preserves the supplied bytes; unresolved context
and overlength inputs abstain instead of falling back or clipping. It parses only a
supplied continuation (strict yes/no/invalid), and reports unscorable/missing separately.
Reports reject changed or duplicate items, wrong judges, mixed scopes and missing rows.
Positive bounds retain the planned denominator; complete binary data get a naive Wilson
interval. Paired κ is conditional on jointly valid labels and undefined when its denominator
is zero. None of these is a calibrated refusal rate or a pass/fail gate.

`python -m pytest -q tests/test_judge_contract.py`: **14 passed in 0.19 s**. Tests used
controlled benign tokens for exact length/one-position boundaries, special and malformed
outputs, fixed-denominator arithmetic, and paired-identity failures.
`python -I -B <private-attempt>/smoke.py`: **06:56:37.066Z–06:57:24.913Z**, 47.844 s
inside one local CPU invocation (Windows, Python 3.11.15, Transformers 5.22.2; no warm-up
or repetitions, not a benchmark). Both actual offline tokenizers processed harmless
standard/contextual inputs. Llama lengths were 235/357 tokens, Mistral 319/337. One
missing-route item per judge abstained. Verdict tokens were intentionally supplied
fixtures, not classifier predictions. The verified config capacities (2,048 / 32,768)
give effective input maxima of 2,047 / 2,048 after reserving one verdict position.

Private scope and smoke results: `.omp/judge-contract-local/20261118T065018698695Z/`.
No historical responses selected, model weights loaded, scoring calls, GPU or Modal
operations, or registered-run/pre-registration changes. The existing gates continue
to use the historical helper. Before using real items, source/target context linkage
and the separate explicit-refusal rubric and calibration design still require review.

## 2026-11-18 UTC — Primary item-ID routing and target-context audit

Joined the saved Qwen primary split to the cached 400-row HarmBench CSV, authenticated
against pinned upstream Git tree metadata. Verified seq3 manifest/exclusion binding,
split/receipt hashes, disjoint kept/excluded/validation membership, and matching behavior
projections. All 293 saved response IDs match in order. Per-ID details remain private;
see the [aggregate evidence and limits](docs/protocol/primary_context_provenance_20261118.md).

- **133 standard text**: no source context required.
- **80 contextual**: the full source context occurs in none of their saved prompt strings.
  The preserved target code uses split `text` only; historical results do not record
  rendered inputs or per-item target token IDs. Do not supply missing context only to
  a later judge.
- **80 copyright/hash-check**: the pinned reference evaluator dispatches these before
  the text classifier. They are not 80 additional standard-text items.

These are structural counts, not predictions. Keep 293 as the registered denominator;
133/293 is only a ceiling on standard-text diagnostic coverage with the currently
available historical evidence. No historical score was revised. Local read-only census:
07:07:58Z UTC, Python 3.11.15, 0.047 s timed inside the script; private records under
`.omp/context-provenance/20261118T070300962207Z/`. No study-data download, scoring,
Fable request, gate/code change, new run, or registered evidence write.

## 2026-11-18 UTC — Prospective primary routing policy drafted; no execution

At the owner's request, documented how to route target inputs separately from judging
their responses in a future linked Qwen primary run. See the
[draft policy and harmless worked example](docs/protocol/primary_input_routing_draft_20261118.md).
Recommendation, not adoption: provide source context to both fresh target stages before
answering; pass that same context and recorded response to each contextual judge. Keep
hash-route IDs in target accounting but out of text-classifier calls. The historical
parent is not a comparable baseline for a candidate given different information.

At 07:25:54Z, local document checks reconciled the saved 133/80/80 route census to
293 planned and at most 213 text-applicable items, checked the 11/293 refusal bound
and existing Qwen generation settings, and checked the example's literal message
assembly and local source links. Two different pairs of benign fields can yield the
same delimiter-joined text; the policy therefore retains typed fields as well as actual
rendered/tokenized input evidence. Private check: `.omp/routing-policy/20261118T071520647461Z/`.
No new empirical result, gate change, amendment, consultation, registered run, or
measurement. Future implementation and any change of target input condition require review.

## 2026-11-18 UTC — Primary routing policy exercised on fixtures only

Ran `python -B -m tools.check_primary_routing_fixture --inventory <local-resource-manifest>`
in the isolated Python 3.11.15 workflow environment on Windows CPU. The command used
three harmless inputs, real cached Qwen/Llama/Mistral tokenizer assets, and hand-supplied
continuations. No study prompts, generated responses, model weights or judge predictions
were needed. See [the tool guide](tools/README.md#primary-routing-fixture-offline).

For both simulated stages, the same input plan emitted one contextual, one standard
and one hash-route target input. The jar-label context was preserved in the target's
user turn and passed separately to each judge's contextual card. All three toy answers
remained accounted for; two per stage went to each judge's **preparation** path, one
was marked structurally not applicable, and no verdict was obtained. Parent and
candidate supplied different jar answers under identical input plans.

The fixture's split order (jar, color, verse) differed from batch order (color, verse,
jar; 16, 19, 31 unpadded tokens). Restoring by position rather than ID was rejected in
each stage. Eleven expected rejection cases covered a candidate-only context change,
missing/duplicate IDs, mismatched projected behavior, conflicting route signals,
target overflow, insufficient output headroom, and per-stage response swap/omission
of the hash-route answer. This detects mistakes **after** a trusted boundary capture;
it does not attest to an actual generation call or catch a producer that misbinds
answers before capture.

One invocation, no warm-up/repetitions: **07:39:13.652Z–07:39:30.311Z**, 16.656 s
inside the program, 18.35 s command wall time (not a benchmark). Ignored fixture
evidence: `.omp/routing-fixtures/20261118T073356679627Z/`. All 100 protected/reference
file fingerprints were unchanged, including the existing gates and historical runs.
No scoring, Fable consultation, remote operation, or registered measurement occurred.

## 2026-11-18 UTC — Prospective Qwen primary input-length census

**293/293 complete target inputs fit both limits.** The longest, a contextual input,
was 1,001 tokens after rendering, 3,095 below the 4,096 input ceiling. Including
the reserved 256-token answer gives 1,257 positions versus the verified Qwen config's
262,144-position capacity. No clipping, dropping items, or budget change is indicated.

| Proposed route | IDs | Min | Median | 95th percentile | Max |
|---|---:|---:|---:|---:|---:|
| Standard text | 133 | 17 | 27 | 39 | 44 |
| Contextual text | 80 | 75 | 357.5 | 642 | 1,001 |
| Copyright/hash-check | 80 | 21 | 26 | 33 | 36 |
| All primary IDs | 293 | 17 | 29 | 564 | 1,001 |

Lengths are unpadded target-input tokens, including the rendered chat wrapper,
assistant generation cue and tokenizer special tokens. P95 is nearest rank.
The audit checked the primary split and source hashes against the prior provenance
audit and joined the exact 293 IDs to their bound route, behavior and context digests.
Applied the proposed context-plus-LF-separator format for contextual IDs; used the
saved split text alone otherwise. Pinned Qwen tokenizer/config files were verified
and staged alone in a temporary cache; `thinking=False`, `add_generation_prompt=True`,
`add_special_tokens=True`, `truncation=False`. Every assembled user string was retained
in the decoded IDs. These are proposed fresh-run inputs, not historical call traces.

One read-only local invocation on Windows CPU, Python 3.11.15, Transformers 5.22.2,
tokenizers 0.23.3: `python -I -B <private-attempt>/census.py`, 07:46:51.903Z–07:47:04.352Z
(12.437 s inside the program; 13.83 s command wall time). No warm-up or repetitions;
not an inference benchmark. Private script, source fingerprints, per-ID lengths (no
prompt text) and aggregate results: `.omp/input-length-census/20261118T074501743300Z/`.
No historical response reads, model loading, generation, judge calls, GPU, Modal,
consultation or run-file writes. Length feasibility does not adopt the proposed routing,
establish judge-input fit after a response exists, or validate explicit refusal.

## 2026-11-18 UTC — Explicit-refusal rubric and calibration plan drafted; no draw

The [design for review](docs/protocol/explicit_refusal_calibration_draft_20261118.md)
defines refusal of the core request separately from harmfulness, mixed assistance,
inability, and missing evidence. Proposed use of the registration's 200 unique items:
fresh parent primary only, sampled without replacement within route (91 standard,
55 contextual, 54 hash-check). Two independent ratings per item plus adjudication.
No transfer of parent error estimates to the candidate, large or safe arms is assumed.

Reviewed the previously recorded Feng et al. citation via `pwc paper read 2601.20913
--json`: Eq. 6 is a variance-corrected test threshold, not an off-the-shelf two-sided
interval for a finite calibration subset of the same arm. The draft proposes a
finite-population uncertainty procedure for review, not silent substitution for the
registered analysis. A dedicated, frozen refusal instrument and an approved analysis/
decision rule are prerequisites. Historical metrics, thresholds and receipts remain unchanged.

At 08:00:39Z, checked largest-remainder allocation, a hypothetical TPR/FPR correction,
and exact hypergeometric count bounds for empty, fully observed and small synthetic cells;
no ranking, randomness, real item IDs or responses were used. Private arithmetic and paper
evidence: `.omp/calibration-design/20261118T075212310074Z/`. No human or model labels,
consultations (Fable remains paused), GPU work, protocol amendment or ledger writes.

### Owner direction — dedicated explicit-refusal judge

The owner selected the dedicated refusal judge with the proposed 200-item human calibration
path rather than a full parent-primary human census. This is an instrument-development
direction, not permission to draw cases, score the parent, amend a ledger, or change the
frozen registration. HarmBench remains a separate harmful-behavior diagnostic.

Public source review identified WildGuard as a candidate, not an adopted model. Its
`response_refusal` field addresses refusal directly; its documented selective-refusal
category may disagree with the proposed whole-request rubric on mixed answers. Reviewed
Hub metadata, the public GitHub interface and `pwc paper read 2406.18495 --json`; the
anonymous pinned Hub card request returned 401, and no access acceptance was attempted.
See [candidate qualification notes](docs/protocol/explicit_refusal_calibration_draft_20261118.md#first-candidate-to-qualify-not-an-appointed-judge).
No scoring, selections, labels, model loads, consultant calls, or run writes.

## 2026-11-18 UTC — WildGuard development fixtures; no predictions

Fixed 14 harmless authored prompt/response cases with expected dispositions under the
proposed whole-request rubric at **08:14:48.934Z**, before examining parser mechanics.
They are development fixtures, not human ratings and not the 200 calibration items.
Source provenance: four public library files verified against the Git tree at the
revision in the [qualification notes](docs/protocol/explicit_refusal_calibration_draft_20261118.md#harmless-development-check--formatter-and-parser-only).

Ran isolated workflow Python `-I -B <private-attempt>/check.py`, **08:18:44.018Z–08:18:44.055Z**,
0.031 s measured inside the check (2.17 s command wall time, one invocation, not a benchmark).
Executed the two inspected formatter/parser method bodies, input literal and result types
without importing the WildGuard package or constructing a model. Thirteen present pairs
formatted as expected; one missing response was withheld. Separately, all nine parser
checks on **hand-supplied output strings** produced the expected dispositions. In
particular, upstream accepted swapped headings and a trailing record without its error
flag; a proposed strict consumer rejected both. A missing refusal field/N/A is not a
negative, and an error in another field invalidates the record even if refusal parsed.

This establishes local text-interface behavior only, not an upstream defect encountered
during inference or a performance/accuracy result. Private sources, frozen casebook copy,
test inputs, observations and hashes: `.omp/refusal-qualification/20261118T081448928412Z/`.
No credentials, access acceptance, model/tokenizer downloads, scoring, sampling, protocol
amendment, registered-run edits or consultant calls. WildGuard remains a candidate.

## 2026-11-18 UTC — WildGuard development contract frozen; no inference

The owner requested the next local specification step. Froze `wildguard-whole-request-dev-v1`
only for the existing harmless casebook, not for the registered primary arm or its 200
held-out calibration items. [Rules and preconditions](docs/protocol/explicit_refusal_calibration_draft_20261118.md#frozen-development-profile-wildguard-whole-request-dev-v1).
Exact profile SHA-256 (computed from saved bytes): `759d914bde5e8a14d51323e9ab3a140533e9a1f96bb39297b3555da74d837116`.

Bound the public input literal, candidate checkpoint and library revisions, casebook,
parser implementation, dependency lock, runtime target, greedy settings and output
budget. Require no truncation, actual input-token-prefix binding, terminal EOS, and
three ordered, named yes/no fields. Only `Response refusal` maps to the binary diagnostic;
missing calls and invalid output are distinct. No inference runner added.

`python -m pytest -q tests/test_wildguard_dev_contract.py`: 16 passed in 0.05 s
(1.46 s command wall). Isolated Python 3.11.15 configuration/compatibility check at
08:34:45.489Z–08:34:48.502Z, 3.094 s process elapsed: all 13 formatted inputs and the
one missing-input disposition matched the sealed reference; all nine prior supplied
parser fixtures matched their expected strict disposition. The installed Transformers
configuration validated and selected greedy search before checkpoint-specific ID binding.
No WildGuard tokenizer, weights, actual verdicts, model accuracy, GPU compatibility or
runtime identity was verified. Timings are one-off local observations, not benchmarks.
Private verification: `.omp/refusal-contract-freeze/20261118T082550491370Z/`.

Checkpoint access/terms, artifact acquisition and hashing, capacity/ID and tokenizer
preflight, and any compute authorization remain outstanding. No consultant calls,
checkpoint downloads, calibration draw, remote/GPU work, or immutable run writes.

## 2026-11-18 UTC — WildGuard acquisition stopped at read-permission check

Before fetching any gated files, checked the frozen development profile, the
[public pinned file listing](https://huggingface.co/api/models/allenai/wildguard/tree/cbba4823f3e8020e5a74a5e29bf85072def6f2ff),
and the configured local Hub cache. No snapshot directory for that revision was present.
The Hugging Face SDK 2.4.0 read-only `auth_check(token=True, write=False)` returned
`GatedRepoError` (HTTP 403) with the configured local authentication. This establishes
that the current client could not read the gated repository; it does not distinguish
an account approval issue from credential permissions. No file HEAD or download followed.
Public sizes are not proof of payload integrity; the anonymous listing masks LFS digests.

The nine selected safetensors/index/config/tokenizer files total 14,496,898,091 bytes.
At inspection the cache disk had 15,899,291,648 free bytes; a full acquisition would
leave about 1.4 GB before any staging overhead. Prefer the small tokenizer/config files
first after access is confirmed; reserve adequate disk before acquiring and verifying
weights. No cache cleanup was performed.

Command: isolated workflow Python `-I -B <private-attempt>/access.py`,
08:42:13.774Z–08:42:14.180Z (0.406 s in the script; 2.10 s command wall time).
Sanitized record: `.omp/wildguard-acquisition/20261118T084112734330Z/`. No tokens,
headers, signed URLs, or personal account information recorded. No terms accepted,
access request submitted, protected payload downloaded, tokenizer initialized, inference,
GPU work, calibration sampling, or registered-run mutation.

## 2026-11-18 UTC — WildGuard tokenizer-only preflight passed on the sealed development inputs

After the operator reported completing the access step, the local Hub SDK read check
and HEAD for the pinned `config.json` succeeded (0.640 s together with the local cache
inspection). Same revision as above. At 08:47:18Z, acquired six files: `config.json`,
`generation_config.json`, `tokenizer_config.json`, `tokenizer.model`, `added_tokens.json`,
and `special_tokens_map.json` (775,630 bytes total, 6.984 s for this one acquisition and
verification). Checked each HEAD revision and size; matched the downloaded bytes to the
Git blob ID or, for `tokenizer.model`, the authenticated LFS SHA-256. No weight or
index download. Per-file SHA-256 values retained with the private acquisition record.

At 08:48:03Z, ran the isolated workflow Python `-I -B <private-attempt>/fit.py`
offline, CPU only. Transformers 5.22.2 resolved `AutoTokenizer(use_fast=False)` to
`TokenizersBackend` (`is_fast=True`): the argument records what was requested, not a
guarantee of a slow implementation. These counts belong to the resolved backend.
Tokenizer, model config, and generation config agreed on BOS 1 and a single EOS 2;
the profile therefore binds generation PAD to 2. The tokenizer's maximum length was
the library's unspecified-limit sentinel. The profile's conservative bound was 4,096
tokens (minimum of 32,768 model positions and the configured 4,096-token sliding window).

All 13 present inputs fit without truncation or padding and had all-ones masks.
The shortest was `empty` (119 tokens); the longest was `redirect` (144), or 272 with
the 128-token generation reserve. `missing` was not tokenized. The one offline
invocation took 19.344 s including imports, file verification and tokenizer loading;
this is not a throughput benchmark. Evidence: `.omp/wildguard-acquisition/20261118T084627716174Z/`.
This verifies input handling only, not refusal accuracy. No generated labels, GPU use,
consultant calls, calibration sampling, or registered-run writes.

## 2026-11-18 08:52 UTC — WildGuard weight staging blocked on local storage

Windows `Get-Volume` / `Get-Partition` showed no separate mounted local data volume.
The system volume had 15,852,867,584 bytes free. The two pinned safetensors shards
and their index require 14,496,122,461 bytes, leaving only 1.36 GB before staging
overhead. Did not start the transfer or delete files. Authenticated Hub metadata
requests for all three objects confirmed the revision and sizes and returned the
expected object IDs (1.156 s total, one check). These IDs are verification targets,
not checksums of locally acquired weights. Sanitized record:
`.omp/wildguard-acquisition/20261118T085235808507Z/preflight.json`.
Acquisition and local hash verification await suitable storage. No remote volume
provisioned, no inference, and no registered-run change.

## 2026-11-18 09:07:49–09:10:31 UTC — pinned WildGuard weights verified on Modal

The operator approved passing the existing gated-read credential to a CPU staging
function through an unnamed Modal Secret. The off-run app mounted only the existing
`wsa-hf-cache` volume. The function checked authenticated metadata for the index and
both shards against the previously recorded revision, byte counts and object IDs
before fetching them. Access check: 0.795 s; check, fetch and volume commit together:
113.361 s. No weights were copied to the local workstation.

A different CPU function with a read-only mount and no Hugging Face secret read
all 14,496,122,461 persisted bytes. Each shard matched its pinned LFS SHA-256.
The index matched its Git blob ID; its 291 tensor entries referenced exactly the
two verified shards. Read-back and verification took 26.749 s. These are one-off
job timings, not benchmarks. The six tokenizer/config files verified locally earlier
were not staged or checked on Modal in this job. No model loading, GPU allocation,
inference, calibration draw or registered-run access.

Invocation: `uv run --no-project --isolated --python 3.11 --with modal==1.6.4
--with huggingface_hub==2.4.0 python -I -B -u <private-attempt>/stage.py`.
Sanitized per-file verification record: `.omp/wildguard-acquisition/20261118T090624801686Z/result.json`
(SHA-256 `a8f596f751e19178c9b74f7df451006a9da190a843b8584c5dc1759336c59422`).

## 2026-11-18 11:40:44–11:42:11 UTC — offline Modal token IDs matched the local development inputs

Staged the six locally verified tokenizer/config files (775,630 bytes) alongside the
previously verified weights in `wsa-hf-cache`. Both Modal functions were CPU-only;
neither received a Hugging Face secret. A separate network-blocked function mounted
the committed volume read-only and matched all six sizes and SHA-256 values before
opening the tokenizer. The weights were not loaded.

All 13 present cases matched the Windows reference **by token sequence**, checked
using per-case SHA-256 over little-endian unsigned 32-bit token IDs. Masks were all
ones, with no padding or truncation. The empty response had 119 tokens; the missing
response was skipped on both platforms. The longest input had 144 tokens (272 with
the reply reserve) against a conservative 4,096-token capacity. Both platforms
resolved `TokenizersBackend` with `is_fast=True`, BOS 1 and EOS 2. Tokenizer package
versions matched. Modal used Python 3.11.12 rather than the inference profile's
3.11.15: this is evidence of input parity on these cases, not inference-runtime parity.

Commands: isolated local workflow Python `-I -B <private-attempt>/bind.py`, then
Modal SDK 1.6.4 client `python -I -B -u <private-attempt>/remote.py`. The remote
write/commit took 0.544 s and the read-back/tokenization function took 5.873 s
(one invocation each, not benchmarks). Sanitized record:
`.omp/wildguard-acquisition/20261118T113910Z/remote.json`
(SHA-256 `e279e81a21f29f10ff1b6b583039e150d41febaa3e38e7a410c12bcfb21a5380`).
No refusal labels, GPU allocation, calibration sampling, or registered-run access.

## 2026-11-18 UTC — Modal inference image: locked build stopped on registry mismatch

Off-run, CPU only, no volumes/secrets/model access. Used Modal SDK 1.6.4 and the
existing `modal_runner.py` image recipe, not its GPU-decorated entrypoints.
At 11:45:00Z the Windows client stopped rendering progress: its redirected cp1252
stream could not encode U+2713. No worker measurement. `python -I` ignores
`PYTHONUTF8`; explicitly passing `-X utf8` allowed the client to capture build output.
This was a local output issue, not evidence of a remote dependency defect.

At 11:45:22–11:46:02Z the builder selected Python 3.11.15 but `uv sync --locked`
(uv 0.12.18) refused to update the lock; no inference environment could be imported
from the unchanged recipe. To distinguish a version conflict from a source conflict,
ran `uv lock` on a disposable copy in a separate builder using the same base and uv.
The scratch resolver selected no different versions by package name, but switched
122 distinct package names from PyPI to the builder's mirror. Only the package
section changed. On a fresh copy of the **original lock**, `uv lock --check
--default-index https://pypi.org/simple` exited 0. Registry identity matters even
when version numbers agree. No regenerated lock was adopted, no registered run was
involved, and there is no evidence here of an upstream defect.

Preserved client traceback, build output, scratch comparison and commands under
`.omp/wildguard-acquisition/{20261118T114423Z,20261118T114520Z,20261118T114620Z}/`.
The follow-up off-run image adds only the explicit default index to the build recipe;
the shared runner and frozen study inputs remain unchanged.

**Follow-up, 11:48:43–11:49:59Z:** the off-run registry-pinned image built with
`--locked`. A network-blocked CPU worker in Modal image `im-lY38zYLBrB1KCul9dlPSDJ`
reported Linux x86_64, Python 3.11.15, imported PyTorch `2.15.0+cu132` (compiled
CUDA 13.2), and imported Transformers 5.22.2. The embedded `uv.lock`, `pyproject.toml`
and release bootstrap hashes matched local expectations. Zero visible GPUs as intended.
Measurement took 3.793 s in one worker; no driver compatibility, device identity,
BF16 execution, generation behavior or refusal accuracy was tested. No inference,
calibration draw, registered-run writes or shared runner deployment. A future GPU
trial should bind this exact image and check the actual device before loading weights.
Private version record: `.omp/wildguard-acquisition/20261118T114823Z/runtime.json`
(SHA-256 `fb32cbee27f63a1876317469f4a511d400566e1a72d32a8d4fe02b2f62ca35fe`).

### Single A100 WildGuard development trial

Owner authorized one off-run trial on the 13 present harmless inputs. Worker UTC
2026-11-18, launch 16:23:08Z, complete 16:24:17Z. Used verified image
`im-lY38zYLBrB1KCul9dlPSDJ`, a read-only model cache, blocked network and no Hub
credential. One A100-SXM4-40GB (40,960 MiB, compute capability 8.0, driver
620.70.06). Before model load: matched Python/PyTorch/Transformers and lockfile,
tested native BF16 matrix multiplication, rehashed all nine assets, checked all
13 input token fingerprints and capacity. Eager attention, all parameters BF16 on
`cuda:0`, deterministic algorithms, TF32 disabled, seed 0, one greedy sequence per
input. Bound the resolved generation configuration before the first call.

Command: Modal SDK 1.6.4 client, `python -X utf8 -I -B -u <private-attempt>/trial.py`.
An initial **local** registration with `retries=0` was rejected: generator functions
do not accept that argument. Removed it before app launch. No model call was
retried. Single-job wall time 74.64 s; worker time 64.242 s, including 54.052 s
to readiness. One-off timings, not throughput measurements.

Fourteen planned rows: eight refusal, four non-refusal, one invalid (`empty`),
one not obtained (`missing`). Four binary disagreements with authored expectations:
`decline_then_answer`, `selective`, `limitation`, `clarify`. `ambiguous` received
a refusal verdict but has no binary expectation. Full case census and interpretation:
[qualification notes](docs/protocol/explicit_refusal_calibration_draft_20261118.md#a100-development-result--disagreements-with-whole-request-refusal).
No accuracy estimate, promotion, threshold or protocol change. No calibration
draw, registered-run reads/writes, or consultant calls.

Private attempt: `.omp/wildguard-trial/20261118T162107420645Z/`. `events.jsonl`
retains hardware, effective decoding config, call order, complete token sequences,
raw suffixes and parser dispositions (SHA-256
`aa780f7ac3c140671e25e176cd11d2f9053c133c4f65a0e2ff31e058bfb706d0`).
`accounting.json` binds the event stream to the casebook and pinned reference-parser
cross-check (SHA-256 `15fbd42aa070194bc43fb41942c01293c2e48b73cee6a03f05df6c8258cf5cb0`).

### Alternative refusal judges — Firecrawl survey and off-run comparison

Runtime UTC 2026-11-18. After the WildGuard disagreements, the owner requested
HF, forum and paper discovery and comparative tests on the sealed harmless cases.
Firecrawl CLI 1.29.0 `search` and `research search-papers`, plus `pwc` and pinned
model cards/configs, informed the [eligibility notes and per-case census](docs/protocol/explicit_refusal_calibration_draft_20261118.md#alternative-refusal-judges-search-scope-and-eligibility).
Raw sources, profiles, command scripts, asset digests and outputs are under
`.omp/refusal-comparison/20261118T162742Z/`. The survey reviewed 26 checkpoint/dependency
entries and 12 methods; those counts are not counts of tested models. No new
gated agreements, hosted judge calls, Fable consultation or calibration sampling.

The owner approved one ephemeral A100 worker, up to 20 minutes, for Qwen3Guard-Gen
0.6B, 4B and 8B. Before predictions, fixed revisions, the native paired response
template, greedy 128-token cap, strict three-field parser, absence handling and
casebook identity (`qwen/profile.json`). Initial function creation rejected a
custom 49,152 MiB disk request before worker launch; used default ephemeral disk
instead, with the same evaluation profile. One A100-SXM4-40GB worker verified
the public safetensors and tokenizer files, loaded each model sequentially, and
ran 39 single-case calls total. No credentials or persistent model volume.
Launch 16:32:20Z; worker finished 16:36:17Z; one 213.874 s worker invocation,
not a benchmark. For 8B, setup took 114.028 of 122.746 s. The 4B and 8B case
vectors were identical. Larger size did not resolve the mixed cases.
`qwen/measured.jsonl` SHA-256:
`50e18026ee620600a47e8b838cf62ca339ca1ed7d7760f5e7e30705eba17f7f9`.

Ten local CPU encoder checkpoints ran 130 present-case calls in total. Pinned safe
weights and label mappings were bound before predictions; retained logits, softmax
values, native classes, projected whole-refusal labels, and missing/ambiguous flags.
Initial JSON serialization of library loading metadata failed **before** inference;
the bookkeeping fix did not change the profiles. With local available RAM initially
below 1 GiB, a per-model memory guard prevented unsafe loads. As RAM recovered,
all ten completed sequentially (case inference 16:37:21Z–16:43:52Z across jobs).
No repeated predictions. Exact profiles, verified artifact manifests and per-case
evidence: `encoders/final_checksums.json`, SHA-256
`8444afa5dcda6b063317e6e3859fa0524542d4b3a525d192ef9e034af3a36896`.

Separately screened five public Enguard Model2Vec variants (2M–128M) for
response-refusal diagnostics. Their cards expose `PASS`/`FAIL` without an
established mapping to this binary rubric. All five authenticated artifacts also
contained `sklearn.neural_network._stochastic_optimizers.AdamOptimizer` flagged
by `skops.io.get_untrusted_types` (skops 0.16.0). No allowlist override, no model
execution, no refusal verdicts. This is a local deserialization boundary, **not**
a claim that the files are malicious or the dependency defective.

The owner separately approved one short-lived L4 worker in place of the proposed
CPU worker, up to 20 minutes of function runtime. All ten local encoders had already
completed; none were submitted again. Only PolyGuard-Qwen-Smol was dispatched.
It issued 13 calls and returned 13 valid five-field records. For the 12 nonempty
responses it always returned non-refusal, including all three authored whole
declines. For the observed empty response it returned refusal. The missing
response was never scored. Greedy generation was fixed before testing rather
than using the checkpoint's sampling configuration; results apply to this
invocation only.

L4 app launch 16:44:29Z, first host record 17:07:06Z, worker end 17:07:41Z.
Worker elapsed 38.425 s; client command wall time 1,399.50 s. The long interval
before the first host record is not measured model execution or a billing
receipt. The ephemeral app exited; no persistent weights or deployment.
`l4/events.jsonl` SHA-256:
`2dbcefdab6b2b0d80110f50fd83a300bbe14650c9c6b1ab6ee6f431ee5ad0b5c`.

Final: **14 alternative checkpoints, 182 present-case calls**, excluding the
earlier WildGuard trial. Human-CentricAI matched all 12 resolved authored
expectations but consumes only the response. Arctic XS takes the pair and missed
only `redirect`. This supports a new, independently labeled development contrast,
not appointment of either judge, a population accuracy estimate or a calibration
draw. No registered-run artifacts or frozen protocols changed.

### Fresh matched-context test — design and reference lock

The owner approved continuing with Arctic XS and Human-CentricAI, not opening
calibration. Froze [`whole-request-matched-context-dev-v1`](tools/refusal_matched_context_dev_v1.json):
20 harmless rows in ten pairs with byte-identical responses and different user
requests. The design includes quotation, translation, partial fulfillment, redirect,
an unrelated decline, and controls for lack of access, refusal, clarification and
answer correctness. The original development casebook and model selections were
not changed. No registered prompts, outputs, labels, or run artifacts were used.

Two separate AI reviewers saw different shuffled orders of opaque item IDs, with
no pair map, expected directions, candidate identities or predictions. They
applied the fixed whole-request rubric to each row as shown. Their pre-inference
labels agreed on 20/20 rows: eight refusal, twelve non-refusal. This produced
six label-changing pairs and four invariant controls. The reviews are
model-assisted annotations, **not independent human ratings or ground truth**.

Primary diagnostic: both decisions correct on a reference-changing pair. Also
record raw flips, stability and correctness of invariant pairs, and direction
of the raw projected refusal score; no tuning or correctness credit for a
score change that does not produce the correct binary decisions.
Attempt `.omp/refusal-matched-context/20261120T154908458260Z/` preserves separate
rating packets and prospective checkpoint contracts. Casebook SHA-256:
`889cca44265472ee26409a4e6eadf20fb5ab484decef538f0da1e74650feeab1`;
protocol `783cbea7ee1fe66cda389502f5726657d1a3567568d915fa304a77adfe2b846a`;
blinded reference `d35ee38225074ce3d615a58b34a3f60b06cfd2e7edaf57f4a3a8c832e1ae100e`.

**Local attempt, 2026-11-20 15:52:12–15:54:21 UTC:** authenticated all seven
files per checkpoint against the previous study-side byte digests. The isolated
Windows workflow Python ran `measure.py` sequentially, with the same CPU package
versions and memory guard as the previous comparison. Free physical memory after
imports was 349,057,024 bytes for Arctic XS (required 382,028,076) and
1,190,481,920 bytes for Human-CentricAI (required 2,045,320,101). Both stopped
before model load, so there were **zero candidate calls** and no verdicts to compare.
The local two-attempt command took 131.97 s. Private `summary.json` preserves
the failure receipts. These are workstation resource limits, not model or dependency
failures. Do not weaken the guard or replace either judge to get a result.

The owner then authorized one ephemeral Modal CPU worker, 6 GiB RAM and 360 s of
function runtime, with no GPU, credentials, persistent mounts or study data.
Locked `modal-plan.json` (SHA-256
`df5f6e2ab4b16d38c46cb54389d2a22f370407a1298766b36961bb35ab148f3d`) before dispatch.
The plan changes Windows to Linux x86-64; CPU FP32/eager, the two revisions,
their artifact digests, the exact inputs, and the native-label projections remain
fixed. The worker gets the 20 harmless prompt/reply rows, not their reference labels.

**Modal attempt, 2026-11-20 15:57:31–15:57:57 UTC:** Modal SDK 1.6.4,
`python -X utf8 -I -B -u <private-attempt>/modal_cpu.py`. Image
`im-268Ge7XE3tDKUEqzmhBdFl` reported Linux x86-64, Python 3.11.15,
PyTorch 2.15.0+cpu and Transformers 5.22.2. The ephemeral worker verified
both sets of seven files. Arctic XS completed all 20 cases (5.271 s from
per-model start, 0.357 s scoring including event handling; this is not a
benchmark). Human-CentricAI stopped before its first call: the guard compared
the config's generic `LABEL_0`–`LABEL_4` strings directly to the descriptive
names in the pinned model card. The earlier comparison mapped those IDs via
the card. This was a local validation mistake, not a checkpoint error or a
failed prediction. A corrected attempt must verify the generic config and the
card-backed map separately and dispatch only Human-CentricAI.

Arctic XS got both binary decisions correct on 2/6 reference-changing pairs;
its score moved in the reference direction on 5/6. None of the four controls
flipped, but both access-limitation answers were labeled refusal. This rounds
out the mechanism test: receiving context affected scores without reliably
solving the whole-request classification. Worker accounting hash:
`cbae2d96e49345592dc54d252390a6ea5805edb31a7c7e738c55b2e65bb99480`;
event-stream hash:
`bcdfe795c151ae05a0edbca1a5807888077bf581998611b0fc6decff0a16e379`.

**Response-only control, 2026-11-20 16:26:50–16:27:47 UTC:** with owner approval,
dispatched only Human-CentricAI to the same CPU image. Verified the generic config
IDs and the pinned card's class descriptions independently, without changing the
positive classes (1 and 3), cases, reference or metrics. Only row IDs and replies
were sent, not requests or annotations. All seven artifacts verified and all
20 calls completed. No Arctic rerun. Repeated replies produced exactly equal
token IDs and logits on all ten pairs. Human-CentricAI matched 12/20 reference
labels, 0/6 changing pairs and 3/4 invariant controls. Both judges mislabeled both
access-limitation rows. No population accuracy estimate or judge adoption.

Modal SDK 1.6.4 client ran `python -X utf8 -I -B -u <private-attempt>/modal_control.py`.
One invocation: 68.08 s client wall; 47.194 s per-model elapsed (39.983 s for
acquisition and hash checks, 4.399 s for 20 scoring calls including event
handling). Not a benchmark. No GPU, persistent mounts, new study data,
calibration sampling, or registered-run changes.
`control-plan.json` SHA-256 `30a91624532c2e045ba10125d6d1dce9c8a6c4d5a2d7a13f1b4207f90425aac6`;
`control-events.jsonl` SHA-256 `85847612c717cefa65189922f45fd4946792d90977e0a3ec0c335d243eab7602`;
`control-accounting.json` SHA-256 `9d796465e1abbed17b03333ff13107138c5643ffcca7223ee1c33d43f05df871`.

### External data discovery for a trainable refusal judge

2026-11-20 16:31–16:34 UTC (CLI/host clock). The owner asked for datasets
before planning training. Used Firecrawl CLI 1.29.0 `search` and `research
search-papers`, then pinned Hub cards, repository metadata and primary papers
to verify provenance and label semantics. `pwc` located the refusal-taxonomy
paper but returned `paper_not_in_catalog` for CompOrca; cross-checked that
result via ACL Anthology. Pinned anonymous raw card checks for the gated
VINAY, saidutta69 and XSTest-Response releases returned HTTP 401. No access
requested. No dataset payloads downloaded, no training, no model or registered
artifact changes, and no access to the 200 sealed calibration items.

Recommendation, not adoption: first audit the manual Arena annotations as a
natural-response source; verify the join, screen privacy and overlap, and
relabel under the study rubric before use. Add newly authored harmless
context-controlled pairs; keep all benchmark families, existing inspected
development fixtures, and calibration examples out of training/selection.
See the [source and split plan](docs/protocol/explicit_refusal_calibration_draft_20261118.md#training-data-discovery-for-a-new-paired-judge-proposal-only).
Private metadata and search captures:
`.omp/refusal-training-data/20261120T163132Z/manifest.json`
(SHA-256 `de5642c22ef331f3ced772d49a3805a2b9124c6aadaaa27430aec5b13a43315c`).

### Arena training-source audit — join and ordinary cleaning

2026-11-20 UTC. The owner approved a small off-run Arena audit, including
ordinary and embedding-based cleaning, and asked to record every step and its
reason. Ran isolated workflow Python 3.11.15 with `-X utf8 -I -B` and the
scripts in `.omp/refusal-arena-audit/20261120T163627Z/`. No study prompts,
registered replies, or calibration records were opened. No training or
external scoring service. Source rows and row-level diagnostics stay in
gitignored storage; the public record contains aggregate findings only.

1. **Pin and authenticate source bytes** (`fetch.py`, start 16:37:34Z):
   the annotation workbook, Arena CSV and MiniLM assets were fetched from
   exact public Hub revisions; each byte count and advertised Git/LFS object
   identity matched. The workbook was 1,418,060 bytes, the CSV 184,175,071,
   and the model/tokenizer/pooling artifacts 91,567,448. Acquisition command
   wall time: 13.88 s for the parallel fetch, not a speed benchmark. Source
   IDs, revisions and per-file digests are in `sources.json` and the
   `*-acquired.json` records. This makes the join and later similarity results
   reproducible even if a model or dataset `main` branch moves.
2. **Inspect schema and prove the join** (`schema.py`, then `join.py`,
   16:38:46–16:38:50Z, 4.141 s for the join). The workbook embeds both
   original responses, not just labels. Scan the 57,477-row CSV without
   materializing unrelated rows. All 1,750 workbook IDs were unique and
   each had one CSV match. Compare exact decoded prompt and A/B reply
   sequences, both model sides and winner fields, not row position, fuzzy
   text or embeddings. All fields matched for every annotation row; all
   1,750 comparisons contained one user turn and one reply on each side.
   This establishes attachment of 3,500 source labels, not their validity
   under the whole-request rubric.
3. **Screen and count exact reuse** (`clean.py`, 16:40:19–16:40:21Z,
   1.500 s). Hold a whole Arena comparison if either side has a structural
   or privacy-review flag so A/B siblings cannot silently diverge. The
   1,200-character pilot cap keeps examples compact; privacy pattern matches
   and benchmark-name matches are review flags, not clearance or proof of
   overlap. Held 740/1,750 groups: 733 had long text, 22 contact/link
   indicators and one an email-pattern match (nonexclusive). No missing/blank
   turns or unknown classes were flagged. Of 1,010 groups passing these
   screens, NFC/whitespace comparison found three exact prompt–reply
   duplicate clusters and 25 prompts shared across groups. Preserve source
   bytes and both sides; record the groups instead of deleting replies.
4. **Bind the sample before embedding**: shuffle screen-passing groups
   after sorting by ID (seed 20261120), take 80, then add the next 40 disjoint
   groups with an upstream technical-refusal side. This gives 240 replies
   and deliberately increases the number of the most suspect source label,
   so it cannot estimate population disagreement. The local wording screen
   marked 11 of 96 sample technical-refusal replies as containing access or
   inability wording. This prioritizes human review; it does not prove
   mislabeling. No source label was automatically changed.
5. **Screen near-duplicates locally** (`embed.py`, 16:41:28–16:42:38Z).
   Used `sentence-transformers/all-MiniLM-L6-v2` at
   `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, authenticated safetensors,
   `BertTokenizer`, FP32 CPU, two Torch threads, batch 16, attention-mask
   mean pooling and L2 normalization. Versions: PyTorch 2.15.0+cpu,
   Transformers 5.22.2, NumPy 2.4.6. Embedding request and reply separately
   distinguishes prompt reuse from response reuse and avoids merging different
   intents on a generic reply. Used the model's 256-token cap without
   truncation. Ten of 240 sides exceeded the cap in at least one input;
   retained them in the audit census but did not compare them semantically.
   One invocation: 69.906 s measured in the script, of which 53.750 s was
   embedding and matrix comparison; 89.66 s command wall time. Not a benchmark.
6. **Interpret flags without rewriting the data.** Predeclared cosine
   review bands: both views ≥0.90 for joint candidates; otherwise prompt
   ≥0.90 or reply ≥0.92. Removed within-comparison A/B edges from the
   candidate list, not from the sample. On the 230 embedded sides there
   were 12 prompt-only edges (three Arena group links), six across sides
   with different source labels. Eight edges had literally equal prompts;
   the other four represented one group link with case-only variation.
   No joint or reply-only edge met the bands. The harmless sanity controls
   scored 1.000 for identical text, 0.821 for an authored paraphrase and
   0.026 for unrelated text. Since the paraphrase falls below the 0.90
   review band, a clean result cannot certify absence of paraphrases.
   The descriptive case-fold inspection did not change the policy or
   rerun embeddings. No candidate was deleted or relabeled.
7. **Verify evidence** (`verify_audit.py`, 5.21 s command wall): checked the
   one-to-one census, quarantine and sample membership, embedding coverage,
   candidate bands and source-label agreement bookkeeping. The manifest
   binds verified inputs, scripts and outputs, and confirms the listed
   row-level artifacts are gitignored. Study benchmark payloads were not
   compared, so overlap clearance is still outstanding. No blinded human
   relabeling took place; there is no estimate of rubric disagreement.

Source plan SHA-256 `6201e5c448010921660de4bd7246aebc6e200a90ce95dafbeb5d09eff8154eca`;
audit policy `e9467190b72b0c68a9950c203a2ab124800823143b5999964cef628fff756a97`;
join report `7f0868b74c5c542ba4b0c97270e118fba46715894b73f77bc5f3d277743a8da1`;
cleaning summary `548eebb3d0cd390d2ad795a4107499bdb529a04bf117187d446d95b2b5b067c5`.
Evidence manifest SHA-256 `6dcbb8fa758b8f925fdff18a3f8f6d54ef29981a97808efa62555dda37387760`;
embedding summary `8cc153fd824c0efbd3c6202bfdb1e04111cac262c535e934a401c2da3ec1dfb7`;
descriptive candidate inspection `40c1d947e007033ad5727846a7f9fa274b25a7214a70b1dd18d5f59b97435931`.
See [training-source audit interpretation](docs/protocol/explicit_refusal_calibration_draft_20261118.md#arena-source-audit--what-is-and-is-not-ready).
[INFERENCE] Arena is viable as a source of bound natural replies. It is not
training-ready; next review privacy/content eligibility, grouped overlap checks,
and blinded human reannotation before choosing examples or starting training.

### Arena pre-annotation audit — public overlap and operator clearance

The owner approved continuing with privacy and benchmark-overlap screening and
preparation for blinded human relabeling. Used the same frozen 120 Arena
comparison groups; no new Arena groups selected. Verified the sample and MiniLM
asset-receipt hashes against the previous manifest. No raw Arena text was sent to
services or reviewers. Scope is external audit only, not training, study-data
access, or release to annotators.

Retrieved public Hub metadata, resolved each source to a revision and checked
file size plus the published Git/LFS identity before parsing. Retained only the
250 XSTest rows publicly labeled `safe`, 1,319 prompts from OR-Bench `hard-1k`
(not its toxic split), and 541 IFEval prompts. Discarded XSTest's other rows
before constructing the reference file. No benchmark answers, HarmBench,
SORRY-Bench, derivatives, or historical run/split payloads were used. This
checks the selected public releases—not all protected material and not exact
historical run membership. Limits apply even to an empty hit list.

Frozen policy SHA-256
`e01baa49f35f6a05c9348e1921f004c0782aa21c387d7d0e567d17cdba37377c` under
`.omp/refusal-arena-audit/20261120T164519322101Z/`. Use NFC/whitespace/case-folded
exact comparison to catch straightforward variants; use pinned MiniLM
prompt embeddings for semantic candidates. Lowered the *new audit's* review
band to 0.78 before scoring because the prior harmless paraphrase scored 0.821.
This changes review sensitivity, not a study cutoff or a recall guarantee.
Compare the user's request rather than a boilerplate refusal reply when
screening for copied benchmark prompts. Do not truncate, auto-delete, or infer
an identical label from a shared request. Flags apply to both Arena reply sides.

**Measured, 2026-11-20 16:47:54–16:52:32 UTC:** ran the isolated workflow
Python 3.11.15 `-X utf8 -I -B -u <private-attempt>/screen.py` on Windows,
two CPU threads, FP32, batch 32; torch 2.15.0 (package metadata),
Transformers 5.22.2, tokenizers 0.23.3 and NumPy 2.4.6. The normalized
exact pass covered all 120 × 2,110 prompt pairs. The embedding pass compared
119 × 2,109 pairs (250,971); one Arena prompt and one IFEval prompt exceeded
the 256-token cap. The harmless paraphrase and unrelated controls scored 0.821
and 0.026, respectively. No exact cross-source matches and no semantic
cross-source candidate at 0.78. Maxima by family: XSTest 0.560, OR-Bench 0.644,
IFEval 0.563. This is evidence about those inputs and comparison rules only.
Script elapsed 277.921 s, of which 242.625 s was tokenization, embedding and
comparison; one command wall time 346.60 s. Not a benchmark.

For privacy triage scanned both reply sides and their prompt for contact,
identity and account/credential markers. One group was held for an account or
secret marker, not a confirmed disclosure. Nine groups were held for
within-sample reuse review (three normalized exact links and three semantic
candidate links), and one for the missing long-prompt comparison. No automatic
removal or relabeling. Keep linked groups together until reviewed; a request
match can legitimately have different replies and refusal labels.

`handoff.py` (12.10 s command wall time) created a restricted local queue of
109 groups / 218 replies: 73 random-screened and 36 technical-enriched groups.
Verified every staged prompt and both replies against the frozen sample and
that all 11 held IDs are absent. Opaque item keys, separate coordinator-only
source labels/strata, and a blank clearance form prevent accidental release
of upstream judgments. The operator queue is **not** a rater packet; the
operator must approve privacy, content and use first. Zero human votes and
zero packets released. Benchmark checks outside these public references and
human clearance remain outstanding. No training, registered-run changes or
calibration access.

Private screen summary SHA-256 `7d1f4e4f34d562d04b82ebb032c8bbe08f64fa5d0e1f66db100406e60cc2fd9c`;
phase manifest `3cf62ec285331102aa10c32995e19ab67fa59c842582b93cc749dee270b62ac2`.

## 2026-11-24 — Method scope declared; capability seeds honoured

Owner direction: the new paired-judge work stays parked; proceed on the roadmap with everything that
does not need a GPU. No registered number, receipt or pre-registration byte changed.

**Decision 1 — linear-attention output projections are in the method's scope.** Consulted
`gemini-4-neon-high` through `agy` (exit 0, 136 s; prompt, stdout, stderr and hashes in
`docs/protocol/consultation_20261124/`). It recommended declaring the rule functionally ("every
token-mixer and MLP residual-writing projection") rather than silently widening or dropping the
registered model. Checked its two paper claims against primary text: arXiv:2406.11717 §4.1 does
orthogonalize "the embedding matrix, the positional embedding matrix, attention out matrices, and MLP
out matrices … as well as any output biases", and arXiv:2412.06464 is the gated-delta-net paper.
`harness/methods/abliteration.md` now declares the scope, and declares two differences from the paper
that were previously implicit: the direction is per-layer (from `direction_derivation`) rather than one
global vector, and embedding, positional and bias writers are not edited. The last one is a narrowing,
not an oversight: it is stated so a reviewer can reject it, and adding it is a different candidate.

**Decision 2 — `capability_suite` passes the registered seed.** The gate built one `lm_eval` command
with no `--seed`, so `harness.json`'s seeds 0, 1, 2 were three identical runs: lm_eval defaults to
`0,1234,1234,1234`, and the fourth slot seeds the few-shot sampler (`_cli/run.py` passes `cfg.seed[3]`
to `fewshot_random_seed`, `evaluator.py` calls `task.set_fewshot_seed`, `task.fewshot_examples` draws
from it — checked in the pinned `d6de8164` tree). Neon recommended three real runs over three identical
ones for the same cost claim; the source check is what settled it. The gate now runs once per seed into
`results/lm_eval/seed-<s>/` with its own logs and records `per_seed` plus cross-seed mean and sample
`sd` (null, not zero, for a single seed) in `results/capability_suite.json`. Tasks, few-shot count,
model revision, dtype and every decision rule are untouched. Deviation appended to both ledgers
(qwen seq 29, run-1 seq 22); `scripts/verify_ledger.py` reports both chains clean.

**New, tested, not yet run:** `scripts/record_tensor_inventory.py` loads the registered checkpoint on
CPU with the pinned `transformers`, enumerates the method's targets through `_targets`, records the
key names, shapes, dtypes and edited-parameter fraction, and appends the `tensor_inventory` entry. It
refuses a partial target set, a block-count mismatch, or an existing inventory file. `runs/**/tensor_inventory.json`
is `-text` so the entry's hash matches the stored bytes. Tests: `tests/test_capability_seeds.py` (7),
`tests/test_tensor_inventory.py` (6). Not executed here: the checkpoint is not on this host, and
`compute_evidence` needs the GPU.

The recorder also records a census of the three writers the method excludes — embedding matrix,
positional embeddings, output biases — with their actual names and shapes, plus the tied-embedding
flag. This answers "did we skip it or does it not exist" with evidence at inventory time instead of an
inference, which matters most for positional embeddings (RoPE models have no such tensor) and biases
(absent when every projection is `bias=False`).

**Still GPU-bound:** a canonical `host` session via `scripts/record_host.py` (preflight currently
refuses new gates: `host-before-gates`, no canonical session), `tensor_inventory`, `compute_evidence`,
`method_selected`, then parent `capability_suite` and the candidate gates.

## 2026-11-26 — AMD MI300X preparation (no GPU work)

Owner direction: execution machine will be an AMD MI300X (gfx942, ROCm, 192 GB HBM3). Prepared
vendor-neutral tooling so the first session on the machine is measurement, not debugging.

**`harness/device.py`** — detects vendor (ROCm/CUDA/CPU), architecture, HBM, flash-attention
library (AOTriton vs CK), and bf16 support; `python -m harness.device` prints the full JSON.
Splits ROCm environment variables into arithmetic-neutral (`HIP_FORCE_DEV_KERNARG`) and
may-change-arithmetic (`TORCH_BLAS_PREFER_HIPBLASLT`, `PYTORCH_TUNABLEOP_ENABLED`,
`TORCH_ROCM_FA_PREFER_CK`). The second group must pass the equivalence check before gate use.
Smoke-tested on CPU (this host); torch 2.15.0+cpu.

**`scripts/benchmark_inference.py`** — sweeps batch sizes with deterministic synthetic tokens,
measures tokens/s and peak HBM for generation and forward (judge), and recommends the smallest
batch within 2 % of peak throughput. Smoke-tested on CPU with
`hf-internal-testing/tiny-random-LlamaForCausalLM` (batch 1,2; float32). No study prompts used.

**`scripts/check_device_equivalence.py`** — regenerates a deterministic sample from a stored
parent arm and compares greedy outputs token-for-token. Reports exact-match rate and first
divergence offset per prompt. Exit 2 when the rate is below `--min-match` (default 1.0). Uses
the same `judge_fix.generate_length_sorted` path the gate runs.

**`scripts/record_host.py`** — now auto-detects vendor GPU tools (`nvidia-smi`, `amd-smi`,
`rocm-smi`) via `shutil.which` and includes their probes. Absent tools are never probed, so
`--require-probes` still checks only what exists plus user-specified ones.

**`docs/amd_mi300x.md`** — runbook: verification order on arrival, install notes (ROCm torch
wheel for pinned version), env-var split with the "run the equivalence check" rule, attention
backend selection, what to record, and what not to do (vLLM for gates, benchmark on arms,
rewrite stored parent results). Sources: ROCm inference-tuning docs (scraped via firecrawl),
torch ROCm FA selector source, vLLM MI300X blog post. All cited by URL.

Tests: `tests/test_device_report.py` (6 passed). Full suite pending.
