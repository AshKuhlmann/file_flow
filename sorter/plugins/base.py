from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class RenamerPlugin(ABC):
    """Abstract base class for all renamer plugins."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", False)
        self.pattern = self.config.get("pattern", "")

    @property
    @abstractmethod
    def name(self) -> str:
        """A unique name for the plugin."""

    @abstractmethod
    def rename(self, file_path: Path) -> Optional[str]:
        """Analyze ``file_path`` and return a new filename or ``None``."""

