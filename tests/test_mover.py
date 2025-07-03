from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from sorter.mover import Mover, move_with_log


@patch("shutil.move")
@patch("pathlib.Path.exists", return_value=False)
@patch("pathlib.Path.mkdir")
@patch("sorter.mover.sha256sum", return_value="deadbeef")
@patch("pathlib.Path.stat")
def test_move_with_log_mocked(
    mock_stat, mock_sha256, mock_mkdir, mock_exists, mock_move
):
    """move_with_log should create directories and call shutil.move."""
    fake_stat = MagicMock(st_size=3)
    mock_stat.return_value = fake_stat
    m_open = mock_open()
    with patch("pathlib.Path.open", m_open):
        src = Path("/tmp/a.txt")
        dst = Path("/tmp/out/a.txt")
        log_path = Path("/tmp/log.jsonl")
        result = move_with_log([(src, dst)], show_progress=False, log_path=log_path)

    mock_mkdir.assert_called_with(parents=True, exist_ok=True)
    mock_move.assert_called_once_with(src, dst)
    assert result == log_path


@patch("shutil.move")
@patch("pathlib.Path.mkdir")
def test_mover_move_file(mock_mkdir, mock_move, tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("x")
    mover = Mover(tmp_path, tmp_path / "dest")
    mover.move_file(src, "Docs", new_name="b.txt")
    target_dir = tmp_path / "dest" / "Docs"
    mock_mkdir.assert_called_with(parents=True, exist_ok=True)
    mock_move.assert_called_with(str(src), str(target_dir / "b.txt"))


@patch("shutil.move")
@patch("pathlib.Path.mkdir")
def test_mover_dry_run(mock_mkdir, mock_move, tmp_path):
    src = tmp_path / "c.txt"
    src.write_text("x")
    mover = Mover(tmp_path, tmp_path / "dest", dry_run=True)
    mover.move_file(src, "Docs")
    mock_mkdir.assert_not_called()
    mock_move.assert_not_called()
