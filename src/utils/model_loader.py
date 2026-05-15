"""
Singleton model loader.
In a Streamlit app, call load_all() decorated with @st.cache_resource so
models are loaded from disk only once per process.
Outside Streamlit (e.g. tests, scripts), call load_all() directly.
"""
import json
import os
import numpy as np
import pandas as pd
import joblib

MODEL_DIR = "models"
DATA_PATH = "data/processed/tracks_features.csv"


def load_all() -> dict:
    required = [
        f"{MODEL_DIR}/scaler.pkl",
        f"{MODEL_DIR}/pca_model.pkl",
        f"{MODEL_DIR}/kmeans_model.pkl",
        f"{MODEL_DIR}/cluster_metadata.json",
    ]
    missing = [p for p in required if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(
            f"Missing model files: {missing}\n"
            "Run 'python scripts/collect_data.py' then 'python scripts/train_pipeline.py' first."
        )

    scaler = joblib.load(f"{MODEL_DIR}/scaler.pkl")
    pca = joblib.load(f"{MODEL_DIR}/pca_model.pkl")
    kmeans = joblib.load(f"{MODEL_DIR}/kmeans_model.pkl")
    centroids = joblib.load(f"{MODEL_DIR}/cluster_centroids.pkl")

    with open(f"{MODEL_DIR}/cluster_metadata.json") as f:
        metadata = json.load(f)

    tracks_df = pd.read_csv(DATA_PATH) if os.path.exists(DATA_PATH) else pd.DataFrame()

    tsne_path = f"{MODEL_DIR}/tsne_2d.npy"
    tsne_2d = np.load(tsne_path) if os.path.exists(tsne_path) else None

    tsne_indices_path = f"{MODEL_DIR}/tsne_indices.npy"
    tsne_indices = np.load(tsne_indices_path) if os.path.exists(tsne_indices_path) else None

    pca_report_path = f"{MODEL_DIR}/pca_report.json"
    pca_report = json.load(open(pca_report_path)) if os.path.exists(pca_report_path) else {}

    k_eval_path = f"{MODEL_DIR}/k_eval.json"
    k_eval = json.load(open(k_eval_path)) if os.path.exists(k_eval_path) else {}

    return {
        "scaler": scaler,
        "pca": pca,
        "kmeans": kmeans,
        "centroids": centroids,
        "metadata": metadata,
        "tracks_df": tracks_df,
        "tsne_2d": tsne_2d,
        "tsne_indices": tsne_indices,
        "pca_report": pca_report,
        "k_eval": k_eval,
    }
