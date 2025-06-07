import pathlib
import json
import time

from sorter.stats import build_dashboard


def _make_log(tmp: pathlib.Path) -> pathlib.Path:
    p = tmp / "file-sort-log_1.jsonl"
    rec = {
        "src": "a",
        "dst": "b",
        "sha256": "x",
        "size": 1,
        "epoch": int(time.time()),
    }
    p.write_text("\n".join(json.dumps(rec) for _ in range(3)))
    return p


def test_dashboard(tmp_path: pathlib.Path) -> None:
    log = _make_log(tmp_path)
    html = build_dashboard([log])
    assert html.exists() and "<html" in html.read_text()
