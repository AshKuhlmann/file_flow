# User Guide

## Installation
```bash
pip install file-flow
```

## Configuration
File-Sorter reads rules from `default_rules.toml`. Copy it and modify as needed.

## Example Usage
```bash
file-sorter move ~/Downloads --dest ~/Sorted --dry-run
```

## FAQ
- **Does it work on Windows?** Yes, via Python 3.9+.
- **Is it safe?** Use `--dry-run` first to preview actions.
