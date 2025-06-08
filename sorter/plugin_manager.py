import importlib
import pkgutil
import pathlib
from typing import Dict, Any, Optional, List

import sorter.plugins
from sorter.plugins.base import RenamerPlugin


class PluginManager:
    def __init__(self, config: Dict[str, Any]):
        self.plugin_config = config.get("plugins", {})
        self.renamer_plugins: List[RenamerPlugin] = self._load_plugins()

    def _load_plugins(self) -> List[RenamerPlugin]:
        """Dynamically load enabled renamer plugins."""
        loaded: List[RenamerPlugin] = []
        for finder, name, ispkg in pkgutil.iter_modules(sorter.plugins.__path__):
            if name == "base":
                continue
            module = importlib.import_module(f"sorter.plugins.{name}")
            if hasattr(module, "Plugin"):
                plugin_config = self.plugin_config.get(name, {})
                plugin_instance = module.Plugin(plugin_config)
                if isinstance(plugin_instance, RenamerPlugin) and plugin_instance.enabled:
                    loaded.append(plugin_instance)
        return loaded

    def rename_with_plugin(self, source_path: pathlib.Path) -> Optional[str]:
        """Try renaming *source_path* with the loaded plugins."""
        for plugin in self.renamer_plugins:
            new_stem = plugin.rename(source_path)
            if new_stem:
                return new_stem
        return None
