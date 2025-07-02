from __future__ import annotations

import pathlib
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel

import json
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
from .config import load_config, Settings

log = logging.getLogger(__name__)


def classify(
    path: pathlib.Path,
    config: Union[Dict[str, Any], Settings],
) -> Optional[str]:
    """Return category label for *path* based on provided config."""
    if isinstance(config, Settings):
        classification_rules = {
            k: v.model_dump() if isinstance(v, BaseModel) else v
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
            "image": "Pictures",
            "text": "Documents",
            "application": "Documents",
        }.get(major)
        log.debug("mime %s -> generic category %s", mime, category)
        return category
    except OSError as exc:
        log.warning("Could not inspect file %s: %s", path, exc)
        return None


def classify_file(path: pathlib.Path) -> str:
    """Classify a file using models and fallback logic."""

    # 1. Supervised model prediction (optional)
    if supervised is not None:
        category = supervised.predict_category(path)
        if category:
            log.info("(Predicted: %s)", category)
            log.debug("final category from supervised model: %s", category)
            return category

    # 2. Explicit rules from user config
    config = load_config()
    rule_category = classify(path, config)
    if rule_category:
        log.debug("final category from rule-based rules: %s", rule_category)
        return rule_category

    # 3. Clustering model fallback using stored labels (optional)
    if clustering is not None and clustering.MODEL_PATH.exists():
        cluster_id = clustering.predict_cluster(path)
        if cluster_id is not None and clustering.LABELS_PATH.exists():
            try:
                with open(clustering.LABELS_PATH) as f:
                    labels: dict[str, str] = json.load(f)
                if str(cluster_id) in labels:
                    label = labels[str(cluster_id)]
                    log.debug(
                        "final category from cluster label %s: %s",
                        cluster_id,
                        label,
                    )
                    return label
            except (OSError, json.JSONDecodeError) as exc:
                log.warning("Could not read cluster labels: %s", exc)

    # 4. Final fallback using basic logic
    final = rule_category or "Unsorted"
    log.debug("final category from fallback: %s", final)
    return final
