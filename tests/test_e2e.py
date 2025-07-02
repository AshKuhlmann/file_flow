import subprocess
from pathlib import Path


def test_cli_sort_e2e(tmp_path: Path) -> None:
    """Run the CLI end-to-end and verify files are moved."""
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "destination"
    source_dir.mkdir()
    (source_dir / "song.mp3").write_text("x")

    result = subprocess.run(
        [
            "python",
            "-m",
            "sorter.cli",
            "move",
            str(source_dir),
            "--dest",
            str(dest_dir),
            "--no-dry-run",
            "--yes",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    audio_dir = dest_dir / "Audio"
    assert audio_dir.exists()
    assert len(list(audio_dir.glob("*.mp3"))) == 1
