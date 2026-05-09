import json
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score

from src.data.preprocessor import CONTINUOUS_FEATURES

CLUSTER_NAME_RULES = [
    ("Party Anthems",    {"energy": (0.7, 1), "valence": (0.6, 1), "danceability": (0.65, 1)}),
    ("Dark Drive",       {"energy": (0.7, 1), "valence": (0, 0.45), "loudness": (-8, 0)}),
    ("Focus Flow",       {"instrumentalness": (0.4, 1), "speechiness": (0, 0.15)}),
    ("Acoustic Chill",   {"acousticness": (0.6, 1), "energy": (0, 0.5)}),
    ("Feel-Good Vibes",  {"valence": (0.65, 1), "energy": (0.4, 0.75)}),
    ("Rap & Spoken Word",{"speechiness": (0.2, 1)}),
    ("Sunny Afternoon",  {"valence": (0.55, 1), "energy": (0, 0.5)}),
    ("Live & Raw",       {"liveness": (0.5, 1)}),
]


def _name_cluster(centroid: dict) -> str:
    best_name, best_score = "Mixed Vibes", 0
    for name, rules in CLUSTER_NAME_RULES:
        score = sum(
            1 for feat, (lo, hi) in rules.items()
            if lo <= centroid.get(feat, 0) <= hi
        )
        ratio = score / len(rules)
        if ratio > best_score:
            best_score, best_name = ratio, name
    return best_name


def find_optimal_k(X_pca: np.ndarray, k_range=range(4, 16)) -> dict:
    results = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_pca)
        sil = silhouette_score(X_pca, labels)
        results[k] = {"inertia": km.inertia_, "silhouette": sil}
        print(f"  k={k:2d}  inertia={km.inertia_:,.0f}  silhouette={sil:.4f}")
    return results


def fit_kmeans(X_pca: np.ndarray, n_clusters: int) -> tuple[KMeans, np.ndarray]:
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    labels = km.fit_predict(X_pca)
    return km, labels


def fit_dbscan(X_pca: np.ndarray, eps: float = 0.8, min_samples: int = 10) -> tuple[DBSCAN, np.ndarray]:
    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(X_pca)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_pct = (labels == -1).mean() * 100
    print(f"DBSCAN: {n_clusters} clusters, {noise_pct:.1f}% noise")
    return db, labels


def evaluate_clustering(X_pca: np.ndarray, labels: np.ndarray, method: str) -> dict:
    mask = labels != -1
    if mask.sum() < 2 or len(set(labels[mask])) < 2:
        return {"method": method, "silhouette": -1, "davies_bouldin": 999, "n_clusters": 0, "noise_pct": 100.0}
    sil = silhouette_score(X_pca[mask], labels[mask])
    db_score = davies_bouldin_score(X_pca[mask], labels[mask])
    n_clusters = len(set(labels[mask]))
    noise_pct = (labels == -1).mean() * 100
    print(f"{method}: silhouette={sil:.4f}  davies_bouldin={db_score:.4f}  clusters={n_clusters}")
    return {
        "method": method,
        "silhouette": round(sil, 4),
        "davies_bouldin": round(db_score, 4),
        "n_clusters": n_clusters,
        "noise_pct": round(noise_pct, 2),
    }


def select_best_model(kmeans_eval: dict, dbscan_eval: dict) -> str:
    if dbscan_eval["silhouette"] < 0:
        return "kmeans"
    return "kmeans" if kmeans_eval["silhouette"] >= dbscan_eval["silhouette"] else "dbscan"


def build_cluster_metadata(
    df_features: pd.DataFrame,
    labels: np.ndarray,
    kmeans_eval: dict,
    dbscan_eval: dict,
    winner: str,
) -> dict:
    df = df_features.copy()
    df["cluster_label"] = labels

    clusters = {}
    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        subset = df[df["cluster_label"] == cid]
        centroid = {feat: round(float(subset[feat].mean()), 4) for feat in CONTINUOUS_FEATURES}
        name = _name_cluster(centroid)
        top_artists = subset["artist_name"].value_counts().head(5).index.tolist()
        rep_tracks = subset.nlargest(5, "popularity")[["track_id", "track_name", "artist_name"]].to_dict("records")
        clusters[str(cid)] = {
            "name": name,
            "track_count": int(len(subset)),
            "centroid": centroid,
            "top_artists": top_artists,
            "representative_tracks": rep_tracks,
        }

    metadata = {
        "clusters": clusters,
        "evaluation": {
            "kmeans_silhouette": kmeans_eval["silhouette"],
            "kmeans_davies_bouldin": kmeans_eval["davies_bouldin"],
            "kmeans_n_clusters": kmeans_eval["n_clusters"],
            "dbscan_silhouette": dbscan_eval["silhouette"],
            "dbscan_davies_bouldin": dbscan_eval["davies_bouldin"],
            "dbscan_n_clusters": dbscan_eval["n_clusters"],
            "dbscan_noise_pct": dbscan_eval["noise_pct"],
            "winner": winner,
        },
    }
    return metadata


def save_models(kmeans: KMeans, dbscan: DBSCAN, centroids: np.ndarray, metadata: dict, path_prefix: str) -> None:
    joblib.dump(kmeans, f"{path_prefix}/kmeans_model.pkl")
    joblib.dump(dbscan, f"{path_prefix}/dbscan_model.pkl")
    joblib.dump(centroids, f"{path_prefix}/cluster_centroids.pkl")
    with open(f"{path_prefix}/cluster_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Models saved to {path_prefix}/")
