import json

import pytest

import importlib

rollback_mod = importlib.import_module("sorter.rollback")


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
