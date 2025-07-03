import pathlib
import json
import time
import importlib
import sys
import builtins
import pytest

import sorter.stats as stats


def _make_log(tmp: pathlib.Path) -> pathlib.Path:
    p = tmp / "file-sort-log_1.jsonl"
    rec = {
        "src": "a",
        "dst": "b",
        "sha256": "x",
        "size": 1,
        "epoch": int(time.time()),
    }
    p.write_text("\n".join(json.dumps(rec) for _ in range(3)))
    return p


def test_dashboard(tmp_path: pathlib.Path) -> None:
    log = _make_log(tmp_path)
    html = stats.build_dashboard([log])
    assert html.exists() and "<html" in html.read_text()


def test_empty_dashboard(tmp_path: pathlib.Path) -> None:
    empty_log = tmp_path / "empty.jsonl"
    empty_log.write_text("")
    with pytest.raises(ValueError):
        stats.build_dashboard([empty_log])


def test_dashboard_missing_matplotlib(tmp_path: pathlib.Path, monkeypatch) -> None:
    monkeypatch.delitem(sys.modules, "sorter.stats", raising=False)
    monkeypatch.delitem(sys.modules, "matplotlib", raising=False)
    monkeypatch.delitem(sys.modules, "matplotlib.pyplot", raising=False)

    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("matplotlib"):
            raise ImportError
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    module = importlib.import_module("sorter.stats")
    importlib.reload(module)
    stats_module = module

    log = _make_log(tmp_path)
    with pytest.raises(ModuleNotFoundError):
        stats_module.build_dashboard([log])
