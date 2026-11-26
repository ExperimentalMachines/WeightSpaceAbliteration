# Dependency and image audit — 2026-11-17 UTC

Status update: Arjhine selected **workflow coverage + Python 3.11.15** for local dependency/
image-definition updates and isolated validation. The findings below describe the preceding
audit, during which root dependency/image files and the installed project environment were
unchanged. Implementation results are recorded in
[`dependency_update_20261117.md`](dependency_update_20261117.md) and `EXECUTION_LOG.md`.

No image build/deployment, model/task-resource download, GPU workload, new registered run,
or historical-artifact change is authorized. Private audit evidence remains under
`.omp/dependency-audit/20261117T152146Z/`.

## Existing lock and recorded environment

The universal lock contains 116 entries for 113 distinct package names. NumPy, SciPy,
and NetworkX each have Python-version branches. For Linux/CPython 3.11.12, the selected
versions include NumPy 2.4.6, SciPy 1.17.1, and NetworkX 3.6.1; selecting the last entry
by name would incorrectly report drift against the recorded host.

All eight comparable versions in the preserved host census match the selected lock branch:
`datasets`, `gdkit`, `lm-eval`, `numpy`, `pyarrow`, `pyyaml`, `torch`, and `transformers`.
The core remains torch 2.15.0, Transformers 5.22.2, lm-eval 0.4.13, and gdkit at the
existing Git commit. The recorded GPU build reports torch `2.15.0+cu132`, CUDA 13.2,
and cuDNN 92600. Package-version agreement is not proof of Windows/Linux binary or
CUDA ABI equivalence, and the historical census did not capture every installed package.

## Recorded supplements absent from the lock

| Package | Proposed recorded pin | Evidence strength |
|---|---|---|
| accelerate | 1.15.0 | Preserved host census and execution log |
| sentence-transformers | 6.3.0 | Preserved host census and execution log |
| tiktoken | 0.14.0 | Execution log and historical consultation of machine installation output |
| sentencepiece | 0.2.3 | Execution log and historical consultation of machine installation output |
| protobuf | 7.36.2 | Execution log; independent machine-output confirmation remains unresolved |

The recipe currently installs these names without the recorded version pins after installing
requirements exported from the lock. That second installation is not governed by the lock.

A source-inspection correction: the current BGE and MiniLM embedding utilities use
Transformers `AutoModel`/`AutoTokenizer` directly; no SentenceTransformer import was found
in the inspected harness/tools/gdkit paths. Retaining sentence-transformers initially is
historical-environment parity, not proof it is a current direct code requirement. A Hub
repository namespace is not the same thing as a required Python package.

## Dependencies of the already-selected workflow

Installed lm-eval 0.4.13 metadata declares an `hf` extra containing Accelerate and PEFT,
and an `ifeval` extra containing langdetect, immutabledict, and NLTK. Transformers 5.22.2
metadata declares `sentencepiece` and `tiktoken` extras, including Protobuf and blobfile.
The configured capability suite already selects the HF backend and IFEval.

Actual import-only checks in the current **local project environment** failed as follows:

- `lm_eval.models.huggingface`: `ModuleNotFoundError: accelerate`.
- `lm_eval.tasks.ifeval.instructions`: `ModuleNotFoundError: langdetect`.

These are project dependency-coverage gaps, not manufactured upstream defects. They do
not establish which packages were absent from the historical remote environment.
No model was constructed and no benchmark/task dataset was loaded.

## Isolated resolution results

Both shadow projects held every existing lock version fixed while checking additions.

| Candidate | New lock entries | Existing version changes | Existing source/sdist/wheel metadata changes |
|---|---:|---:|---:|
| Five recorded supplements | 6 | 0 | 0 |
| Supplements plus selected backend/task/tokenizer extras | 11 | 0 | 0 |

The common sixth entry is psutil, a transitive dependency. The extra workflow coverage
comes from `lm-eval[hf,ifeval]` and `transformers[sentencepiece,tiktoken]`, not from adding
new scientific tasks or performance backends.

| Newly resolved dependency beyond the five recorded pins | Shadow pin |
|---|---|
| psutil | 7.2.2 |
| blobfile | 3.3.0 |
| immutabledict | 4.3.1 |
| langdetect | 1.0.9 |
| peft | 0.21.3 |
| pycryptodomex | 3.24.2 |

These are future-environment proposals, not recovered historical versions. New-to-lock
does not necessarily mean new-to-historical-runtime.
Presence-sensitive optional packages, including PEFT, can enable different library paths
even when existing versions stay fixed. Resolver success is not numerical-equivalence evidence.

