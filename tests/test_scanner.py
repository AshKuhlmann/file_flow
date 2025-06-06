import pathlib
import socket

from sorter import scan_paths


def _create_hidden(p: pathlib.Path):
    hidden = p / ".hidden"
    hidden.touch()
    return hidden


def test_scan_basic(tmp_path):
    root = tmp_path / "proj"
    files = [
        root / "a.txt",
        root / "b" / "c.md",
        root / "b" / "d" / "e.jpg",
    ]
    for f in files:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x")

    # Add a socket to ensure it’s ignored
    sock_path = root / "mysock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.bind(str(sock_path))

    result = scan_paths([root])
    assert sorted(result) == sorted(map(pathlib.Path, files))


def test_skip_hidden(tmp_path):
    root = tmp_path / "proj"
    visible = root / "v.dat"
    visible.parent.mkdir(parents=True)
    visible.write_text("ok")
    hidden = _create_hidden(root)
    found = scan_paths([root], skip_hidden=True)
    assert hidden not in found and visible in found


def test_follow_symlinks(tmp_path):
    root = tmp_path / "r"
    target = root / "data.txt"
    target.parent.mkdir(parents=True)
    target.write_text("z")
    symlink = root / "link"
    symlink.symlink_to(target)
    out1 = scan_paths([root], follow_symlinks=False)
    out2 = scan_paths([root], follow_symlinks=True)
    assert symlink not in out1 and target in out1
    assert target in out2  # real file always present
