from __future__ import annotations

import json
import logging
import pathlib
import shutil
import time
from typing import Any, Sequence, TYPE_CHECKING, Callable

from .utils import sha256sum

log = logging.getLogger(__name__)


class Mover:
    """Handles the moving and renaming of files."""

    def __init__(self, source_dir: pathlib.Path, target_dir: pathlib.Path, dry_run: bool = False) -> None:
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.dry_run = dry_run
        self.log = logging.getLogger(__name__)

    def move_file(self, source_path: pathlib.Path, destination_folder: str, new_name: str | None = None) -> None:
        """Move ``source_path`` into ``destination_folder`` optionally renaming it."""

        target_path = self.target_dir / destination_folder
        final_destination = target_path / (new_name or source_path.name)

        self.log.info("Plan: Move '%s' to '%s'", source_path, final_destination)

        if self.dry_run:
            return

        try:
            target_path.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(final_destination))
            self.log.info("Success: Moved '%s' to '%s'", source_path, final_destination)
        except PermissionError:
            self.log.error("Failed to move '%s': Permission denied.", source_path)
        except FileNotFoundError:
            self.log.error("Failed to move '%s': Source file not found.", source_path)
        except Exception as exc:  # pragma: no cover - unexpected
            self.log.error("An unexpected error occurred while moving '%s': %s", source_path, exc)

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
    from rich.progress import Progress as _RichProgress

    _RealProgress = _RichProgress
    _HAS_RICH = True
except ModuleNotFoundError:
    _RealProgress = None


def move_with_log(
    mapping: Sequence[tuple[pathlib.Path, pathlib.Path]],
    *,
    log_path: pathlib.Path | None = None,
    show_progress: bool = True,
    progress_callback: Callable[[int, pathlib.Path], None] | None = None,
) -> pathlib.Path:
    """Move *mapping* (src→dst) atomically and log each step.

    ``progress_callback`` is invoked after each file is moved with the
    completion percentage and the source path.
    """

    if log_path is None:
        log_path = pathlib.Path.cwd() / f"file-sort-log_{int(time.time())}.jsonl"
    log_path = log_path.expanduser().resolve()

    if any(dst.exists() for _, dst in mapping):
        raise FileExistsError("destination already exists")

    progress: Progress | None = None
    task_id = None
    if _HAS_RICH and show_progress:
        assert _RealProgress is not None
        progress = _RealProgress()
        task_id = progress.add_task("Moving", total=len(mapping))

    with log_path.open("w", encoding="utf-8") as logfp:
        for idx, (src, dst) in enumerate(mapping):
            dst.parent.mkdir(parents=True, exist_ok=True)
            checksum = sha256sum(src)
            category = dst.parent.name
            logfp.write(
                json.dumps(
                    {
                        "src": src.as_posix(),
                        "dst": dst.as_posix(),
                        "category": category,
                        "sha256": checksum,
                        "size": src.stat().st_size,
                        "epoch": int(time.time()),
                    }
                )
                + "\n"
            )
            try:
                shutil.move(src, dst)
            except FileNotFoundError:
                log.error("Source file not found: %s", src)
                raise
            except PermissionError:
                log.error(
                    "Permission denied moving %s to %s. Check folder permissions.",
                    src,
                    dst,
                )
                raise
            except shutil.Error as exc:
                log.error("Error during move to %s: %s", dst, exc)
                raise
            except Exception as exc:  # pragma: no cover - defensive
                log.critical(
                    "Unexpected error moving %s -> %s: %s", src, dst, exc,
                    exc_info=True,
                )
                raise
            else:
                log.info("moved %s -> %s", src, dst)
            if progress and task_id is not None:
                progress.update(task_id, advance=1)
            if progress_callback:
                percent = int(((idx + 1) / len(mapping)) * 100)
                progress_callback(percent, src)
    if progress:
        progress.stop()
    log.info("log file written to %s", log_path)
    return log_path
