import json
import pathlib

from sorter import move_with_log, rollback


def _touch(tmp: pathlib.Path, name: str, data=b"x") -> pathlib.Path:
    p = tmp / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def test_move_and_rollback(tmp_path):
    a = _touch(tmp_path, "in/a.txt", b"abc")
    b = _touch(tmp_path, "in/b.txt", b"def")
    dst_a = tmp_path / "out/a.txt"
    dst_b = tmp_path / "out/b.txt"

    log = move_with_log([(a, dst_a), (b, dst_b)], show_progress=False)
    assert not a.exists() and not b.exists()
    assert dst_a.exists() and dst_b.exists()

    rollback(log, strict=True)
    assert a.exists() and b.exists()
    assert not dst_a.exists() and not dst_b.exists()

    recs = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(recs) == 2 and recs[0]["sha256"].isalnum()
