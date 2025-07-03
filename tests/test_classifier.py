import pytest
from sorter import classify
from sorter.classifier import classify_file
from sorter.config import DEFAULT_RULES


@pytest.fixture
def rules():
    return {
        "Documents": {"extensions": [".pdf"]},
        "Images": {"extensions": [".jpg", ".jpeg"]},
    }


def test_extension_lookup(tmp_path):
    f = tmp_path / "movie.mp4"
    f.write_bytes(b"dummy")
    cfg = {"classification": DEFAULT_RULES}
    assert classify(f, cfg) == "Videos"


def test_case_insensitive(tmp_path):
    f = tmp_path / "PIC.JPG"
    f.write_bytes(b"dummy")
    cfg = {"classification": DEFAULT_RULES}
    assert classify(f, cfg) == "Images"


def test_magic_fallback(monkeypatch, tmp_path):
    f = tmp_path / "mystery.bin"
    f.write_bytes(b"dummy")

    # Force libmagic path without extension
    def fake_from_file(_: str, mime: bool = False):
        return "audio/wav" if mime else "WAVE audio"

    monkeypatch.setattr("magic.from_file", fake_from_file)
    cfg = {"classification": DEFAULT_RULES}
    assert classify(f, cfg) == "Audio"


def test_document_category(tmp_path):
    f = tmp_path / "report.pdf"
    f.write_bytes(b"dummy")
    cfg = {"classification": DEFAULT_RULES}
    assert classify(f, cfg) == "Documents"


def test_archive_category(tmp_path):
    f = tmp_path / "archive.zip"
    f.write_bytes(b"dummy")
    cfg = {"classification": DEFAULT_RULES}
    assert classify(f, cfg) == "Archives"


def test_script_category(tmp_path):
    f = tmp_path / "run.sh"
    f.write_bytes(b"dummy")
    cfg = {"classification": DEFAULT_RULES}
    assert classify(f, cfg) == "Scripts"


@pytest.mark.parametrize(
    "filename, expected_dest",
    [
        ("document.pdf", "Documents"),
        ("photo.JPG", "Images"),
        ("archive.zip", None),
        ("file_without_extension", None),
        (".hiddenfile", None),
    ],
)
def test_classify_file_edge_cases(tmp_path, rules, filename, expected_dest):
    test_file = tmp_path / filename
    test_file.touch()
    destination = classify_file(test_file, rules)
    assert destination == expected_dest
