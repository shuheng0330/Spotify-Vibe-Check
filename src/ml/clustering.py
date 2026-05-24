import json
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.neighbors import NearestNeighbors

from src.data.preprocessor import CONTINUOUS_FEATURES

CLUSTER_NAME_RULES = [
    ("Party Anthems",    {"energy": (0.7, 1), "valence": (0.6, 1), "danceability": (0.65, 1)}),
    ("Dark Drive",       {"energy": (0.7, 1), "valence": (0, 0.45)}),
    ("Focus Flow",       {"instrumentalness": (0.4, 1), "speechiness": (0, 0.15)}),
    ("Acoustic Chill",   {"acousticness": (0.6, 1), "energy": (0, 0.5)}),
    ("Feel-Good Vibes",  {"valence": (0.65, 1), "energy": (0.4, 0.75)}),
    ("Rap & Spoken Word",{"speechiness": (0.2, 1)}),
    ("Sunny Afternoon",  {"valence": (0.55, 1), "energy": (0, 0.5)}),
]


def _rank_cluster_names(centroid: dict) -> list[tuple[str, float]]:
    scores = []
    for name, rules in CLUSTER_NAME_RULES:
        matched, depth_sum = 0, 0.0
        for feat, (lo, hi) in rules.items():
            v = centroid.get(feat, 0)
            if lo <= v <= hi:
                matched += 1
                half = (hi - lo) / 2
                mid = lo + half
                depth_sum += 1.0 - abs(v - mid) / half if half > 0 else 1.0
        if matched:
            scores.append((name, round((matched / len(rules)) * (depth_sum / matched), 4)))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def find_optimal_k(X_pca: np.ndarray, k_range=range(3, 15)) -> dict:
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


def fit_dbscan(X_pca: np.ndarray, min_samples: int = 5) -> tuple[DBSCAN, np.ndarray, float]:
    # Estimate eps via k-distance at the 80th percentile on a subsample
    rng = np.random.default_rng(42)
    sample_n = min(10_000, len(X_pca))
    idx = rng.choice(len(X_pca), size=sample_n, replace=False)
    nbrs = NearestNeighbors(n_neighbors=min_samples).fit(X_pca[idx])
    distances, _ = nbrs.kneighbors(X_pca[idx])
    eps = float(np.percentile(np.sort(distances[:, -1]), 80))
    print(f"  DBSCAN auto-eps={eps:.4f}  min_samples={min_samples}")
    dbscan = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)
    labels = dbscan.fit_predict(X_pca)
    return dbscan, labels, eps


def fit_gmm(X_pca: np.ndarray, n_components: int) -> tuple[GaussianMixture, np.ndarray]:
    gmm = GaussianMixture(n_components=n_components, random_state=42, n_init=3)
    labels = gmm.fit_predict(X_pca)
    return gmm, labels


def select_best_model(km_eval: dict, gmm_eval: dict) -> str:
    return "gmm" if gmm_eval["silhouette"] > km_eval["silhouette"] else "kmeans"


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


def build_cluster_metadata(
    df_features: pd.DataFrame,
    labels: np.ndarray,
    winner_eval: dict,
    km_eval: dict | None = None,
    gmm_eval: dict | None = None,
    dbscan_eval: dict | None = None,
) -> dict:
    df = df_features.copy()
    df["cluster_label"] = labels

    # Pass 1: compute centroids and ranked name candidates for every cluster
    cluster_rankings: dict[int, tuple[dict, list]] = {}
    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        subset = df[df["cluster_label"] == cid]
        centroid = {feat: round(float(subset[feat].mean()), 4) for feat in CONTINUOUS_FEATURES}
        cluster_rankings[cid] = (centroid, _rank_cluster_names(centroid))

    # Pass 2: greedy unique assignment — highest-scoring cluster claims each name first
    all_picks = [
        (score, cid, name)
        for cid, (_, rankings) in cluster_rankings.items()
        for name, score in rankings
    ]
    all_picks.sort(reverse=True, key=lambda x: x[0])
    assigned_names: dict[int, str] = {}
    used_names: set[str] = set()
    for _, cid, name in all_picks:
        if cid not in assigned_names and name not in used_names:
            assigned_names[cid] = name
            used_names.add(name)
    for cid in cluster_rankings:
        if cid not in assigned_names:
            assigned_names[cid] = "Mixed Vibes"

    clusters = {}
    for cid, (centroid, _) in cluster_rankings.items():
        subset = df[df["cluster_label"] == cid]
        top_artists = subset["artist_name"].value_counts().head(5).index.tolist()
        rep_tracks = subset.nlargest(5, "popularity")[["track_id", "track_name", "artist_name"]].to_dict("records")
        clusters[str(cid)] = {
            "name": assigned_names[cid],
            "track_count": int(len(subset)),
            "centroid": centroid,
            "top_artists": top_artists,
            "representative_tracks": rep_tracks,
        }

    def _eval_summary(e: dict) -> dict:
        return {
            "silhouette": e["silhouette"],
            "davies_bouldin": e["davies_bouldin"],
            "n_clusters": e["n_clusters"],
            "noise_pct": e.get("noise_pct", 0.0),
        }

    metadata = {
        "clusters": clusters,
        "evaluation": {
            "algorithm": winner_eval["method"],
            "silhouette": winner_eval["silhouette"],
            "davies_bouldin": winner_eval["davies_bouldin"],
            "n_clusters": winner_eval["n_clusters"],
            "kmeans": _eval_summary(km_eval) if km_eval else {},
            "gmm": _eval_summary(gmm_eval) if gmm_eval else {},
            "dbscan": _eval_summary(dbscan_eval) if dbscan_eval else {},
        },
    }
    return metadata


def save_models(model, centroids: np.ndarray, metadata: dict, path_prefix: str) -> None:
    joblib.dump(model, f"{path_prefix}/kmeans_model.pkl")
    joblib.dump(centroids, f"{path_prefix}/cluster_centroids.pkl")
    with open(f"{path_prefix}/cluster_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Models saved to {path_prefix}/")
