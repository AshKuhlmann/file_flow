import pathlib
import tomllib
import os
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_CONFIG_PATH = pathlib.Path.home() / ".file-sorter" / "config.toml"


class ClassificationRule(BaseModel):
    extensions: list[str] = Field(default_factory=list)
    mimetypes: list[str] = Field(default_factory=list)


class PluginConfig(BaseModel):
    enabled: bool = False
    pattern: str = ""


class Settings(BaseSettings):
    """Application configuration loaded from file, env vars and defaults."""

    model_config = SettingsConfigDict(
        env_prefix="FILEFLOW_",
        case_sensitive=False,
        extra="allow",
    )

    fallback_category: Optional[str] = "Other"
    classification: dict[str, ClassificationRule] = Field(default_factory=dict)
    plugins: dict[str, PluginConfig] = Field(default_factory=dict)

    @classmethod
    def load(cls, path: pathlib.Path = DEFAULT_CONFIG_PATH) -> "Settings":
        if not path.exists():
            return cls()
        with path.open("rb") as fp:
            data = tomllib.load(fp)

        env_settings = cls()
        merged = env_settings.model_dump()
        for key, value in data.items():
            if key not in env_settings.model_fields_set:
                merged[key] = value
        return cls(**merged)


def load_config(path: pathlib.Path = DEFAULT_CONFIG_PATH) -> Settings:
    """Load the TOML configuration file and validate it."""
    # Explicit path argument takes precedence
    if path != DEFAULT_CONFIG_PATH:
        cfg = Settings.load(path)
    else:
        cfg_path = path
        # Environment variable to override location
        env = os.getenv("FILEFLOW_CONFIG")
        if env:
            cfg_path = pathlib.Path(env).expanduser()
        elif not cfg_path.exists():
            local = pathlib.Path.cwd() / "config.toml"
            if local.exists():
                cfg_path = local
        cfg = Settings.load(cfg_path)

    if not cfg.classification:
        cfg.classification = {
            k: ClassificationRule(**v) if not isinstance(v, ClassificationRule) else v
            for k, v in DEFAULT_RULES.items()
        }
    return cfg


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
