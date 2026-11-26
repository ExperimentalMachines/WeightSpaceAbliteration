"""Non-destructive transfer tests use real temporary bytes and a mutating fake volume."""

from __future__ import annotations

import io
import json
import os
import stat
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Thread
from types import SimpleNamespace

import pytest

from harness import artifact_sync
from harness.artifact_guard import LOCK_NAME, run_write_lock
from harness.artifact_sync import ArtifactTransferError, pull_run_artifacts, upload_run_artifacts

ARTIFACT = "runs/r1/receipts/gate.json"
LEDGER = "runs/r1/ledger.jsonl"
PATTERNS = ["runs/*/ledger.jsonl", "runs/*/receipts/*.json", "runs/*/results/**", "runs/*/logs/*.log"]


class FakeVolume:
    """Storage, not mock echoes: batch streams are consumed at commit and mutate files."""

    def __init__(self, files=None, directories=(), entries=()):
        self.files = dict(files or {})
        self.directories = set(directories)
        self.extra_entries = list(entries)
        self.batch_calls = []
        self.on_batch = None
        self.on_read = None
        self.list_error = None
        self.read_errors = {}

    def listdir(self, path, recursive=False):
        assert path == "runs/" and recursive is True
        if self.list_error:
            raise self.list_error
        directories = set(self.directories)
        for name in self.files:
            parts = name.strip("/").split("/")
            directories.update("/".join(parts[:index]) for index in range(1, len(parts)))
        result = [SimpleNamespace(path=name, type=2) for name in sorted(directories)]
        result.extend(SimpleNamespace(path=name, type=1) for name in self.files)
        return result + self.extra_entries

    def read_file(self, path):
        if self.on_read:
            self.on_read(path)
        key = path if path in self.files else path.lstrip("/")
        data = self.files[key]
        midpoint = len(data) // 2
        yield data[:midpoint]
        if path in self.read_errors:
            raise self.read_errors[path]
        yield data[midpoint:]

    @contextmanager
    def batch_upload(self, *, force):
        self.batch_calls.append(force)
        pending = []

        def put_file(stream, path):
            assert isinstance(stream, io.BytesIO)
            pending.append((path.lstrip("/"), stream))

        yield SimpleNamespace(put_file=put_file)
        if self.on_batch:
            self.on_batch()
        snapshots = [(path, stream.getvalue()) for path, stream in pending]
        for path, _ in snapshots:
            if not force and (path in self.files or path in self.directories):
                raise FileExistsError(path)
            for parent in Path(path).parents:
                if parent.as_posix() in self.files:
                    raise NotADirectoryError(parent)
        self.files.update(snapshots)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    return root


def put(repo, relative, data):
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def ledger_bytes(tmp_path, *, run_id="r1", events=2):
    from gdkit.ledger import Ledger

    directory = tmp_path / f"ledger-source-{run_id}-{events}"
    directory.mkdir()
    path = directory / "ledger.jsonl"
    ledger = Ledger(path, run_id=run_id, mode="explore")
    versions = []
    for index in range(events):
        ledger.record_event(f"event_{index}")
        versions.append(path.read_bytes())
    return versions


def quarantined(repo, error):
    summary = error.value.summary
    assert summary.quarantine and summary.quarantine.startswith("../")
    directory = (repo / summary.quarantine).resolve()
    assert directory.parent == repo.parent
    assert not directory.is_relative_to(repo)
    if os.name != "nt":
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    records = json.loads((directory / "index.json").read_bytes())
    for record in records:
        for key in ("incoming", "existing"):
            if key in record:
                record[key] = (directory / record[key]).read_bytes()
    return records


def test_pull_new_then_identical_does_not_rewrite(repo):
    volume = FakeVolume({ARTIFACT: b"receipt\r\n\x00"})
    first = pull_run_artifacts(volume, repo, PATTERNS)
    target = repo / ARTIFACT
    assert first.created == [ARTIFACT]
    assert target.read_bytes() == b"receipt\r\n\x00"
    before = target.stat()
    second = pull_run_artifacts(volume, repo, PATTERNS)
    assert second.identical == [ARTIFACT]
    assert second.created == []
    assert target.stat().st_mtime_ns == before.st_mtime_ns
    assert target.stat().st_ino == before.st_ino
    assert not (repo / "runs/r1" / LOCK_NAME).exists()


