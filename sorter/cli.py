from __future__ import annotations

import pathlib

import typer
import logging
from . import __version__

from .logging_config import setup_logging
from .scanner import scan_paths
from .reporter import build_report
from .review import ReviewQueue
from .mover import move_with_log
from .planner import plan_moves
from .dupes import find_duplicates, delete_older as _delete_older
from .cli_utils import handle_cli_errors


app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)

log = logging.getLogger(__name__)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def _global_options(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Enable verbose DEBUG level logging."
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the application version and exit.",
    ),
) -> None:
    """Global options for the file-sorter CLI."""
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(console_level=log_level)
    if verbose:
        log.debug("Verbose logging enabled.")
    else:
        log.debug("Logging level: %s", logging.getLevelName(log_level))


@handle_cli_errors
@app.command()
def scan(
    dirs: list[pathlib.Path] = typer.Argument(
        ..., exists=True, readable=True, file_okay=False
    )
) -> None:
    """Scan directories and report file count."""
    log.debug("Scanning %d root directories", len(dirs))
    if log.isEnabledFor(logging.DEBUG):
        for d in dirs:
            log.debug(" - %s", d)

    files = scan_paths(dirs)

    log.info("%d files found.", len(files))
    if log.isEnabledFor(logging.DEBUG):
        for f in files:
            log.debug("found: %s", f)


@handle_cli_errors
@app.command()
def report(
    dirs: list[pathlib.Path] = typer.Argument(
        ..., exists=True, readable=True, file_okay=False
    ),
    dest: pathlib.Path = typer.Option(None, "--dest", file_okay=False, dir_okay=True),
    pattern: str | None = typer.Option(None, "--pattern", help="rename pattern"),
    auto_open: bool = typer.Option(False, "--auto-open", help="open report when done"),
    fmt: str = typer.Option("xlsx", "--format", help="output format: xlsx, csv, json"),
) -> None:
    """Generate a report describing proposed moves."""
    log.debug("Generating report from %d source dirs", len(dirs))
    base = dest or pathlib.Path.cwd()
    mapping = plan_moves(dirs, base, pattern=pattern)
    log.info("%d files will be included in the report", len(mapping))
    for src, dst in mapping:
        log.debug("map %s -> %s", src, dst)

    out = build_report(mapping, auto_open=auto_open, fmt=fmt)
    log.info("Report ready: %s", out)


@handle_cli_errors
@app.command()
def review(
    dirs: list[pathlib.Path] = typer.Argument(
        ..., exists=True, readable=True, file_okay=False
    )
) -> None:
    """Add files to review queue and list any due today."""
    log.debug("Updating review queue from %d dirs", len(dirs))
    files = scan_paths(dirs)
    log.info("%d files scanned for review", len(files))
    queue = ReviewQueue()
    queue.upsert_files(files)
    due = queue.select_for_review(limit=5)
    if not due:
        log.info("No files pending review.")
        return
    log.info("Files to review:")
    for p in due:
        log.info("  • %s", p)


