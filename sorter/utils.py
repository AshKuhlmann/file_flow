from __future__ import annotations

import hashlib
import pathlib
from typing import Final

BUF_SIZE: Final = 1 << 20  # 1 MiB


def sha256sum(path: pathlib.Path, *, buf_size: int = BUF_SIZE) -> str:
    """Return SHA-256 checksum of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as fp:
        while chunk := fp.read(buf_size):
            h.update(chunk)
    return h.hexdigest()


__all__ = ["sha256sum", "BUF_SIZE"]