def test_pull_preserves_every_conflict_and_preflights_before_new_writes(repo):
    second = "runs/r1/logs/gate.log"
    fresh = "runs/r1/results/new.json"
    put(repo, ARTIFACT, b"local receipt")
    put(repo, second, b"local log")
    volume = FakeVolume({fresh: b"new", ARTIFACT: b"remote receipt", second: b"remote log"})
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(volume, repo, PATTERNS)
    records = quarantined(repo, error)
    assert {item["path"]: item["incoming"] for item in records} == {
        ARTIFACT: b"remote receipt", second: b"remote log"
    }
    assert {item["path"]: item["existing"] for item in records} == {
        ARTIFACT: b"local receipt", second: b"local log"
    }
    assert (repo / ARTIFACT).read_bytes() == b"local receipt"
    assert (repo / second).read_bytes() == b"local log"
    assert not (repo / fresh).exists()
    assert not error.value.summary.created


def test_pull_verified_ledger_appends_suffix_without_replacing_prefix(repo, tmp_path):
    old, new = ledger_bytes(tmp_path)
    target = put(repo, LEDGER, old)
    before = target.stat()
    result = pull_run_artifacts(FakeVolume({LEDGER: new}), repo, PATTERNS)
    assert result.appended == [LEDGER]
    assert target.read_bytes() == new
    assert target.stat().st_ino == before.st_ino
    assert target.read_bytes()[:len(old)] == old


def test_pull_new_verified_ledger(repo, tmp_path):
    incoming = ledger_bytes(tmp_path, events=1)[0]
    result = pull_run_artifacts(FakeVolume({LEDGER: incoming}), repo, PATTERNS)
    assert result.created == [LEDGER]
    assert (repo / LEDGER).read_bytes() == incoming


@pytest.mark.parametrize("variant", ["rewrite", "truncate", "malformed", "partial", "partial-prefix", "empty", "wrong-run"])
def test_pull_rejects_non_append_ledgers_preserving_both(repo, tmp_path, variant):
    first, full = ledger_bytes(tmp_path)
    old = first
    incoming = full
    if variant == "rewrite":
        incoming = full.replace(b"event_1", b"changed")
    elif variant == "truncate":
        old, incoming = full, first
    elif variant == "malformed":
        incoming = first + b"not json\n"
    elif variant == "partial":
        incoming = full[:-5]
    elif variant == "partial-prefix":
        old = first[:-1]
    elif variant == "empty":
        incoming = b""
    elif variant == "wrong-run":
        incoming = ledger_bytes(tmp_path, run_id="r2", events=1)[0]
    put(repo, LEDGER, old)
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(FakeVolume({LEDGER: incoming}), repo, PATTERNS)
    assert (repo / LEDGER).read_bytes() == old
    records = quarantined(repo, error)
    assert records[0]["incoming"] == incoming
    assert records[0]["existing"] == old


def test_pull_rejects_valid_rewritten_chain(repo, tmp_path):
    old = ledger_bytes(tmp_path, events=1)[0]
    # A separately generated, internally valid chain is not an extension of old bytes.
    from gdkit.ledger import Ledger

    path = tmp_path / "other-ledger.jsonl"
    Ledger(path, "r1", "explore").record_event("replacement_genesis")
    incoming = path.read_bytes()
    put(repo, LEDGER, old)
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(FakeVolume({LEDGER: incoming}), repo, PATTERNS)
    assert (repo / LEDGER).read_bytes() == old
    assert quarantined(repo, error)[0]["incoming"] == incoming


@pytest.mark.parametrize("incoming", [b"", b"\n", b"{}\n", b"broken\n", b'{"seq":0}'])
def test_invalid_new_ledger_is_quarantined_not_published(repo, incoming):
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(FakeVolume({LEDGER: incoming}), repo, PATTERNS)
    assert not (repo / LEDGER).exists()
    assert quarantined(repo, error)[0]["incoming"] == incoming


def test_ledger_identity_consistency_uses_every_verified_entry(repo, tmp_path):
    from gdkit.ledger import Ledger

    path = tmp_path / "mixed-ledger.jsonl"
    Ledger(path, "r1", "explore").record_event("first")
    old = path.read_bytes()
    Ledger(path, "r2", "explore").record_event("second")
    incoming = path.read_bytes()
    put(repo, LEDGER, old)
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(FakeVolume({LEDGER: incoming}), repo, PATTERNS)
    assert (repo / LEDGER).read_bytes() == old
    assert quarantined(repo, error)[0]["incoming"] == incoming


