import pathlib

from sorter.dupes import find_duplicates, delete_older


def _make(tmp: pathlib.Path, name: str, data: bytes) -> pathlib.Path:
    p = tmp / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def test_duplicate_detection(tmp_path):
    a = _make(tmp_path, "a.txt", b"same")
    b = _make(tmp_path, "b/b.txt", b"same")
    c = _make(tmp_path, "c.txt", b"diff")

    groups = find_duplicates([a, b, c])
    assert len(groups) == 1
    only = next(iter(groups.values()))
    assert set(only) == {a, b}


def test_duplicate_detection_md5(tmp_path):
    a = _make(tmp_path, "a.txt", b"same")
    b = _make(tmp_path, "b.txt", b"same")

    groups = find_duplicates([a, b], algorithm="md5")
    assert len(groups) == 1
    only = next(iter(groups.values()))
    assert set(only) == {a, b}


def test_delete_older(tmp_path):
    a = _make(tmp_path, "old.txt", b"x")
    b = _make(tmp_path, "new.txt", b"x")
    # make 'a' older
    a.touch()
    import os

    os.utime(a, (1_000_000_000, 1_000_000_000))

    deleted = delete_older([a, b])
    assert deleted == [a] and not a.exists() and b.exists()
