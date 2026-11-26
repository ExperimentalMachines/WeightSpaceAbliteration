"""Inventory local model snapshots and English punkt_tab bytes, without fetching or loading models.

Print JSON to stdout. --compare checks repeatability against an earlier inventory, NOT
upstream authenticity, loadability, or historical use. Missing files remain observations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

ROLES = ('model', 'parent', 'judge', 'judge_alt', 'embedding')
ENGLISH_TABLES = ('abbrev_types.txt', 'collocations.tab', 'ortho_context.tab', 'sent_starters.txt')


def fingerprint(path: Path) -> dict:
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f'not a regular file: {path.name}')
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        after = path.stat()
    if not os.path.samestat(before, after) or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f'file changed during inventory: {path.name}')
    return {'bytes': before.st_size, 'sha256': digest}


def redirected(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def files_below(root: Path, blobs: Path | None = None) -> dict:
    files = {}
    pending = [root]
    while pending:
        directory = pending.pop()
        if redirected(directory):
            raise ValueError(f'redirected directory: {directory.name}')
        for path in directory.iterdir():
            name = path.relative_to(root).as_posix()
            if redirected(path):
                # Standard HF snapshots link to regular blobs in the SAME repository cache.
                target = path.resolve(strict=True)
                if blobs is None or target.parent != blobs or redirected(blobs) or not target.is_file():
                    raise ValueError(f'unexpected redirected entry: {name}')
            elif path.is_dir():
                pending.append(path)
                continue
            elif not path.is_file():
                raise ValueError(f'unsupported file type: {name}')
            files[name] = fingerprint(path)
    return files


def missing_model_files(root: Path, files: dict) -> list[str]:
    missing = [name for name in ('config.json', 'tokenizer_config.json') if name not in files]
    if not {'tokenizer.json', 'tokenizer.model', 'vocab.txt', 'vocab.json'}.intersection(files):
        missing.append('tokenizer vocabulary')
    weights_present = False
    for filename in ('model.safetensors', 'pytorch_model.bin'):
        weights_present |= files.get(filename, {}).get('bytes', 0) > 0
        index = filename + '.index.json'
        if index in files:
            shards = json.loads((root / index).read_bytes()).get('weight_map')
            if not isinstance(shards, dict) or not shards or not all(isinstance(v, str) for v in shards.values()):
                raise ValueError(f'invalid weight map: {index}')
            absent = sorted(s for s in set(shards.values()) if files.get(s, {}).get('bytes', 0) == 0)
            missing.extend(f'{index}: {s}' for s in absent)
            weights_present |= not absent
    if not weights_present:
        missing.append('standard weights or complete indexed shards')
    return missing


def inventory(config: Path, cache: Path, punkt_english: Path | None) -> dict:
    config_bytes = config.read_bytes()
    cfg = json.loads(config_bytes)
    refs = {}
    for role in ROLES:
        repo, rev = cfg[role]['id'], cfg[role]['revision']
        if not re.fullmatch(r'[\w-]+/[\w.-]+', repo, re.ASCII) or repo.endswith(('.', ' ')) or '--' in repo:
            raise ValueError(f'invalid Hub repository for {role}')
        if not re.fullmatch(r'[a-f0-9]{40}', rev):
            raise ValueError(f'expected immutable commit for {role}')
        refs.setdefault((repo, rev), []).append(role)

    snapshots = []
    cache = cache.resolve()
    for (repo, rev), roles in sorted(refs.items()):
        directory = cache / ('models--' + repo.replace('/', '--'))
        root = directory / 'snapshots' / rev
        if root.resolve() != root:
            raise ValueError(f'redirected snapshot path for {repo}')
        present = root.is_dir()
        files = files_below(root, directory / 'blobs') if present else {}
        snapshots.append({'repo': repo, 'revision': rev, 'roles': roles, 'snapshot_present': present,
                          'files': files, 'missing_standard_inputs': missing_model_files(root, files)})
    punkt_files = {} if punkt_english is None or not punkt_english.is_dir() else files_below(punkt_english)
    return {'schema': 1, 'config_sha256': hashlib.sha256(config_bytes).hexdigest(), 'snapshots': snapshots,
            'punkt_tab_english': {'files': punkt_files, 'missing_tables': sorted(set(ENGLISH_TABLES) - punkt_files.keys())}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--hf-cache', type=Path, help='Hub cache root; default: configured HF_HUB_CACHE')
    parser.add_argument('--punkt-english', type=Path, help='unpacked English resource directory; default: NLTK lookup')
    parser.add_argument('--compare', type=Path, help='read-only comparison with a saved inventory')
    args = parser.parse_args(argv)
    try:
        cache = args.hf_cache
        if cache is None:
            from huggingface_hub.constants import HF_HUB_CACHE
            cache = Path(HF_HUB_CACHE)
        punkt = args.punkt_english
        if punkt is None:
            import nltk.data
            try:
                pointer = nltk.data.find('tokenizers/punkt_tab/english/')
            except LookupError:
                pass
            else:
                if not isinstance(pointer, nltk.data.FileSystemPathPointer):
                    raise ValueError('expected an unpacked punkt_tab directory')
                punkt = Path(pointer.path)
        current = inventory(args.config, cache, punkt)
        if args.compare is not None:
            matches = current == json.loads(args.compare.read_bytes())
            print(json.dumps({'matches_local_inventory': matches}, sort_keys=True))
            return 0 if matches else 1
        print(json.dumps(current, sort_keys=True, indent=2))
        return 0
    except (OSError, KeyError, ValueError, TypeError) as exc:
        print(f'inventory refused: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
