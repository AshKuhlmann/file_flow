import sys
import types
import importlib.util
import pathlib


def _load_module(name: str, path: pathlib.Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    sys.modules[name] = module
    if "." in name:
        pkg, attr = name.rsplit(".", 1)
        parent = sys.modules.setdefault(pkg, types.ModuleType(pkg))
        setattr(parent, attr, module)
    return module


# Load plugin_manager and RenamerPlugin without executing sorter.__init__
ROOT = pathlib.Path(__file__).resolve().parents[1]
_sorter = types.ModuleType("sorter")
_sorter.__path__ = [str(ROOT / "sorter")]
sys.modules.setdefault("sorter", _sorter)

_plugins_pkg = types.ModuleType("sorter.plugins")
_plugins_pkg.__path__ = [str(ROOT / "sorter" / "plugins")]
sys.modules.setdefault("sorter.plugins", _plugins_pkg)
setattr(_sorter, "plugins", _plugins_pkg)

RenamerPlugin = _load_module(
    "sorter.plugins.base",
    ROOT / "sorter" / "plugins" / "base.py",
).RenamerPlugin
PluginManager = _load_module(
    "sorter.plugin_manager",
    ROOT / "sorter" / "plugin_manager.py",
).PluginManager


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
