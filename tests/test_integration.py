import pathlib
import os
import datetime as _dt

from tests.conftest import run_cli


# Helper function to create dummy files


def create_dummy_file(path: pathlib.Path, content: str = "dummy content"):
    """Creates a dummy file with some content and fixed modification time."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    ts = int(_dt.datetime(2025, 6, 30).timestamp())
    os.utime(path, (ts, ts))


def test_move_command_dry_run(tmp_path):
    """Tests the 'move' command with --dry-run to ensure no files are actually moved."""
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "destination"
    create_dummy_file(source_dir / "test_file.txt")

    result = run_cli(["move", str(source_dir), "--dest", str(dest_dir), "--dry-run"])

    assert result.exit_code == 0
    assert "Dry-run complete" in result.stdout
    assert (source_dir / "test_file.txt").exists()
    assert not (dest_dir / "Unsorted" / "test_file.txt").exists()


def test_move_command_with_classification(tmp_path):
    """Tests the 'move' command to ensure files are classified and moved to
    the correct subdirectories."""
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "destination"
    create_dummy_file(source_dir / "image.jpg")
    create_dummy_file(source_dir / "document.pdf")

    result = run_cli([
        "move",
        str(source_dir),
        "--dest",
        str(dest_dir),
        "--no-dry-run",
        "--yes",
    ])

    assert result.exit_code == 0
    assert not (source_dir / "image.jpg").exists()
    assert not (source_dir / "document.pdf").exists()
    assert (
        dest_dir / "Pictures" / f"{source_dir.name}_2025-06-30_image.jpg"
    ).exists()
    assert (
        dest_dir / "Documents" / f"{source_dir.name}_2025-06-30_document.pdf"
    ).exists()


def test_dupes_command(tmp_path):
    """Tests the 'dupes' command to ensure it correctly identifies duplicate files."""
    source_dir = tmp_path / "source"
    create_dummy_file(source_dir / "file1.txt", "same content")
    create_dummy_file(source_dir / "file2.txt", "same content")
    create_dummy_file(source_dir / "file3.txt", "different content")

    result = run_cli(["dupes", str(source_dir)])

    assert result.exit_code == 0
    assert "Found group with hash" in result.stdout
    assert "file1.txt" in result.stdout
    assert "file2.txt" in result.stdout
    assert "file3.txt" not in result.stdout


def test_report_command(tmp_path):
    """Tests the 'report' command to ensure it generates a report of proposed moves."""
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "destination"
    create_dummy_file(source_dir / "report_file.txt")

    result = run_cli(["report", str(source_dir), "--dest", str(dest_dir)])

    assert result.exit_code == 0
    assert "Report ready" in result.stdout
    report_file = next(pathlib.Path.cwd().glob("file-sort-report_*.xlsx"))
    assert report_file.exists()
    report_file.unlink()  # Clean up the created report


def test_undo_command(tmp_path):
    """Tests the 'undo' command to ensure it can roll back a move operation."""
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "destination"
    test_file = source_dir / "undo_test.txt"
    create_dummy_file(test_file)

    # Remove any existing logs to avoid picking up old entries
    for lf in pathlib.Path.cwd().glob("file-sort-log_*.jsonl"):
        lf.unlink()

    # First, move the file
    result_move = run_cli([
        "move",
        str(source_dir),
        "--dest",
        str(dest_dir),
        "--no-dry-run",
        "--yes",
    ])
    assert result_move.exit_code == 0

    # Find the log file
    log_file = next(pathlib.Path.cwd().glob("file-sort-log_*.jsonl"))

    # Now, undo the move
    result_undo = run_cli(["undo", str(log_file)])
    assert result_undo.exit_code == 0
    assert "Rollback complete" in result_undo.stdout
    assert test_file.exists()

    # Clean up the log file
    log_file.unlink()


def test_move_with_custom_pattern(tmp_path):
    """Tests the 'move' command with a custom naming pattern."""
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "destination"
    create_dummy_file(source_dir / "pattern_test.txt")

    pattern = "{stem}_{date}{ext}"
    result = run_cli([
        "move",
        str(source_dir),
        "--dest",
        str(dest_dir),
        "--pattern",
        pattern,
        "--no-dry-run",
        "--yes",
    ])

    assert result.exit_code == 0
    moved_file = dest_dir / "Documents" / "pattern-test_2025-06-30.txt"
    assert moved_file.exists()