def test_identical_invalid_ledger_is_not_reported_as_success(repo):
    put(repo, LEDGER, b"{}\n")
    with pytest.raises(ArtifactTransferError):
        pull_run_artifacts(FakeVolume({LEDGER: b"{}\n"}), repo, PATTERNS)
    assert (repo / LEDGER).read_bytes() == b"{}\n"


def test_modal_absolute_path_is_normalized(repo):
    result = pull_run_artifacts(FakeVolume({"/" + ARTIFACT: b"remote"}), repo, PATTERNS)
    assert result.created == [ARTIFACT]
    assert (repo / ARTIFACT).read_bytes() == b"remote"


@pytest.mark.parametrize("path", [
    "runs/r1/../receipts/gate.json", "runs/r1/./receipts/gate.json", "runs//r1/receipts/gate.json",
    "//runs/r1/receipts/gate.json", "runs\\r1\\receipts\\gate.json", "C:/runs/r1/receipts/gate.json",
    "runs/r1/receipts/C:gate.json", "runs/r1/receipts/NUL.json", "runs/r1/receipts/trailing. ",
    "/outside/receipts/gate.json",
])
def test_unsafe_remote_paths_never_escape_and_are_quarantined(repo, path):
    volume = FakeVolume({path: b"untrusted bytes"})
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(volume, repo, PATTERNS)
    records = quarantined(repo, error)
    assert any(item.get("incoming") == b"untrusted bytes" for item in records)
    assert not list(repo.rglob("*.json"))


def symlink_or_skip(path, target, *, directory=False):
    try:
        path.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")


@pytest.mark.parametrize("collision", ["directory", "broken-link", "file-link", "parent-link", "parent-file"])
def test_pull_local_path_and_type_collisions_preserve_incoming(repo, tmp_path, collision):
    target = repo / ARTIFACT
    target.parent.mkdir(parents=True)
    if collision == "directory":
        target.mkdir()
    elif collision == "broken-link":
        symlink_or_skip(target, tmp_path / "missing")
    elif collision == "file-link":
        external = tmp_path / "external.json"
        external.write_bytes(b"external")
        symlink_or_skip(target, external)
    elif collision == "parent-link":
        target.parent.rmdir()
        external = tmp_path / "external"
        external.mkdir()
        symlink_or_skip(target.parent, external, directory=True)
    else:
        target.parent.rmdir()
        target.parent.write_bytes(b"blocking parent")
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(FakeVolume({ARTIFACT: b"incoming"}), repo, PATTERNS)
    assert quarantined(repo, error)[0]["incoming"] == b"incoming"
    if collision == "file-link":
        assert external.read_bytes() == b"external"
    elif collision == "parent-link":
        assert not list(external.iterdir())


def test_selected_remote_directory_is_file_type_conflict(repo):
    volume = FakeVolume(directories=[ARTIFACT])
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(volume, repo, PATTERNS)
    assert any("remote directory" in item for item in error.value.summary.conflicts)
    assert not (repo / ARTIFACT).exists()


def test_subtree_directories_are_ignored_unless_colliding(repo):
    path = "runs/r1/results/nested/result.json"
    volume = FakeVolume({path: b"result"}, directories=["runs/r1/unselected"])
    result = pull_run_artifacts(volume, repo, PATTERNS)
    assert result.created == [path]
    assert (repo / path).read_bytes() == b"result"
    assert not (repo / "runs/r1/unselected").exists()


def test_selected_remote_subtree_directory_collides_with_local_file(repo):
    put(repo, "runs/r1/results/nested", b"original file")
    volume = FakeVolume(directories=["runs/r1/results/nested"])
    with pytest.raises(ArtifactTransferError):
        pull_run_artifacts(volume, repo, PATTERNS)
    assert (repo / "runs/r1/results/nested").read_bytes() == b"original file"


@pytest.mark.parametrize("kind", [3, 4, 5, 0, 99])
def test_remote_nonregular_selected_entry_refused(repo, kind):
    volume = FakeVolume(entries=[SimpleNamespace(path=ARTIFACT, type=kind)])
    with pytest.raises(ArtifactTransferError):
        pull_run_artifacts(volume, repo, PATTERNS)
    assert not (repo / ARTIFACT).exists()


