import pathlib
import json
import joblib
import logging
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from .ml_features import extract_raw_features, create_feature_pipeline

MODEL_PATH = pathlib.Path.home() / ".file-sorter" / "supervised_model.joblib"

log = logging.getLogger(__name__)


def train_supervised_model(logs_dir: pathlib.Path):
    """Train a Random Forest model from log files."""
    log_files = list(logs_dir.glob("file-sort-log_*.jsonl"))
    if not log_files:
        log.info(
            "No log files found. Sort some files first to create training data."
        )
        return

    records = []
    for log_file in log_files:
        with open(log_file, "r") as f:
            for line in f:
                records.append(json.loads(line))

    log_df = pd.DataFrame(records)
    log_df["path"] = log_df["src"].apply(pathlib.Path)

    log.info("Loaded %d records from logs.", len(log_df))

    feature_df = extract_raw_features(log_df["path"].tolist())
    training_df = pd.merge(feature_df, log_df[["path", "category"]], on="path")

    X = training_df
    y = training_df["category"]

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    feature_pipeline = create_feature_pipeline()

    model_pipeline = Pipeline(
        steps=[
            ("features", feature_pipeline),
            (
                "classifier",
                RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
            ),
        ]
    )

    log.info("Training supervised classification model...")
    model_pipeline.fit(X, y_encoded)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"model": model_pipeline, "labels": label_encoder}, MODEL_PATH)
    log.info("Supervised model saved to %s", MODEL_PATH)


def predict_category(file_path: pathlib.Path) -> str | None:
    """Predict the category for a single file."""
    if not MODEL_PATH.exists():
        return None

    data = joblib.load(MODEL_PATH)
    model = data["model"]
    label_encoder = data["labels"]

    df = extract_raw_features([file_path])
    if df.empty:
        return None

    prediction_encoded = model.predict(df)
    category = label_encoder.inverse_transform(prediction_encoded)
    return category[0]
