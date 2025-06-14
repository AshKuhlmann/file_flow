import importlib
import pkgutil
import pathlib
from typing import Dict, Any, Optional, List, Union

import sorter.plugins
from sorter.plugins.base import RenamerPlugin
from .config import Settings


class PluginManager:
    def __init__(self, config: Union[Dict[str, Any], Settings]):
        if isinstance(config, Settings):
            self.plugin_config = {
                name: cfg.model_dump() if hasattr(cfg, "model_dump") else cfg
                for name, cfg in config.plugins.items()
            }
        else:
            self.plugin_config = config.get("plugins", {})
        self.renamer_plugins: List[RenamerPlugin] = self._load_plugins()

    def _load_plugins(self) -> List[RenamerPlugin]:
        """Dynamically loads all plugins that inherit from RenamerPlugin."""
        loaded: List[RenamerPlugin] = []
        for finder, name, ispkg in pkgutil.iter_modules(sorter.plugins.__path__):
            if name == "base":
                continue
            try:
                module = importlib.import_module(f"sorter.plugins.{name}")
            except Exception:  # pragma: no cover - optional plugin deps missing
                continue
            if hasattr(module, "Plugin"):
                plugin_config = self.plugin_config.get(name, {})
                plugin_instance = module.Plugin(plugin_config)
                if (
                    isinstance(plugin_instance, RenamerPlugin)
                    and plugin_instance.enabled
                ):
                    loaded.append(plugin_instance)
        return loaded

    def rename_with_plugin(self, source_path: pathlib.Path) -> Optional[str]:
        """Tries to rename a file using the first successful plugin."""
        for plugin in self.renamer_plugins:
            new_stem = plugin.rename(source_path)
            if new_stem:
                return new_stem
        return None
