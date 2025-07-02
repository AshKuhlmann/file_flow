import argparse
import logging
import pathlib
from typing import Iterable

from . import __version__
from .logging_config import setup_logging
from .scanner import scan_paths
from .reporter import build_report
from .review import ReviewQueue
from .mover import move_with_log
from .planner import plan_moves
from .dupes import find_duplicates, delete_older as _delete_older
from .cli_utils import handle_cli_errors

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

@handle_cli_errors
def handle_scan(args: argparse.Namespace) -> None:
    dirs = [p.resolve() for p in args.dirs]
    for d in dirs:
        if not d.exists():
            raise FileNotFoundError(f"{d} does not exist")
    log.debug("Scanning %d root directories", len(dirs))
    files = scan_paths(dirs)
    log.info("%d files found.", len(files))
    if log.isEnabledFor(logging.DEBUG):
        for f in files:
            log.debug("found: %s", f)


@handle_cli_errors
def handle_report(args: argparse.Namespace) -> None:
    dirs = [p.resolve() for p in args.dirs]
    for d in dirs:
        if not d.exists():
            raise FileNotFoundError(f"{d} does not exist")
    base = args.dest or pathlib.Path.cwd()
    mapping = plan_moves(dirs, base, pattern=args.pattern)
    log.info("%d files will be included in the report", len(mapping))
    for src, dst in mapping:
        log.debug("map %s -> %s", src, dst)
    out = build_report(mapping, auto_open=args.auto_open, fmt=args.fmt)
    log.info("Report ready: %s", out)


@handle_cli_errors
def handle_review(args: argparse.Namespace) -> None:
    dirs = [p.resolve() for p in args.dirs]
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


@handle_cli_errors
def handle_move(args: argparse.Namespace) -> None:
    dirs = [p.resolve() for p in args.dirs]
    for d in dirs:
        if not d.exists():
            raise FileNotFoundError(f"{d} does not exist")
    try:
        log.debug("Beginning move operation into %s", args.dest)
        mapping = plan_moves(dirs, args.dest, pattern=args.pattern)
        log.info("%d files to process", len(mapping))
        for src, dst in mapping:
            log.debug("plan move %s -> %s", src, dst)
        report_path = build_report(mapping, auto_open=False)
        log.info("Report ready: %s", report_path)
        if args.dry_run:
            log.warning("Dry-run complete — no files were moved.")
            return
        if not args.yes:
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


@handle_cli_errors
def handle_undo(args: argparse.Namespace) -> None:
    log.debug("Rolling back moves using log %s", args.log_file)
    from .rollback import rollback as _rollback
    _rollback(args.log_file)
    log.info("Rollback complete.")


@handle_cli_errors
def handle_dupes(args: argparse.Namespace) -> None:
    dirs = [p.resolve() for p in args.dirs]
    for d in dirs:
        if not d.exists():
            raise FileNotFoundError(f"{d} does not exist")
    log.debug("Scanning for duplicates in %d dirs", len(dirs))
    files = scan_paths(dirs)
    log.info(
        "Scanning %d files for duplicates using %s",
        len(files),
        args.algorithm,
    )
    groups = find_duplicates(files, algorithm=args.algorithm)
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
    if args.delete_older:
        confirm = input("Delete older copies? [y/N]: ")
        if confirm.strip().lower() in {"y", "yes"}:
            for paths in groups.values():
                for removed in _delete_older(paths):
                    log.info("- deleted %s", removed)
    if args.hardlink and not args.delete_older:
        log.warning("⚠️  hardlink requires delete_older to leave single copy.")


@handle_cli_errors
def handle_schedule(args: argparse.Namespace) -> None:
    from .scheduler import validate_cron, install_job
    log.debug(
        "Scheduling job '%s' for dirs: %s",
        args.cron,
        ", ".join(str(d) for d in args.dirs),
    )
    validate_cron(args.cron)
    install_job(args.cron, dirs=[*args.dirs], dest=args.dest)
    log.info("Scheduler entry installed.")


@handle_cli_errors
def handle_stats(args: argparse.Namespace) -> None:
    logs = sorted(args.logs_dir.glob("file-sort-log_*.jsonl"))
    if not logs:
        log.error("No log files found.")
        raise FileNotFoundError("No log files found.")
    from .stats import build_dashboard
    dash = build_dashboard(logs, dest=args.out)
    log.info("Dashboard written to %s", dash)
    log.debug("Processed %d log files", len(logs))


