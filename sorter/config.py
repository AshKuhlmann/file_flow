import os
import pathlib
import tomllib
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_CONFIG_PATH = pathlib.Path.home() / ".file-sorter" / "config.toml"
DEFAULT_RULES_PATH = pathlib.Path(__file__).parent.parent / "data" / "default_rules.toml"


def _load_default_rules() -> dict[str, dict[str, list[str]]]:
    """Read the bundled default rules from the TOML data file."""
    try:
        with open(DEFAULT_RULES_PATH, "rb") as f:
            raw = tomllib.load(f)
    except OSError:
        return {}

    ext_map: dict[str, str] = raw.get("ext", {})
    rules: dict[str, dict[str, list[str]]] = {}
    for ext, category in ext_map.items():
        rules.setdefault(category, {"extensions": []})["extensions"].append(ext)
    return rules


DEFAULT_RULES = _load_default_rules()


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
