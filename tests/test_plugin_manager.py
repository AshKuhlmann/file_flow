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


def test_real_plugins_loading(monkeypatch):
    cfg = {
        "plugins": {
            "exif_renamer": {"enabled": True},
            "id3_renamer": {"enabled": True},
        }
    }
    monkeypatch.setattr(
        "sorter.plugins.exif_renamer.Plugin.rename",
        lambda self, p: "exif",
    )
    monkeypatch.setattr(
        "sorter.plugins.id3_renamer.Plugin.rename",
        lambda self, p: "id3",
    )
    manager = PluginManager(cfg)
    modules = [
        p.__class__.__module__.split(".")[-1]
        for p in manager.renamer_plugins
    ]
    assert modules == ["exif_renamer", "id3_renamer"]
    assert manager.rename_with_plugin(pathlib.Path("file.jpg")) == "exif"


def test_multiple_plugins_order(monkeypatch):
    cfg = {
        "plugins": {
            "exif_renamer": {"enabled": True},
            "id3_renamer": {"enabled": True},
        }
    }
    calls = []

    def exif_rename(self, p):
        calls.append("exif")
        return None

    def id3_rename(self, p):
        calls.append("id3")
        return "done"

    monkeypatch.setattr("sorter.plugins.exif_renamer.Plugin.rename", exif_rename)
    monkeypatch.setattr("sorter.plugins.id3_renamer.Plugin.rename", id3_rename)
    manager = PluginManager(cfg)
    manager.rename_with_plugin(pathlib.Path("song.mp3"))
    assert calls == ["exif", "id3"]
