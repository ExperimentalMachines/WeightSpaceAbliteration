# Dependency target adoption — 2026-11-17 UTC

## Approved scope

The operator selected workflow coverage and Python 3.11.15 after the
[dependency/image audit](dependency_image_audit_20261117.md). Local dependency and image-
definition updates plus isolated validation were authorized. No image build/deployment,
model/task-resource download, GPU workload, new registered run, or historical-artifact
change was authorized or performed.

## Applied changes

- `pyproject.toml` declares `lm-eval[hf,ifeval]` and
  `transformers[sentencepiece,tiktoken]`, plus the five recorded supplementary pins.
- `uv.lock` adopts the generated 127-entry proposal: eleven additions, no existing package
  version or source/sdist/wheel metadata changes. The gdkit Git commit is unchanged.
- The project requires uv 0.12.18. Its setuptools build dependency is constrained to the
  already-locked 84.2.1 using archive hashes extracted programmatically from the prior lock.
- `modal_runner.py` references the registry-returned Linux/amd64 digest for the selected
  Python 3.11.15 Bookworm base and requires Modal SDK 1.6.4. No digest was invented.
- The export-plus-unpinned-supplements recipe is replaced by one `Image.uv_sync` operation.
  It uses `frozen=False` with `--locked --no-dev --no-python-downloads`: this prevents the
  SDK from adding `--frozen` and makes uv reject stale project/lock metadata rather than
  silently trust it or update it during the build. Dependency and code delivery remain separate.
- The runner refuses an unexpected Python patch before preparing a selected remote release.
  Existing apt Git installation remains explicit; this is not a claim of a hermetic OS rebuild.

The active project `.venv` was deliberately not synchronized. Validation used the separate
ignored environment at `.omp/dependency-update/20261117T164529Z/environment/`. A 125-name
package census of the original environment remains unchanged, as do all 96 protected
run/pre-registration files. No working-repository commit or push was made.

## Observed validation

| Check | Result | Timing |
|---|---|---:|
| Root project/lock correspondence | `uv lock --check` passed | resolver reported 29 ms |
| Isolated locked installation | 103 packages installed; dependency inputs unchanged during installation | 34.14 s |
| Installed-package census | 103 expected and 103 present; zero version mismatches or unexpected packages; gdkit commit matches | included in import validation |
| Selected workflow/tokenizer-support imports | Six passed; zero network/download attempts recorded by the guards | 79.94 s process wall time |
| Core provenance/preservation/census regressions in the isolated environment | 298 passed, 20 skipped | pytest 124.70 s; wrapper 126.594 s |
| Publication/SDK boundary regressions with pinned SDK | 11 passed | pytest 15.69 s; command wall 20.95 s |
| Actual local release/host/gate/verifier CLI lifecycle in the isolated environment | Passed | 6.40 s process wall time |
| Intentionally unsupported SDK invocation | SDK 1.5.5 invocation refused with the required-1.6.4 message before image preparation | 2.58 s |

The installation ran **2026-11-17T16:57:51Z–16:58:25Z**. Import validation was recorded
**17:04:08Z–17:05:25Z**; module-import timings are not inference benchmarks and are not
comparable to the earlier failing cold-import durations. The regression wrapper ran
**17:19:34Z–17:21:40Z**. Skips require Windows symlink privileges unavailable on this host;
no complete-suite or Linux/CUDA runtime pass is claimed.

The six import checks were:

- `lm_eval.models.huggingface`
- `lm_eval.tasks.ifeval.instructions`
- `tiktoken`
- `sentencepiece`
- `google.protobuf`
- `blobfile`

The validation used Hugging Face offline/telemetry settings, Python socket guards, and a
refusing NLTK-download guard. No model constructor or task-evaluation API was invoked.
IFEval used the already-existing local `punkt_tab` resource. Its bytes were not certified,
and its availability here does not prove it is provisioned in the future image.

The CLI lifecycle smoke used two temporary fixture rows, not study data: build and verify
an actual development release, record a real CPU host, execute the cheap split-integrity
gate, verify the receipt, refuse occupied outputs, preserve an earlier receipt after a
second host session, distinguish stale from invalid, and detect changed input bytes.

The install log records a local langdetect wheel build. It does not establish a fresh
Linux gdkit build: gdkit was installed from its pinned VCS identity with cache reuse.
Build constraints are now configured, but fresh image/build-tool validation remains pending.

## What remains unverified

- The image definition has not been pulled, built, deployed, or run. Local SDK construction
  is not a remote image-build test. Supported builder behavior, apt/OS versions, actual
  built-image identity and resolved in-image packages still need recording.
- No Linux/CUDA import, ABI, model-loading, numerical-equivalence or throughput test ran.
- Configured model revisions do not certify downloaded weight/tokenizer/config bytes.
- NLTK data, task datasets/access, and offline resource provisioning remain separate inputs.
- Presence-sensitive optional packages can affect library paths; unchanged existing versions
  do not establish equivalence to the incomplete historical environment.
- Scientific refusal calibration, capability seeds/prompt policy/output coverage, controls,
  candidate admission and promotion remain separately gated.

Private commands, exact outputs, metadata, hashes, environment census, release snapshots and
fixture evidence are retained under `.omp/dependency-update/20261117T164529Z/`. Do not
publish the environment tree, raw host records or diagnostic paths.

Next: review/provision the required external artifacts and define an isolated CPU-only
image validation before seeking permission to build or deploy. Historical remote evidence
remains untouched under C1, and the future linked run remains uncreated under B1.
