import pathlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sorter import scan_paths


def setup_tree(tmp_path, n=10_000):
    base = tmp_path / "data"
    for i in range(n):
        p = base / f"file_{i}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    return base


def test_scan_speed(benchmark, tmp_path):
    root = setup_tree(tmp_path)
    benchmark(lambda: scan_paths([root]))
