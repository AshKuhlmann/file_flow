from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Dict, List, Optional
from pathlib import Path


class Settings(BaseSettings):
    """Defines the application's configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="FILEFLOW_",
        case_sensitive=False,
    )

    source_dir: Optional[Path] = Field(
        None, description="Default source directory to scan."
    )
    destination_dir: Optional[Path] = Field(
        None, description="Default destination for sorted files."
    )
    log_file: Optional[Path] = Field(None, description="Path to write logs to.")
    dry_run: bool = False

    rules: Dict[str, List[str]] = Field(default_factory=dict)


# Instantiate a single settings object for the app to import
# Explicitly pass defaults so mypy recognizes the provided values.
settings = Settings(
    source_dir=None,
    destination_dir=None,
    log_file=None,
    dry_run=False,
)