A clean minimal proposal was also resolved after removing the audit-only duplicate
constraints. It retains the same additions and preserves all previous package versions
and source/artifact metadata. Its proposed `[tool.uv]` requires uv 0.12.18 and constrains
the gdkit build's setuptools input to the already-locked 84.2.1, using archive hashes
extracted programmatically from the existing lock. The clean proposal resolved in
1.531 seconds. No candidate ML environment was installed and no wheel-build validation
was performed. The historical exporter probe provisioned uv 0.8.17 in an isolated tool
cache only; it did not change the project's installed environment.

## Image and toolchain boundaries

The recipe also leaves these inputs floating or incompletely recorded:

- Python is specified as the `3.11` series, not a patch release.
- `pip install uv` does not specify a version. Historical build inspection found 0.8.17
  in an initial build; that is not a complete identity for every measurement image.
- Debian/base-image identity and apt Git installation are not pinned by the Python lock.
- Export uses `--no-hashes` before the second unconstrained package installation.
- The pinned gdkit Git source declares `setuptools>=77` for isolated builds. Runtime
  package pins alone do not fix that build environment.

The local resolver is uv 0.12.18. The SDK used in the local publication checks is Modal
1.6.4; the earlier read-only volume inventory used 1.5.5. Historical uv 0.8.17 successfully
exported both the root lock and the runtime shadow proposal. That does not mean it should
silently consume the final proposal's new exact installer requirement/build constraints.

[Modal's Image API](https://modal.com/docs/reference/modal.Image) supports full Python
versions and `uv_sync(frozen=True, uv_version=...)`. The latter creates a virtual environment,
includes `pyproject.toml`/`uv.lock`, and does not install local project source. It can replace
the export-plus-supplements recipe while keeping code delivery separate.

[uv's documentation](https://docs.astral.sh/uv/concepts/projects/sync/) distinguishes
`--frozen` (trust the lock without checking freshness) from `uv lock --check`/`--locked`
(require correspondence with project metadata). The root `uv lock --check` passed during
this audit. The proposed pipeline should check correspondence before using a frozen image
installation. [Build constraints](https://docs.astral.sh/uv/reference/settings/#build-constraint-dependencies)
bound isolated build dependencies separately from runtime dependencies.

Public Docker Hub metadata confirms active Linux/amd64 Bookworm bases for both
[Python 3.11.15](https://hub.docker.com/v2/repositories/library/python/tags/3.11.15-slim-bookworm)
and [Python 3.11.12](https://hub.docker.com/v2/repositories/library/python/tags/3.11.12-slim-bookworm).
Registry-returned digests are captured privately, not hand-written. This is availability
metadata only: neither image was pulled/built, and neither is established as the exact
historical Modal base. Complete historical image/base IDs and apt/build-tool versions
were not recovered from the checked records; permanent loss is not established.

## Resources outside the Python lock

IFEval's `instructions_util.py` checks/downloads NLTK `punkt_tab` at import time when
missing on rank 0. NLTK 3.10.4 is already locked, but its data is a separate artifact.
The current local filesystem has `punkt_tab`; its exact bytes and remote availability
were not certified, and nothing was downloaded during this audit.

Before remote evaluation, explicitly provision and hash the required resource, set its
location, and fail closed when unavailable instead of relying on runtime downloads.
Model/tokenizer bytes, task datasets/access, and scientific gate correctness remain
separate validation requirements. A resolver pass is not an image, import, ABI, or model pass.

## Recommendation and owner decisions

Independent Fable/Argon reviews and the requested Opus reconciliation recommend the
workflow-coverage profile and a deliberately recorded future target aligned to local
Python 3.11.15 with uv 0.12.18 and Modal SDK 1.6.4. Reviewer wording that treated missing
historical identities as unrecoverable was rejected; the inventory only establishes
not-found-in-checked-records.

The owner selected the first option in each of these presented choices:

1. Adopt the workflow-coverage profile, or stage only the five recorded supplements first
   and explicitly keep capability dependency completion blocked.
2. Target Python 3.11.15 to align with the currently exercised local verifier, or preserve
   the recorded GPU Python 3.11.12 patch and provision a matching auditor interpreter.
   Neither choice recreates the historical image. The minimal proposal uses the audited,
   pinned uv 0.12.18 for future installation rather than an unpinned bootstrap.

After approval, local adoption should preserve the demonstrated additions-only lock diff,
use the selected digest-pinned base and a single locked install recipe, and verify in an
isolated environment. Image builds/deployments, resource/model downloads, GPU measurements,
new run creation, and changes to historical remote files remain separately gated.

## Executed checks and timing

The primary probes began at **2026-11-17T15:40:32Z**. Recorded-supplement resolution took
**2.609 s**; workflow resolution **2.625 s**; historical-tool export **12.141 s**. Import-only
failures were captured after **32.922 s** (HF) and **20.172 s** (IFEval); these are process
startup/import timings, not inference benchmarks. The clean proposal probe ran at
**16:11:17Z–16:11:19Z**. Exact commands, stdout/stderr, metadata and hashes are retained
privately. No permanent tests were added for this investigation.
