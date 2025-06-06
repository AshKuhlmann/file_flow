from typer.testing import CliRunner
from sorter import app

runner = CliRunner()


def test_scan_smoke(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    result = runner.invoke(app, ["scan", str(tmp_path)])
    assert result.exit_code == 0
    assert "Total 1" in result.stdout


def test_move_dry_run(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    (src / "b.txt").write_text("hi")
    result = runner.invoke(app, ["move", str(src), "--dest", str(dest)])
    assert result.exit_code == 0
    assert (src / "b.txt").exists()
    assert "Dry-run complete" in result.stdout
