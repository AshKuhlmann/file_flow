from __future__ import annotations

import pathlib
from typing import Any, Dict, Optional, Union

import json
import logging
import magic  # python-magic

try:  # optional ML modules
    from . import supervised  # type: ignore
except Exception:  # pragma: no cover - optional dep missing
    supervised = None  # type: ignore

try:
    from . import clustering  # type: ignore
except Exception:  # pragma: no cover - optional dep missing
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
            k: v.model_dump() if hasattr(v, "model_dump") else v
            for k, v in config.classification.items()
        }
        fallback_category = config.fallback_category
    else:
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


def classify_file(path: pathlib.Path) -> str:
    """Classify a file using models and fallback logic."""

    # 1. Supervised model prediction (optional)
    if supervised is not None:
        category = supervised.predict_category(path)
        if category:
            log.info("(Predicted: %s)", category)
            return category

    # 2. Explicit rules from user config
    config = load_config()
    rule_category = classify(path, config)
    if rule_category:
        return rule_category

    # 3. Clustering model fallback using stored labels (optional)
    if clustering is not None and clustering.MODEL_PATH.exists():
        cluster_id = clustering.predict_cluster(path)
        if cluster_id is not None and clustering.LABELS_PATH.exists():
            try:
                with open(clustering.LABELS_PATH) as f:
                    labels: dict[str, str] = json.load(f)
                if str(cluster_id) in labels:
                    return labels[str(cluster_id)]
            except Exception:
                pass

    # 4. Final fallback using basic logic
    return rule_category or "Unsorted"
