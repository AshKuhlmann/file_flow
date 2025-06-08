import pathlib
import tomllib
from typing import Any, Dict

DEFAULT_CONFIG_PATH = pathlib.Path.home() / ".file-sorter" / "config.toml"


def load_config(path: pathlib.Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load the TOML configuration file."""
    if not path.exists():
        return {}
    with path.open("rb") as fp:
        return tomllib.load(fp)


# Default classification rules used when no config is provided
DEFAULT_RULES = {
    "Pictures": {"extensions": [".jpg", ".jpeg", ".png", ".gif"]},
    "Videos": {"extensions": [".mp4", ".mov", ".avi"]},
}
