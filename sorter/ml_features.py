import pathlib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


def extract_raw_features(file_paths: list[pathlib.Path]) -> pd.DataFrame:
    """Extract raw features from a list of file paths into a DataFrame."""
    features = []
    for path in file_paths:
        try:
            stat = path.stat()
            features.append(
                {
                    "path": path,
                    "file_size": stat.st_size,
                    "file_extension": path.suffix.lower() or ".none",
                    "file_name_text": path.stem,
                    "modification_hour": pd.to_datetime(stat.st_mtime, unit="s").hour,
                    "modification_day": pd.to_datetime(
                        stat.st_mtime, unit="s"
                    ).dayofweek,
                }
            )
        except (FileNotFoundError, PermissionError):
            continue
    return pd.DataFrame(features)


def create_feature_pipeline() -> Pipeline:
    """Create sklearn pipeline to process feature DataFrame."""
    numeric_features = ["file_size", "modification_hour", "modification_day"]
    numeric_transformer = StandardScaler()

    categorical_features = ["file_extension"]
    categorical_transformer = OneHotEncoder(handle_unknown="ignore")

    text_features = "file_name_text"
    text_transformer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5))

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
            ("text", text_transformer, text_features),
        ],
        remainder="drop",
        n_jobs=-1,
    )

    return Pipeline(steps=[("preprocessor", preprocessor)])
