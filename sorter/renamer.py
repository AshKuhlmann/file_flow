from __future__ import annotations

import datetime as _dt
import pathlib
from typing import Final, Iterable, Pattern

try:
    from slugify import slugify as _slugify  # type: ignore
except Exception:  # pragma: no cover - optional dep missing
    import re

    def _slugify(
        text: str,
        entities: bool = False,
        decimal: bool = False,
        hexadecimal: bool = False,
        max_length: int = 0,
        word_boundary: bool = False,
        separator: str = "-",
        save_order: bool = False,
        stopwords: Iterable[str] = (),
        regex_pattern: Pattern[str] | str | None = None,
        lowercase: bool = True,
        replacements: Iterable[Iterable[str]] = (),
        allow_unicode: bool = False,
    ) -> str:
        text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
        text = text.strip().lower()
        text = re.sub(r"\s+", separator, text)
        return text

_DATE_FMT: Final = "%Y-%m-%d"


def generate_name(
    src: pathlib.Path,
    target_dir: pathlib.Path,
    *,
    include_parent: bool = True,
    date_from_mtime: bool = True,
) -> pathlib.Path:
    """Return a collision-free destination path inside *target_dir*.

    Naming pattern (default):
      <parent-slug>_<YYYY-MM-DD>_<base-slug>[__<N>].<ext>
    Rules:
      • parent-slug comes from ``src.parent.name`` (omit if ``include_parent`` is
        False or parent is root).
      • Date is file mtime if ``date_from_mtime``, else today.
      • base-slug from stem (no extension).
      • If filename already exists in ``target_dir`` (case-insensitive), append
        ``__2``, ``__3``, … until unused.
    Returns absolute ``Path``.
    """

    target_dir = target_dir.expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    parent_part = (
        _slugify(src.parent.name)
        if include_parent and src.parent.name and src.parent != pathlib.Path(src.anchor)
        else ""
    )

    date_part = (
        _dt.date.fromtimestamp(src.stat().st_mtime).strftime(_DATE_FMT)
        if date_from_mtime
        else _dt.date.today().strftime(_DATE_FMT)
    )

    base_part = _slugify(src.stem) or "file"
    ext = src.suffix.lower()

    pieces = [p for p in (parent_part, date_part, base_part) if p]
    stem = "_".join(pieces)

    candidate = target_dir / f"{stem}{ext}"
    counter = 2
    existing = {p.name.lower() for p in target_dir.iterdir()}
    while candidate.name.lower() in existing:
        candidate = target_dir / f"{stem}__{counter}{ext}"
        counter += 1
    return candidate.resolve()
