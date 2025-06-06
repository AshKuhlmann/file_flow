from __future__ import annotations

import pathlib
import sys  # noqa: F401
import json  # noqa: F401
import tempfile  # noqa: F401

import typer
from rich import print

from .scanner import scan_paths
from .classifier import classify
from .reporter import build_report
from .review import ReviewQueue
from .renamer import generate_name
from .mover import move_with_log
from .rollback import rollback

app = typer.Typer(add_completion=False, rich_markup_mode="rich")


@app.command()
def scan(
    dirs: list[pathlib.Path] = typer.Argument(..., exists=True, readable=True),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    files = scan_paths(dirs)
    if verbose:
        for f in files:
            print(f.as_posix())
    print(f"[bold]Total {len(files)} files[/bold]")


@app.command()
def report(
    dirs: list[pathlib.Path] = typer.Argument(..., exists=True, readable=True),
    dest: pathlib.Path = typer.Option(
        pathlib.Path.cwd(), "--dest", file_okay=False, dir_okay=True
    ),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    files = scan_paths(dirs)
    mapping: list[tuple[pathlib.Path, pathlib.Path]] = []
    for f in files:
        cat = classify(f) or "Unsorted"
        target_dir = dest / cat
        mapping.append((f, generate_name(f, target_dir)))
    xlsx = build_report(mapping, auto_open=False)
    print(f"[bold]Report ready:[/bold] {xlsx}")


@app.command()
def review(
    dirs: list[pathlib.Path] = typer.Argument(..., exists=True, readable=True),
    limit: int = typer.Option(5, "--limit"),
    db: pathlib.Path | None = typer.Option(None, "--db"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    files = scan_paths(dirs)
    rq = ReviewQueue(db_path=db) if db else ReviewQueue()
    rq.upsert_files(files)
    picks = rq.select_for_review(limit=limit)
    for p in picks:
        print(p.as_posix())
    print(f"[bold]{len(picks)} files ready for review[/bold]")


@app.command()
def move(
    dirs: list[pathlib.Path] = typer.Argument(..., exists=True, readable=True),
    dest: pathlib.Path = typer.Option(..., "--dest", file_okay=False, dir_okay=True),
    yes: bool = typer.Option(False, "--yes", help="skip confirmation"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    files = scan_paths(dirs)
    mapping: list[tuple[pathlib.Path, pathlib.Path]] = []
    for f in files:
        cat = classify(f) or "Unsorted"
        target_dir = dest / cat
        mapping.append((f, generate_name(f, target_dir)))
    report = build_report(mapping, auto_open=False)
    print(f"[bold]Report ready:[/bold] {report}")
    if dry_run:
        print("[yellow]Dry-run complete — no files moved.[/yellow]")
        raise typer.Exit()
    if not yes and not typer.confirm("Proceed with move?"):
        raise typer.Exit()
    log = move_with_log(mapping)
    print(f"[green]Move done.[/green] Log: {log}")


@app.command()
def undo(
    log_file: pathlib.Path = typer.Argument(..., exists=True, readable=True),
    yes: bool = typer.Option(False, "--yes", help="skip confirmation"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    if dry_run:
        print("[yellow]Dry-run complete — no changes.[/yellow]")
        raise typer.Exit()
    if not yes and not typer.confirm("Proceed with rollback?"):
        raise typer.Exit()
    rollback(log_file)
    print("[green]Rollback complete.[/green]")
