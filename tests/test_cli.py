from conftest import run_cli
from sorter.config import Settings


def test_dupes_command(tmp_path, monkeypatch):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("x")
    b.write_text("x")

    def fake_scan(dirs):
        return [a, b]

    monkeypatch.setattr("sorter.cli.scan_paths", fake_scan)
    monkeypatch.setattr(
        "sorter.cli.find_duplicates",
        lambda files, *, algorithm="sha256": {"deadbeef": [a, b]},
    )
    result = run_cli(["dupes", str(tmp_path)])
    assert result.exit_code == 0
    assert "deadbeef"[:8] in result.stdout


def test_dupes_algorithm_option(tmp_path, monkeypatch):
    calls = {}

    def fake_scan(dirs):
        return []

    def fake_find(files, *, algorithm="sha256", validate_full=True):
        calls["alg"] = algorithm
        return {}

    monkeypatch.setattr("sorter.cli.scan_paths", fake_scan)
    monkeypatch.setattr("sorter.cli.find_duplicates", fake_find)
    result = run_cli(["dupes", str(tmp_path), "--algorithm", "md5"])
    assert result.exit_code == 0
    assert calls["alg"] == "md5"


def test_schedule_command(tmp_path, monkeypatch):
    calls = {}

    def fake_validate(expr):
        calls["validate"] = expr

    def fake_install(cron, *, dirs, dest):
        calls["install"] = (cron, dirs, dest)

    monkeypatch.setattr("sorter.scheduler.validate_cron", fake_validate)
    monkeypatch.setattr("sorter.scheduler.install_job", fake_install)
    dest = tmp_path / "dest"
    result = run_cli(
        [
            "schedule",
            str(tmp_path),
            "--dest",
            str(dest),
            "--cron",
            "5 4 * * *",
        ]
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
    result = run_cli(["stats", str(tmp_path), "--out", str(dest)])
    assert result.exit_code == 0
    assert calls["dash"] == ([log], dest)


def test_scan_smoke(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    result = run_cli(["scan", str(tmp_path)])
    assert result.exit_code == 0
    assert "1" in result.stdout


def test_move_dry_run(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("x")
    monkeypatch.setattr(
        "sorter.cli.build_report", lambda *a, **k: tmp_path / "rep.xlsx"
    )
    dest = tmp_path / "dest"
    result = run_cli(["move", str(tmp_path), "--dest", str(dest)])
    assert result.exit_code == 0
    assert "Dry-run" in result.stdout


def test_move_custom_pattern(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("x")
    monkeypatch.setattr(
        "sorter.cli.build_report", lambda *a, **k: tmp_path / "rep.xlsx"
    )

    captured = {}

    def fake_gen(*args, **kwargs):
        captured["pattern"] = kwargs.get("pattern")
        return tmp_path / "dest" / "a.txt"

    monkeypatch.setattr("sorter.planner.generate_name", fake_gen)
    dest = tmp_path / "dest"
    result = run_cli(
        [
            "move",
            str(tmp_path),
            "--dest",
            str(dest),
            "--pattern",
            "{stem}{ext}",
        ]
    )
    assert result.exit_code == 0
    assert captured["pattern"] == "{stem}{ext}"


def test_stats_no_logs(tmp_path):
    result = run_cli(["stats", str(tmp_path)])
    assert result.exit_code == 1
    assert "No log files found." in result.stdout


def test_move_destination_exists(tmp_path, monkeypatch):
    src = tmp_path / "a.txt"
    src.write_text("x")

    dest_root = tmp_path / "dest"
    conflict = dest_root / "Unsorted" / "a.txt"
    conflict.parent.mkdir(parents=True, exist_ok=True)
    conflict.write_text("y")

    monkeypatch.setattr("sorter.planner.load_config", lambda: Settings())

    class PM:
        def __init__(self, cfg):
            pass

        def rename_with_plugin(self, path):
            return None

    monkeypatch.setattr("sorter.planner.PluginManager", PM)
    monkeypatch.setattr("sorter.planner.classify_file", lambda p, r: None)
    monkeypatch.setattr("sorter.planner.generate_name", lambda *a, **k: conflict)
    monkeypatch.setattr(
        "sorter.cli.build_report", lambda *a, **k: tmp_path / "rep.xlsx"
    )
    result = run_cli(
        [
            "move",
            str(tmp_path),
            "--dest",
            str(dest_root),
            "--no-dry-run",
            "--yes",
        ]
    )
    assert result.exit_code == 1
    assert "destination already exists" in result.stdout


def test_report_format_option(tmp_path, monkeypatch):
    src = tmp_path / "a.txt"
    src.write_text("x")

    monkeypatch.setattr("sorter.planner.scan_paths", lambda dirs: [src])
    monkeypatch.setattr("sorter.planner.classify_file", lambda p, r: None)
    monkeypatch.setattr(
        "sorter.planner.generate_name", lambda *a, **k: tmp_path / "dest" / "a.txt"
    )

    captured = {}

    def fake_build_report(mapping, *, auto_open=False, fmt="xlsx"):
        captured["fmt"] = fmt
        return tmp_path / f"rep.{fmt}"

    monkeypatch.setattr("sorter.cli.build_report", fake_build_report)
    result = run_cli(["report", str(tmp_path), "--format", "json"])
    assert result.exit_code == 0
    assert captured["fmt"] == "json"


def test_version_option():
    result = run_cli(["--version"])
    assert result.exit_code == 0
    assert "1.0.0" in result.stdout


def test_scan_invalid_directory():
    result = run_cli(["scan", "/nonexistent"])
    assert result.exit_code != 0
    assert "does not exist" in result.stdout


def test_move_invalid_pattern(tmp_path):
    (tmp_path / "file.txt").write_text("x")
    dest = tmp_path / "dest"
    result = run_cli(
        [
            "move",
            str(tmp_path),
            "--dest",
            str(dest),
            "--pattern",
            "{foo}",
            "--no-dry-run",
            "--yes",
        ]
    )
    assert result.exit_code != 0


def test_scan_permission_denied(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "sorter.cli.scan_paths",
        lambda dirs: (_ for _ in ()).throw(PermissionError("denied")),
    )
    result = run_cli(["scan", str(tmp_path)])
    assert result.exit_code == 1


def test_move_permission_denied(monkeypatch, tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("x")
    dest = tmp_path / "dest"
    monkeypatch.setattr(
        "sorter.cli.plan_moves",
        lambda *a, **k: [(f, dest / f.name)],
    )
    monkeypatch.setattr(
        "sorter.cli.build_report",
        lambda *a, **k: tmp_path / "rep.xlsx",
    )
    monkeypatch.setattr(
        "sorter.cli.move_with_log",
        lambda *a, **k: (_ for _ in ()).throw(PermissionError("denied")),
    )
    result = run_cli(
        [
            "move",
            str(tmp_path),
            "--dest",
            str(dest),
            "--no-dry-run",
            "--yes",
        ]
    )
    assert result.exit_code == 1
