from __future__ import annotations

import pathlib
import sqlite3
import time
from typing import Final, Sequence

_SECONDS_IN_DAY: Final = 86_400
_DEFAULT_DB_NAME = "review.db"
_COOLDOWN_DAYS = 30


class ReviewQueue:
    """Manages file-review cadence with 30-day cool-down."""

    def __init__(self, db_path: pathlib.Path | None = None) -> None:
        if db_path is None:
            db_path = pathlib.Path.home() / ".file-sorter" / _DEFAULT_DB_NAME
        db_path = db_path.expanduser()
        db_path.parent.mkdir(exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._create_schema()

    def __del__(self) -> None:  # pragma: no cover - destructor
        try:
            self._conn.close()
        except Exception:
            pass

    # ---------- public API ------------
    def upsert_files(self, files: Sequence[pathlib.Path]) -> None:
        """Ensure *files* exist in table; untouched if already present."""
        rows: list[tuple[str, int, int]] = []
        for p in files:
            abs_p = p.expanduser().resolve()
            try:
                stat = abs_p.stat()
            except OSError:
                continue
            rows.append(
                (
                    abs_p.as_posix(),
                    stat.st_size,
                    int(stat.st_mtime),
                )
            )
        with self._conn:
            self._conn.executemany(
                "INSERT OR IGNORE INTO reviewed (path, next_ts, last_size, last_mtime)"
                " VALUES (?, 0, ?, ?)",
                rows,
            )

    def select_for_review(
        self, *, limit: int = 5, now: int | None = None
    ) -> list[pathlib.Path]:
        """Return at most *limit* Paths whose next_ts <= now."""
        if now is None:
            now = int(time.time())
        cur = self._conn.execute(
            "SELECT path FROM reviewed WHERE next_ts <= ?"
            " ORDER BY last_mtime DESC, path ASC LIMIT ?",
            (now, limit),
        )
        return [pathlib.Path(row[0]) for row in cur.fetchall()]

    def mark_keep(self, path: pathlib.Path, *, now: int | None = None) -> None:
        """User kept file → push next_ts forward by 30 days."""
        abs_p = path.expanduser().resolve()
        if now is None:
            now = int(time.time())
        next_ts = now + _COOLDOWN_DAYS * _SECONDS_IN_DAY
        with self._conn:
            self._conn.execute(
                "UPDATE reviewed SET next_ts = ? WHERE path = ?",
                (next_ts, abs_p.as_posix()),
            )

    def mark_delete(self, path: pathlib.Path) -> None:
        """Remove file entry; caller deletes file on disk."""
        abs_p = path.expanduser().resolve()
        with self._conn:
            self._conn.execute(
                "DELETE FROM reviewed WHERE path = ?",
                (abs_p.as_posix(),),
            )

    # ---------- internals ------------
    def _create_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reviewed (
                    path       TEXT PRIMARY KEY,
                    next_ts    INTEGER NOT NULL,
                    last_size  INTEGER NOT NULL,
                    last_mtime INTEGER NOT NULL
                );
                """
            )


__all__ = ["ReviewQueue"]
