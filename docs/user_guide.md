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

### Custom naming patterns
You can customize how files are renamed using the ``--pattern`` option. The
pattern can contain ``{parent}``, ``{date}``, ``{stem}`` and ``{ext}`` tokens.
For example:
```bash
file-sorter move ~/Downloads --dest ~/Sorted --pattern "{date}-{stem}{ext}"
```

## Analytics
After moving files you can generate a dashboard:
```bash
file-sorter stats ~/Downloads
```

## FAQ
- **Does it work on Windows?** Yes, via Python 3.9+.
- **Is it safe?** Use `--dry-run` first to preview actions.
