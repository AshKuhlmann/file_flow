from __future__ import annotations

import os
import pathlib
import platform
import subprocess
import textwrap
from typing import Final

from croniter import croniter  # type: ignore[import-untyped]

_DAY_NAMES: Final = {
    "sun": 0,
    "mon": 1,
    "tue": 2,
    "wed": 3,
    "thu": 4,
    "fri": 5,
    "sat": 6,
}


def validate_cron(expr: str) -> None:
    """Raise `ValueError` if *expr* is not a valid 5-field cron."""
    if not croniter.is_valid(expr):
        raise ValueError(f"invalid cron expression: {expr}")


def build_cron(*, time: str | None = None, day: str | None = None) -> str:
    """Create a cron expression from *time* and optional weekday."""
    if time is None:
        hour, minute = 3, 0
    else:
        if ":" not in time:
            raise ValueError(f"invalid time format: {time}")
        h_str, m_str = time.split(":", 1)
        if not h_str.isdigit() or not m_str.isdigit():
            raise ValueError(f"invalid time format: {time}")
        hour = int(h_str)
        minute = int(m_str)
        if hour not in range(24) or minute not in range(60):
            raise ValueError(f"invalid time: {time}")

    dow = "*"
    if day is not None:
        key = day.lower()[:3]
        if key.isdigit():
            dow_val = int(key)
            if dow_val not in range(7):
                raise ValueError(f"invalid day: {day}")
            dow = str(dow_val)
        elif key in _DAY_NAMES:
            dow = str(_DAY_NAMES[key])
        else:
            raise ValueError(f"invalid day: {day}")

    cron = f"{minute} {hour} * * {dow}"
    validate_cron(cron)
    return cron


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

    dow_field = cron_expr.split()[4]
    days_xml = ""
    if dow_field != "*":
        day_tags = []
        for part in dow_field.split(","):
            key = part.lower()[:3]
            if key.isdigit():
                val = int(key)
            elif key in _DAY_NAMES:
                val = _DAY_NAMES[key]
            else:
                continue
            tag = [
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            ][val]
            day_tags.append(f"<{tag}/>")
        if day_tags:
            days_xml = (
                "<ScheduleByWeek><DaysOfWeek>"
                + "".join(day_tags)
                + "</DaysOfWeek><WeeksInterval>1</WeeksInterval></ScheduleByWeek>"
            )

    if not days_xml:
        days_xml = "<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>"

    task_xml = textwrap.dedent(
        f"""
        <Task version='1.2'
              xmlns='http://schemas.microsoft.com/windows/2004/02/mit/task'>
          <Triggers>
            <CalendarTrigger>
              <StartBoundary>2024-01-01T{hour:02d}:{minute:02d}:00</StartBoundary>
              {days_xml}
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
