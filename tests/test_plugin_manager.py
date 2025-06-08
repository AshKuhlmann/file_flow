import pathlib
import sys
import types

from sorter.plugin_manager import PluginManager
from sorter.plugins.base import RenamerPlugin


def test_plugin_loading_and_rename(monkeypatch):
    unique_stem = "unique_stem"
    calls = []

    module = types.ModuleType("sorter.plugins.temp_plugin")

    class Plugin(RenamerPlugin):
        def rename(self, source_path: pathlib.Path):
            calls.append(source_path)
            return unique_stem

    module.Plugin = Plugin
    monkeypatch.setitem(sys.modules, "sorter.plugins.temp_plugin", module)

    def fake_iter_modules(_path):
        yield None, "temp_plugin", False

    monkeypatch.setattr("sorter.plugin_manager.pkgutil.iter_modules", fake_iter_modules)

    manager = PluginManager({"plugins": {"temp_plugin": {"enabled": True}}})
    assert len(manager.renamer_plugins) == 1
    assert isinstance(manager.renamer_plugins[0], Plugin)

    result = manager.rename_with_plugin(pathlib.Path("file.txt"))
    assert result == unique_stem
    assert len(calls) == 1

    disabled = PluginManager({"plugins": {"temp_plugin": {"enabled": False}}})
    assert disabled.renamer_plugins == []
