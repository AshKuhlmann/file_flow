from __future__ import annotations

import pathlib
import logging
from typing import Any, Optional

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

from .base import RenamerPlugin
from ..utils import sanitize_filename


class Id3Renamer(RenamerPlugin):
    """Rename audio files using ID3/FLAC/MP4 tags."""

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config)

    @property
    def name(self) -> str:  # pragma: no cover - simple property
        return "id3"

    def rename(self, source_path: pathlib.Path) -> Optional[str]:
        suffix = source_path.suffix.lower()

        audio: Any
        try:
            if suffix == ".mp3":
                audio = EasyID3(source_path)
            elif suffix == ".flac":
                audio = FLAC(source_path)
            elif suffix == ".m4a":
                audio = MP4(source_path)
            else:
                return None
        except Exception as exc:
            # errors may occur if file lacks tags or mutagen cannot parse
            logging.getLogger(__name__).warning(
                "Failed to read tags from %s: %s", source_path, exc
            )
            return None

        format_data = {
            "artist": audio.get("artist", ["Unknown Artist"])[0],
            "album": audio.get("album", ["Unknown Album"])[0],
            "title": audio.get("title", [source_path.stem])[0],
            "track_number": int(audio.get("tracknumber", ["0"])[0].split("/")[0]),
            "genre": audio.get("genre", ["Unknown Genre"])[0],
        }

        new_stem = self.pattern.format(**format_data)
        return sanitize_filename(new_stem)
