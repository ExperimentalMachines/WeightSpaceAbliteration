"""Local, manifest-bound gdkit execution and read-only historical verification.

This is a cooperative filesystem contract, not a sandbox or signature scheme. Callable
checks cover explicitly registered Python modules, not arbitrary native code or OS I/O.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import inspect
import json
import os
import platform
import sys
import traceback
import types
from datetime import datetime, timezone
from pathlib import Path

from gdkit.gates import Gate, receipt_hash, run_gate
from gdkit.ledger import verify as verify_ledger
from harness.artifact_guard import require_fresh_paths, require_regular_file, safe_artifact_path
from harness.verification import CONTRACT_VERSION


class ExecutionError(RuntimeError):
    """Execution provenance is incomplete or changed during the check."""


_CONSTANTS: dict[str, dict] = {}
_DEPENDENCIES: dict[str, dict] = {}


_REGISTERED: dict[str, dict] = {}


def _json(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _code_constant(value):
    """Canonicalize unordered constants instead of hashing process-dependent repr."""
    if isinstance(value, types.CodeType):
        return _code(value)
    if isinstance(value, frozenset):
        members = [_code_constant(item) for item in value]
        return {"frozenset": sorted(members, key=lambda item: _json(item))}
    if isinstance(value, tuple):
        return {"tuple": [_code_constant(item) for item in value]}
    return repr(value)


def _code(code: types.CodeType) -> dict:
    """Filename-independent executable identity, including nested code and constants."""
    return {
        "bytecode": code.co_code.hex(), "exceptiontable": code.co_exceptiontable.hex(),
        "names": code.co_names, "varnames": code.co_varnames,
        "freevars": code.co_freevars, "cellvars": code.co_cellvars,
        "args": [code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount],
        "flags": code.co_flags,
        "constants": [_code_constant(c) for c in code.co_consts],
    }


def _callable_state(fn) -> dict:
    if not inspect.isfunction(fn):
        raise ExecutionError("registered callable is no longer a Python function")
    return {"code_sha256": hashlib.sha256(_json(_code(fn.__code__))).hexdigest(),
            "defaults": repr(fn.__defaults__), "kwdefaults": repr(fn.__kwdefaults__)}


def register_module(module_name: str) -> None:
    """Freeze explicit top-level callable references once, at module initialization."""
    module = sys.modules[module_name]
    if module_name in _REGISTERED:
        raise ExecutionError(f"callable module already registered: {module_name}")
    constants = {}
    for name, value in vars(module).items():
        if name.isupper() and not name.startswith("_"):
            try:
                constants[name] = json.loads(_json(value))
            except (TypeError, ValueError):
                continue
    _CONSTANTS[module_name] = constants
    _DEPENDENCIES[module_name] = {
        name: value for name, value in vars(module).items()
        if isinstance(value, types.ModuleType) and value.__name__.startswith("harness.")
    }
    _REGISTERED[module_name] = {
        name: (fn, _callable_state(fn)) for name, fn in vars(module).items()
        if inspect.isfunction(fn) and not hasattr(fn, "__wrapped__")
        and (fn.__module__ == module_name or fn.__module__.startswith("harness."))
    }


def _compiled_functions(path: Path) -> dict:
    code = compile(path.read_bytes(), str(path), "exec", optimize=sys.flags.optimize)
    return {c.co_name: c for c in code.co_consts if isinstance(c, types.CodeType)}


def _callables(source_root: Path, release: dict, gate: Gate) -> dict:
    records = {}
    compiled_sources = {}
    # The gate module registers itself and the statically imported inference helpers.
    for module_name, functions in _REGISTERED.items():
        module = sys.modules[module_name]
        for name, expected_value in _CONSTANTS[module_name].items():
            if json.loads(_json(getattr(module, name, None))) != expected_value:
                raise ExecutionError(f"mutated runtime constant: {module_name}.{name}")
        for name, expected_module in _DEPENDENCIES[module_name].items():
            if getattr(module, name, None) is not expected_module:
                raise ExecutionError(f"mutated helper module: {module_name}.{name}")
        for name, (original, state) in functions.items():
            current = getattr(module, name, None)
            if current is not original or _callable_state(current) != state:
                raise ExecutionError(f"mutated callable: {module_name}.{name}")
            path = Path(inspect.getsourcefile(current) or "").resolve()
            try:
                relative = path.relative_to(source_root.resolve()).as_posix()
            except ValueError as exc:
                raise ExecutionError(f"callable source outside release: {module_name}.{name}") from exc
            if relative not in release["files"]:
                raise ExecutionError(f"callable source absent from release: {relative}")
            if path not in compiled_sources:
                compiled_sources[path] = _compiled_functions(path)
            expected = compiled_sources[path].get(current.__name__)
            if expected is None or _code(current.__code__) != _code(expected):
                raise ExecutionError(f"live callable differs from source: {module_name}.{name}")
            records[f"{module_name}.{name}"] = {"source": relative, "name": current.__name__, **state}
    module = sys.modules.get(gate.check.__module__)
    if gate.check.__module__ not in _REGISTERED:
        raise ExecutionError("gate module must register its bounded callables before execution")
    if module is None or getattr(module, gate.check.__name__, None) is not gate.check:
        raise ExecutionError("gate callable is not its declared module reference")
    path = Path(inspect.getsourcefile(gate.check) or "").resolve()
    try:
        relative = path.relative_to(source_root.resolve()).as_posix()
    except ValueError as exc:
        raise ExecutionError("gate callable source outside release") from exc
    if relative not in release["files"]:
        raise ExecutionError("gate callable source absent from release")
    expected = _compiled_functions(path).get(gate.check.__name__)
    if expected is None or _code(expected) != _code(gate.check.__code__):
        raise ExecutionError("gate callable differs from source")
    records["gate.check"] = {"source": relative, "name": gate.check.__name__, **_callable_state(gate.check)}
    return records


def _ledger(run_dir: Path) -> list[dict]:
    path = require_regular_file(run_dir, "ledger.jsonl")
    verify_ledger(path)
    entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not entries:
        raise ExecutionError("empty ledger")
    return entries


def _hash_inputs(run_dir: Path, inputs: list[str]) -> dict[str, str]:
    return {rel: _sha(require_regular_file(run_dir, rel)) for rel in sorted(set(inputs))}


def _hash_outputs(run_dir: Path, outputs: list[str]) -> dict[str, str]:
    artifacts = {}
    for rel in outputs:
        path = safe_artifact_path(run_dir, rel)
        if path.is_dir() and not path.is_symlink():
            # Validate every directory too, including empty/reparse-point directories.
            safe_artifact_path(run_dir, f"{rel}/.containment-check")
            children = sorted(path.rglob("*"))
            files = []
            for child in children:
                child_rel = child.relative_to(run_dir.absolute()).as_posix()
                if child.is_dir():
                    safe_artifact_path(run_dir, f"{child_rel}/.containment-check")
                else:
                    files.append(child_rel)
            if not files:
                raise ExecutionError(f"required output directory is empty: {rel}")
            artifacts.update(_hash_inputs(run_dir, files))
        else:
            artifacts[rel] = _sha(require_regular_file(run_dir, rel))
    return artifacts


def _runtime() -> dict:
    packages = {}
    for name in ("gdkit", "torch", "transformers", "accelerate", "numpy", "lm-eval", "safetensors"):
        try:
            dist = importlib.metadata.distribution(name)
            direct = dist.read_text("direct_url.json")
            # Keep revision metadata, never local installation/account paths or credentials.
            vcs = json.loads(direct).get("vcs_info") if direct else None
            packages[name] = {"version": dist.version, "vcs_info": vcs}
        except importlib.metadata.PackageNotFoundError:
            packages[name] = {"version": None, "vcs_info": None}
    kind = os.environ.get("WSA_EXECUTION_KIND", "local-process")
    return {"kind": kind, "python": platform.python_version(),
            "implementation": platform.python_implementation(), "platform": sys.platform,
            "machine": platform.machine(), "packages": packages,
            "modal_image_identity": os.environ.get("WSA_IMAGE_ID") if kind == "modal" else None,
            "runner_release_id": os.environ.get("WSA_RELEASE_ID") if kind == "modal" else None,
            "remote_validation": "unvalidated" if kind == "modal" else "not-applicable"}


def _write_new(run_dir: Path, relative: str, value: dict) -> Path:
    path = safe_artifact_path(run_dir, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(_json(value))
    return path


def _source_constants(path: Path) -> dict:
    values = {}
    for statement in ast.parse(path.read_bytes()).body:
        if isinstance(statement, ast.Assign):
            targets, value = statement.targets, statement.value
        elif isinstance(statement, ast.AnnAssign):
            targets, value = [statement.target], statement.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id.isupper() and not target.id.startswith("_"):
                try:
                    values[target.id] = json.loads(_json(ast.literal_eval(value)))
                except (ValueError, TypeError):
                    pass
    return values


def _require_model_references(name: str, cfg: dict) -> None:
    roles = {
        "direction_derivation": ("model",),
        "refusal_eval": ("model", "judge"),
        "judge_agreement": ("judge_alt",),
        "over_refusal_eval": ("model", "judge"),
        "kl_divergence": ("model", "parent"),
        "activation_extraction": ("model",),
        "probe_train": ("model",),
        "capability_suite": ("model",),
    }
    for role in roles.get(name, ()):
        reference = cfg.get(role)
        if not isinstance(reference, dict) or any(
            not isinstance(reference.get(key), str) or not reference[key].strip()
            for key in ("id", "revision")
        ):
            raise ExecutionError(f"{name}: {role}.id and {role}.revision are required; no default/latest identity")
        revision = reference["revision"]
        if len(revision) != 40 or any(char not in "0123456789abcdefABCDEF" for char in revision):
            raise ExecutionError(f"{name}: {role}.revision must be an immutable 40-character commit ID")


def _model_references(cfg: dict) -> dict:
    models = {}
    for key in ("model", "parent", "judge", "judge_alt", "embedding"):
        if key not in cfg:
            continue
        reference = {name: cfg[key][name] for name in
                     ("id", "revision", "dtype", "thinking", "max_new_tokens") if name in cfg[key]}
        identifier = reference.get("id")
        if isinstance(identifier, str) and (identifier.startswith(("/", "\\")) or
                "\\" in identifier or ".." in identifier.split("/") or
                (len(identifier) > 1 and identifier[1] == ":") or "://" in identifier):
            reference["id"] = {"kind": "private-reference", "sha256": hashlib.sha256(identifier.encode()).hexdigest()}
        reference["identity_status"] = "configured-reference-unvalidated"
        models[key] = reference
    return models


def run_bound_gate(run_dir: Path, gate: Gate, *, release_dir: Path, source_root: Path,
                   inputs: list[str], outputs: list[str], run_id: str, ledger_head: str) -> Path:
    """Execute under the caller's run lock; never acquire a second lock.

    The manifest is immutable and precedes execution. gdkit alone writes the receipt
    and captured log. Exceptions keep that log and a distinct failure record, then raise.
    """
    from harness.host import require_current_host
    from harness.releases import verify_source
    if "harness.releases" not in _REGISTERED:
        register_module("harness.releases")

    run_dir = Path(run_dir).absolute()
    source_root, release_dir = Path(source_root), Path(release_dir)
    manifest_rel, failure_rel = f"execution/{gate.name}.json", f"failures/{gate.name}.json"
    require_fresh_paths(run_dir, [manifest_rel, failure_rel, f"receipts/{gate.name}.json",
                                 f"logs/{gate.name}.log", f"logs/{gate.name}.log.partial", *outputs])
    for rel in inputs:
        safe_artifact_path(run_dir, rel)
    if set(inputs) & set(outputs):
        raise ExecutionError("input and output paths overlap")
    release = verify_source(release_dir, source_root)
    host = require_current_host(run_dir)
    if host.get("checked") is not True:
        raise ExecutionError("canonical same-host check did not run")
    entries = _ledger(run_dir)
    if entries[-1]["entry_hash"] != ledger_head or entries[-1]["run_id"] != run_id:
        raise ExecutionError("run ID or ledger head changed before execution")
    input_hashes = _hash_inputs(run_dir, inputs)
    callables = _callables(source_root, release, gate)
    cfg = json.loads((run_dir / "harness.json").read_text(encoding="utf-8")) if "harness.json" in input_hashes else {}
    _require_model_references(gate.name, cfg)
    manifest = {
        "contract_version": CONTRACT_VERSION, "gate": gate.name, "run_id": run_id,
        "gate_code_hash": gate.code_hash,
        "created_at": datetime.now(timezone.utc).isoformat(), "ledger_head": ledger_head,
        "release": release, "release_manifest_sha256": _sha(release_dir / "release-manifest.json"),
        "host": host, "runtime": _runtime(), "callables": callables,
        "constants": json.loads(_json(_CONSTANTS)),
        "constant_sources": {name: Path(sys.modules[name].__file__).resolve().relative_to(source_root.resolve()).as_posix()
                             for name in _CONSTANTS},
        "models": _model_references(cfg),
        "inputs": input_hashes, "expected_outputs": sorted(set(outputs)),
        "limitations": ["bounded registered Python callables; not OS I/O tracing or a sandbox",
                        "model revisions are configured references, not proof of downloaded model bytes",
                        "legacy measurement semantics remain unvalidated; provenance is not scientific validation"],
    }
    manifest_path = _write_new(run_dir, manifest_rel, manifest)
    manifest_digest = _sha(manifest_path)
    attempt_result = None

    def bound_check(directory: Path) -> dict:
        nonlocal attempt_result
        try:
            for relative in outputs:
                safe_artifact_path(directory, relative).parent.mkdir(parents=True, exist_ok=True)
            result = gate.check(directory)
            attempt_result = result
            if not isinstance(result, dict) or not isinstance(result.get("passed"), bool):
                raise ExecutionError("gate returned no boolean passed result")
            verify_source(release_dir, source_root)
            if _callables(source_root, release, gate) != callables:
                raise ExecutionError("callable bindings changed during execution")
            if _hash_inputs(directory, inputs) != input_hashes or _sha(manifest_path) != manifest_digest:
                raise ExecutionError("execution input changed during execution")
            if _ledger(directory)[-1]["entry_hash"] != ledger_head:
                raise ExecutionError("ledger changed during execution")
            current_host = require_current_host(directory)
            if current_host != host:
                raise ExecutionError("bound host changed during execution")
            artifacts = _hash_outputs(directory, outputs)
            return {**result, "artifacts": artifacts, "execution_manifest": manifest_rel,
                    "execution_status": "completed", "scientific_validation": "legacy-unvalidated"}
        except BaseException:
            traceback.print_exc()
            raise

    class BoundGate(Gate):
        @property
        def code_hash(self) -> str:
            # gdkit still identifies the real gate, not this provenance wrapper.
            return gate.code_hash

    try:
        # Keep gdkit's real same-host enforcement enabled, in addition to the canonical check.
        path = run_gate(run_dir, BoundGate(gate.name, gate.cheap, bound_check),
                        inputs=[*sorted(input_hashes), manifest_rel], run_id=run_id,
                        ledger_head=ledger_head, contract_version=CONTRACT_VERSION, capture_log=True)
        return path
    except BaseException as exc:
        log = safe_artifact_path(run_dir, f"logs/{gate.name}.log")
        failure = {"status": "execution-failed", "gate": gate.name, "run_id": run_id,
                   "manifest": manifest_rel, "manifest_sha256": manifest_digest,
                   "exception_type": type(exc).__name__, "exception": str(exc),
                   "gate_result_repr": repr(attempt_result),
                   "traceback": traceback.format_exc(),
                   "log": {"path": f"logs/{gate.name}.log", "sha256": _sha(log)} if log.is_file() else None}
        _write_new(run_dir, failure_rel, failure)
        raise


def verify_execution(run_dir: Path, receipt_path: Path, *, release_dir: Path | None = None,
                     source_root: Path | None = None) -> dict:
    """Read-only audit; freshness never substitutes for validity.

    ``release_dir`` is the available archived snapshot (required for validated identity).
    ``source_root`` optionally checks present source bytes; it does not compare the
    auditor's machine to the execution machine. A different Python interpreter is
    reported incomplete, not as evidence of mutated bytecode. No artifact is rewritten.
    """
    from harness.host import verify_recorded_host
    from harness.releases import verify_release, verify_source

    run_dir = Path(run_dir).absolute()
    report = {"validity": "invalid", "currentness": "unknown", "legacy": False,
              "execution_identity": "unvalidated", "scientific_validation": "legacy-unvalidated",
              "errors": [], "limitations": []}
    errors = report["errors"]
    try:
        receipt_path = Path(receipt_path).absolute()
        relative = receipt_path.relative_to(run_dir).as_posix()
        receipt = json.loads(require_regular_file(run_dir, relative).read_text(encoding="utf-8"))
        report["gate_passed"] = receipt.get("result", {}).get("passed")
        if receipt.get("receipt_hash") != receipt_hash(receipt):
            errors.append("receipt selfhash mismatch")
        if receipt.get("receipt_schema", 0) not in (0, 1):
            errors.append("unsupported gdkit receipt schema")
        entries = _ledger(run_dir)
        heads = {entry["entry_hash"] for entry in entries}
        head = receipt.get("ledger_head")
        report["currentness"] = "current" if head == entries[-1]["entry_hash"] else "stale" if head in heads else "unknown-head"
        if head not in heads:
            errors.append("receipt ledger head is absent from verified ledger")
        if receipt.get("run_id") != entries[-1]["run_id"]:
            errors.append("receipt run ID mismatch")
        for rel, expected in receipt.get("inputs", {}).items():
            if _sha(require_regular_file(run_dir, rel)) != expected:
                errors.append(f"input digest mismatch: {rel}")
        log = receipt.get("log")
        if receipt.get("receipt_schema", 0) == 0:
            matches = [e for e in entries if e.get("op") == "gate_log" and
                       e.get("params", {}).get("receipt_sha256") == receipt.get("receipt_hash")]
            if not matches:
                errors.append("legacy receipt has no gate_log binding")
            else:
                log = {"path": matches[-1]["params"]["log"], "sha256": matches[-1]["output_hash"]}
        if not log:
            errors.append("receipt has no log binding")
        elif _sha(require_regular_file(run_dir, log["path"])) != log["sha256"]:
            errors.append("log digest mismatch")
        version = receipt.get("contract_version")
        if version != CONTRACT_VERSION:
            report["legacy"] = version is None or isinstance(version, int) and version < CONTRACT_VERSION
            report["limitations"].append("unsupported or historical contract: execution closure is not validated")
            report["validity"] = "invalid" if errors else "legacy-incomplete" if report["legacy"] else "unsupported-contract"
            return report
        if receipt.get("receipt_schema") != 1:
            errors.append("bound execution requires existing gdkit receipt schema 1")
        manifest_rel = receipt.get("result", {}).get("execution_manifest")
        if manifest_rel != f"execution/{receipt.get('gate')}.json" or manifest_rel not in receipt.get("inputs", {}):
            raise ExecutionError("receipt does not bind its expected execution manifest")
        manifest = json.loads(require_regular_file(run_dir, manifest_rel).read_text(encoding="utf-8"))
        for key in ("gate", "run_id", "ledger_head", "contract_version", "gate_code_hash"):
            if manifest.get(key) != receipt.get(key):
                errors.append(f"manifest/receipt {key} mismatch")
        if manifest.get("inputs") != {k: v for k, v in receipt["inputs"].items() if k != manifest_rel}:
            errors.append("manifest input closure mismatch")
        expected_artifacts = _hash_outputs(run_dir, manifest["expected_outputs"])
        if receipt.get("result", {}).get("artifacts") != expected_artifacts:
            errors.append("output artifact closure/digest mismatch")
        host = manifest["host"]
        recorded = verify_recorded_host(run_dir, host["host_sha256"])
        for key in ("path", "sha256", "session_id", "event_hash", "event_seq"):
            if recorded.get(key) != host.get(key):
                errors.append(f"host reference mismatch: {key}")
        host_entries = [e for e in entries if e.get("op") == "host" and e.get("event") and
                        e["seq"] <= next(e["seq"] for e in entries if e["entry_hash"] == head)]
        if not host_entries or host_entries[-1]["params"].get("sha256") != host["host_sha256"]:
            errors.append("host was not canonical at execution ledger head")
        if receipt.get("host_check", {}).get("checked") is not True or receipt["host_check"].get("host_sha256") != host["host_sha256"]:
            errors.append("receipt same-host check is not bound to manifest host")
        if release_dir is None:
            report["limitations"].append("release snapshot unavailable; execution identity is not validated")
        else:
            release_dir = Path(release_dir)
            release = verify_release(release_dir)
            if release != manifest["release"] or _sha(release_dir / "release-manifest.json") != manifest["release_manifest_sha256"]:
                errors.append("release snapshot/manifest mismatch")
            else:
                # Re-derive recorded executable code from the archived source, without importing it.
                identity_errors_before = len(errors)
                compiled_sources = {}
                same_interpreter = (
                    manifest["runtime"].get("python") == platform.python_version()
                    and manifest["runtime"].get("implementation") == platform.python_implementation()
                )
                if not same_interpreter:
                    report["limitations"].append("matching execution interpreter unavailable; bytecode binding is unchecked")
                for binding, state in manifest["callables"].items():
                    relative = state["source"]
                    if relative not in release["files"]:
                        errors.append(f"callable source absent from release: {binding}")
                        continue
                    if not same_interpreter:
                        continue
                    name = state.get("name", binding.rsplit(".", 1)[-1])
                    if relative not in compiled_sources:
                        compiled_sources[relative] = _compiled_functions(release_dir / relative)
                    code = compiled_sources[relative].get(name)
                    if code is None or hashlib.sha256(_json(_code(code))).hexdigest() != state["code_sha256"]:
                        errors.append(f"release callable mismatch: {binding}")
                for module_name, values in manifest["constants"].items():
                    relative = manifest["constant_sources"][module_name]
                    if relative not in release["files"]:
                        errors.append(f"constant source absent from release: {module_name}")
                        continue
                    literals = _source_constants(release_dir / relative)
                    for name, expected in values.items():
                        if name in literals and literals[name] != expected:
                            errors.append(f"release constant mismatch: {module_name}.{name}")
                        if name == "CONTRACT_VERSION" and expected != CONTRACT_VERSION:
                            errors.append(f"contract constant mismatch: {module_name}.{name}")
                if len(errors) == identity_errors_before:
                    report["execution_identity"] = "release-bound" if same_interpreter else "source-bound"
            if source_root is not None:
                verify_source(release_dir, Path(source_root))
        report["limitations"].extend(manifest.get("limitations", []))
        report["validity"] = "invalid" if errors else "valid" if report["execution_identity"] == "release-bound" else "incomplete"
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
        report["validity"] = "invalid"
    return report


register_module(__name__)

# The release builder stays stdlib-only; registration belongs to the executor.
from harness import releases as _release_module

register_module(_release_module.__name__)
