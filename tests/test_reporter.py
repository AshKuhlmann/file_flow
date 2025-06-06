import pathlib

import pandas as pd
from sorter import build_report


def _create(tmp: pathlib.Path, name: str, size: int = 10) -> pathlib.Path:
    p = tmp / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x" * size)
    return p


def test_report_content(tmp_path: pathlib.Path) -> None:
    src1 = _create(tmp_path, "a.txt", 3)
    dst1 = tmp_path / "Docs" / "a.txt"
    src2 = _create(tmp_path, "b/b.jpg", 6)
    dst2 = tmp_path / "Pics" / "b.jpg"

    xlsx = build_report([(src1, dst1), (src2, dst2)], dest=tmp_path / "out.xlsx")
    assert xlsx.exists()

    df = pd.read_excel(xlsx)
    assert list(df.columns) == ["old_path", "new_path", "size_bytes", "modified_iso"]
    assert df.shape == (2, 4)
    assert set(df["size_bytes"]) == {3, 6}
