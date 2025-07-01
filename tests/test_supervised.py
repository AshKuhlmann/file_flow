import json
import pandas as pd
from sklearn.preprocessing import FunctionTransformer
from sklearn.pipeline import Pipeline
from sorter import supervised


def test_supervised_training_and_prediction(tmp_path, monkeypatch):
    log_file = tmp_path / "file-sort-log_1.jsonl"
    record = {"src": str(tmp_path / "a.txt"), "dst": "", "category": "Docs", "sha256": "", "size": 1, "epoch": 0}
    log_file.write_text(json.dumps(record) + "\n")

    def fake_extract(paths):
        return pd.DataFrame({
            "path": paths,
            "file_size": [1],
            "file_extension": [".txt"],
            "file_name_text": ["a"],
            "modification_hour": [0],
            "modification_day": [0],
            "content": ["text"],
        })

    class DummyModel:
        def fit(self, X, y):
            self.label = y[0]
        def predict(self, X):
            return [self.label]

    monkeypatch.setattr(supervised, "MODEL_PATH", tmp_path / "model.joblib")
    monkeypatch.setattr(supervised, "extract_raw_features", fake_extract)
    monkeypatch.setattr(supervised, "create_feature_pipeline", lambda: FunctionTransformer(lambda x: x))
    monkeypatch.setattr(supervised, "RandomForestClassifier", lambda **k: DummyModel())
    stored = {}
    def fake_dump(obj, path):
        stored['obj'] = obj["model"]
        open(path, "wb").write(b"model")
    def fake_load(path):
        return {"model": stored['obj'], "labels": supervised.LabelEncoder().fit(["Docs"])}
    monkeypatch.setattr(supervised.joblib, "dump", fake_dump)
    monkeypatch.setattr(supervised.joblib, "load", fake_load)

    supervised.train_supervised_model(tmp_path)
    assert supervised.MODEL_PATH.exists()
    cat = supervised.predict_category(tmp_path / "a.txt")
    assert cat == "Docs"
