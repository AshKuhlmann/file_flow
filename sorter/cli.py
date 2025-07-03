import logging
from pathlib import Path
from typing import Iterable, Optional

import typer
from typing_extensions import Annotated

from . import __version__
from .logging_config import setup_logging
from .scanner import scan_paths
from .reporter import build_report
from .review import ReviewQueue
from .mover import move_with_log
from .planner import plan_moves
from .dupes import find_duplicates, delete_older as _delete_older
from .cli_utils import handle_cli_errors
from .config import load_config, Settings

app = typer.Typer(
    name="sorter",
    help="A smart file sorter and organizer.",
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def _main_callback(
    ctx: typer.Context,
    verbose: Annotated[
        int,
        typer.Option("-v", "--verbose", count=True, help="Increase verbosity"),
    ] = 0,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
) -> None:
    """Set up logging and load configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(console_level=log_level)
    if verbose:
        log.debug("Verbose logging enabled.")
    else:
        log.debug("Logging level: %s", logging.getLevelName(log_level))
    ctx.obj = load_config()


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


@app.command("scan")
@handle_cli_errors
def handle_scan(
    ctx: typer.Context,
    dirs: Annotated[list[Path], typer.Argument()],
) -> None:
    dirs = [p.resolve() for p in dirs]
    for d in dirs:
        if not d.exists():
            raise FileNotFoundError(f"{d} does not exist")
    log.debug("Scanning %d root directories", len(dirs))
    files = scan_paths(dirs)
    log.info("%d files found.", len(files))
    if log.isEnabledFor(logging.DEBUG):
        for f in files:
            log.debug("found: %s", f)


@app.command("report")
@handle_cli_errors
def handle_report(
    ctx: typer.Context,
    dirs: Annotated[list[Path], typer.Argument()],
    dest: Annotated[Optional[Path], typer.Option("--dest")] = None,
    pattern: Annotated[Optional[str], typer.Option("--pattern")] = None,
    auto_open: Annotated[bool, typer.Option("--auto-open")] = False,
    fmt: Annotated[str, typer.Option("--format")] = "xlsx",
) -> None:
    dirs = [p.resolve() for p in dirs]
    for d in dirs:
        if not d.exists():
            raise FileNotFoundError(f"{d} does not exist")
    base = dest or Path.cwd()
    mapping = plan_moves(dirs, base, pattern=pattern)
    log.info("%d files will be included in the report", len(mapping))
    for src, dst in mapping:
        log.debug("map %s -> %s", src, dst)
    out = build_report(mapping, auto_open=auto_open, fmt=fmt)
    log.info("Report ready: %s", out)


@app.command("review")
@handle_cli_errors
def handle_review(
    ctx: typer.Context, dirs: Annotated[list[Path], typer.Argument()]
) -> None:
    dirs = [p.resolve() for p in dirs]
    for d in dirs:
        if not d.exists():
            raise FileNotFoundError(f"{d} does not exist")
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


@app.command("move")
@handle_cli_errors
def handle_move(
    ctx: typer.Context,
    dirs: Annotated[list[Path], typer.Argument()],
    dest: Annotated[Path, typer.Option("--dest")],
    pattern: Annotated[Optional[str], typer.Option("--pattern")] = None,
    yes: Annotated[bool, typer.Option("--yes", help="skip confirmation")] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run/--no-dry-run", help="simulate without moving"),
    ] = True,
) -> None:
    cfg: Settings = ctx.obj
    cfg.dry_run = dry_run
    dirs = [p.resolve() for p in dirs]
    for d in dirs:
        if not d.exists():
            raise FileNotFoundError(f"{d} does not exist")
    try:
        log.debug("Beginning move operation into %s", dest)
        mapping = plan_moves(dirs, dest, pattern=pattern)
        log.info("%d files to process", len(mapping))
        for src, dst in mapping:
            log.debug("plan move %s -> %s", src, dst)
        report_path = build_report(mapping, auto_open=False)
        log.info("Report ready: %s", report_path)
        if dry_run:
            log.warning("Dry-run complete — no files were moved.")
            return
        if not yes:
            ans = input("Proceed with move? [y/N]: ")
            if ans.strip().lower() not in {"y", "yes"}:
                log.info("User cancelled operation.")
                return
        log_path = move_with_log(mapping)
        log.info("Move complete. Log available at: %s", log_path)
        if log.isEnabledFor(logging.DEBUG):
            for src, dst in mapping:
                log.debug("moved %s -> %s", src, dst)
    except FileExistsError as exc:
        log.error("Move aborted: destination already exists (%s)", exc)
        raise


@app.command("undo")
@handle_cli_errors
def handle_undo(
    ctx: typer.Context,
    log_file: Annotated[Path, typer.Argument()],
) -> None:
    log.debug("Rolling back moves using log %s", log_file)
    from .rollback import rollback as _rollback

    _rollback(log_file)
    log.info("Rollback complete.")


@app.command("dupes")
@handle_cli_errors
def handle_dupes(
    ctx: typer.Context,
    dirs: Annotated[list[Path], typer.Argument()],
    delete_older: Annotated[bool, typer.Option("--delete-older")] = False,
    hardlink: Annotated[bool, typer.Option("--hardlink")] = False,
    algorithm: Annotated[str, typer.Option("--algorithm")] = "sha256",
) -> None:
    dirs = [p.resolve() for p in dirs]
    for d in dirs:
        if not d.exists():
            raise FileNotFoundError(f"{d} does not exist")
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
    if delete_older:
        confirm = input("Delete older copies? [y/N]: ")
        if confirm.strip().lower() in {"y", "yes"}:
            for paths in groups.values():
                for removed in _delete_older(paths):
                    log.info("- deleted %s", removed)
    if hardlink and not delete_older:
        log.warning("⚠️  hardlink requires delete_older to leave single copy.")


@app.command("schedule")
@handle_cli_errors
def handle_schedule(
    ctx: typer.Context,
    dirs: Annotated[list[Path], typer.Argument()],
    dest: Annotated[Path, typer.Option("--dest")],
    cron: Annotated[str, typer.Option("--cron")] = "0 3 * * *",
) -> None:
    from .scheduler import validate_cron, install_job

    log.debug(
        "Scheduling job '%s' for dirs: %s",
        cron,
        ", ".join(str(d) for d in dirs),
    )
    validate_cron(cron)
    install_job(cron, dirs=[*dirs], dest=dest)
    log.info("Scheduler entry installed.")


@app.command("stats")
@handle_cli_errors
def handle_stats(
    ctx: typer.Context,
    logs_dir: Annotated[Path, typer.Argument()],
    out: Annotated[Optional[Path], typer.Option("--out")] = None,
) -> None:
    logs = sorted(logs_dir.glob("file-sort-log_*.jsonl"))
    if not logs:
        log.error("No log files found.")
        raise FileNotFoundError("No log files found.")
    from .stats import build_dashboard

    dash = build_dashboard(logs, dest=out)
    log.info("Dashboard written to %s", dash)
    log.debug("Processed %d log files", len(logs))


@app.command("learn-clusters")
@handle_cli_errors
def handle_learn_clusters(
    ctx: typer.Context, source_dir: Annotated[Path, typer.Argument()]
) -> None:
    from . import clustering
    import shutil

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


@app.command("train")
@handle_cli_errors
def handle_train(
    ctx: typer.Context,
    logs_dir: Annotated[Path, typer.Argument()] = Path.cwd(),
) -> None:
    from . import supervised

    log.debug("Training classifier using logs in %s", logs_dir)
    supervised.train_supervised_model(logs_dir)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> None:
    """Entry point for ``file-sorter`` command."""
    app(  # type: ignore[call-arg]
        args=list(argv) if argv is not None else None,
        prog_name=None,
    )


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
