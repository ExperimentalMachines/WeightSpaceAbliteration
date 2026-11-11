#!/usr/bin/env python3
"""Append-only check for run artifacts.

Ledgers may only grow. Receipts, logs, attestations and scope files may be added, never modified or
deleted. `splits/manifest.json` may be replaced, because a rebuild is a recorded event with its own
ledger entry.

One narrow exception: a raw pwc response under `paper_lookups/` may be rewritten to the exact bytes its
own `paper_lookup` entry recorded. The entry must already be in the run's ledger before the change (HEAD
for a pre-commit check, the base for CI), name this file as `raw_response_path`, and carry the sha256 of
the new bytes as `response_sha256`. This repairs a file git stored with converted line endings; it cannot
introduce content the ledger did not already vouch for.

    python scripts/check_append_only.py                 # staged changes against HEAD (pre-commit)
    python scripts/check_append_only.py --base <sha>    # everything since <sha> (CI)

Exit 0 when every change under runs/ is an addition or a legal append, 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys

LEDGER = "ledger.jsonl"
REBUILDABLE = "splits/manifest.json"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def blob(ref: str, path: str) -> str | None:
    """File content as git would materialise it, with line endings normalised.

    The comparison is about content, not transport: `text=auto` rewrites CRLF to LF on the way into
    the index, and a difference that exists only in line endings is not an edit to the ledger.
    """
    spec = f"{ref}:{path}"  # an empty ref addresses the index: ":path"
    proc = subprocess.run(["git", "show", spec], capture_output=True, text=True)
    return proc.stdout.replace("\r\n", "\n") if proc.returncode == 0 else None


def raw_blob(ref: str, path: str) -> bytes | None:
    """File content exactly as git stores it, as bytes: no decoding, no line-ending conversion."""
    proc = subprocess.run(["git", "cat-file", "blob", f"{ref}:{path}"], capture_output=True)
    return proc.stdout if proc.returncode == 0 else None


def restores_recorded_lookup(path: str, old_ref: str, new_ref: str) -> bool:
    """True when ``path`` is a raw pwc response rewritten to the bytes its own, pre-existing entry recorded."""
    parts = path.split("/")
    if len(parts) != 4 or parts[0] != "runs" or parts[2] != "paper_lookups":
        return False
    ledger = raw_blob(old_ref, f"runs/{parts[1]}/{LEDGER}")
    new = raw_blob(new_ref, path)
    if ledger is None or new is None:
        return False
    relative = "/".join(parts[2:])
    digest = hashlib.sha256(new).hexdigest()
    for line in ledger.decode("utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        params = entry.get("params") or {}
        if (entry.get("op") == "paper_lookup" and params.get("raw_response_path") in (relative, path)
                and params.get("response_sha256") == digest):
            return True
    return False


def changes(base: str | None) -> list[tuple[str, str]]:
    # -z and --no-renames: a move is a delete plus an add, so a run file moved out of runs/ is still seen.
    args = ["diff", "-z", "--no-renames", "--name-status"]
    args += [base, "HEAD"] if base else ["--cached"]
    fields = [f for f in git(*args).split("\0") if f]
    return [(fields[i][0], fields[i + 1]) for i in range(0, len(fields) - 1, 2)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_append_only")
    parser.add_argument("--base")
    args = parser.parse_args(argv)

    violations: list[str] = []
    for status, path in changes(args.base):
        if not path.startswith("runs/") or path.endswith("README.md"):
            continue
        if status == "A":
            continue
        if status == "M" and path.endswith(LEDGER):
            old = blob(args.base or "HEAD", path)
            new = blob("HEAD", path) if args.base else blob("", path)
            if old is None or new is None or not new.startswith(old):
                violations.append(f"{path}: the ledger is not a byte-prefix extension of its previous state")
            continue
        if status == "M" and path.endswith(REBUILDABLE):
            continue
        if status == "M" and restores_recorded_lookup(path, args.base or "HEAD", "HEAD" if args.base else ""):
            continue
        violations.append(f"{path}: {status} — run artifacts are append-only")

    for item in violations:
        print(item, file=sys.stderr)
    if violations:
        print("\nA correction is a new entry, not an edit "
              "(docs/protocol/RUN_PROTOCOL.md#deviations).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
