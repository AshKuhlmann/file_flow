import pathlib
from typing import Dict, Any, Optional


class RenamerPlugin:
    """Base class for renamer plugins."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", False)

    def rename(self, source_path: pathlib.Path) -> Optional[pathlib.Path]:
        """Return a new Path or None if plugin does not apply."""
        raise NotImplementedError
