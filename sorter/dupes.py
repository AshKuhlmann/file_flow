from __future__ import annotations

import hashlib
import pathlib
from io import SEEK_END
from collections import defaultdict
from typing import Iterable, Sequence, Dict, List

from .utils import hash_file


def _quick_hash(
    path: pathlib.Path,
    /,
    sample: int = 64 * 1024,
    *,
    algorithm: str = "sha256",
) -> str:
    """Return *algorithm* hash of first + last *sample* bytes."""
    size = path.stat().st_size
    h = hashlib.new(algorithm)
    with path.open("rb") as fp:
        h.update(fp.read(sample))
        if size > sample:
            fp.seek(-sample, SEEK_END)
            h.update(fp.read(sample))
    return h.hexdigest()


def _full_hash(path: pathlib.Path, *, algorithm: str = "sha256") -> str:
    return hash_file(path, algorithm=algorithm)


def find_duplicates(
    files: Iterable[pathlib.Path],
    *,
    validate_full: bool = True,
    algorithm: str = "sha256",
) -> Dict[str, List[pathlib.Path]]:
    """Group *files* by identical content using *algorithm* hash."""
    quick: Dict[str, List[pathlib.Path]] = defaultdict(list)
    for f in files:
        quick[_quick_hash(f, algorithm=algorithm)].append(f)
    dupes: Dict[str, List[pathlib.Path]] = {}
    for group in quick.values():
        if len(group) < 2:
            continue
        if validate_full:
            full_map: Dict[str, List[pathlib.Path]] = defaultdict(list)
            for p in group:
                full_map[_full_hash(p, algorithm=algorithm)].append(p)
            dupes.update({k: v for k, v in full_map.items() if len(v) > 1})
        else:
            dupes[_quick_hash(group[0], algorithm=algorithm)] = group
    return dupes


def delete_older(dupe_group: Sequence[pathlib.Path]) -> list[pathlib.Path]:
    """Keep newest mtime, delete others; return deleted paths."""
    newest = max(dupe_group, key=lambda p: p.stat().st_mtime)
    deleted: list[pathlib.Path] = []
    for p in dupe_group:
        if p is newest:
            continue
        p.unlink()
        deleted.append(p)
    return deleted


__all__ = [
    "find_duplicates",
    "delete_older",
]
