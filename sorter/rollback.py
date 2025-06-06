from __future__ import annotations

import csv
import pathlib
import shutil


def rollback(log_file: pathlib.Path) -> None:
    """Reverse operations recorded in *log_file*."""
    log_file = log_file.expanduser().resolve()
    if not log_file.exists():
        return
    with log_file.open(newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    for row in reversed(rows):
        dst = pathlib.Path(row["dst"])
        src = pathlib.Path(row["src"])
        if dst.exists():
            src.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(dst.as_posix(), src.as_posix())


__all__ = ["rollback"]
