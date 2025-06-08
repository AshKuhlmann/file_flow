from __future__ import annotations

import pathlib
from typing import Any, Dict, Optional

import magic  # python-magic


def classify(path: pathlib.Path, config: Dict[str, Any]) -> Optional[str]:
    """Return category label for *path* based on provided config."""
    classification_rules = config.get("classification", {})
    fallback_category = config.get("fallback_category", "Other")

    for category, rules in classification_rules.items():
        if path.suffix.lower() in rules.get("extensions", []):
            return category
        try:
            mime = magic.from_file(path.as_posix(), mime=True)
            if mime in rules.get("mimetypes", []):
                return category
        except Exception:
            pass

    try:
        mime = magic.from_file(path.as_posix(), mime=True)
        major = mime.split("/", 1)[0]
        if major in ["video", "audio", "image", "text", "application"]:
            return {
                "video": "Videos",
                "audio": "Audio",
                "image": "Pictures",
                "text": "Documents",
                "application": "Documents",
            }.get(major)
    except Exception:
        return fallback_category

    return fallback_category
