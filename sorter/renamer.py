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
    pattern: str | None = None,
) -> pathlib.Path:
    """Return a collision-free destination path inside *target_dir*.

    Naming pattern can be customized using ``pattern``. Tokens available:
      ``{parent}`` - slugified parent directory name
      ``{date}``   - formatted date string (YYYY-MM-DD)
      ``{stem}``   - slugified base file name
      ``{ext}``    - original file extension
    Default pattern:
      ``{parent}_{date}_{stem}{ext}`` with ``__N`` appended on collision.
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

    if pattern:
        name = _get_name_from_pattern(src, pattern, include_parent, date_from_mtime)
    else:
        name = _get_default_name(src, include_parent, date_from_mtime)

    return _resolve_collisions(target_dir, name)


def _build_tokens(
    src: pathlib.Path,
    include_parent: bool,
    date_from_mtime: bool,
) -> dict[str, str]:
    """Return tokens used for naming."""

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

    return {"parent": parent_part, "date": date_part, "stem": base_part, "ext": ext}


def _get_name_from_pattern(
    src: pathlib.Path, pattern: str, include_parent: bool, date_from_mtime: bool
) -> str:
    """Generate a file name from a user-provided pattern."""

    tokens = _build_tokens(src, include_parent, date_from_mtime)
    return pattern.format(**tokens)


def _get_default_name(
    src: pathlib.Path,
    include_parent: bool,
    date_from_mtime: bool,
) -> str:
    """Generate a default file name."""

    tokens = _build_tokens(src, include_parent, date_from_mtime)
    pieces = [p for p in (tokens["parent"], tokens["date"], tokens["stem"]) if p]
    stem = "_".join(pieces)
    return f"{stem}{tokens['ext']}"


def _resolve_collisions(target_dir: pathlib.Path, name: str) -> pathlib.Path:
    """Append a counter to ``name`` if a file with the same name already exists."""

    candidate = target_dir / name
    stem = pathlib.Path(name).stem
    ext = pathlib.Path(name).suffix
    counter = 2
    existing = {p.name.lower() for p in target_dir.iterdir()}
    while candidate.name.lower() in existing:
        candidate = target_dir / f"{stem}__{counter}{ext}"
        counter += 1

    return candidate.resolve()
