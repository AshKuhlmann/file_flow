import json
import sys
import types
import importlib.util
import pathlib


def _load_module(name: str, path: pathlib.Path):
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


ROOT = pathlib.Path(__file__).resolve().parents[1]
_sorter = types.ModuleType("sorter")
_sorter.__path__ = [str(ROOT / "sorter")]
sys.modules.setdefault("sorter", _sorter)

rollback_mod = _load_module("sorter.rollback", ROOT / "sorter" / "rollback.py")

import pytest


def test_checksum_mismatch(tmp_path, monkeypatch):
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    dst.write_text("x")
    log = tmp_path / "log.jsonl"
    rec = {
        "src": str(src),
        "dst": str(dst),
        "sha256": "expected",
        "size": 1,
        "epoch": 0,
    }
    log.write_text(json.dumps(rec) + "\n")

    monkeypatch.setattr(rollback_mod, "_sha256", lambda p: "actual")
    with pytest.raises(ValueError):
        rollback_mod.rollback(log, strict=True)


def test_checksum_mismatch_non_strict(tmp_path, monkeypatch):
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    dst.write_text("y")
    log = tmp_path / "log.jsonl"
    rec = {
        "src": str(src),
        "dst": str(dst),
        "sha256": "expected",
        "size": 1,
        "epoch": 0,
    }
    log.write_text(json.dumps(rec) + "\n")

    monkeypatch.setattr(rollback_mod, "_sha256", lambda p: "actual")

    rollback_mod.rollback(log, strict=False)
    assert src.exists() and src.read_text() == "y"
    assert not dst.exists()
