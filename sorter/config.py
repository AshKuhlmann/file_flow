import pathlib
import tomllib
from typing import Optional

from pydantic import BaseModel, Field


DEFAULT_CONFIG_PATH = pathlib.Path.home() / ".file-sorter" / "config.toml"


class ClassificationRule(BaseModel):
    extensions: list[str] = Field(default_factory=list)
    mimetypes: list[str] = Field(default_factory=list)


class PluginConfig(BaseModel):
    enabled: bool = False
    pattern: str = ""


class Settings(BaseModel):
    fallback_category: Optional[str] = "Other"
    classification: dict[str, ClassificationRule] = Field(default_factory=dict)
    plugins: dict[str, PluginConfig] = Field(default_factory=dict)

    model_config = {
        "extra": "allow",
    }

    @classmethod
    def load(cls, path: pathlib.Path = DEFAULT_CONFIG_PATH) -> "Settings":
        if not path.exists():
            return cls()
        with path.open("rb") as fp:
            data = tomllib.load(fp)
        return cls.model_validate(data)


def load_config(path: pathlib.Path = DEFAULT_CONFIG_PATH) -> Settings:
    """Load the TOML configuration file and validate it."""
    return Settings.load(path)


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
