import pathlib
from typing import Optional

import exifread

from .base import RenamerPlugin


class Plugin(RenamerPlugin):
    def rename(self, source_path: pathlib.Path) -> Optional[pathlib.Path]:
        if source_path.suffix.lower() not in [".jpg", ".jpeg", ".tiff"]:
            return None

        with source_path.open("rb") as f:
            tags = exifread.process_file(f, details=False)
            if "EXIF DateTimeOriginal" in tags:
                dt_str = str(tags["EXIF DateTimeOriginal"])
                year, month, day = dt_str[:10].split(":")
                hour, minute, second = dt_str[11:].split(":")
                pattern = self.config.get(
                    "pattern",
                    "{year}{month}{day}_{hour}{minute}{second}",
                )
                new_stem = pattern.format(
                    year=year,
                    month=month,
                    day=day,
                    hour=hour,
                    minute=minute,
                    second=second,
                    model=str(tags.get("Image Model", "")),
                )
                return pathlib.Path(new_stem + source_path.suffix)
        return None
