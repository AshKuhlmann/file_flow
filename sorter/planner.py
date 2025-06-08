from __future__ import annotations

import pathlib
from typing import Sequence

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
    """Return mapping of source files to destination paths.

    This performs scanning, classification and plugin-based renaming so that
    both the CLI and GUI can share identical logic.
    """

    config = load_config()
    plugin_manager = PluginManager(config)
    files = scan_paths(list(dirs))

    mapping: list[tuple[pathlib.Path, pathlib.Path]] = []
    for f in files:
        category = classify_file(f) or "Unsorted"
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
