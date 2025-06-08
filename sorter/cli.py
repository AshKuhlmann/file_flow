from __future__ import annotations

import pathlib
import json

import typer
import logging

from .logging_config import setup_logging
from .scanner import scan_paths
from .classifier import classify_file
from .config import load_config
from .plugin_manager import PluginManager
from .reporter import build_report
from .review import ReviewQueue
from .renamer import generate_name
from .mover import move_with_log
from .dupes import find_duplicates, delete_older as _delete_older


app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)

log = logging.getLogger(__name__)


@app.callback()
def _global_options(
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Enable verbose DEBUG level logging."
    ),
) -> None:
    """Global options for the file-sorter CLI."""
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(console_level=log_level)
    log.debug("Verbose logging enabled.")


@app.command()
def scan(
    dirs: list[pathlib.Path] = typer.Argument(
        ..., exists=True, readable=True, file_okay=False
    )
) -> None:
    """Scan directories and report file count."""
    try:
        files = scan_paths(dirs)
        log.info("%d files found.", len(files))
    except PermissionError as exc:
        log.error("Permission denied while scanning: %s", exc)
        raise typer.Exit(1)
    except OSError as exc:  # pragma: no cover - unexpected filesystem issue
        log.error("Failed to scan directories: %s", exc)
        raise typer.Exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        log.exception("Unexpected error during scan: %s", exc)
        raise typer.Exit(1)


@app.command()
def report(
    dirs: list[pathlib.Path] = typer.Argument(
        ..., exists=True, readable=True, file_okay=False
    ),
    dest: pathlib.Path = typer.Option(None, "--dest", file_okay=False, dir_okay=True),
    auto_open: bool = typer.Option(False, "--auto-open", help="open XLSX when done"),
) -> None:
    """Generate an Excel report describing proposed moves."""
    try:
        files = scan_paths(dirs)
        mapping: list[tuple[pathlib.Path, pathlib.Path]] = []
        base = dest or pathlib.Path.cwd()
        for f in files:
            cat = classify_file(f) or "Unsorted"
            target_dir = base / cat
            mapping.append((f, generate_name(f, target_dir)))

        out = build_report(mapping, auto_open=auto_open)
        log.info("Report ready: %s", out)
    except ModuleNotFoundError as exc:
        log.error(
            "Missing dependency '%s'. Install optional reporting extras to use this command.",
            exc.name,
        )
        raise typer.Exit(1)
    except PermissionError as exc:
        log.error("Permission denied while generating report: %s", exc)
        raise typer.Exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        log.exception("Unexpected error during report generation: %s", exc)
        raise typer.Exit(1)


@app.command()
def review(
    dirs: list[pathlib.Path] = typer.Argument(
        ..., exists=True, readable=True, file_okay=False
    )
) -> None:
    """Add files to review queue and list any due today."""
    try:
        files = scan_paths(dirs)
        queue = ReviewQueue()
        queue.upsert_files(files)
        due = queue.select_for_review(limit=5)
        if not due:
            log.info("No files pending review.")
            return
        log.info("Files to review:")
        for p in due:
            log.info("  • %s", p)
    except PermissionError as exc:
        log.error("Permission denied while updating review queue: %s", exc)
        raise typer.Exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        log.exception("Unexpected error during review operation: %s", exc)
        raise typer.Exit(1)


