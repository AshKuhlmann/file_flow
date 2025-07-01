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

def test_partial_rollback_missing_source(tmp_path):
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    dst.write_text("y")
    log = tmp_path / "log.jsonl"
    rec = {"src": str(src), "dst": str(dst), "sha256": "dummy", "size": 1, "epoch": 0}
    log.write_text(json.dumps(rec) + "\n")
    rollback(log, strict=False)
    assert src.exists() and src.read_text() == "y"
    assert not dst.exists()


def test_empty_log_file(tmp_path):
    log = tmp_path / "empty.jsonl"
    log.write_text("")
    rollback(log)


def test_malformed_log_file(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text("not-json")
    with pytest.raises(ValueError):
        rollback(bad)
