import pathlib
import time

from sorter import ReviewQueue


def _touch(tmp: pathlib.Path, name: str) -> pathlib.Path:
    p = tmp / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x")
    return p


def test_basic_flow(tmp_path):
    now = int(time.time())
    db = tmp_path / "db.sqlite"
    rq = ReviewQueue(db_path=db)

    a = _touch(tmp_path, "a.txt")
    b = _touch(tmp_path, "b/b.txt")

    rq.upsert_files([a, b])
    picks = rq.select_for_review(limit=5, now=now)
    assert set(picks) == {a, b}

    rq.mark_keep(a, now=now)
    # a should be deferred 30 days
    later = rq.select_for_review(limit=5, now=now + 10)
    assert a not in later and b in later


def test_delete_flow(tmp_path):
    rq = ReviewQueue(db_path=tmp_path / "db.sqlite")
    f = _touch(tmp_path, "c.txt")
    rq.upsert_files([f])
    rq.mark_delete(f)
    assert rq.select_for_review(now=int(time.time())) == []
