"""Modal entrypoints for explicitly selected code releases and run namespaces.

Local preparation (no Modal API calls):
    python scripts/build_release.py build --repo . --output .omp/releases --working-tree
    python scripts/build_release.py verify .omp/releases/<release_id> --source-root .

Remote operations require separate owner authorization. A committed revision does not
imply human review; upload_release requires an explicit --reviewed attestation. Development
bundles are local-only. GPU functions require both --run and --release-id, never default to
historical runs, and must not run concurrently against a run/volume. No CPU-only smoke is
provided by these GPU-decorated entrypoints.
"""
from __future__ import annotations

import hashlib
import io
import os
import platform
from pathlib import Path
import re
import shlex
import subprocess
import sys

import modal

SOURCE_ROOT = Path(__file__).resolve().parent
RUNNER_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
IMAGE_INPUT_SHA256 = {
    name: hashlib.sha256((SOURCE_ROOT / name).read_bytes()).hexdigest()
    for name in ('pyproject.toml', 'uv.lock')
}
WORKSPACE = Path('/workspace')

PYTHON_VERSION = '3.11.15'
UV_VERSION = '0.12.18'
MODAL_SDK_VERSION = '1.6.4'
BASE_IMAGE_REFERENCE = 'python@sha256:77923445c077d8eb971b14b2b114a1d9cd4a87edb4c75654820ca4832ee8cb15'

if modal.__version__ != MODAL_SDK_VERSION:
    raise RuntimeError(f'Modal SDK {MODAL_SDK_VERSION} is required; use the pinned deployment environment')

# The base digest comes from recorded Docker Hub linux/amd64 metadata. Apt Git and
# actual built-image identity still require recording after a separately approved build.
image = (
    modal.Image.from_registry(BASE_IMAGE_REFERENCE)
    .apt_install('git')
    .uv_sync(
        uv_project_dir=str(SOURCE_ROOT), uv_version=UV_VERSION,
        # --locked rejects stale project metadata rather than silently trusting a
        # frozen lock. frozen=False here prevents the SDK adding --frozen as well.
        frozen=False, extra_options='--locked --no-dev --no-python-downloads',
    )
    .add_local_file(str(SOURCE_ROOT / 'harness/releases.py'), '/opt/wsa/releases.py', copy=True)
    .env({'HF_HOME': '/hf-cache', 'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'})
)
app = modal.App('wsa-study')
workspace_vol = modal.Volume.from_name('wsa-workspace')
hf_cache_vol = modal.Volume.from_name('wsa-hf-cache')
VOLUMES = {'/workspace': workspace_vol, '/hf-cache': hf_cache_vol}
PULL_PATTERNS = [
    'runs/*/ledger.jsonl', 'runs/*/host.json', 'runs/*/hosts/**',
    'runs/*/harness.json', 'runs/*/receipts/*.json', 'runs/*/logs/*.log',
    'runs/*/logs/*.log.partial', 'runs/*/results/**', 'runs/*/execution/*.json',
    'runs/*/failures/*.json',
]


