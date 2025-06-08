import json
import importlib
import pytest
from sorter import rollback

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
        rollback(log, strict=True)


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

    rollback(log, strict=False)
    assert src.exists() and src.read_text() == "y"
    assert not dst.exists()
