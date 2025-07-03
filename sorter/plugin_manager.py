import importlib.metadata
import pathlib
import logging
from typing import Any, Dict, List, Optional, Union

from sorter.plugins.base import RenamerPlugin
from .config import Settings


log = logging.getLogger(__name__)


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
        """Discover and instantiate enabled renamer plugins."""
        loaded: List[RenamerPlugin] = []

        try:
            eps = list(importlib.metadata.entry_points(group="file_flow.renamers"))
        except TypeError:  # pragma: no cover - older Python
            all_eps = importlib.metadata.entry_points()
            if isinstance(all_eps, dict):
                eps = [
                    ep
                    for group_eps in all_eps.values()
                    for ep in group_eps
                    if getattr(ep, "group", "") == "file_flow.renamers"
                ]
            else:
                eps = [
                    ep
                    for ep in all_eps
                    if getattr(ep, "group", "") == "file_flow.renamers"
                ]

        for ep in eps:
            name = ep.name
            log.debug("checking plugin: %s", name)
            cfg = self.plugin_config.get(name, {})
            try:
                plugin_class = ep.load()
                plugin_instance = plugin_class(cfg)
            except Exception as exc:  # pragma: no cover - plugin error isolation
                log.error("failed to load plugin %s: %s", name, exc)
                continue

            if not isinstance(plugin_instance, RenamerPlugin):
                log.debug("plugin %s is not a RenamerPlugin", name)
                continue

            if not plugin_instance.enabled:
                log.debug("plugin %s disabled", name)
                continue

            loaded.append(plugin_instance)
            log.debug("loaded plugin: %s", name)

        return loaded

    def rename_with_plugin(self, source_path: pathlib.Path) -> Optional[str]:
        """Tries to rename a file using the first successful plugin."""
        for plugin in self.renamer_plugins:
            plugin_name = plugin.name
            log.debug("trying plugin %s for %s", plugin_name, source_path)
            try:
                new_stem = plugin.rename(source_path)
            except Exception as exc:  # pragma: no cover - plugin error isolation
                log.error("plugin %s failed on %s: %s", plugin_name, source_path, exc)
                continue
            if new_stem:
                log.debug(
                    "plugin %s renamed %s -> %s",
                    plugin_name,
                    source_path,
                    new_stem,
                )
                return new_stem
        return None
