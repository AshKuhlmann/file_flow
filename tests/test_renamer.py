import os
import pathlib

from sorter import generate_name


def _touch(tmp: pathlib.Path, name: str, mtime: int | None = None) -> pathlib.Path:
    p = tmp / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x")
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


def test_basic_pattern(tmp_path):
    src = _touch(tmp_path / "in", "Example File.TXT", mtime=946684800)
    dest_dir = tmp_path / "out"
    new_path = generate_name(src, dest_dir)
    assert new_path.parent == dest_dir.resolve()
    assert new_path.name.startswith("in_2000-01-01_example-file")


def test_collision_resolution(tmp_path):
    dest = tmp_path / "out"
    a = _touch(tmp_path / "x", "a.txt")
    n1 = generate_name(a, dest, include_parent=False, date_from_mtime=False)
    dest.mkdir(exist_ok=True)
    (dest / n1.name).write_text("exists")
    n2 = generate_name(a, dest, include_parent=False, date_from_mtime=False)
    assert n2.name.endswith("__2.txt")


def test_case_insensitive_collision(tmp_path):
    dest = tmp_path / "out"
    src = _touch(tmp_path, "UPPER.TXT")
    (dest).mkdir()
    (dest / "upper.txt").write_text("lowercase duplicate")
    result = generate_name(src, dest)
    assert result.name != "upper.txt" and result.name.lower() != "upper.txt"
