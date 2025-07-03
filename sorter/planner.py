from __future__ import annotations

import pathlib
from typing import Sequence

from pydantic import BaseModel

from .scanner import scan_paths
from .classifier import classify_file
from .renamer import generate_name
from .config import load_config
from .plugin_manager import PluginManager


def plan_moves(
    dirs: Sequence[pathlib.Path],
    dest: pathlib.Path,
    *,
    pattern: str | None = None,
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
    config = load_config()
    plugin_manager = PluginManager(config)
    files = scan_paths(list(dirs))
    classification_rules = {
        k: v.model_dump() if isinstance(v, BaseModel) else v
        for k, v in config.classification.items()
    }

    mapping: list[tuple[pathlib.Path, pathlib.Path]] = []
    for f in files:
        category = classify_file(f, classification_rules) or "Unsorted"
        target_dir = dest / category
        new_stem = plugin_manager.rename_with_plugin(f)
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
