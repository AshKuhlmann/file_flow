from __future__ import annotations

import pathlib
from typing import Sequence, Dict, Any

from pydantic import BaseModel

from .scanner import scan_paths
from .classifier import classify_file
from .renamer import generate_name
from .config import load_config, Settings
from .plugin_manager import PluginManager


class Planner:
    """Plan file moves based on classification ``rules``."""

    def __init__(self, rules: Dict[str, Any], config: Settings) -> None:
        self.rules = rules
        self._plugin_manager = PluginManager(config)

    def plan(
        self,
        dirs: Sequence[pathlib.Path],
        dest: pathlib.Path,
        *,
        pattern: str | None = None,
    ) -> list[tuple[pathlib.Path, pathlib.Path]]:
        files = scan_paths(list(dirs))
        mapping: list[tuple[pathlib.Path, pathlib.Path]] = []
        for f in files:
            category = classify_file(f, self.rules) or "Unsorted"
            target_dir = dest / category
            new_stem = self._plugin_manager.rename_with_plugin(f)
            if new_stem:
                temp = f.with_stem(new_stem)
                final_dest = generate_name(
                    temp,
                    target_dir,
                    include_parent=False,
                    date_from_mtime=False,
                    pattern=pattern,
                )
            else:
                final_dest = generate_name(f, target_dir, pattern=pattern)
            mapping.append((f, final_dest))
        return mapping


def plan_moves(
    dirs: Sequence[pathlib.Path],
    dest: pathlib.Path,
    *,
    pattern: str | None = None,
    config: Settings | None = None,
) -> list[tuple[pathlib.Path, pathlib.Path]]:
    """Generate destination paths for all files found in ``dirs``.

    The function scans the provided directories, classifies each file and
    optionally renames it using installed plugins. The resulting mapping can be
    used by both the CLI and GUI interfaces to carry out move operations.

    Args:
        dirs: A sequence of directories to scan for files.
        dest: The root directory where files will be moved.
        pattern: Optional naming pattern overriding the default renamer
            behaviour.

    Returns:
        A list of ``(source, destination)`` path tuples representing where each
        file should be moved.

    Raises:
        ValueError: If ``dest`` does not represent a valid directory.
    """
    cfg = config or load_config()
    classification_rules = {
        k: v.model_dump() if isinstance(v, BaseModel) else v
        for k, v in cfg.classification.items()
    }
    planner = Planner(classification_rules, cfg)
    return planner.plan(dirs, dest, pattern=pattern)
