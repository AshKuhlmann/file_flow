from __future__ import annotations

import datetime as _dt
import os
import pathlib
import subprocess
import sys
from typing import Iterable, Final, cast

import pandas as _pd
from openpyxl.utils import get_column_letter as _col

_DATE_FMT: Final = "%Y%m%d_%H%M%S"


def build_report(
    mapping: Iterable[tuple[pathlib.Path, pathlib.Path]],
    *,
    dest: pathlib.Path | None = None,
    auto_open: bool = False,
) -> pathlib.Path:
    """Write an XLSX file describing the proposed moves.

    *mapping* – iterable of (src, dst) absolute Paths.
    Returns the path to the newly-created XLSX.
    Columns: old_path, new_path, size_bytes, modified_iso.
    Rows sorted lexicographically by old_path for reproducibility.
    If *auto_open* is True, attempts to open the file using OS default.
    """

    rows: list[dict[str, str | int]] = []
    for src, dst in mapping:
        stat = src.stat()
        rows.append(
            {
                "old_path": src.as_posix(),
                "new_path": dst.as_posix(),
                "size_bytes": stat.st_size,
                "modified_iso": _dt.datetime.utcfromtimestamp(stat.st_mtime).isoformat(
                    timespec="seconds"
                )
                + "Z",
            }
        )

    df = _pd.DataFrame(
        cast(
            list[dict[str, str | int]],
            sorted(rows, key=lambda r: cast(str, r["old_path"])),
        )
    )

    if dest is None:
        dest = (
            pathlib.Path.cwd()
            / f"file-sort-report_{_dt.datetime.now().strftime(_DATE_FMT)}.xlsx"
        )
    else:
        dest = dest.expanduser().resolve()

    with _pd.ExcelWriter(dest, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Report", index=False)
        ws = writer.sheets["Report"]
        for idx, column in enumerate(df.columns, start=1):
            col = _col(idx)
            ws[f"{col}1"].font = ws[f"{col}1"].font.copy(bold=True)
            col_values = [column, *df.iloc[:, idx - 1].tolist()]
            max_len = max(len(str(x)) for x in col_values)
            ws.column_dimensions[col].width = min(max_len + 2, 80)

    if auto_open:
        _open_with_os(dest)

    return dest


def _open_with_os(path: pathlib.Path) -> None:
    """Best-effort open file with default app on current OS."""
    try:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception:
        pass
