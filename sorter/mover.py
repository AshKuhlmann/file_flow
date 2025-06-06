from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import time
from typing import Any, Final, Sequence, TYPE_CHECKING

# This block handles the optional import of the 'rich' library for progress bars.
# If 'rich' is not installed, it provides a mock Progress class so the program
# can run without errors, albeit without visual progress updates.
if TYPE_CHECKING:  # pragma: no cover - typing support
    from rich.progress import Progress
else:
    class Progress:
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...
        def add_task(self, *args: Any, **kwargs: Any) -> Any: ...
        def update(self, *args: Any, **kwargs: Any) -> Any: ...
        def stop(self) -> None: ...


_HAS_RICH = False
_RealProgress: type[Progress] | None
try:
    from rich.progress import Progress as _RealProgress

    _HAS_RICH = True
except ModuleNotFoundError:
    _RealProgress = None

# Define a constant for the buffer size (1 MiB) used when hashing files.
# This avoids reading the entire file into memory at once.
_BUF: Final = 1 << 20  # 1 MiB copy buffer


def _sha256(path: pathlib.Path) -> str:
    """
    Calculates the SHA256 hash of a file.

    Args:
        path: The path to the file.

    Returns:
        The hex digest of the file's SHA256 hash.
    """
    h = hashlib.sha256()
    with path.open("rb") as fp:
        while chunk := fp.read(_BUF):
            h.update(chunk)
    return h.hexdigest()


def move_with_log(
    mapping: Sequence[tuple[pathlib.Path, pathlib.Path]],
    *,
    log_path: pathlib.Path | None = None,
    show_progress: bool = True,
) -> pathlib.Path:
    """
    Moves a sequence of files, logging each operation to a JSONL file.

    This function ensures data integrity by calculating a SHA256 checksum before
    moving the file. It logs the source, destination, checksum, size, and
    timestamp for each move, which can be used for rollbacks or auditing.

    Args:
        mapping: A sequence of (source_path, destination_path) tuples.
        log_path: An optional path for the log file. If not provided, a default
                  timestamped log is created in the current directory.
        show_progress: Whether to display a progress bar if 'rich' is installed.

    Returns:
        The absolute path to the generated log file.

    Raises:
        FileExistsError: If any of the destination paths already exist.
    """
    if log_path is None:
        log_path = pathlib.Path.cwd() / f"file-sort-log_{int(time.time())}.jsonl"
    log_path = log_path.expanduser().resolve()

    # Pre-flight check to prevent overwriting existing files.
    if any(dst.exists() for _, dst in mapping):
        raise FileExistsError("One or more destination paths already exist.")

    # Initialize the progress bar if 'rich' is available and requested.
    progress: Progress | None = None
    task_id = None
    if _HAS_RICH and show_progress:
        assert _RealProgress is not None
        progress = _RealProgress()
        task_id = progress.add_task("Moving files...", total=len(mapping))

    # Open the log file and process each file move.
    with log_path.open("w", encoding="utf-8") as logfp:
        for src, dst in mapping:
            # Ensure the destination directory exists.
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Calculate checksum for integrity check.
            checksum = _sha256(src)

            # Write a detailed log entry in JSONL format before moving.
            log_entry = {
                "src": src.as_posix(),
                "dst": dst.as_posix(),
                "sha256": checksum,
                "size": src.stat().st_size,
                "epoch": int(time.time()),
            }
            logfp.write(json.dumps(log_entry) + "\n")

            # Perform the file move.
            shutil.move(src, dst)

            # Update the progress bar.
            if progress and task_id is not None:
                progress.update(task_id, advance=1)

    # Stop the progress bar once all files are moved.
    if progress:
        progress.stop()

    return log_path

__all__ = ["move_with_log"]
