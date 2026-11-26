"""Code-only publication against a real temporary filesystem volume adapter.

Modal is an optional CLI dependency. These tests never make Modal API calls.
"""
from contextlib import contextmanager
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest

pytest.importorskip('modal')
from modal.volume import FileEntryType

import modal_runner
from harness.releases import RUNTIME_FILES, build_release, verify_release


class DiskVolume:
    def __init__(self, root):
        self.root = root
        self.fail_after = None

    def listdir(self, prefix, recursive=False):
        assert prefix.startswith('releases/')
        path = self.root / prefix
        if not path.exists():
            raise FileNotFoundError(prefix)
        return [SimpleNamespace(path=p.relative_to(self.root).as_posix(),
                                type=FileEntryType.DIRECTORY if p.is_dir() else FileEntryType.FILE)
                for p in sorted(path.rglob('*'))]

    def read_file(self, path):
        yield (self.root / path.lstrip('/')).read_bytes()

    @contextmanager
    def batch_upload(self, force=False):
        assert not force
        volume = self

        class Batch:
            written = 0

            def put_file(self, stream, remote):
                assert remote.startswith('/releases/')
                if volume.fail_after is not None and self.written >= volume.fail_after:
                    raise OSError('interrupted publication')
                path = volume.root / remote.lstrip('/')
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as handle:
                    handle.write(stream.read())
                self.written += 1

        yield Batch()


def git(repo, *args):
    subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def publication(tmp_path):
    if shutil.which('git') is None:
        pytest.skip('Git unavailable')
    repo = tmp_path / 'source'
    repo.mkdir()
    git(repo, 'init', '-q')
    git(repo, 'config', 'core.autocrlf', 'false')
    git(repo, 'config', 'user.email', 'test@example.invalid')
    git(repo, 'config', 'user.name', 'Test')
    for name in RUNTIME_FILES:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(('fixture bytes for ' + name + '\n').encode())
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'fixture runtime')
    release = build_release(repo, tmp_path / 'releases')
    remote = tmp_path / 'remote'
    (remote / 'runs' / 'historical').mkdir(parents=True)
    historical = remote / 'runs' / 'historical' / 'ledger.jsonl'
    historical.write_bytes(b'preserved historical ledger\n')
    return repo, release, DiskVolume(remote), historical


def test_publication_never_touches_run_and_identical_repeat_does_not_rewrite(publication):
    _, release, volume, historical = publication
    original = historical.read_bytes(), historical.stat().st_mtime_ns
    modal_runner.upload_code_release(volume, release, reviewed=True)
    destination = volume.root / 'releases' / release.name
    assert verify_release(destination) == verify_release(release)
    before = {p.relative_to(volume.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
              for p in volume.root.rglob('*') if p.is_file()}
    modal_runner.upload_code_release(volume, release, reviewed=True)
    after = {p.relative_to(volume.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
             for p in volume.root.rglob('*') if p.is_file()}
    assert before == after
    assert (historical.read_bytes(), historical.stat().st_mtime_ns) == original


def test_review_is_required_and_development_bundle_is_not_deployable(publication, tmp_path):
    repo, release, volume, historical = publication
    with pytest.raises(ValueError, match='review'):
        modal_runner.upload_code_release(volume, release, reviewed=False)
    development = build_release(repo, tmp_path / 'development', working_tree=True)
    with pytest.raises(ValueError, match='development'):
        modal_runner.upload_code_release(volume, development, reviewed=True)
    assert not (volume.root / 'releases').exists()
    assert historical.read_bytes() == b'preserved historical ledger\n'


def test_conflicting_partial_release_is_never_replaced(publication):
    _, release, volume, historical = publication
    target = volume.root / 'releases' / release.name / 'harness' / 'gates.py'
    target.parent.mkdir(parents=True)
    target.write_bytes(b'conflicting source\n')
    with pytest.raises(ValueError, match='differ'):
        modal_runner.upload_code_release(volume, release, reviewed=True)
    assert target.read_bytes() == b'conflicting source\n'
    assert not (target.parent.parent / 'release-manifest.json').exists()
    assert historical.read_bytes() == b'preserved historical ledger\n'


def test_interrupted_new_publication_can_resume_without_rewriting(publication):
    _, release, volume, _ = publication
    volume.fail_after = 2
    with pytest.raises(OSError, match='interrupted'):
        modal_runner.upload_code_release(volume, release, reviewed=True)
    destination = volume.root / 'releases' / release.name
    before = {p.relative_to(destination): (p.read_bytes(), p.stat().st_mtime_ns)
              for p in destination.rglob('*') if p.is_file()}
    assert not (destination / 'release-manifest.json').exists()
    volume.fail_after = None
    modal_runner.upload_code_release(volume, release, reviewed=True)
    assert verify_release(destination) == verify_release(release)
    for relative, original in before.items():
        p = destination / relative
        assert (p.read_bytes(), p.stat().st_mtime_ns) == original


@pytest.mark.parametrize('relative', ['private.txt', '.omp/notes.md', 'extra/hidden.py'])
def test_unexpected_remote_bytes_block_publication(publication, relative):
    _, release, volume, _ = publication
    target = volume.root / 'releases' / release.name / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b'not part of the release\n')
    with pytest.raises(ValueError, match='unexpected'):
        modal_runner.upload_code_release(volume, release, reviewed=True)
    assert target.read_bytes() == b'not part of the release\n'
    assert not (volume.root / 'releases' / release.name / 'release-manifest.json').exists()


@pytest.mark.parametrize('run,release_id', [('../runs/r1', 'a'*64), ('runs/r1/../../r2', 'a'*64),
                                          ('runs/r1', '../release'), ('runs/r1', 'a'*63)])
def test_remote_path_validation_rejects_escapes_before_execution(run, release_id):
    with pytest.raises(ValueError):
        modal_runner._prepare_release(run, release_id)
