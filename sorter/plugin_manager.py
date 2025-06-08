import importlib
import pkgutil
import pathlib
from typing import Dict, Any, Optional

import sorter.plugins
from sorter.plugins.base import RenamerPlugin


class PluginManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("plugins", {})
        self._plugins = self._load_plugins()

    def _load_plugins(self) -> Dict[str, RenamerPlugin]:
        loaded_plugins = {}
        for finder, name, ispkg in pkgutil.iter_modules(sorter.plugins.__path__):
            if name == "base":
                continue
            module = importlib.import_module(f"sorter.plugins.{name}")
            plugin_config = self.config.get(name, {})
            if hasattr(module, "Plugin"):
                plugin_instance = module.Plugin(plugin_config)
                if plugin_instance.enabled:
                    loaded_plugins[name] = plugin_instance
        return loaded_plugins

    def rename_with_plugin(self, source_path: pathlib.Path) -> Optional[pathlib.Path]:
        for plugin in self._plugins.values():
            new_name = plugin.rename(source_path)
            if new_name:
                return new_name
        return None
