#!/usr/bin/env python3
"""Build or verify local immutable code-only releases; never contact a service."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Direct invocation works from any working directory without installing this repo.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.releases import ReleaseError, build_release, verify_release, verify_source


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    build = actions.add_parser("build", help="publish selected runtime bytes once")
    build.add_argument("--repo", type=Path, default=Path("."), help="Git repository root")
    build.add_argument("--output", type=Path, required=True, help="local release parent directory")
    build.add_argument("--revision", default="HEAD", help="Git commit/ref (reference only in development mode)")
    build.add_argument(
        "--working-tree", action="store_true",
        help="explicit local development snapshot, NOT a reviewed Git snapshot or deployable release",
    )
    verify = actions.add_parser("verify", help="verify complete release, optionally actual runtime source")
    verify.add_argument("release", type=Path)
    verify.add_argument("--source-root", type=Path, help="also require exact selected local source bytes")
    args = parser.parse_args(argv)
    try:
        if args.action == "build":
            release = build_release(args.repo, args.output, revision=args.revision, working_tree=args.working_tree)
            print(release)
        else:
            manifest = (
                verify_source(args.release, args.source_root)
                if args.source_root is not None else verify_release(args.release)
            )
            print(json.dumps({
                "release_id": manifest["release_id"], "source": manifest["source"], "verified": True,
            }, sort_keys=True))
    except (ReleaseError, OSError) as exc:
        print(f"release refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
