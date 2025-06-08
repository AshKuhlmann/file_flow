import pathlib
import tomllib
from typing import Any, Dict

DEFAULT_CONFIG_PATH = pathlib.Path.home() / ".file-sorter" / "config.toml"


def load_config(path: pathlib.Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load the TOML configuration file."""
    if not path.exists():
        return {}
    with path.open("rb") as fp:
        return tomllib.load(fp)


# Default classification rules used when no config is provided
DEFAULT_RULES = {
    "Pictures": {
        "extensions": [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".svg",
            ".webp",
        ]
    },
    "Videos": {
        "extensions": [
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".wmv",
            ".flv",
        ]
    },
    "Documents": {
        "extensions": [
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".rtf",
            ".odt",
        ]
    },
    "Spreadsheets": {
        "extensions": [
            ".xls",
            ".xlsx",
            ".ods",
            ".csv",
        ]
    },
    "Presentations": {
        "extensions": [
            ".ppt",
            ".pptx",
            ".odp",
        ]
    },
    "Audio": {
        "extensions": [
            ".mp3",
            ".wav",
            ".flac",
            ".aac",
            ".ogg",
            ".m4a",
            ".wma",
        ]
    },
    "Archives": {
        "extensions": [
            ".zip",
            ".tar",
            ".gz",
            ".rar",
            ".7z",
            ".bz2",
            ".xz",
        ]
    },
    "Scripts": {
        "extensions": [
            ".py",
            ".js",
            ".sh",
            ".bat",
            ".ps1",
            ".pl",
            ".rb",
        ]
    },
    "Fonts": {
        "extensions": [
            ".ttf",
            ".otf",
            ".woff",
            ".woff2",
        ]
    },
    "Books": {"extensions": [".epub", ".mobi"]},
    "Packages": {"extensions": [".deb", ".rpm", ".pkg"]},
}