@handle_cli_errors
def handle_learn_clusters(args: argparse.Namespace) -> None:
    from . import clustering
    import shutil
    files = scan_paths([args.source_dir])
    clustered_df = clustering.train_cluster_model(files)
    if clustered_df is None:
        return
    for cluster_id, group in clustered_df.groupby("cluster"):
        cluster_name = f"Cluster {cluster_id}"
        cluster_dir = args.source_dir / cluster_name
        cluster_dir.mkdir(exist_ok=True)
        for file_path in group["path"]:
            shutil.move(str(file_path), str(cluster_dir))
    log.info("Files have been sorted into cluster subdirectories.")


@handle_cli_errors
def handle_train(args: argparse.Namespace) -> None:
    from . import supervised
    log.debug("Training classifier using logs in %s", args.logs_dir)
    supervised.train_supervised_model(args.logs_dir)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A smart file sorter and organizer."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan
    sp = subparsers.add_parser("scan", help="Scan directories and report file count.")
    sp.add_argument("dirs", nargs="+", type=pathlib.Path)
    sp.set_defaults(func=handle_scan)

    # report
    sp = subparsers.add_parser(
        "report", help="Generate a report of proposed moves."
    )
    sp.add_argument("dirs", nargs="+", type=pathlib.Path)
    sp.add_argument("--dest", type=pathlib.Path, default=None)
    sp.add_argument("--pattern", type=str, default=None)
    sp.add_argument("--auto-open", action="store_true")
    sp.add_argument("--format", dest="fmt", default="xlsx")
    sp.set_defaults(func=handle_report)

    # review
    sp = subparsers.add_parser(
        "review", help="Queue files for review and list due items."
    )
    sp.add_argument("dirs", nargs="+", type=pathlib.Path)
    sp.set_defaults(func=handle_review)

    # move
    sp = subparsers.add_parser("move", help="Scan, classify and move files.")
    sp.add_argument("dirs", nargs="+", type=pathlib.Path)
    sp.add_argument("--dest", type=pathlib.Path, required=True)
    sp.add_argument("--pattern", type=str, default=None)
    sp.add_argument("--yes", action="store_true", help="skip confirmation")
    sp.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    sp.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    sp.set_defaults(func=handle_move)

    # undo
    sp = subparsers.add_parser("undo", help="Undo file moves recorded in log file.")
    sp.add_argument("log_file", type=pathlib.Path)
    sp.set_defaults(func=handle_undo)

    # dupes
    sp = subparsers.add_parser("dupes", help="Find duplicate files.")
    sp.add_argument("dirs", nargs="+", type=pathlib.Path)
    sp.add_argument("--delete-older", action="store_true")
    sp.add_argument("--hardlink", action="store_true")
    sp.add_argument("--algorithm", default="sha256")
    sp.set_defaults(func=handle_dupes)

    # schedule
    sp = subparsers.add_parser(
        "schedule", help="Install nightly dry-run job to email report."
    )
    sp.add_argument("dirs", nargs="+", type=pathlib.Path)
    sp.add_argument("--dest", type=pathlib.Path, required=True)
    sp.add_argument("--cron", default="0 3 * * *")
    sp.set_defaults(func=handle_schedule)

    # stats
    sp = subparsers.add_parser(
        "stats", help="Generate HTML dashboard from move logs."
    )
    sp.add_argument("logs_dir", type=pathlib.Path)
    sp.add_argument("--out", type=pathlib.Path, default=None)
    sp.set_defaults(func=handle_stats)

    # learn-clusters
    sp = subparsers.add_parser(
        "learn-clusters", help="Analyze a directory to discover categories."
    )
    sp.add_argument("source_dir", type=pathlib.Path)
    sp.set_defaults(func=handle_learn_clusters)

    # train
    sp = subparsers.add_parser(
        "train", help="Train a classifier from move history."
    )
    sp.add_argument("logs_dir", type=pathlib.Path, default=pathlib.Path.cwd())
    sp.set_defaults(func=handle_train)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Iterable[str] | None = None) -> None:
    parser = get_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(console_level=log_level)
    if args.verbose:
        log.debug("Verbose logging enabled.")
    else:
        log.debug("Logging level: %s", logging.getLevelName(log_level))
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
