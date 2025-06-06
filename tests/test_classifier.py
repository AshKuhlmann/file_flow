from sorter import classify


def test_extension_lookup(tmp_path):
    f = tmp_path / "movie.mp4"
    f.write_bytes(b"dummy")
    assert classify(f) == "Videos"


def test_case_insensitive(tmp_path):
    f = tmp_path / "PIC.JPG"
    f.write_bytes(b"dummy")
    assert classify(f) == "Pictures"


def test_magic_fallback(monkeypatch, tmp_path):
    f = tmp_path / "mystery.bin"
    f.write_bytes(b"dummy")

    # Force libmagic path without extension
    def fake_from_file(_: str, mime: bool = False):
        return "audio/wav" if mime else "WAVE audio"

    monkeypatch.setattr("magic.from_file", fake_from_file)
    assert classify(f) == "Audio"
