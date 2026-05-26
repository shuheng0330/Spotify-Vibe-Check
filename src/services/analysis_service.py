"""Analysis helpers shared by the FastAPI routes.

The Streamlit app rendered these diagnostics directly in-process. The React app
needs the same information as JSON and image routes instead.
"""
from pathlib import Path
from typing import Any

import numpy as np

from src.ml.dimensionality import SCALED_FEATURE_COLS
from src.ml.silhouette_analysis import (
    compute_cohesion_separation,
    generate_analysis_report,
)


MODEL_DIR = Path("models")
PLOT_FILES = {
    "silhouette_diagram": {
        "filename": "silhouette_diagram.png",
        "title": "Silhouette Diagram",
    },
    "scree_plot": {
        "filename": "scree_plot.png",
        "title": "PCA Scree Plot",
    },
    "elbow_curve": {
        "filename": "elbow_curve.png",
        "title": "Elbow Curve",
    },
}
AUDIO_FEATURES = [
    "energy",
    "valence",
    "danceability",
    "acousticness",
    "tempo",
    "speechiness",
    "instrumentalness",
]


def diagnostic_plots() -> dict[str, dict[str, Any]]:
    plots = {}
    for key, info in PLOT_FILES.items():
        path = MODEL_DIR / info["filename"]
        plots[key] = {
            "title": info["title"],
            "available": path.exists(),
            "url": f"/api/analysis/plots/{key}",
        }
    return plots


def get_plot_path(plot_name: str) -> Path | None:
    info = PLOT_FILES.get(plot_name)
    if not info:
        return None
    path = MODEL_DIR / info["filename"]
    return path if path.exists() else None


def cluster_name_lookup(metadata: dict) -> dict[int, str]:
    return {
        int(cluster_id): info.get("name", f"Cluster {cluster_id}")
        for cluster_id, info in metadata.get("clusters", {}).items()
    }


def cohesion_separation_rows(models: dict) -> list[dict[str, Any]]:
    df = models["tracks_df"]
    pca = models.get("pca")
    metadata = models["metadata"]
    if pca is None or "cluster_label" not in df.columns:
        return []
    if any(feature not in df.columns for feature in SCALED_FEATURE_COLS):
        return []

    x_scaled = df[SCALED_FEATURE_COLS].values
    x_pca = pca.transform(x_scaled)
    labels = df["cluster_label"].values
    cohesion_df = compute_cohesion_separation(x_pca, labels)
    cluster_names = cluster_name_lookup(metadata)
    cohesion_df.insert(1, "cluster_name", cohesion_df["cluster_id"].map(cluster_names))
    return cohesion_df.replace({np.nan: None}).to_dict(orient="records")


def analysis_report(models: dict, cohesion_rows: list[dict[str, Any]]) -> str:
    if not cohesion_rows:
        return ""
    import pandas as pd

    cohesion_df = pd.DataFrame(cohesion_rows).drop(columns=["cluster_name"], errors="ignore")
    return generate_analysis_report(models["metadata"].get("evaluation", {}), cohesion_df)


def feature_distributions(models: dict) -> dict[str, Any]:
    df = models["tracks_df"]
    metadata = models["metadata"]
    if "cluster_label" not in df.columns:
        return {"features": [], "distributions": {}}

    cluster_names = cluster_name_lookup(metadata)
    df_plot = df[df["cluster_label"] != -1].copy()
    features = [feature for feature in AUDIO_FEATURES if feature in df_plot.columns]
    distributions: dict[str, list[dict[str, Any]]] = {}

    for feature in features:
        rows = []
        for cluster_id, group in df_plot.groupby("cluster_label"):
            values = group[feature].dropna()
            if values.empty:
                continue
            cid = int(cluster_id)
            rows.append(
                {
                    "cluster_id": cid,
                    "cluster_name": cluster_names.get(cid, f"Cluster {cid}"),
                    "count": int(values.count()),
                    "min": float(values.min()),
                    "q1": float(values.quantile(0.25)),
                    "median": float(values.median()),
                    "q3": float(values.quantile(0.75)),
                    "max": float(values.max()),
                    "mean": float(values.mean()),
                }
            )
        distributions[feature] = rows

    return {"features": features, "distributions": distributions}