@app.command()
def move(
    dirs: list[pathlib.Path] = typer.Argument(
        ..., exists=True, readable=True, file_okay=False
    ),
    dest: pathlib.Path = typer.Option(..., "--dest", file_okay=False, dir_okay=True),
    pattern: str | None = typer.Option(None, "--pattern", help="rename pattern"),
    yes: bool = typer.Option(False, "--yes", help="skip confirmation"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
) -> None:
    """Scan, classify and move files into *dest*."""
    try:
        log.debug("Beginning move operation into %s", dest)
        mapping = plan_moves(dirs, dest, pattern=pattern)
        log.info("%d files to process", len(mapping))
        for src, dst in mapping:
            log.debug("plan move %s -> %s", src, dst)

        report_path = build_report(mapping, auto_open=False)
        log.info("Report ready: %s", report_path)
        log.debug("%d planned moves recorded", len(mapping))

        if dry_run:
            log.warning("Dry-run complete — no files were moved.")
            return

        if not yes and not typer.confirm("Proceed with move?"):
            log.info("User cancelled operation.")
            return

        log_path = move_with_log(mapping)
        log.info("Move complete. Log available at: %s", log_path)
        if log.isEnabledFor(logging.DEBUG):
            for src, dst in mapping:
                log.debug("moved %s -> %s", src, dst)
    except FileExistsError as exc:
        log.error("Move aborted: destination already exists (%s)", exc)
        raise typer.Exit(1)


@handle_cli_errors
@app.command()
def undo(
    log_file: pathlib.Path = typer.Argument(..., exists=True, readable=True)
) -> None:
    """Undo file moves recorded in *log_file*."""
    log.debug("Rolling back moves using log %s", log_file)
    from .rollback import rollback as _rollback

    _rollback(log_file)
    log.info("Rollback complete.")


# Existing commands -------------------------------------------------------


@app.command()
def dupes(
    dirs: list[pathlib.Path] = typer.Argument(..., exists=True, readable=True),
    delete_older: bool = typer.Option(False, help="auto-delete older copies"),
    hardlink: bool = typer.Option(False, help="replace duplicates with hardlink"),
    algorithm: str = typer.Option("sha256", "--algorithm", help="hash algorithm"),
) -> None:
    """Find duplicate files using *algorithm* hash."""
    log.debug("Scanning for duplicates in %d dirs", len(dirs))
    files = scan_paths(dirs)
    log.info(
        "Scanning %d files for duplicates using %s",
        len(files),
        algorithm,
    )
    groups = find_duplicates(files, algorithm=algorithm)
    if not groups:
        log.info("No duplicates detected.")
        return
    for digest, paths in groups.items():
        log.info(
            "Found group with hash %s containing %d files:",
            digest[:10],
            len(paths),
        )
        log.debug("paths: %s", ", ".join(str(p) for p in paths))
        for p in paths:
            log.info("  • %s", p)
    if delete_older and typer.confirm("Delete older copies?"):
        for paths in groups.values():
            for removed in _delete_older(paths):
                log.info("- deleted %s", removed)
    if hardlink and not delete_older:
        log.warning("⚠️  hardlink requires delete_older to leave single copy.")


@handle_cli_errors
@app.command()
def schedule(
    dirs: list[pathlib.Path] = typer.Argument(...),
    dest: pathlib.Path = typer.Option(..., "--dest"),
    cron: str | None = typer.Option(None, "--cron", help="cron expression"),
    time: str | None = typer.Option(None, "--time", help="HH:MM run time"),
    day: str | None = typer.Option(None, "--day", help="day of week"),
) -> None:
    """Install scheduled dry-run that emails report."""
    from .scheduler import install_job, build_cron, validate_cron

    if cron is not None:
        validate_cron(cron)
        cron_expr = cron
    else:
        cron_expr = build_cron(time=time, day=day)

    dir_list = ", ".join(str(d) for d in dirs)
    log.debug("Scheduling job '%s' for dirs: %s", cron_expr, dir_list)
    install_job(cron_expr, dirs=[*dirs], dest=dest)
    log.info("Scheduler entry installed.")


@handle_cli_errors
@app.command()
def stats(
    logs_dir: pathlib.Path = typer.Argument(..., dir_okay=True),
    out: pathlib.Path = typer.Option(None, "--out", file_okay=True),
) -> None:
    """Generate HTML analytics dashboard from move logs."""
    log.debug("Building stats from logs in %s", logs_dir)
    logs = sorted(logs_dir.glob("file-sort-log_*.jsonl"))
    if not logs:
        log.error("No log files found.")
        raise typer.Exit(1)
    from .stats import build_dashboard

    dash = build_dashboard(logs, dest=out)
    log.info("Dashboard written to %s", dash)
    log.debug("Processed %d log files", len(logs))


@handle_cli_errors
@app.command()
def learn_clusters(
    source_dir: pathlib.Path = typer.Argument(..., exists=True, file_okay=False),
) -> None:
    """Analyze a directory to discover and label potential file categories."""
    from . import clustering
    import shutil

    log.debug("Learning clusters from %s", source_dir)
    files = scan_paths([source_dir])
    clustered_df = clustering.train_cluster_model(files)

    if clustered_df is None:
        return

    for cluster_id, group in clustered_df.groupby("cluster"):
        cluster_name = f"Cluster {cluster_id}"
        cluster_dir = source_dir / cluster_name
        cluster_dir.mkdir(exist_ok=True)
        for file_path in group["path"]:
            shutil.move(str(file_path), str(cluster_dir))
    log.info("Files have been sorted into cluster subdirectories.")


@handle_cli_errors
@app.command()
def train(
    logs_dir: pathlib.Path = typer.Argument(
        pathlib.Path.cwd(),
        help="Directory containing your 'file-sort-log_*.jsonl' files.",
    )
) -> None:
    """Train a personalized classifier based on your move history."""
    from . import supervised

    log.debug("Training classifier using logs in %s", logs_dir)
    supervised.train_supervised_model(logs_dir)


def main() -> None:  # pragma: no cover - manual execution
    app()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
