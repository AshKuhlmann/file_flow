# File-Sorter

[![CI](https://github.com/AshKuhlmann/file-sorter/actions/workflows/ci.yml/badge.svg)](https://github.com/AshKuhlmann/file-sorter/actions/workflows/ci.yml) [![Coverage](https://codecov.io/gh/AshKuhlmann/file-sorter/branch/main/graph/badge.svg)](https://codecov.io/gh/AshKuhlmann/file-sorter/branch/main) ![PyPI](https://img.shields.io/pypi/v/file-sorter) [![Docs](https://img.shields.io/badge/docs-online-blue)](https://ashkuhlmann.github.io/file-sorter/)

File-Sorter automatically organizes messy download folders. Point it at a directory and it will classify, rename and move files in seconds.

## Features
- Automatic classification and renaming
- Duplicate detection to keep your folders tidy
- Undo command to roll back the last move
- Desktop GUI for point-and-click usage
- Built-in scheduler for recurring organization
- Stats dashboard to visualize activity

## Quick Demo

![Demo](media/demo.svg)

## Installation
```bash
pip install file-flow
```

## Basic Usage
```bash
file-sorter move ~/Downloads --dest ~/Sorted --dry-run
```

### Custom naming patterns
Use the ``--pattern`` option to change how files are renamed. Supported tokens
include ``{parent}``, ``{date}``, ``{stem}`` and ``{ext}``.
```bash
file-sorter move ~/Downloads --dest ~/Sorted --pattern "{date}-{stem}{ext}"
```

The classifier now recognizes a wide range of common file types out of the box.
Pictures, videos, documents, spreadsheets, presentations, archives, scripts and
more are automatically sorted into matching folders.

Configuration options are defined in a `config.toml` file and validated using
Pydantic for safety and autocomplete support.


## Desktop GUI
After installing, launch with:
```bash
file-sorter-gui
```

## Find Duplicates
```bash
file-sorter dupes ~/Downloads
```

## Scheduling
```bash
file-sorter schedule "0 3 * * *" ~/Downloads --dest ~/Sorted
```

## Analytics
Generate an interactive dashboard from your move logs:
```bash
file-sorter stats ~/Downloads
```

## Undo
Rollback a move operation using the log file path:
```bash
file-sorter undo /path/to/move.log
```

## Review
Update the review queue and display any files that need attention:
```bash
file-sorter review ~/Downloads
```

## Development
Set up pre-commit hooks to automatically run formatting and tests. See [CONTRIBUTING.md](CONTRIBUTING.md) for coding conventions and setup steps:
```bash
pre-commit install
pre-commit install -t pre-push
```
After installation, the following checks run on each commit and push:
- **black** for code formatting
- **flake8** for linting
- **mypy** for type checking (commit and push)
- **pytest** for unit tests
- **poetry lock** to update dependencies when `pyproject.toml` changes
