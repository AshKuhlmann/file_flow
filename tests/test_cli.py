from typer.testing import CliRunner

from sorter import app


def test_dupes_command(tmp_path, monkeypatch):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("x")
    b.write_text("x")

    def fake_scan(dirs):
        return [a, b]

    monkeypatch.setattr("sorter.cli.scan_paths", fake_scan)
    monkeypatch.setattr(
        "sorter.cli.find_duplicates", lambda files: {"deadbeef": [a, b]}
    )

    runner = CliRunner()
    result = runner.invoke(app, ["dupes", str(tmp_path)])
    assert result.exit_code == 0
    assert "deadbeef"[:8] in result.stdout


def test_schedule_command(tmp_path, monkeypatch):
    calls = {}

    def fake_validate(expr):
        calls["validate"] = expr

    def fake_install(cron, *, dirs, dest):
        calls["install"] = (cron, dirs, dest)

    monkeypatch.setattr("sorter.scheduler.validate_cron", fake_validate)
    monkeypatch.setattr("sorter.scheduler.install_job", fake_install)

    runner = CliRunner()
    dest = tmp_path / "dest"
    result = runner.invoke(
        app,
        ["schedule", str(tmp_path), "--dest", str(dest), "--cron", "5 4 * * *"],
    )
    assert result.exit_code == 0
    assert calls["validate"] == "5 4 * * *"
    assert calls["install"] == ("5 4 * * *", [tmp_path], dest)


def test_stats_command(tmp_path, monkeypatch):
    log = tmp_path / "file-sort-log_1.jsonl"
    log.write_text("{}\n")
    dest = tmp_path / "out.html"
    calls = {}

    def fake_dash(logs, dest):
        calls["dash"] = (logs, dest)
        return dest

    monkeypatch.setattr("sorter.stats.build_dashboard", fake_dash)

    runner = CliRunner()
    result = runner.invoke(app, ["stats", str(tmp_path), "--out", str(dest)])
    assert result.exit_code == 0
    assert calls["dash"] == ([log], dest)


def test_scan_smoke(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    runner = CliRunner()
    result = runner.invoke(app, ["scan", str(tmp_path)])
    assert result.exit_code == 0
    assert "1" in result.stdout


def test_move_dry_run(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("x")
    monkeypatch.setattr("sorter.cli.build_report", lambda *a, **k: tmp_path / "rep.xlsx")
    dest = tmp_path / "dest"
    runner = CliRunner()
    result = runner.invoke(app, ["move", str(tmp_path), "--dest", str(dest)])
    assert result.exit_code == 0
    assert "Dry-run" in result.stdout
