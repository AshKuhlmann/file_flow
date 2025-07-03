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
    """Create a move plan for files.

    This function scans ``dirs`` for files, classifies each one using the
    configured rules and generates destination paths. Files that don't match any
    rule are placed in an ``Unsorted`` folder.

    Args:
        dirs: Directories to scan for files.
        dest: Root directory where files will be moved.
        pattern: Optional renaming pattern.
        config: Existing settings to use instead of :func:`load_config`.

    Returns:
        A list of ``(source, destination)`` tuples representing the move plan.
    """
    cfg = config or load_config()
    # This is a dictionary comprehension, a concise way to build a dict. It's
    # equivalent to a for loop that populates ``classification_rules``.
    classification_rules = {
        k: v.dict() if isinstance(v, BaseModel) else v
        for k, v in cfg.classification.items()
    }
    planner = Planner(classification_rules, cfg)
    return planner.plan(dirs, dest, pattern=pattern)
