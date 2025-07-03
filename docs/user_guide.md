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

# Getting Started: A 5-Minute Tutorial

Welcome to File-Flow! Let's organize your messy `Downloads` folder.

### Step 1: Installation

First, install File-Flow using pip:

```bash
pip install file-flow
```

### Step 2: Perform a Dry Run

A "dry run" shows you what changes will be made *without* moving any files. It's a safe way to start.

Open your terminal and run the following command. Replace `~/Downloads` with the path to your downloads folder and `~/Documents/Sorted` with where you want the organized files to go.

```bash
file-flow sort --source ~/Downloads --destination ~/Documents/Sorted --dry-run
```

You'll see output like this, showing the plan:
```
INFO: Plan: Move '~/Downloads/receipt.pdf' to '~/Documents/Sorted/Documents/receipt.pdf'
INFO: Plan: Move '~/Downloads/vacation.jpg' to '~/Documents/Sorted/Images/vacation.jpg'
...
```

### Step 3: Run it for Real!

If you're happy with the plan, run the same command without the `--dry-run` flag to actually move the files.

```bash
file-flow sort --source ~/Downloads --destination ~/Documents/Sorted
```

That's it! Your files are now neatly organized.

### Next Steps

* Learn how to [customize the rules](#configuration).
* Try the [graphical user interface](../README.md#desktop-gui) by running `file-sorter-gui`.
