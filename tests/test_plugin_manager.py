import pathlib
import sys
import types
import importlib.metadata

from sorter.plugin_manager import PluginManager
from sorter.plugins.base import RenamerPlugin


def test_plugin_loading_and_rename(monkeypatch):
    unique_stem = "unique_stem"
    calls = []

    module = types.ModuleType("sorter.plugins.temp_plugin")

    class TempPlugin(RenamerPlugin):
        @property
        def name(self) -> str:
            return "temp"

        def rename(self, source_path: pathlib.Path):
            calls.append(source_path)
            return unique_stem

    module.TempPlugin = TempPlugin
    monkeypatch.setitem(sys.modules, "sorter.plugins.temp_plugin", module)

    ep = importlib.metadata.EntryPoint(
        name="temp",
        value="sorter.plugins.temp_plugin:TempPlugin",
        group="file_flow.renamers",
    )

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group=None: [ep] if group == "file_flow.renamers" else [],
    )

    manager = PluginManager({"plugins": {"temp": {"enabled": True}}})
    assert len(manager.renamer_plugins) == 1
    assert isinstance(manager.renamer_plugins[0], TempPlugin)

    result = manager.rename_with_plugin(pathlib.Path("file.txt"))
    assert result == unique_stem
    assert len(calls) == 1

    disabled = PluginManager({"plugins": {"temp": {"enabled": False}}})
    assert disabled.renamer_plugins == []


def test_real_plugins_loading(monkeypatch):
    cfg = {
        "plugins": {
            "exif": {"enabled": True},
            "id3": {"enabled": True},
        }
    }
    monkeypatch.setattr(
        "sorter.plugins.exif_renamer.ExifRenamer.rename", lambda self, p: "exif"
    )
    monkeypatch.setattr(
        "sorter.plugins.id3_renamer.Id3Renamer.rename", lambda self, p: "id3"
    )

    ep1 = importlib.metadata.EntryPoint(
        name="exif",
        value="sorter.plugins.exif_renamer:ExifRenamer",
        group="file_flow.renamers",
    )
    ep2 = importlib.metadata.EntryPoint(
        name="id3",
        value="sorter.plugins.id3_renamer:Id3Renamer",
        group="file_flow.renamers",
    )
    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group=None: [ep1, ep2] if group == "file_flow.renamers" else [],
    )

    manager = PluginManager(cfg)
    modules = [p.name for p in manager.renamer_plugins]
    assert modules == ["exif", "id3"]
    assert manager.rename_with_plugin(pathlib.Path("file.jpg")) == "exif"


def test_multiple_plugins_order(monkeypatch):
    cfg = {
        "plugins": {
            "exif": {"enabled": True},
            "id3": {"enabled": True},
        }
    }
    calls = []

    def exif_rename(self, p):
        calls.append("exif")
        return None

    def id3_rename(self, p):
        calls.append("id3")
        return "done"

    monkeypatch.setattr("sorter.plugins.exif_renamer.ExifRenamer.rename", exif_rename)
    monkeypatch.setattr("sorter.plugins.id3_renamer.Id3Renamer.rename", id3_rename)

    ep1 = importlib.metadata.EntryPoint(
        name="exif",
        value="sorter.plugins.exif_renamer:ExifRenamer",
        group="file_flow.renamers",
    )
    ep2 = importlib.metadata.EntryPoint(
        name="id3",
        value="sorter.plugins.id3_renamer:Id3Renamer",
        group="file_flow.renamers",
    )
    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group=None: [ep1, ep2] if group == "file_flow.renamers" else [],
    )

    manager = PluginManager(cfg)
    manager.rename_with_plugin(pathlib.Path("song.mp3"))
    assert calls == ["exif", "id3"]
