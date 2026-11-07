#!/usr/bin/env python3
"""Verify the dataset inventory against live APIs and build a hash manifest.

Reads every ```json fenced block under datasets/inventory/*.md, re-checks each row's
``pinned_revision`` against the HuggingFace or GitHub API, and writes:

  datasets/inventory/_verified.json   one row per dataset, with verified_sha and status
  datasets/inventory/_manifest.json   sha256 of the canonical JSON of _verified.json

Status values: VERIFIED, MISMATCH, UNVERIFIED, BAD_ROW, API_FAIL.
A row is never repaired from the API; a mismatch is reported, not silently corrected.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "datasets" / "inventory"
UA = {"User-Agent": "gdkit-inventory/0.1 (+preflight)"}
BLOCK = re.compile(r"```json\s*(.*?)```", re.S)


def api_json(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def rows_from(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    out: list[dict] = []
    for raw in BLOCK.findall(text):
        try:
            data = json.loads(raw)
        except ValueError as exc:
            print(f"  ! {path.name}: unparsable json block ({exc})", file=sys.stderr)
            continue
        if isinstance(data, dict):
            data = data.get("datasets") or data.get("rows") or [data]
        if not isinstance(data, list):
            continue
        for row in data:
            if isinstance(row, dict):
                out.append({"_source_file": path.name, **row})
    return out


def github_head(owner: str, name: str) -> str | None:
    """HEAD sha for a GitHub repo. API first, then `git ls-remote` (no rate limit)."""
    try:
        commits = api_json(f"https://api.github.com/repos/{owner}/{name}/commits?per_page=1")
        if isinstance(commits, list) and commits:
            return commits[0]["sha"]
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
        print(f"  ~ {owner}/{name}: API {exc}; falling back to ls-remote", file=sys.stderr)
    try:
        out = subprocess.run(
            ["git", "ls-remote", f"https://github.com/{owner}/{name}", "HEAD"],
            capture_output=True, text=True, timeout=45,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.split()[0]
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def commit_exists(owner: str, name: str, sha: str) -> bool:
    """True when GitHub serves a page for this commit, i.e. the sha exists in the repo."""
    url = f"https://github.com/{owner}/{name}/commit/{sha}"
    req = urllib.request.Request(url, headers=UA, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as exc:
        return exc.code == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def live_sha(row: dict) -> tuple[str, str | None]:
    """(status, actual_sha). Never guesses a revision."""
    url = str(row.get("canonical_url") or row.get("url") or "")
    ident = str(row.get("id") or row.get("dataset_id") or row.get("dataset") or "").strip()
    claimed = str(row.get("pinned_revision") or row.get("revision") or "").strip()
    if not ident:
        return "BAD_ROW", None
    if ident.count("/") != 1 or any(ch in ident for ch in " ;,()"):
        return "MULTI", None  # a row naming more than one dataset cannot be pinned to one sha
    if not claimed or claimed.upper().startswith("UNVERIFIED"):
        return "UNVERIFIED", None
    owner, name = ident.split("/", 1)
    try:
        if not url:
            url = f"https://huggingface.co/datasets/{ident}"
        if "huggingface.co" in url and "/datasets/" in url:
            actual = api_json(f"https://huggingface.co/api/datasets/{owner}/{name}").get("sha")
        elif "huggingface.co" in url:
            actual = api_json(f"https://huggingface.co/api/models/{owner}/{name}").get("sha")
        elif "github.com" in url:
            actual = github_head(owner, name)
        else:
            return "API_FAIL", None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
        print(f"  ! {ident}: {exc}", file=sys.stderr)
        return "API_FAIL", None
    if not actual:
        return "API_FAIL", None
    if actual.startswith(claimed[:12]):
        return "VERIFIED", actual
    if "github.com" in url and commit_exists(owner, name, claimed):
        return "PINNED", actual  # a deliberate historical or tag pin, still real
    return "MISMATCH", actual


def main() -> int:
    if not INVENTORY.is_dir():
        print(f"no inventory at {INVENTORY}", file=sys.stderr)
        return 1
    rows: list[dict] = []
    for path in sorted(INVENTORY.glob("*.md")):
        found = rows_from(path)
        print(f"{path.name}: {len(found)} row(s)")
        rows.extend(found)

    verified: list[dict] = []
    for row in rows:
        status, actual = live_sha(row)
        verified.append({**row, "status": status, "verified_sha": actual})
        name = row.get("name") or row.get("task") or row.get("item") or row.get("id") or row.get("dataset_id") or "?"
        print(f"  {status:10s} {name}")

    counts: dict[str, int] = {}
    for row in verified:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    out = INVENTORY / "_verified.json"
    out.write_bytes(canonical(verified) + b"\n")
    manifest = {
        "file": out.name,
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "rows": len(verified),
        "status_counts": counts,
    }
    (INVENTORY / "_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("\n" + json.dumps(manifest, indent=2))
    return 0 if counts.get("MISMATCH", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