@app.command()
def move(
    dirs: list[pathlib.Path] = typer.Argument(
        ..., exists=True, readable=True, file_okay=False
    ),
    dest: pathlib.Path = typer.Option(..., "--dest", file_okay=False, dir_okay=True),
    yes: bool = typer.Option(False, "--yes", help="skip confirmation"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
) -> None:
    """Scan, classify and move files into *dest*."""
    try:
        config = load_config()
        plugin_manager = PluginManager(config)
        files = scan_paths(dirs)
        mapping: list[tuple[pathlib.Path, pathlib.Path]] = []
        for f in files:
            cat = classify_file(f) or "Unsorted"
            target_dir = dest / cat

            new_stem_from_plugin = plugin_manager.rename_with_plugin(f)

            if new_stem_from_plugin:
                temp_path_for_collision_check = f.with_stem(new_stem_from_plugin)
                final_dest = generate_name(
                    temp_path_for_collision_check,
                    target_dir,
                    include_parent=False,
                    date_from_mtime=False,
                )
            else:
                final_dest = generate_name(f, target_dir)

            mapping.append((f, final_dest))

        report_path = build_report(mapping, auto_open=False)
        log.info("Report ready: %s", report_path)

        if dry_run:
            log.warning("Dry-run complete — no files were moved.")
            return

        if not yes and not typer.confirm("Proceed with move?"):
            log.info("User cancelled operation.")
            return

        log_path = move_with_log(mapping)
        log.info("Move complete. Log available at: %s", log_path)
    except FileExistsError as exc:
        log.error("Move aborted: destination already exists (%s)", exc)
        raise typer.Exit(1)
    except ModuleNotFoundError as exc:
        log.error(
            "Missing dependency '%s'. Install optional extras to enable moving.",
            exc.name,
        )
        raise typer.Exit(1)
    except PermissionError as exc:
        log.error("Permission denied while moving files: %s", exc)
        raise typer.Exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        log.exception("Unexpected error during move: %s", exc)
        raise typer.Exit(1)


@app.command()
def undo(
    log_file: pathlib.Path = typer.Argument(..., exists=True, readable=True)
) -> None:
    """Undo file moves recorded in *log_file*."""
    try:
        from .rollback import rollback as _rollback

        _rollback(log_file)
        log.info("Rollback complete.")
    except FileNotFoundError as exc:
        log.error("Log file not found: %s", exc)
        raise typer.Exit(1)
    except ValueError as exc:
        log.error("Rollback failed due to integrity error: %s", exc)
        raise typer.Exit(1)
    except PermissionError as exc:
        log.error("Permission denied during rollback: %s", exc)
        raise typer.Exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        log.exception("Unexpected error during rollback: %s", exc)
        raise typer.Exit(1)


# Existing commands -------------------------------------------------------


@app.command()
def dupes(
    dirs: list[pathlib.Path] = typer.Argument(..., exists=True, readable=True),
    delete_older: bool = typer.Option(False, help="auto-delete older copies"),
    hardlink: bool = typer.Option(False, help="replace duplicates with hardlink"),
) -> None:
    """Find duplicate files by SHA-256 hash."""
    files = scan_paths(dirs)
    groups = find_duplicates(files)
    if not groups:
        log.info("No duplicates detected.")
        return
    for digest, paths in groups.items():
        log.info(
            "Found group with hash %s containing %d files:",
            digest[:10],
            len(paths),
        )
        for p in paths:
            log.info("  • %s", p)
    if delete_older and typer.confirm("Delete older copies?"):
        for paths in groups.values():
            for removed in _delete_older(paths):
                log.info("- deleted %s", removed)
    if hardlink and not delete_older:
        log.warning("⚠️  hardlink requires delete_older to leave single copy.")


@app.command()
def schedule(
    cron: str = typer.Option("0 3 * * *", help="cron expression"),
    dirs: list[pathlib.Path] = typer.Argument(...),
    dest: pathlib.Path = typer.Option(..., "--dest"),
) -> None:
    """Install nightly dry-run that emails report."""
    from .scheduler import validate_cron, install_job

    validate_cron(cron)
    install_job(cron, dirs=[*dirs], dest=dest)
    log.info("Scheduler entry installed.")


@app.command()
def stats(
    logs_dir: pathlib.Path = typer.Argument(..., dir_okay=True),
    out: pathlib.Path = typer.Option(None, "--out", file_okay=True),
) -> None:
    """Generate HTML analytics dashboard from move logs."""
    logs = sorted(logs_dir.glob("file-sort-log_*.jsonl"))
    if not logs:
        log.error("No log files found.")
        raise typer.Exit(1)
    from .stats import build_dashboard

    try:
        dash = build_dashboard(logs, dest=out)
        log.info("Dashboard written to %s", dash)
    except ModuleNotFoundError as exc:
        log.error(
            "Missing dependency '%s'. Install optional stats extras to use this command.",
            exc.name,
        )
        raise typer.Exit(1)
    except ValueError as exc:
        log.error("Cannot build dashboard: %s", exc)
        raise typer.Exit(1)
    except PermissionError as exc:
        log.error("Permission denied while writing dashboard: %s", exc)
        raise typer.Exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        log.exception("Unexpected error while building dashboard: %s", exc)
        raise typer.Exit(1)


@app.command()
def learn_clusters(
    source_dir: pathlib.Path = typer.Argument(..., exists=True, file_okay=False),
    clusters: int = typer.Option(
        10, "--k", help="The number of categories to look for."
    ),
) -> None:
    """Analyze a directory to discover and label potential file categories."""
    from . import clustering

    try:
        files = scan_paths([source_dir])
        clustered_df = clustering.train_cluster_model(files, n_clusters=clusters)

        if clustered_df is None:
            return

        cluster_labels: dict[str, str] = {}
        for cluster_id, group in clustered_df.groupby("cluster"):
            log.info("\n--- Cluster %s ---", cluster_id)
            sample_files = [path.name for path in group["path"].head(5)]
            log.info("Contains files like: %s", ", ".join(sample_files))
            category_name = typer.prompt(
                "What would you like to name this category? (or press Enter to skip)"
            )
            if category_name:
                cluster_labels[str(cluster_id)] = category_name

        if cluster_labels:
            with open(clustering.LABELS_PATH, "w") as f:
                json.dump(cluster_labels, f)
            log.info("\nCategory labels saved to %s", clustering.LABELS_PATH)
    except ModuleNotFoundError as exc:
        log.error(
            "Missing dependency '%s'. Install optional clustering extras to use this command.",
            exc.name,
        )
        raise typer.Exit(1)
    except PermissionError as exc:
        log.error("Permission denied while writing cluster labels: %s", exc)
        raise typer.Exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        log.exception("Unexpected error during clustering: %s", exc)
        raise typer.Exit(1)


@app.command()
def train(
    logs_dir: pathlib.Path = typer.Argument(
        pathlib.Path.cwd(),
        help="Directory containing your 'file-sort-log_*.jsonl' files.",
    )
) -> None:
    """Train a personalized classifier based on your move history."""
    from . import supervised

    try:
        supervised.train_supervised_model(logs_dir)
    except ModuleNotFoundError as exc:
        log.error(
            "Missing dependency '%s'. Install optional training extras to use this command.",
            exc.name,
        )
        raise typer.Exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        log.exception("Unexpected error during training: %s", exc)
        raise typer.Exit(1)


def main() -> None:  # pragma: no cover - manual execution
    app()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
