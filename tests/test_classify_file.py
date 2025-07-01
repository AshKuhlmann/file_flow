import json
from sorter.classifier import classify_file
from sorter.config import Settings


def test_supervised_prediction(tmp_path, monkeypatch):
    f = tmp_path / "file.txt"
    f.write_text("x")

    monkeypatch.setattr("sorter.supervised.predict_category", lambda p: "Docs")
    monkeypatch.setattr("sorter.classifier.load_config", lambda: Settings())

    assert classify_file(f) == "Docs"


def test_rule_based(tmp_path, monkeypatch):
    f = tmp_path / "picture.jpg"
    f.write_bytes(b"x")

    monkeypatch.setattr("sorter.supervised.predict_category", lambda p: None)
    monkeypatch.setattr(
        "sorter.classifier.load_config",
        lambda: Settings(
            classification={"Pictures": {"extensions": [".jpg"]}}
        ),
    )

    assert classify_file(f) == "Pictures"


def test_cluster_label(tmp_path, monkeypatch):
    f = tmp_path / "unknown.bin"
    f.write_bytes(b"x")

    model_path = tmp_path / "model.joblib"
    model_path.touch()
    labels_path = tmp_path / "labels.json"
    labels_path.write_text(json.dumps({"1": "Music"}))

    monkeypatch.setattr("sorter.supervised.predict_category", lambda p: None)
    monkeypatch.setattr(
        "sorter.classifier.load_config", lambda: Settings(fallback_category=None)
    )
    monkeypatch.setattr("sorter.classifier.classify", lambda p, c: None)
    monkeypatch.setattr("sorter.clustering.MODEL_PATH", model_path)
    monkeypatch.setattr("sorter.clustering.LABELS_PATH", labels_path)
    monkeypatch.setattr("sorter.clustering.predict_cluster", lambda p: 1)

    assert classify_file(f) == "Music"


def test_unsorted(tmp_path, monkeypatch):
    f = tmp_path / "mystery.dat"
    f.write_bytes(b"x")

    monkeypatch.setattr("sorter.supervised.predict_category", lambda p: None)
    monkeypatch.setattr(
        "sorter.classifier.load_config", lambda: Settings(fallback_category=None)
    )
    monkeypatch.setattr("sorter.classifier.classify", lambda p, c: None)
    monkeypatch.setattr("sorter.clustering.MODEL_PATH", tmp_path / "no_model")
    monkeypatch.setattr("sorter.clustering.LABELS_PATH", tmp_path / "no_labels")
    monkeypatch.setattr("sorter.clustering.predict_cluster", lambda p: None)

    assert classify_file(f) == "Unsorted"

def test_custom_config_rules(tmp_path, monkeypatch):
    f = tmp_path / "data.xyz"
    f.write_text("x")
    cfg = Settings(classification={"XYZ": {"extensions": [".xyz"]}})
    monkeypatch.setattr("sorter.classifier.load_config", lambda: cfg)
    monkeypatch.setattr("sorter.supervised.predict_category", lambda p: None)
    assert classify_file(f) == "XYZ"


def test_mime_type_classification(monkeypatch, tmp_path):
    f = tmp_path / "foo.bin"
    f.write_bytes(b"x")
    monkeypatch.setattr("magic.from_file", lambda *a, **k: "audio/flac")
    cfg = Settings(classification={"Audio": {"mimetypes": ["audio/flac"]}})
    monkeypatch.setattr("sorter.classifier.load_config", lambda: cfg)
    monkeypatch.setattr("sorter.supervised.predict_category", lambda p: None)
    assert classify_file(f) == "Audio"
