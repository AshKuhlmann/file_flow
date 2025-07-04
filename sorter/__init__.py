"""Public API for the file-sorter package.

This module used to eagerly import all submodules which required a long list of
optional third-party packages. In lightweight environments these imports would
fail and make ``import sorter`` unusable. To avoid that, we now lazily load the
needed objects on first access.
"""

from importlib import import_module
from typing import Any, Dict, Tuple

__version__ = "1.0.0"

_EXPORTS: Dict[str, Tuple[str, str]] = {
    "scan_paths": ("scanner", "scan_paths"),
    "find_duplicates": ("dupes", "find_duplicates"),
    "classify": ("classifier", "classify"),
    "classify_file": ("classifier", "classify_file"),
    "load_config": ("config", "load_config"),
    "get_config": ("config", "get_config"),
    "get_rules": ("config", "get_rules"),
    "Settings": ("config", "Settings"),
    "PluginManager": ("plugin_manager", "PluginManager"),
    "build_report": ("reporter", "build_report"),
    "ReviewQueue": ("review", "ReviewQueue"),
    "generate_name": ("renamer", "generate_name"),
    "Mover": ("mover", "Mover"),
    "move_with_log": ("mover", "move_with_log"),
    "plan_moves": ("planner", "plan_moves"),
    "Planner": ("planner", "Planner"),
    "rollback": ("rollback", "rollback"),
    "build_dashboard": ("stats", "build_dashboard"),
    "main": ("cli", "main"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr = _EXPORTS[name]
    module = import_module(f".{module_name}", __name__)
    value = getattr(module, attr)
    globals()[name] = value
    return value


__all__ = list(_EXPORTS)

__all__ = [
    "scan_paths",
    "classify",
    "classify_file",
    "load_config",
    "get_config",
    "get_rules",
    "Settings",
    "PluginManager",
    "build_report",
    "ReviewQueue",
    "generate_name",
    "Mover",
    "move_with_log",
    "plan_moves",
    "Planner",
    "find_duplicates",
    "rollback",
    "build_dashboard",
    "main",
    "__version__",
]
