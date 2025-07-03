# User Guide

## Installation
```bash
pip install file-flow
```

## Configuration
File-Sorter reads settings from `config.toml` and validates them using
Pydantic. Copy the example file and modify as needed.
Default rules for common extensions are loaded from `data/default_rules.toml`.

Here is a minimal configuration showing how to add custom categories and enable
plugins:

```toml
fallback_category = "Other"

[classification.Pictures]
extensions = [".jpg", ".png"]

[plugins.exif]
enabled = true
pattern = "{year}-{month}-{day}_{model}"
```

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
