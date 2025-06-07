# File-Sorter

![CI](https://github.com/<ORG>/file-sorter/actions/workflows/ci.yml/badge.svg) ![Coverage](https://codecov.io/gh/<ORG>/file-sorter/branch/main/graph/badge.svg) ![PyPI](https://img.shields.io/pypi/v/file-sorter) ![Docs](https://img.shields.io/badge/docs-online-blue)

File-Sorter automatically organizes messy download folders. Point it at a directory and it will classify, rename and move files in seconds.

## Quick Demo

![Demo](media/demo.svg)

## Installation
```bash
pip install file-sorter
```

## Basic Usage
```bash
file-sorter move ~/Downloads --dest ~/Sorted --dry-run
```


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

## Development
Set up pre-commit hooks to automatically run formatting and tests:
```bash
pre-commit install
```
After installation, the following checks run on each commit:
- **black** for code formatting
- **flake8** for linting
- **mypy** for type checking
- **pytest** for unit tests
