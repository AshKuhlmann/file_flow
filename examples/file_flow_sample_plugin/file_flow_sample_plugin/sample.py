from pathlib import Path
from sorter.plugins.base import RenamerPlugin


class SamplePlugin(RenamerPlugin):
    """Example plugin that prefixes filenames."""

    def __init__(self, config=None) -> None:
        super().__init__(config)
        if not self.pattern:
            self.pattern = "sample_{stem}"

    @property
    def name(self) -> str:
        return "sample"

    def rename(self, file_path: Path) -> str | None:
        return self.pattern.format(stem=file_path.stem, ext=file_path.suffix)
