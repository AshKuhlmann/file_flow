from __future__ import annotations

import json
import pathlib
import shutil
import time
from typing import Any, Sequence, TYPE_CHECKING

from .utils import sha256sum

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
) -> pathlib.Path:
    """Move *mapping* (src→dst) atomically and log each step."""

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
        for src, dst in mapping:
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
            shutil.move(src, dst)
            if progress and task_id is not None:
                progress.update(task_id, advance=1)
    if progress:
        progress.stop()
    return log_path