def upload_code_release(volume, release_dir: Path, *, reviewed: bool) -> dict:
    """Publish only a verified immutable release, never any run or private artifact."""
    from harness.releases import verify_release
    from modal.exception import NotFoundError

    release_dir = Path(release_dir)
    manifest = verify_release(release_dir)
    if manifest['source']['development']:
        raise ValueError('development working-tree bundles cannot be uploaded')
    if not reviewed:
        raise ValueError('explicit review attestation is required; a commit is not review evidence')
    prefix = f"releases/{manifest['release_id']}"
    expected = dict(manifest['files'])
    manifest_bytes = (release_dir / 'release-manifest.json').read_bytes()
    expected['release-manifest.json'] = hashlib.sha256(manifest_bytes).hexdigest()
    try:
        entries = list(volume.listdir(prefix, recursive=True))
    except (FileNotFoundError, NotFoundError):
        entries = []
    present = set()
    for entry in entries:
        remote = entry.path.lstrip('/')
        if not remote.startswith(prefix + '/'):
            raise ValueError('remote release listing escaped the selected prefix')
        relative = remote[len(prefix) + 1:]
        kind = getattr(entry.type, 'name', '')
        if kind == 'DIRECTORY':
            if not any(path.startswith(relative + '/') for path in expected):
                raise ValueError('unexpected remote release directory')
            continue
        if kind != 'FILE' or relative not in expected or relative in present:
            raise ValueError('unexpected or duplicate remote release entry')
        digest = hashlib.sha256()
        for chunk in volume.read_file(entry.path):
            digest.update(chunk)
        if digest.hexdigest() != expected[relative]:
            raise ValueError('remote release bytes differ; replacement refused')
        present.add(relative)
    missing = sorted(set(expected) - present)
    # Snapshot and recheck all source bytes before beginning the batch. The manifest
    # is published last, but consumers still verify the complete payload before use.
    snapshots = {}
    for relative in missing:
        data = (release_dir / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected[relative]:
            raise ValueError('local release changed during publication preflight')
        snapshots[relative] = data
    ordered = [name for name in missing if name != 'release-manifest.json']
    if 'release-manifest.json' in missing:
        ordered.append('release-manifest.json')
    streams = [io.BytesIO(snapshots[name]) for name in ordered]
    try:
        if ordered:
            with volume.batch_upload(force=False) as batch:
                for name, stream in zip(ordered, streams):
                    batch.put_file(stream, f'/{prefix}/{name}')
    finally:
        for stream in streams:
            stream.close()
    return {'release_id': manifest['release_id'], 'uploaded': len(ordered),
            'identical': len(present), 'run_files_touched': 0}


@app.local_entrypoint()
def upload_release(release: str, reviewed: bool = False):
    """Publish a reviewed Git release; requires separate remote-write authorization."""
    print(upload_code_release(workspace_vol, Path(release), reviewed=reviewed))


@app.local_entrypoint()
def pull_results():
    """Pull new evidence and verified suffixes; preserve conflicts outside runs/."""
    from harness.artifact_sync import pull_run_artifacts

    print(pull_run_artifacts(workspace_vol, SOURCE_ROOT, PULL_PATTERNS))


def _prepare_release(run: str, release_id: str):
    """Validate trusted bootstrap, release bytes, and explicit contained run path."""
    if not re.fullmatch(r'[0-9a-f]{64}', release_id):
        raise ValueError('release_id must be the generated 64-character release digest')
    if not re.fullmatch(r'runs/[A-Za-z0-9][A-Za-z0-9_.-]*', run):
        raise ValueError('run must be an explicit runs/<run_id> path')
    if platform.python_version() != PYTHON_VERSION:
        raise ValueError(f'expected Python {PYTHON_VERSION} in the selected image')
    release_dir = WORKSPACE / 'releases' / release_id
    run_dir = WORKSPACE / run
    for path in (release_dir, run_dir):
        if not path.is_dir() or path.resolve() != path.absolute():
            raise ValueError('release and run must be existing, nonredirected directories')
    sys.dont_write_bytecode = True
    # This verifier comes from the image, not from unverified volume code.
    sys.path.insert(0, '/opt/wsa')
    import releases as trusted_release

    manifest = trusted_release.verify_release(release_dir)
    if manifest['source']['development']:
        raise ValueError('development releases are not remote execution releases')
    expected = manifest['files']
    bootstrap_digest = hashlib.sha256(Path(trusted_release.__file__).read_bytes()).hexdigest()
    if bootstrap_digest != expected['harness/releases.py']:
        raise ValueError('image bootstrap differs from the selected release')
    if RUNNER_SOURCE_SHA256 != expected['modal_runner.py']:
        raise ValueError('deployed runner differs from the selected release')
    if any(expected[name] != digest for name, digest in IMAGE_INPUT_SHA256.items()):
        raise ValueError('image dependency inputs differ from the selected release')
    # The exact image ID must be available; never invent one for provenance.
    image_id = image.object_id
    env = {**os.environ, 'PYTHONPATH': str(release_dir), 'PYTHONDONTWRITEBYTECODE': '1',
           'PYTHONUTF8': '1', 'WSA_EXECUTION_KIND': 'modal',
           'WSA_RELEASE_ID': release_id, 'WSA_IMAGE_ID': image_id}
    return run_dir, release_dir, env


def _command(args: list[str], release_dir: Path, env: dict) -> None:
    result = subprocess.run([sys.executable, *args], cwd=release_dir, env=env,
                            capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode:
        raise RuntimeError(f'command refused or failed (exit {result.returncode})')


def _precheck_gates(run_dir: Path, release_dir: Path, env: dict, names: list[str]) -> None:
    if not names:
        return
    # Precheck the whole list in the selected release before any host/run write.
    _command(['-c', 'import sys; from pathlib import Path; '
              'from harness.artifact_guard import require_fresh_gates; '
              'require_fresh_gates(Path(sys.argv[1]), sys.argv[2:])',
              str(run_dir), *names], release_dir, env)


def _host_command(run_dir: Path) -> list[str]:
    gpu_probe = ['nvidia-smi', '--query-gpu=name,uuid,driver_version,memory.total,compute_cap',
                 '--format=csv,noheader']
    runtime_probe = [sys.executable, '-c', 'import json,torch; '
                     'print(json.dumps({"torch":torch.__version__,"cuda":torch.version.cuda,'
                     '"cudnn":torch.backends.cudnn.version()},sort_keys=True))']
    return ['scripts/record_host.py', '--run', str(run_dir), '--require-probes',
            '--probe', shlex.join(gpu_probe), '--probe', shlex.join(runtime_probe)]


@app.function(image=image, volumes=VOLUMES, gpu='a100-40gb', timeout=120)
def check_env(run: str, release_id: str):
    """Read the selected runtime's environment; this entrypoint allocates a GPU."""
    _, release_dir, env = _prepare_release(run, release_id)
    _command(['-c', 'import json, platform, torch; from importlib.metadata import version; '
              'print(json.dumps({"python":platform.python_version(),"torch":torch.__version__, '
              '"transformers":version("transformers"),"cuda":torch.version.cuda, '
              '"cudnn":torch.backends.cudnn.version(), '
              '"devices":[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]},indent=2))'],
             release_dir, env)


@app.function(image=image, volumes=VOLUMES, gpu='a100-40gb', timeout=300)
def record_host(run: str, release_id: str):
    """Record an immutable canonical session host in an explicitly selected new-contract run."""
    run_dir, release_dir, env = _prepare_release(run, release_id)
    try:
        _command(_host_command(run_dir), release_dir, env)
    finally:
        workspace_vol.commit()


@app.function(image=image, volumes=VOLUMES, gpu='a100-40gb', timeout=600)
def smoke_test(run: str, release_id: str):
    """Check gate inputs; this legacy GPU-decorated entrypoint is not a CPU smoke."""
    run_dir, release_dir, env = _prepare_release(run, release_id)
    _command(['-m', 'harness.gates', '--run', str(run_dir), '--smoke'], release_dir, env)


@app.function(image=image, volumes=VOLUMES, gpu='a100-40gb', timeout=7200)
def run_gate(run: str, release_id: str, gate: str):
    """Run one bound gate after an explicit session host has been recorded."""
    run_dir, release_dir, env = _prepare_release(run, release_id)
    _precheck_gates(run_dir, release_dir, env, [gate])
    try:
        _command(['-m', 'harness.gates', '--run', str(run_dir), '--gate', gate,
                  '--release', str(release_dir)], release_dir, env)
    finally:
        workspace_vol.commit()


@app.function(image=image, volumes=VOLUMES, gpu='a100-40gb', timeout=14400)
def baseline_session(run: str, release_id: str, gates: str = ''):
    """Precheck all gates, record one session host, then execute static bound gates."""
    run_dir, release_dir, env = _prepare_release(run, release_id)
    names = [name.strip() for name in gates.split(',')] if gates else []
    _precheck_gates(run_dir, release_dir, env, names)
    try:
        _command(_host_command(run_dir), release_dir, env)
        workspace_vol.commit()
        for name in names:
            _command(['-m', 'harness.gates', '--run', str(run_dir), '--gate', name,
                      '--release', str(release_dir)], release_dir, env)
            workspace_vol.commit()
    finally:
        workspace_vol.commit()
