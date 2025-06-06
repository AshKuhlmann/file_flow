from __future__ import annotations

import csv
import datetime as _dt
import pathlib
import shutil
from typing import Iterable


def move_with_log(
    mapping: Iterable[tuple[pathlib.Path, pathlib.Path]],
    log: pathlib.Path | None = None,
) -> pathlib.Path:
    """Move each src to dst and record operations in a CSV log."""
    entries = list(mapping)
    if log is None:
        log = (
            pathlib.Path.cwd()
            / f"file-sort-log_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
    log = log.expanduser().resolve()
    with log.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["src", "dst"])
        for src, dst in entries:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src.as_posix(), dst.as_posix())
            writer.writerow([src.as_posix(), dst.as_posix()])
    return log


__all__ = ["move_with_log"]
