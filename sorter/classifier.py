from __future__ import annotations

import pathlib
import tomllib
import importlib.resources as pkg_res
from typing import Final

import magic  # python-magic

_DEFAULT_RULES_PKG: Final = "data"
_DEFAULT_RULES_FILE: Final = "default_rules.toml"

with pkg_res.files(_DEFAULT_RULES_PKG).joinpath(_DEFAULT_RULES_FILE).open("rb") as fp:
    _EXT_MAP: dict[str, str] = tomllib.load(fp)["ext"]


def classify(path: pathlib.Path) -> str | None:
    """Return category label for *path* or *None* if unknown.

    Order of precedence:
    1. Extension lookup (case-insensitive).
    2. MIME sniff via libmagic, using `type_sub:major`.
       e.g. "video/mp4" → "Videos" when major=="video".
    3. Fallback: None.
    """

    ext = path.suffix.lower()
    if ext in _EXT_MAP:
        return _EXT_MAP[ext]

    try:
        mime = magic.from_file(path.as_posix(), mime=True)
    except Exception:
        return None

    major = mime.split("/", 1)[0]
    return {
        "video": "Videos",
        "audio": "Audio",
        "image": "Pictures",
        "text": "Documents",
        "application": "Documents",
    }.get(major)
