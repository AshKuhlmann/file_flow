from __future__ import annotations

import os
import pathlib
import platform
import subprocess
import textwrap
from typing import Final

from croniter import croniter  # type: ignore[import-untyped]


def validate_cron(expr: str) -> None:
    """Raise `ValueError` if *expr* is not a valid 5-field cron."""
    if not croniter.is_valid(expr):
        raise ValueError(f"invalid cron expression: {expr}")


def install_job(
    cron_expr: str,
    *,
    dirs: list[pathlib.Path],
    dest: pathlib.Path,
) -> None:
    """Register OS-level schedule that runs nightly dry-run."""
    cmd = f"file-sorter move {' '.join(map(str, dirs))} --dest {dest} --dry-run"
    if platform.system() == "Windows":
        _install_windows(cron_expr, cmd)
    else:
        _install_cron(cron_expr, cmd)


_DEF_HEADER: Final = "# file-sorter"


def _install_cron(cron_expr: str, cmd: str) -> None:
    current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    lines = [
        line for line in current.stdout.splitlines() if not line.startswith(_DEF_HEADER)
    ]

    shell_cmd = f"{cmd} && file-sorter report --auto-open"
    entry = f"{cron_expr} {shell_cmd}"

    lines.append(_DEF_HEADER)
    lines.append(entry)
    new_cron = "\n".join(lines) + "\n"
    subprocess.run(["crontab", "-"], input=new_cron, text=True, check=False)


def _install_windows(cron_expr: str, cmd: str) -> None:
    """Create or update Windows Task Scheduler entry."""
    from datetime import datetime

    itr = croniter(cron_expr, datetime.now())
    next_time = itr.get_next(datetime)
    hour = next_time.hour
    minute = next_time.minute

    task_xml = textwrap.dedent(
        f"""
        <Task version='1.2'
              xmlns='http://schemas.microsoft.com/windows/2004/02/mit/task'>
          <Triggers>
            <CalendarTrigger>
              <StartBoundary>2024-01-01T{hour:02d}:{minute:02d}:00</StartBoundary>
              <ScheduleByDay>
                <DaysInterval>1</DaysInterval>
              </ScheduleByDay>
            </CalendarTrigger>
          </Triggers>
          <Actions Context='Author'>
            <Exec>
              <Command>{cmd}</Command>
            </Exec>
          </Actions>
        </Task>
        """
    ).strip()

    temp = pathlib.Path(os.getenv("TEMP", ".")) / "Task.xml"
    temp.write_text(task_xml, encoding="utf-8")
    subprocess.run(
        [
            "schtasks",
            "/Create",
            "/TN",
            "FileSorterNightly",
            "/XML",
            str(temp),
            "/F",
        ],
        check=False,
    )
