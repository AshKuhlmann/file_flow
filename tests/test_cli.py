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
    monkeypatch.setattr(
        "sorter.cli.build_report", lambda *a, **k: tmp_path / "rep.xlsx"
    )
    dest = tmp_path / "dest"
    runner = CliRunner()
    result = runner.invoke(app, ["move", str(tmp_path), "--dest", str(dest)])
    assert result.exit_code == 0
    assert "Dry-run" in result.stdout


def test_stats_no_logs(tmp_path):
    runner = CliRunner()
    result = runner.invoke(app, ["stats", str(tmp_path)])
    assert result.exit_code == 1
    assert "No log files found." in result.stdout


def test_move_destination_exists(tmp_path, monkeypatch):
    src = tmp_path / "a.txt"
    src.write_text("x")

    dest_root = tmp_path / "dest"
    conflict = dest_root / "Unsorted" / "a.txt"
    conflict.parent.mkdir(parents=True, exist_ok=True)
    conflict.write_text("y")

    monkeypatch.setattr("sorter.cli.load_config", lambda: {})

    class PM:
        def __init__(self, cfg):
            pass

        def rename_with_plugin(self, path):
            return None

    monkeypatch.setattr("sorter.cli.PluginManager", PM)
    monkeypatch.setattr("sorter.cli.classify_file", lambda p: None)
    monkeypatch.setattr("sorter.cli.generate_name", lambda *a, **k: conflict)
    monkeypatch.setattr(
        "sorter.cli.build_report", lambda *a, **k: tmp_path / "rep.xlsx"
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "move",
            str(tmp_path),
            "--dest",
            str(dest_root),
            "--no-dry-run",
            "--yes",
        ],
    )
    assert result.exit_code == 1
    assert "destination already exists" in result.stdout


def test_version_option():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "1.0.0" in result.stdout
