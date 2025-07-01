import pathlib
from unittest.mock import patch

from sorter import clustering


def test_train_cluster_model(tmp_path: pathlib.Path):
    """Verify that the clustering model can be trained and used."""
    # Create dummy files with distinct content
    (tmp_path / "file1.txt").write_text("This is a test file about dogs.")
    (tmp_path / "file2.txt").write_text("This is another test file about dogs.")
    (tmp_path / "file3.txt").write_text("This is a file about cats.")
    (tmp_path / "file4.txt").write_text("This is another file about cats.")

    files = list(tmp_path.glob("*.txt"))

    with patch("sorter.clustering.KMeans") as mock_kmeans:
        clustered_df = clustering.train_cluster_model(files)

    # Check that the model was trained and files were clustered
    assert clustered_df is not None
    assert "cluster" in clustered_df.columns
    assert len(clustered_df) == 4
    # Verify that KMeans was called multiple times to find the best k
    assert mock_kmeans.call_count > 1

def test_train_cluster_model_integration(tmp_path, monkeypatch):
    (tmp_path / "a1.txt").write_text("dog dog dog")
    (tmp_path / "a2.txt").write_text("dog dog")
    (tmp_path / "b1.txt").write_text("cat cat")
    (tmp_path / "b2.txt").write_text("cat")
    files = sorted(tmp_path.glob("*.txt"))
    monkeypatch.setattr(clustering, "MODEL_PATH", tmp_path / "model.joblib")
    monkeypatch.setattr(clustering, "silhouette_score", lambda X, y: 1.0)
    monkeypatch.setitem(clustering.__dict__, "range", lambda *a: [2])
    df = clustering.train_cluster_model(files)
    assert df is not None
    assert clustering.MODEL_PATH.exists()
    assert "cluster" in df.columns