def test_duplicate_normalized_remote_paths_are_not_published(repo):
    volume = FakeVolume({ARTIFACT: b"first", "/" + ARTIFACT: b"second"})
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(volume, repo, PATTERNS)
    assert any("duplicate" in item for item in error.value.summary.conflicts)
    assert not (repo / ARTIFACT).exists()
    assert {item["incoming"] for item in quarantined(repo, error)} == {b"first", b"second"}


def test_atomic_publication_cannot_clobber_concurrent_unlocked_writer(repo, monkeypatch):
    ready = Event()
    published = Event()
    original = os.link
    errors = []

    def concurrent_writer():
        if ready.wait(5):
            (repo / ARTIFACT).write_bytes(b"concurrent winner")
            published.set()

    def racing_link(source, target):
        ready.set()
        assert published.wait(5)
        return original(source, target)

    thread = Thread(target=concurrent_writer)
    thread.start()
    monkeypatch.setattr(artifact_sync.os, "link", racing_link)
    try:
        with pytest.raises(ArtifactTransferError) as error:
            pull_run_artifacts(FakeVolume({ARTIFACT: b"incoming loser"}), repo, PATTERNS)
        errors.extend(quarantined(repo, error))
    finally:
        ready.set()
        thread.join(5)
    assert not thread.is_alive()
    assert (repo / ARTIFACT).read_bytes() == b"concurrent winner"
    assert errors[0]["incoming"] == b"incoming loser"
    assert not list((repo / ARTIFACT).parent.glob(".artifact-incoming-*"))


def test_concurrent_guarded_transfer_is_refused_without_clobber(repo):
    reading = Event()
    proceed = Event()
    results = []
    failures = []
    volume = FakeVolume({ARTIFACT: b"winner"})

    def pause(path):
        reading.set()
        assert proceed.wait(5)

    volume.on_read = pause

    def first():
        try:
            results.append(pull_run_artifacts(volume, repo, PATTERNS))
        except Exception as exc:
            failures.append(exc)

    thread = Thread(target=first)
    thread.start()
    try:
        assert reading.wait(5)
        with pytest.raises(ArtifactTransferError) as error:
            pull_run_artifacts(FakeVolume({ARTIFACT: b"loser"}), repo, PATTERNS)
        assert "transfer lock" in str(error.value)
    finally:
        proceed.set()
        thread.join(5)
    assert not thread.is_alive() and not failures
    assert results[0].created == [ARTIFACT]
    assert (repo / ARTIFACT).read_bytes() == b"winner"


def test_pull_refuses_occupied_producer_lock_and_preserves_incoming(repo):
    run = repo / "runs/r1"
    run.mkdir(parents=True)
    with run_write_lock(run):
        with pytest.raises(ArtifactTransferError) as error:
            pull_run_artifacts(FakeVolume({ARTIFACT: b"incoming"}), repo, PATTERNS)
        assert quarantined(repo, error)[0]["incoming"] == b"incoming"
        assert (run / LOCK_NAME).exists()
    assert not (repo / ARTIFACT).exists()


def test_ledger_rechecked_after_preflight_without_prefix_replacement(repo, tmp_path, monkeypatch):
    old, incoming = ledger_bytes(tmp_path)
    target = put(repo, LEDGER, old)
    original = artifact_sync._append_ledger
    changed = old + b"external partial"

    def race(root, item):
        target.write_bytes(changed)
        return original(root, item)

    monkeypatch.setattr(artifact_sync, "_append_ledger", race)
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(FakeVolume({LEDGER: incoming}), repo, PATTERNS)
    assert target.read_bytes() == changed
    assert "0/" in str(error.value)
    assert quarantined(repo, error)[0]["incoming"] == incoming


def test_partial_ledger_append_reported_honestly_without_rollback(repo, tmp_path, monkeypatch):
    old, incoming = ledger_bytes(tmp_path)
    target = put(repo, LEDGER, old)
    suffix = incoming[len(old):]
    real_write = os.write
    first = True

    def fail_after_partial(fd, data):
        nonlocal first
        if os.path.samestat(os.fstat(fd), target.stat()):
            if first:
                first = False
                return real_write(fd, data[:7])
            raise OSError("simulated disk failure")
        return real_write(fd, data)

    monkeypatch.setattr(artifact_sync.os, "write", fail_after_partial)
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(FakeVolume({LEDGER: incoming}), repo, PATTERNS)
    assert target.read_bytes() == old + suffix[:7]
    assert "7/" in str(error.value) and "partial suffix may remain" in str(error.value)
    assert not error.value.summary.appended
    assert quarantined(repo, error)[0]["incoming"] == incoming


