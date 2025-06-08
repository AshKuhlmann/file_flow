from __future__ import annotations

import hashlib
import pathlib
import re
from typing import Final

BUF_SIZE: Final = 1 << 20  # 1 MiB


def hash_file(
    path: pathlib.Path, *, algorithm: str = "sha256", buf_size: int = BUF_SIZE
) -> str:
    """Return *algorithm* hash of *path*."""
    h = hashlib.new(algorithm)
    with path.open("rb") as fp:
        while chunk := fp.read(buf_size):
            h.update(chunk)
    return h.hexdigest()


def sha256sum(path: pathlib.Path, *, buf_size: int = BUF_SIZE) -> str:
    """Return SHA-256 checksum of *path*."""
    return hash_file(path, algorithm="sha256", buf_size=buf_size)


def sanitize_filename(name: str) -> str:
    """Remove characters that are invalid for file names."""
    return re.sub(r'[\\/*?:"<>|]', "", name)


__all__ = ["hash_file", "sha256sum", "BUF_SIZE", "sanitize_filename"]
