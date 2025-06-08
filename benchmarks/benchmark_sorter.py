import pytest
from sorter import scan_paths

pytest.importorskip("pytest_benchmark")


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