def test_remote_listing_and_partial_read_failures_raise(repo):
    broken = FakeVolume()
    broken.list_error = RuntimeError("listing unavailable")
    with pytest.raises(ArtifactTransferError, match="listing unavailable"):
        pull_run_artifacts(broken, repo, PATTERNS)
    broken = FakeVolume({ARTIFACT: b"abcdefgh"})
    broken.read_errors[ARTIFACT] = OSError("network failure")
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(broken, repo, PATTERNS)
    assert not (repo / ARTIFACT).exists()
    assert quarantined(repo, error)[0]["incoming"] == b"abcd"
    assert error.value.summary.failures


def test_upload_new_and_identical_only_without_force(repo):
    first = put(repo, ARTIFACT, b"local receipt")
    identical = put(repo, "runs/r1/logs/gate.log", b"same")
    volume = FakeVolume({"runs/r1/logs/gate.log": b"same"})
    result = upload_run_artifacts(volume, repo, [first, identical])
    assert result.created == [ARTIFACT]
    assert result.identical == ["runs/r1/logs/gate.log"]
    assert volume.files == {ARTIFACT: b"local receipt", "runs/r1/logs/gate.log": b"same"}
    assert volume.batch_calls == [False]
    result = upload_run_artifacts(volume, repo, [first])
    assert result.identical == [ARTIFACT]
    assert volume.batch_calls == [False]


def test_upload_all_conflicts_staged_before_any_batch(repo):
    log = "runs/r1/logs/gate.log"
    new = "runs/r1/results/new.json"
    paths = [put(repo, path, data) for path, data in [
        (new, b"fresh"), (ARTIFACT, b"local receipt"), (log, b"local log")
    ]]
    volume = FakeVolume({ARTIFACT: b"remote receipt", log: b"remote log"})
    with pytest.raises(ArtifactTransferError) as error:
        upload_run_artifacts(volume, repo, paths)
    assert not volume.batch_calls
    assert new not in volume.files
    assert volume.files == {ARTIFACT: b"remote receipt", log: b"remote log"}
    records = quarantined(repo, error)
    assert {item["path"]: item["incoming"] for item in records} == {
        ARTIFACT: b"local receipt", log: b"local log"
    }
    assert {item["path"]: item["existing"] for item in records} == volume.files


def test_upload_even_valid_remote_ledger_extension_never_forces(repo, tmp_path):
    old, new = ledger_bytes(tmp_path)
    path = put(repo, LEDGER, new)
    volume = FakeVolume({LEDGER: old})
    with pytest.raises(ArtifactTransferError, match="coordinated append") as error:
        upload_run_artifacts(volume, repo, [path])
    assert volume.files[LEDGER] == old
    assert not volume.batch_calls
    records = quarantined(repo, error)
    assert records[0]["incoming"] == new and records[0]["existing"] == old


def test_upload_snapshot_cannot_change_between_preflight_and_batch(repo):
    path = put(repo, ARTIFACT, b"snapshot")
    volume = FakeVolume()
    volume.on_batch = lambda: path.write_bytes(b"changed after snapshot")
    upload_run_artifacts(volume, repo, [path])
    assert path.read_bytes() == b"changed after snapshot"
    assert volume.files[ARTIFACT] == b"snapshot"


def test_upload_remote_concurrent_creation_is_not_overwritten(repo):
    path = put(repo, ARTIFACT, b"incoming")
    volume = FakeVolume()
    volume.on_batch = lambda: volume.files.update({ARTIFACT: b"concurrent winner"})
    with pytest.raises(ArtifactTransferError) as error:
        upload_run_artifacts(volume, repo, [path])
    assert volume.files[ARTIFACT] == b"concurrent winner"
    assert volume.batch_calls == [False]
    assert quarantined(repo, error)[0]["incoming"] == b"incoming"
    assert not error.value.summary.created


