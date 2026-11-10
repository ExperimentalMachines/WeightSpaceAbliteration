#!/usr/bin/env python3
"""Append-only check for run artifacts.

Ledgers may only grow. Receipts, logs, attestations and scope files may be added, never modified or
deleted. `splits/manifest.json` may be replaced, because a rebuild is a recorded event with its own
ledger entry.

    python scripts/check_append_only.py                 # staged changes against HEAD (pre-commit)
    python scripts/check_append_only.py --base <sha>    # everything since <sha> (CI)

Exit 0 when every change under runs/ is an addition or a legal append, 1 otherwise.
"""

from __future__ import annotations

import argparse
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


def changes(base: str | None) -> list[tuple[str, str]]:
    args = ["diff", "--name-status", base, "HEAD"] if base else ["diff", "--cached", "--name-status"]
    out = []
    for line in git(*args).splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        out.append((parts[0][0], parts[-1]))
    return out


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
