import pathlib
from typing import Optional, Any

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

from .base import RenamerPlugin
from ..utils import sanitize_filename


class Plugin(RenamerPlugin):
    """A renamer plugin for audio files based on ID3, MP4, or FLAC tags."""

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
        except Exception:
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
