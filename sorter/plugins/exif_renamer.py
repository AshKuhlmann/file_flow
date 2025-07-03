from __future__ import annotations

import pathlib
import re
from typing import Any, Dict, Optional

import exifread

from .base import RenamerPlugin
from ..utils import sanitize_filename


class ExifRenamer(RenamerPlugin):
    """Rename photos based on EXIF metadata."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)

    @property
    def name(self) -> str:  # pragma: no cover - simple property
        return "exif"

    def rename(self, source_path: pathlib.Path) -> Optional[str]:
        # This plugin only handles common image file types
        if source_path.suffix.lower() not in [".jpg", ".jpeg", ".tiff"]:
            return None

        with source_path.open("rb") as f:
            tags = exifread.process_file(
                f, details=False, stop_tag="EXIF DateTimeOriginal"
            )

            if "EXIF DateTimeOriginal" not in tags:
                return None

            dt_str = str(tags["EXIF DateTimeOriginal"])
            dt_parts = re.match(
                r"(\d{4}):(\d{2}):(\d{2}) (\d{2}):(\d{2}):(\d{2})",
                dt_str,
            )
            if not dt_parts:
                return None

            year, month, day, hour, minute, second = dt_parts.groups()

            format_data: Dict[str, Any] = {
                "year": year,
                "month": month,
                "day": day,
                "hour": hour,
                "minute": minute,
                "second": second,
                "model": str(tags.get("Image Model", "UnknownModel")).strip(),
                "make": str(tags.get("Image Make", "UnknownMake")).strip(),
            }

            new_stem = self.pattern.format(**format_data)
            return sanitize_filename(new_stem)