@pytest.mark.parametrize("kind", [2, 3, 4])
def test_upload_remote_destination_type_collision(repo, kind):
    path = put(repo, ARTIFACT, b"incoming")
    volume = FakeVolume(entries=[SimpleNamespace(path=ARTIFACT, type=kind)])
    with pytest.raises(ArtifactTransferError) as error:
        upload_run_artifacts(volume, repo, [path])
    assert not volume.batch_calls
    assert quarantined(repo, error)[0]["incoming"] == b"incoming"


def test_upload_remote_parent_file_collision(repo):
    path = put(repo, ARTIFACT, b"incoming")
    volume = FakeVolume({"runs/r1/receipts": b"blocking parent"})
    with pytest.raises(ArtifactTransferError):
        upload_run_artifacts(volume, repo, [path])
    assert volume.files["runs/r1/receipts"] == b"blocking parent"
    assert not volume.batch_calls


@pytest.mark.parametrize("location", ["local", "remote", "local-broken-link", "remote-symlink"])
def test_upload_occupied_run_lock_refused_even_when_not_selected(repo, tmp_path, location):
    path = put(repo, ARTIFACT, b"incoming")
    volume = FakeVolume()
    lock = repo / "runs/r1" / LOCK_NAME
    if location == "local":
        lock.write_bytes(b"occupied")
    elif location == "remote":
        volume.files[f"runs/r1/{LOCK_NAME}"] = b"occupied"
    elif location == "local-broken-link":
        symlink_or_skip(lock, tmp_path / "nonexistent")
    else:
        volume.extra_entries.append(SimpleNamespace(path=f"runs/r1/{LOCK_NAME}", type=3))
    with pytest.raises(ArtifactTransferError):
        upload_run_artifacts(volume, repo, [path])
    assert not volume.batch_calls
    assert ARTIFACT not in volume.files


def test_upload_invalid_new_ledger_is_quarantined(repo):
    path = put(repo, LEDGER, b"malformed\n")
    volume = FakeVolume()
    with pytest.raises(ArtifactTransferError) as error:
        upload_run_artifacts(volume, repo, [path])
    assert not volume.files and not volume.batch_calls
    assert quarantined(repo, error)[0]["incoming"] == b"malformed\n"


def test_upload_duplicate_or_outside_paths_refused(repo, tmp_path):
    path = put(repo, ARTIFACT, b"local")
    volume = FakeVolume()
    with pytest.raises(ArtifactTransferError, match="duplicate"):
        upload_run_artifacts(volume, repo, [path, path])
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    with pytest.raises(ArtifactTransferError):
        upload_run_artifacts(volume, repo, [outside])
    assert not volume.files and not volume.batch_calls


def test_upload_absent_remote_runs_is_empty_but_other_list_errors_fail(repo):
    path = put(repo, ARTIFACT, b"incoming")
    volume = FakeVolume()
    volume.list_error = FileNotFoundError("runs/")
    result = upload_run_artifacts(volume, repo, [path])
    assert result.created == [ARTIFACT] and volume.files[ARTIFACT] == b"incoming"
    volume.list_error = PermissionError("denied")
    with pytest.raises(ArtifactTransferError, match="denied"):
        upload_run_artifacts(volume, repo, [path])
    assert volume.batch_calls == [False]


def test_only_root_run_ledger_is_appendable(repo):
    nested = "runs/r1/results/ledger.jsonl"
    put(repo, nested, b"original result\n")
    incoming = b"original result\nadditional result\n"
    with pytest.raises(ArtifactTransferError) as error:
        pull_run_artifacts(FakeVolume({nested: incoming}), repo, PATTERNS)
    assert (repo / nested).read_bytes() == b"original result\n"
    assert quarantined(repo, error)[0]["incoming"] == incoming


def test_upload_new_verified_ledger_and_identical_skip(repo, tmp_path):
    data = ledger_bytes(tmp_path, events=1)[0]
    path = put(repo, LEDGER, data)
    volume = FakeVolume()
    result = upload_run_artifacts(volume, repo, [path])
    assert result.created == [LEDGER]
    assert volume.files[LEDGER] == data
    result = upload_run_artifacts(volume, repo, [path])
    assert result.identical == [LEDGER]
    assert volume.batch_calls == [False]


def test_recursive_run_pattern_ignores_ordinary_selected_directories(repo):
    volume = FakeVolume({ARTIFACT: b"receipt"})
    result = pull_run_artifacts(volume, repo, ["runs/**"])
    assert result.created == [ARTIFACT]
    assert (repo / ARTIFACT).read_bytes() == b"receipt"
