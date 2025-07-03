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

[classification.Images]
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

## Writing Renamer Plugins

File-Sorter can be extended with third-party plugins that implement
`RenamerPlugin`. Plugins are discovered via the `file_flow.renamers`
entry point.

```python
from pathlib import Path
from sorter.plugins.base import RenamerPlugin


class SamplePlugin(RenamerPlugin):
    @property
    def name(self) -> str:
        return "sample"

    def rename(self, file_path: Path) -> str | None:
        return self.pattern.format(stem=file_path.stem, ext=file_path.suffix)
```

Expose the plugin in your `pyproject.toml`:

```toml
[project.entry-points."file_flow.renamers"]
sample = "file_flow_sample_plugin.sample:SamplePlugin"
```

Enable it in `config.toml` with optional configuration keys
`enabled` and `pattern`:

```toml
[plugins.sample]
enabled = true
pattern = "{stem}"
```

See `examples/file_flow_sample_plugin` for a complete example package.

## Analytics
After moving files you can generate a dashboard:
```bash
file-sorter stats ~/Downloads
```

## FAQ
- **Does it work on Windows?** Yes, via Python 3.9+.
- **Is it safe?** Use `--dry-run` first to preview actions.
