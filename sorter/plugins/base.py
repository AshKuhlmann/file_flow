import pathlib
from typing import Dict, Any, Optional


class RenamerPlugin:
    """Base class for all renamer plugins."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", False)
        self.pattern = config.get("pattern", "")

    def rename(self, source_path: pathlib.Path) -> Optional[str]:
        """Return a new sanitized stem or ``None`` if plugin does not apply."""
        raise NotImplementedError
