from __future__ import annotations

import pathlib
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel

import logging
import magic  # python-magic

try:  # optional ML modules
    from . import supervised  # type: ignore
except ImportError:  # pragma: no cover - optional dep missing
    supervised = None  # type: ignore

try:
    from . import clustering  # type: ignore
except ImportError:  # pragma: no cover - optional dep missing
    clustering = None  # type: ignore
from .config import Settings

log = logging.getLogger(__name__)


class RuleMatcher:
    """Encapsulates the logic for matching a file against a rule."""

    def __init__(self, file_path: pathlib.Path, rule: Dict[str, Any]):
        self.file_path = file_path
        self.rule = rule
        self._mime_type: Optional[str] = None

    @property
    def mime_type(self) -> str:
        """Lazily compute the MIME type for the file."""
        if self._mime_type is None:
            self._mime_type = magic.from_file(self.file_path.as_posix(), mime=True)
        return self._mime_type

    def match(self) -> bool:
        """Return True if the file matches the rule."""
        if "extensions" in self.rule:
            if self._match_by_extension():
                return True
        if "mimetypes" in self.rule:
            if self._match_by_mime_type():
                return True
        return False

    def _match_by_extension(self) -> bool:
        return self.file_path.suffix.lower() in self.rule.get("extensions", [])

    def _match_by_mime_type(self) -> bool:
        return self.mime_type in self.rule.get("mimetypes", [])


def classify(
    path: pathlib.Path,
    config: Union[Dict[str, Any], Settings],
) -> Optional[str]:
    """Return category label for *path* based on provided config."""
    if isinstance(config, Settings):
        classification_rules = {
            k: v.dict() if isinstance(v, BaseModel) else v
            for k, v in config.classification.items()
        }
        fallback_category = config.fallback_category
    else:
        classification_rules = config.get("classification", {})
        fallback_category = config.get("fallback_category", "Other")

    # 1. Check for a match in the classification rules (by extension or mimetype)
    for category, rules in classification_rules.items():
        if path.suffix.lower() in rules.get("extensions", []):
            log.debug("extension rule match for %s -> %s", path.name, category)
            return category
        if _matches_mimetype(path, rules.get("mimetypes", [])):
            log.debug("mimetype rule match for %s -> %s", path.name, category)
            return category

    # 2. Fallback to a generic category based on the major mimetype
    return _get_generic_category(path) or fallback_category


def _matches_mimetype(path: pathlib.Path, mimetypes: list[str]) -> bool:
    """Check if the file's mimetype is in the provided list."""
    if not mimetypes:
        return False
    try:
        mime = magic.from_file(path.as_posix(), mime=True)
        return mime in mimetypes
    except OSError as exc:
        log.warning("Could not determine mimetype for %s: %s", path, exc)
        return False


def _get_generic_category(path: pathlib.Path) -> Optional[str]:
    """Get a generic category based on the file's major mimetype."""
    try:
        mime = magic.from_file(path.as_posix(), mime=True)
        major, _, _ = mime.partition("/")
        category = {
            "video": "Videos",
            "audio": "Audio",
            "image": "Images",
            "text": "Documents",
            "application": "Documents",
        }.get(major)
        log.debug("mime %s -> generic category %s", mime, category)
        return category
    except OSError as exc:
        log.warning("Could not inspect file %s: %s", path, exc)
        return None


def classify_file(file_path: pathlib.Path, rules: Dict[str, Any]) -> Optional[str]:
    """Classify ``file_path`` using a dictionary of ``rules``."""

    # Sort rules by priority, highest first. Missing priority defaults to 0.
    sorted_rules = sorted(
        rules.items(),
        key=lambda item: item[1].get("priority", 0),
        reverse=True,
    )

    for destination, rule_config in sorted_rules:
        matcher = RuleMatcher(file_path, rule_config)
        if matcher.match():
            return rule_config.get("destination", destination)
    return None
