import magic
from sorter.classifier import classify_file


def test_extension_rule(tmp_path):
    f = tmp_path / "foo.xyz"
    f.write_text("data")
    rules = {"Dest": {"extensions": [".xyz"]}}
    assert classify_file(f, rules) == "Dest"


def test_mimetype_rule(tmp_path, monkeypatch):
    f = tmp_path / "bar.bin"
    f.write_bytes(b"x")
    monkeypatch.setattr(magic, "from_file", lambda *a, **k: "audio/flac")
    rules = {"Music": {"mimetypes": ["audio/flac"]}}
    assert classify_file(f, rules) == "Music"
