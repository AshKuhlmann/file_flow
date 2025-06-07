from __future__ import annotations

import pathlib

import typer  # type: ignore[import-not-found]
from rich import print

from . import scan_paths
from .dupes import find_duplicates, delete_older as _delete_older

app = typer.Typer()


@app.command()  # type: ignore[misc]
def dupes(
    dirs: list[pathlib.Path] = typer.Argument(..., exists=True, readable=True),
    delete_older: bool = typer.Option(False, help="auto-delete older copies"),
    hardlink: bool = typer.Option(False, help="replace duplicates with hardlink"),
) -> None:
    files = scan_paths(dirs)
    groups = find_duplicates(files)
    if not groups:
        print("[green]No duplicates detected.")
        raise typer.Exit()
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


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
