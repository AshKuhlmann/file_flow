from __future__ import annotations

import json
import pathlib
import shutil
from typing import Final

from .utils import sha256sum as _sha256

_TRASH_SUFFIX: Final = "__rollback_trash"


def rollback(log_path: pathlib.Path, *, strict: bool = True) -> None:
    """Undo moves recorded in *log_path* (last-in-first-out)."""

    log_path = log_path.expanduser().resolve()
    entries = [json.loads(line) for line in log_path.read_text().splitlines()]
    for rec in reversed(entries):
        src, dst = pathlib.Path(rec["src"]), pathlib.Path(rec["dst"])
        if strict and dst.exists() and _sha256(dst) != rec["sha256"]:
            raise ValueError(f"checksum mismatch for {dst}")
        if src.exists():
            src.replace(src.with_suffix(src.suffix + _TRASH_SUFFIX))
        if dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(dst, src)
