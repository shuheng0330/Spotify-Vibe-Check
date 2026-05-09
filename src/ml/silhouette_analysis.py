import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from sklearn.metrics import silhouette_samples


def plot_silhouette_diagram(X_pca: np.ndarray, labels: np.ndarray, model_name: str) -> plt.Figure:
    mask = labels != -1
    X_clean, labels_clean = X_pca[mask], labels[mask]
    n_clusters = len(set(labels_clean))
    sample_sil = silhouette_samples(X_clean, labels_clean)

    fig, ax = plt.subplots(figsize=(8, 5))
    y_lower = 10
    for cid in sorted(set(labels_clean)):
        vals = np.sort(sample_sil[labels_clean == cid])
        y_upper = y_lower + len(vals)
        ax.fill_betweenx(np.arange(y_lower, y_upper), 0, vals, alpha=0.7)
        ax.text(-0.05, y_lower + len(vals) / 2, str(cid), fontsize=9)
        y_lower = y_upper + 5

    avg = sample_sil.mean()
    ax.axvline(x=avg, color="red", linestyle="--", linewidth=1)
    ax.set_title(f"Silhouette Diagram — {model_name} (avg={avg:.3f})")
    ax.set_xlabel("Silhouette Coefficient")
    ax.set_ylabel("Cluster")
    ax.set_yticks([])
    fig.tight_layout()
    return fig


def plot_explained_variance(pca_report: dict) -> plt.Figure:
    individual = pca_report["individual"]
    cumulative = pca_report["cumulative"]
    x = range(1, len(individual) + 1)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x, individual, alpha=0.6, label="Individual")
    ax.plot(x, cumulative, marker="o", color="red", linewidth=1.5, label="Cumulative")
    ax.axhline(0.95, color="gray", linestyle="--", linewidth=1, label="95% threshold")
    ax.set_xlabel("Principal Component")
    ax.set_ylabel("Explained Variance Ratio")
    ax.set_title("PCA Scree Plot")
    ax.legend()
    ax.set_xticks(list(x))
    fig.tight_layout()
    return fig


def plot_elbow(k_values: list, eval_results: dict) -> plt.Figure:
    inertias = [eval_results[k]["inertia"] for k in k_values]
    silhouettes = [eval_results[k]["silhouette"] for k in k_values]

    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax2 = ax1.twinx()
    ax1.plot(k_values, inertias, marker="o", color="steelblue", label="Inertia")
    ax2.plot(k_values, silhouettes, marker="s", color="darkorange", linestyle="--", label="Silhouette")
    ax1.set_xlabel("Number of Clusters (k)")
    ax1.set_ylabel("Inertia", color="steelblue")
    ax2.set_ylabel("Silhouette Score", color="darkorange")
    ax1.set_title("Elbow Curve & Silhouette Scores")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    fig.tight_layout()
    return fig


def compute_cohesion_separation(X_pca: np.ndarray, labels: np.ndarray) -> pd.DataFrame:
    rows = []
    unique = sorted(set(labels) - {-1})
    centroids = np.array([X_pca[labels == cid].mean(axis=0) for cid in unique])
    for i, cid in enumerate(unique):
        cluster_pts = X_pca[labels == cid]
        cohesion = np.mean(np.linalg.norm(cluster_pts - centroids[i], axis=1))
        other_centroids = np.delete(centroids, i, axis=0)
        if len(other_centroids):
            separation = np.min(np.linalg.norm(other_centroids - centroids[i], axis=1))
        else:
            separation = 0.0
        rows.append({"cluster_id": cid, "cohesion (avg intra-dist)": round(cohesion, 4),
                     "separation (min inter-dist)": round(separation, 4),
                     "ratio (sep/coh)": round(separation / (cohesion + 1e-9), 4)})
    return pd.DataFrame(rows)


def plot_cluster_scatter_2d(X_tsne: np.ndarray, labels: np.ndarray,
                             track_names: list, artist_names: list) -> go.Figure:
    unique_labels = sorted(set(labels))
    fig = go.Figure()
    for cid in unique_labels:
        mask = labels == cid
        label_str = f"Cluster {cid}" if cid != -1 else "Noise"
        fig.add_trace(go.Scatter(
            x=X_tsne[mask, 0], y=X_tsne[mask, 1],
            mode="markers",
            name=label_str,
            marker=dict(size=5, opacity=0.7),
            text=[f"{t}<br>{a}" for t, a in
                  zip(np.array(track_names)[mask], np.array(artist_names)[mask])],
            hovertemplate="%{text}<extra></extra>",
        ))
    fig.update_layout(
        title="t-SNE Cluster Map",
        template="plotly_white",
        xaxis_title="t-SNE 1",
        yaxis_title="t-SNE 2",
        legend_title="Cluster",
        height=520,
    )
    return fig


def generate_analysis_report(eval_dict: dict, cohesion_df: pd.DataFrame) -> str:
    km_sil = eval_dict.get("kmeans_silhouette", 0)
    db_sil = eval_dict.get("dbscan_silhouette", 0)
    winner = eval_dict.get("winner", "kmeans")
    n_clusters = eval_dict.get("kmeans_n_clusters" if winner == "kmeans" else "dbscan_n_clusters", 0)
    avg_coh = cohesion_df["cohesion (avg intra-dist)"].mean() if len(cohesion_df) else 0
    avg_sep = cohesion_df["separation (min inter-dist)"].mean() if len(cohesion_df) else 0

    report = f"""## Cluster Analysis Report

### Dimensionality Reduction
Principal Component Analysis (PCA) was applied to the 10-dimensional audio feature space.
Components were retained to explain at least 95% of the total variance, reducing noise and
decorrelating correlated features such as energy and loudness.

### Clustering Algorithm Comparison
Two unsupervised algorithms were evaluated: **K-Means** and **DBSCAN**.

| Metric | K-Means | DBSCAN |
|--------|---------|--------|
| Silhouette Score | {km_sil:.4f} | {db_sil:.4f} |
| Davies-Bouldin Index | {eval_dict.get('kmeans_davies_bouldin', 0):.4f} | {eval_dict.get('dbscan_davies_bouldin', 0):.4f} |
| Number of Clusters | {eval_dict.get('kmeans_n_clusters', 0)} | {eval_dict.get('dbscan_n_clusters', 0)} |
| Noise Points | 0% | {eval_dict.get('dbscan_noise_pct', 0):.1f}% |

**Selected model: {winner.upper()}** — higher Silhouette Score indicates better-defined cluster boundaries.

### Silhouette Analysis
The Silhouette Coefficient (range: −1 to +1) measures how similar a track is to its own cluster
compared to other clusters. A score above 0.2 indicates reasonable structure. The selected model
achieved a mean Silhouette Score of **{max(km_sil, db_sil):.4f}**, which is typical for continuous
audio feature spaces where genre boundaries are inherently fuzzy.

### Cohesion and Separation
Across the {n_clusters} clusters, the average intra-cluster distance (cohesion) was **{avg_coh:.4f}**
and the average nearest-centroid inter-cluster distance (separation) was **{avg_sep:.4f}**.
A higher separation-to-cohesion ratio indicates more distinct clusters.

### Interpretation
The clustering reveals meaningful acoustic groupings that align with intuitive listening contexts
(e.g., high-energy dance tracks, low-energy acoustic recordings, instrumental focus music).
These groups provide a principled basis for cold-start playlist recommendations without reliance
on genre tags or collaborative filtering signals.
"""
    return report
