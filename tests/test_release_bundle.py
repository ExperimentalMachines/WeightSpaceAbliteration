"""Actual temporary Git/blob and filesystem exercises; no remote or model operations."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from harness import releases


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, input=b"",
    ).stdout


def put(root, relative, data):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    git(root, "init")
    git(root, "config", "core.autocrlf", "false")
    git(root, "config", "user.name", "Release Fixture")
    git(root, "config", "user.email", "release-fixture@example.invalid")
    for relative in releases.RUNTIME_FILES:
        data = (f"VALUE = {relative!r}\n").encode() if relative.endswith(".py") else b"# fixture config\n"
        put(root, relative, data)
    for relative in (
        "runs/private/ledger.jsonl", ".omp/upstream-notes/private.txt", ".env",
        "credentials.json", "harness/gates_optimized.py", "harness/fast_inference.py",
        "harness/methods/secret.py", "harness/verification/private.py", "datasets/private.json",
    ):
        put(root, relative, b"PRIVATE MUST NEVER BE COPIED\n")
    git(root, "add", ".")
    git(root, "-c", "core.hooksPath=", "commit", "-m", "Temporary release fixture")
    return root


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def read_manifest(release):
    return json.loads((release / releases.MANIFEST_NAME).read_bytes())


def symlink(link, target, *, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")


def test_deterministic_identity_exact_git_bytes_and_verified_reuse(repo, tmp_path):
    first = releases.build_release(repo, tmp_path / "one")
    second = releases.build_release(repo, tmp_path / "two", revision="HEAD~0")
    manifest = releases.verify_release(first)
    assert first.name == second.name == manifest["release_id"]
    assert (first / releases.MANIFEST_NAME).read_bytes() == (second / releases.MANIFEST_NAME).read_bytes()
    assert releases.build_release(repo, tmp_path / "one") == first
    body = {key: value for key, value in manifest.items() if key != "release_id"}
    assert first.name == hashlib.sha256(canonical(body)).hexdigest()
    assert releases.MANIFEST_NAME not in manifest["files"]
    assert manifest["source"] == {
        "kind": "git-revision", "development": False,
        "revision": git(repo, "rev-parse", "HEAD").decode().strip(),
    }
    for relative, digest in manifest["files"].items():
        blob = git(repo, "show", f"HEAD:{relative}")
        assert (first / relative).read_bytes() == blob
        assert digest == hashlib.sha256(blob).hexdigest()
    assert releases.verify_source(first, repo) == manifest


@pytest.mark.parametrize("working_tree", [False, True])
def test_runtime_allowlist_excludes_private_tracked_and_untracked(repo, tmp_path, working_tree):
    put(repo, ".omp/raw-untracked.txt", b"untracked private bytes")
    put(repo, "harness/extra-untracked.py", b"untracked private bytes")
    release = releases.build_release(repo, tmp_path / "releases", working_tree=working_tree)
    manifest = releases.verify_release(release)
    assert set(manifest["files"]) == set(releases.RUNTIME_FILES)
    assert not (release / "runs").exists()
    assert not (release / ".omp").exists()
    assert all(b"PRIVATE MUST NEVER BE COPIED" not in (release / relative).read_bytes() for relative in manifest["files"])


def test_git_snapshot_ignores_dirty_index_and_untracked_work(repo, tmp_path):
    original = git(repo, "show", "HEAD:harness/gates.py")
    put(repo, "harness/gates.py", b"staged change\n")
    git(repo, "add", "harness/gates.py")
    put(repo, "harness/gates.py", b"unstaged different change\n")
    put(repo, "untracked.txt", b"unrelated private work")
    release = releases.build_release(repo, tmp_path / "releases")
    assert (release / "harness/gates.py").read_bytes() == original
    with pytest.raises(releases.ReleaseError, match="source file hash mismatch"):
        releases.verify_source(release, repo)
    assert (repo / "harness/gates.py").read_bytes() == b"unstaged different change\n"


def test_explicit_development_snapshot_captures_exact_bytes_and_distinct_identity(repo, tmp_path):
    selected = releases.build_release(repo, tmp_path / "releases")
    development = releases.build_release(repo, tmp_path / "releases", working_tree=True)
    assert selected != development  # Same bytes do not erase development provenance.
    assert releases.verify_release(development)["source"]["development"] is True
    changed = b"# development only\r\nVALUE = 123\r\n"
    put(repo, "harness/gates.py", changed)
    modified = releases.build_release(repo, tmp_path / "releases", working_tree=True)
    assert modified != development
    assert (modified / "harness/gates.py").read_bytes() == changed
    assert releases.verify_source(modified, repo)["source"]["kind"] == "development-working-tree"
    with pytest.raises(releases.ReleaseError, match="source file hash mismatch"):
        releases.verify_source(development, repo)


def test_source_drift_and_unrelated_changes_are_distinguished(repo, tmp_path):
    release = releases.build_release(repo, tmp_path / "releases")
    put(repo, "runs/private/ledger.jsonl", b"unrelated preserved change\n")
    put(repo, ".omp/new-note.txt", b"unrelated note\n")
    releases.verify_source(release, repo)
    put(repo, "harness/judge_fix.py", b"changed helper\n")
    with pytest.raises(releases.ReleaseError, match="source file hash mismatch: harness/judge_fix.py"):
        releases.verify_source(release, repo)


@pytest.mark.parametrize("relative", releases.OPTIONAL_PACKAGE_FILES)
def test_optional_package_initializers_are_bound_and_absence_is_checked(repo, tmp_path, relative):
    without = releases.build_release(repo, tmp_path / "releases")
    put(repo, relative, b"# import-affecting initializer\n")
    with pytest.raises(releases.ReleaseError, match="unbound package initializer"):
        releases.verify_source(without, repo)
    development = releases.build_release(repo, tmp_path / "releases", working_tree=True)
    assert relative in releases.verify_source(development, repo)["files"]
    git(repo, "add", relative)
    git(repo, "-c", "core.hooksPath=", "commit", "-m", "Bind package initializer")
    selected = releases.build_release(repo, tmp_path / "releases")
    assert relative in releases.verify_source(selected, repo)["files"]
    put(repo, relative, b"# changed import behavior\n")
    with pytest.raises(releases.ReleaseError, match="source file hash mismatch"):
        releases.verify_source(selected, repo)


def test_changed_release_never_overwrites_original_or_repairs_damage(repo, tmp_path):
    release = releases.build_release(repo, tmp_path / "releases")
    original_manifest = (release / releases.MANIFEST_NAME).read_bytes()
    changed = b"occupied changed bytes\n"
    put(release, "harness/gates.py", changed)
    with pytest.raises(releases.ReleaseError, match="release file hash mismatch"):
        releases.build_release(repo, tmp_path / "releases")
    assert (release / "harness/gates.py").read_bytes() == changed
    assert (release / releases.MANIFEST_NAME).read_bytes() == original_manifest


def test_interrupted_publication_remains_occupied(repo, tmp_path):
    complete = releases.build_release(repo, tmp_path / "complete")
    output = tmp_path / "occupied"
    partial = output / complete.name
    marker = put(partial, "harness/gates.py", b"partial original\n")
    with pytest.raises(releases.ReleaseError, match="missing or unsafe"):
        releases.build_release(repo, output)
    assert marker.read_bytes() == b"partial original\n"
    assert not (partial / releases.MANIFEST_NAME).exists()


@pytest.mark.parametrize("mode", ["missing", "directory"])
def test_required_working_file_must_be_regular_and_present(repo, tmp_path, mode):
    path = repo / "harness/gates.py"
    path.unlink()
    if mode == "directory":
        path.mkdir()
    with pytest.raises(releases.ReleaseError, match="missing or unsafe"):
        releases.build_release(repo, tmp_path / "releases", working_tree=True)
    assert not (tmp_path / "releases").exists()


def test_selected_revision_missing_required_module_is_refused(repo, tmp_path):
    git(repo, "rm", "harness/gates.py")
    git(repo, "-c", "core.hooksPath=", "commit", "-m", "Remove required runtime")
    with pytest.raises(releases.ReleaseError, match="revision lacks required runtime files"):
        releases.build_release(repo, tmp_path / "releases")
    assert not (tmp_path / "releases").exists()


def test_git_symlink_blob_is_refused_without_traversal(repo, tmp_path):
    oid = git(repo, "hash-object", "-w", "--stdin")  # Empty link target is still a symlink blob.
    git(repo, "update-index", "--cacheinfo", "120000", oid.decode().strip(), "harness/gates.py")
    git(repo, "-c", "core.hooksPath=", "commit", "-m", "Unsafe symlink fixture")
    with pytest.raises(releases.ReleaseError, match="unsafe Git runtime file"):
        releases.build_release(repo, tmp_path / "releases")


@pytest.mark.parametrize("location", ["source-file", "source-parent", "output", "release-file", "release-root"])
def test_symlinks_are_refused(repo, tmp_path, location):
    output = tmp_path / "releases"
    if location == "source-file":
        path = repo / "harness/gates.py"
        path.unlink()
        symlink(path, repo / "harness/judge_fix.py")
        with pytest.raises(releases.ReleaseError):
            releases.build_release(repo, output, working_tree=True)
    elif location == "source-parent":
        target = tmp_path / "other-harness"
        (repo / "harness").rename(target)
        symlink(repo / "harness", target, directory=True)
        with pytest.raises(releases.ReleaseError):
            releases.build_release(repo, output, working_tree=True)
    elif location == "output":
        target = tmp_path / "other-output"
        target.mkdir()
        symlink(output, target, directory=True)
        with pytest.raises(releases.ReleaseError):
            releases.build_release(repo, output)
        assert not tuple(target.iterdir())
    else:
        release = releases.build_release(repo, output)
        if location == "release-file":
            path = release / "harness/gates.py"
            path.unlink()
            symlink(path, repo / "harness/gates.py")
            with pytest.raises(releases.ReleaseError):
                releases.verify_release(release)
        else:
            linked = tmp_path / release.name
            symlink(linked, release, directory=True)
            with pytest.raises(releases.ReleaseError):
                releases.verify_release(linked)


@pytest.mark.parametrize("relative", ["../escape.py", "/absolute.py", "harness\\escape.py", "C:/escape.py", "harness/../escape.py", "runs/private.py"])
def test_unsafe_or_non_allowlisted_manifest_paths_are_refused(repo, tmp_path, relative):
    release = releases.build_release(repo, tmp_path / "releases")
    manifest = read_manifest(release)
    manifest["files"][relative] = hashlib.sha256(b"unsafe").hexdigest()
    body = {key: value for key, value in manifest.items() if key != "release_id"}
    manifest["release_id"] = hashlib.sha256(canonical(body)).hexdigest()
    (release / releases.MANIFEST_NAME).write_bytes(canonical(manifest))
    with pytest.raises(releases.ReleaseError, match="unsafe release file path|outside runtime allowlist"):
        releases.verify_release(release)


@pytest.mark.parametrize("mutation", ["manifest", "missing", "extra-file", "extra-directory", "wrong-name"])
def test_manifest_identity_inventory_and_directory_identity_are_verified(repo, tmp_path, mutation):
    release = releases.build_release(repo, tmp_path / "releases")
    if mutation == "manifest":
        manifest = read_manifest(release)
        manifest["source"]["revision"] = hashlib.sha1(b"other revision").hexdigest()
        (release / releases.MANIFEST_NAME).write_bytes(canonical(manifest))
    elif mutation == "missing":
        (release / "harness/gates.py").unlink()
    elif mutation == "extra-file":
        put(release, "credentials.json", b"unexpected private bytes")
    elif mutation == "extra-directory":
        (release / "runs").mkdir()
    else:
        renamed = release.with_name("not-the-release-id")
        release.rename(renamed)
        release = renamed
    with pytest.raises(releases.ReleaseError):
        releases.verify_release(release)


def test_actual_cli_build_verify_and_source_refusal(repo, tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/build_release.py"
    command = [sys.executable, str(script)]
    output = tmp_path / "releases"
    built = subprocess.run(
        [*command, "build", "--repo", str(repo), "--output", str(output), "--working-tree"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    release = Path(built.stdout.strip())
    checked = subprocess.run(
        [*command, "verify", str(release), "--source-root", str(repo)],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    report = json.loads(checked.stdout)
    assert report["verified"] is True
    assert report["source"]["development"] is True
    put(repo, "harness/gates.py", b"changed source\n")
    refused = subprocess.run(
        [*command, "verify", str(release), "--source-root", str(repo)],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert refused.returncode == 1
    assert "source file hash mismatch" in refused.stderr


@pytest.mark.parametrize("protected", ["runs", ".gdkit", ".git"])
def test_release_output_cannot_create_files_in_protected_source_trees(repo, protected):
    destination = repo / protected / "releases"
    with pytest.raises(releases.ReleaseError, match="protected"):
        releases.build_release(repo, destination)
    assert not destination.exists()
