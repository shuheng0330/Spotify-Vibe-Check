"""
Member B — Run once after collect_data.py to train and save all models.

Usage:
    python scripts/train_pipeline.py
"""
import sys
import os
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import joblib

from src.ml.dimensionality import (
    SCALED_FEATURE_COLS, fit_pca, fit_tsne,
    get_explained_variance_report, save_pca,
)
from src.ml.clustering import (
    find_optimal_k, fit_kmeans, fit_dbscan,
    evaluate_clustering, select_best_model,
    build_cluster_metadata, save_models,
)
from src.ml.silhouette_analysis import plot_silhouette_diagram, plot_explained_variance, plot_elbow

PROCESSED_CSV = "data/processed/tracks_features.csv"
MODEL_DIR = "models"

if __name__ == "__main__":
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Loading processed features...")
    df = pd.read_csv(PROCESSED_CSV)
    X = df[SCALED_FEATURE_COLS].values
    print(f"  Feature matrix: {X.shape}")

    print("\nStep 1: PCA")
    pca, X_pca, n_comp = fit_pca(X)
    save_pca(pca, f"{MODEL_DIR}/pca_model.pkl")
    pca_report = get_explained_variance_report(pca)

    print("\nStep 2: t-SNE (2D for visualization)")
    X_tsne = fit_tsne(X_pca)
    np.save(f"{MODEL_DIR}/tsne_2d.npy", X_tsne)

    print("\nStep 3: Finding optimal k for KMeans...")
    k_eval = find_optimal_k(X_pca, range(4, 16))
    best_k = max(k_eval, key=lambda k: k_eval[k]["silhouette"])
    print(f"\nBest k = {best_k}")

    print(f"\nStep 4: Fitting KMeans (k={best_k})")
    kmeans, km_labels = fit_kmeans(X_pca, best_k)
    km_eval = evaluate_clustering(X_pca, km_labels, "KMeans")

    print("\nStep 5: Fitting DBSCAN")
    dbscan, db_labels = fit_dbscan(X_pca, eps=0.8, min_samples=10)
    db_eval = evaluate_clustering(X_pca, db_labels, "DBSCAN")

    print("\nStep 6: Selecting best model")
    winner = select_best_model(km_eval, db_eval)
    print(f"  Winner: {winner.upper()}")

    winner_labels = km_labels if winner == "kmeans" else db_labels
    unique_clusters = sorted(set(winner_labels) - {-1})
    centroids_original = np.array([
        df[[c.replace("_scaled", "") for c in SCALED_FEATURE_COLS]].values[winner_labels == cid].mean(axis=0)
        for cid in unique_clusters
    ])
    joblib.dump(centroids_original, f"{MODEL_DIR}/cluster_centroids.pkl")
    df["cluster_label"] = winner_labels

    print("\nStep 7: Building cluster metadata")
    from src.data.preprocessor import CONTINUOUS_FEATURES
    metadata = build_cluster_metadata(df, winner_labels, km_eval, db_eval, winner)
    metadata["tsne_available"] = True

    print("\nStep 8: Saving models")
    save_models(kmeans, dbscan, centroids_original, metadata, MODEL_DIR)
    df.to_csv(PROCESSED_CSV, index=False)

    print("\nStep 9: Saving diagnostic plots")
    fig_sil = plot_silhouette_diagram(X_pca, winner_labels, winner.upper())
    fig_sil.savefig(f"{MODEL_DIR}/silhouette_diagram.png", dpi=120)

    fig_scree = plot_explained_variance(pca_report)
    fig_scree.savefig(f"{MODEL_DIR}/scree_plot.png", dpi=120)

    fig_elbow = plot_elbow(list(k_eval.keys()), k_eval)
    fig_elbow.savefig(f"{MODEL_DIR}/elbow_curve.png", dpi=120)

    with open(f"{MODEL_DIR}/pca_report.json", "w") as f:
        json.dump(pca_report, f, indent=2)
    with open(f"{MODEL_DIR}/k_eval.json", "w") as f:
        json.dump({str(k): v for k, v in k_eval.items()}, f, indent=2)

    print(f"\nAll done!")
    print(f"  KMeans silhouette : {km_eval['silhouette']:.4f}")
    print(f"  DBSCAN silhouette : {db_eval['silhouette']:.4f}")
    print(f"  Winner            : {winner.upper()}")
    print(f"  Clusters          : {metadata['evaluation']['kmeans_n_clusters' if winner=='kmeans' else 'dbscan_n_clusters']}")
