import pathlib
import joblib
import logging
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline

from .ml_features import extract_raw_features, create_feature_pipeline

log = logging.getLogger(__name__)

MODEL_PATH = pathlib.Path.home() / ".file-sorter" / "cluster_model.joblib"
LABELS_PATH = pathlib.Path.home() / ".file-sorter" / "cluster_labels.json"


def train_cluster_model(file_paths: list[pathlib.Path], n_clusters: int = 10):
    """Train a K-Means clustering model and save it."""
    log.info("Extracting features from files...")
    df = extract_raw_features(file_paths)
    if df.empty:
        log.info("No valid files found to process.")
        return

    feature_pipeline = create_feature_pipeline()

    model_pipeline = Pipeline(
        steps=[
            ("features", feature_pipeline),
            (
                "clusterer",
                KMeans(n_clusters=n_clusters, random_state=42, n_init="auto"),
            ),
        ]
    )

    log.info("Training K-Means model to find %d clusters...", n_clusters)
    model_pipeline.fit(df)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model_pipeline, MODEL_PATH)
    log.info("Clustering model saved to %s", MODEL_PATH)

    df["cluster"] = model_pipeline.predict(df)
    return df[["path", "cluster"]]


def predict_cluster(file_path: pathlib.Path) -> int | None:
    """Predict the cluster for a single file."""
    if not MODEL_PATH.exists():
        return None

    model = joblib.load(MODEL_PATH)
    df = extract_raw_features([file_path])
    if df.empty:
        return None

    prediction = model.predict(df)
    return prediction[0]
