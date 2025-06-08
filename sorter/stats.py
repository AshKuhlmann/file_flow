from __future__ import annotations

import json
import pathlib
import io

import pandas as _pd  # type: ignore[import-untyped]


def build_dashboard(
    logs: list[pathlib.Path],
    *,
    dest: pathlib.Path | None = None,
) -> pathlib.Path:
    """Generate HTML dashboard from *logs*; return output path."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as _plt

    rows = []
    for lp in logs:
        for line in lp.read_text().splitlines():
            rec = json.loads(line)
            rows.append(rec)
    df = _pd.DataFrame(rows)
    if df.empty:
        raise ValueError("no data in logs")

    df["epoch"] = _pd.to_datetime(df["epoch"], unit="s")
    df["date"] = df["epoch"].dt.date

    summary: dict[str, str | int] = {
        "files_moved": len(df),
        "total_bytes": int(df["size"].sum()),
        "first_move": str(df["epoch"].min()),
        "last_move": str(df["epoch"].max()),
    }

    by_day = df.groupby("date").size()
    fig = _plt.figure(figsize=(6, 4))
    by_day.plot(kind="bar")
    _plt.xlabel("Date")
    _plt.ylabel("Files moved")
    buf = io.BytesIO()
    _plt.tight_layout()
    fig.savefig(buf, format="png", dpi=150)
    _plt.close(fig)
    img_b64 = buf.getvalue().hex()

    html = f"""
    <html><head><meta charset='utf-8'><title>File-Sorter Stats</title>
    <style>table,th,td{{border:1px solid #ccc;border-collapse:collapse;
    padding:4px}}</style></head><body>
    <h1>File-Sorter Dashboard</h1>
    <h2>Summary</h2><table>
    {''.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in summary.items())}
    </table><h2>Files moved per day</h2>
    <img src="data:image/png;hex,{img_b64}" alt="chart">
    </body></html>
    """

    if dest is None:
        dest = pathlib.Path.cwd() / "dashboard.html"
    dest.write_text(html, encoding="utf-8")
    return dest
