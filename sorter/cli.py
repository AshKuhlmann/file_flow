from __future__ import annotations

import pathlib
import json

import typer
from rich import print

from .scanner import scan_paths
from .classifier import classify_file
from .config import load_config
from .plugin_manager import PluginManager
from .reporter import build_report
from .review import ReviewQueue
from .renamer import generate_name
from .mover import move_with_log
from .rollback import rollback
from .dupes import find_duplicates, delete_older as _delete_older
from . import clustering
from . import supervised


app = typer.Typer(add_completion=False, rich_markup_mode="rich")


@app.callback()
def _global_options(
    verbose: bool = typer.Option(False, "--verbose", help="enable verbose output"),
) -> None:
    """Global options that may be ignored for now."""
    if not verbose:
        return
    # No structured verbosity yet; placeholder for future diagnostics


@app.command()
def scan(
    dirs: list[pathlib.Path] = typer.Argument(
        ..., exists=True, readable=True, file_okay=False
    )
) -> None:
    """Scan directories and report file count."""
    try:
        files = scan_paths(dirs)
        print(f"[green]{len(files)} files found.[/green]")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[red]{exc}[/red]")
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
        print(f"[bold]Report ready:[/bold] {out}")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[red]{exc}[/red]")
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
            print("[green]No files pending review.[/green]")
            return
        print("[bold]Files to review:[/bold]")
        for p in due:
            print(f"  • {p}")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[red]{exc}[/red]")
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

            new_name_from_plugin = plugin_manager.rename_with_plugin(f)
            if new_name_from_plugin:
                final_dest = target_dir / new_name_from_plugin
            else:
                final_dest = generate_name(f, target_dir)

            mapping.append((f, final_dest))

        report_path = build_report(mapping, auto_open=False)
        print(f"[bold]Report ready:[/bold] {report_path}")
        if dry_run:
            print("[yellow]Dry-run complete — no files moved.[/yellow]")
            return
        if not yes and not typer.confirm("Proceed with move?"):
            return
        log_path = move_with_log(mapping)
        print(f"[green]Move done.[/green] Log: {log_path}")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command()
def undo(
    log_file: pathlib.Path = typer.Argument(..., exists=True, readable=True)
) -> None:
    """Undo file moves recorded in *log_file*."""
    try:
        rollback(log_file)
        print("[green]Rollback complete.[/green]")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[red]{exc}[/red]")
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
        print("[green]No duplicates detected.")
        return
    for digest, paths in groups.items():
        print(f"[bold yellow]{len(paths)}×[/bold yellow] {digest[:10]} →")
        for p in paths:
            print(f"  • {p}")
    if delete_older and typer.confirm("Delete older copies?"):
        for paths in groups.values():
            for removed in _delete_older(paths):
                print(f"[red]- deleted[/red] {removed}")
    if hardlink and not delete_older:
        print("⚠️  hardlink requires delete_older to leave single copy.")


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
    print("[green]Scheduler entry installed.[/green]")


@app.command()
def stats(
    logs_dir: pathlib.Path = typer.Argument(..., dir_okay=True),
    out: pathlib.Path = typer.Option(None, "--out", file_okay=True),
) -> None:
    """Generate HTML analytics dashboard from move logs."""
    logs = sorted(logs_dir.glob("file-sort-log_*.jsonl"))
    if not logs:
        print("[red]No log files found.[/red]")
        raise typer.Exit(1)
    from .stats import build_dashboard

    dash = build_dashboard(logs, dest=out)
    print(f"[green]Dashboard written to {dash}[/green]")


@app.command()
def learn_clusters(
    source_dir: pathlib.Path = typer.Argument(..., exists=True, file_okay=False),
    clusters: int = typer.Option(
        10, "--k", help="The number of categories to look for."
    ),
) -> None:
    """Analyze a directory to discover and label potential file categories."""
    files = scan_paths([source_dir])
    clustered_df = clustering.train_cluster_model(files, n_clusters=clusters)

    if clustered_df is None:
        return

    cluster_labels: dict[str, str] = {}
    for cluster_id, group in clustered_df.groupby("cluster"):
        print(f"\n--- Cluster {cluster_id} ---")
        sample_files = [path.name for path in group["path"].head(5)]
        print("Contains files like:", ", ".join(sample_files))
        category_name = typer.prompt(
            "What would you like to name this category? (or press Enter to skip)"
        )
        if category_name:
            cluster_labels[str(cluster_id)] = category_name

    if cluster_labels:
        with open(clustering.LABELS_PATH, "w") as f:
            json.dump(cluster_labels, f)
        print(f"\nCategory labels saved to {clustering.LABELS_PATH}")


@app.command()
def train(
    logs_dir: pathlib.Path = typer.Argument(
        pathlib.Path.cwd(),
        help="Directory containing your 'file-sort-log_*.jsonl' files.",
    )
) -> None:
    """Train a personalized classifier based on your move history."""
    supervised.train_supervised_model(logs_dir)


def main() -> None:  # pragma: no cover - manual execution
    app()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
