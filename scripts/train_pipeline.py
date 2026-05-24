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
    find_optimal_k, fit_kmeans, fit_gmm, fit_dbscan, select_best_model,
    evaluate_clustering,
    build_cluster_metadata, save_models,
)
from src.ml.silhouette_analysis import plot_silhouette_diagram, plot_explained_variance, plot_elbow

PROCESSED_CSV = "data/processed/tracks_features.csv"
MODEL_DIR = "models"
TSNE_SAMPLE_SIZE = 5000
KSEARCH_SAMPLE_SIZE = 50000 # silhouette_score is O(n²) — subsample for speed

if __name__ == "__main__":
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Loading processed features...")
    df = pd.read_csv(PROCESSED_CSV)
    print(f"  Full matrix: {df.shape[0]:,} tracks")

    # Remove outliers before clustering — cleaner centroids, better silhouette
    clean_mask = ~df["is_outlier"].astype(bool)
    df_clean = df[clean_mask].reset_index(drop=True)
    clean_orig_idx = df.index[clean_mask].values  # original row positions in df
    X_clean = df_clean[SCALED_FEATURE_COLS].values
    X_full = df[SCALED_FEATURE_COLS].values
    print(f"  Clean matrix (no outliers): {X_clean.shape}")

    print("\nStep 1: PCA")
    pca, X_pca, n_comp = fit_pca(X_clean)
    save_pca(pca, f"{MODEL_DIR}/pca_model.pkl")
    pca_report = get_explained_variance_report(pca)

    print(f"\nStep 2: t-SNE (2D for visualization, sample of {TSNE_SAMPLE_SIZE})")
    tsne_n = min(TSNE_SAMPLE_SIZE, len(X_pca))
    rng = np.random.default_rng(42)
    local_tsne_idx = np.sort(rng.choice(len(X_pca), size=tsne_n, replace=False))
    df_tsne_orig_idx = clean_orig_idx[local_tsne_idx]  # positions in full df
    X_tsne = fit_tsne(X_pca[local_tsne_idx])
    np.save(f"{MODEL_DIR}/tsne_2d.npy", X_tsne)
    np.save(f"{MODEL_DIR}/tsne_indices.npy", df_tsne_orig_idx)

    print("\nStep 3: Finding optimal k for KMeans...")
    ksearch_n = min(KSEARCH_SAMPLE_SIZE, len(X_pca))
    ksearch_idx = np.sort(rng.choice(len(X_pca), size=ksearch_n, replace=False))
    X_pca_ksearch = X_pca[ksearch_idx]
    print(f"  (using {ksearch_n:,}-track subsample for silhouette scoring)")
    k_eval = find_optimal_k(X_pca_ksearch)
    best_k = max(k_eval, key=lambda k: k_eval[k]["silhouette"])
    print(f"\nBest k = {best_k}")

    print(f"\nStep 4: Fitting KMeans (k={best_k}) on full dataset")
    kmeans, km_labels = fit_kmeans(X_pca, best_k)
    km_eval = evaluate_clustering(X_pca, km_labels, "KMeans")

    print(f"\nStep 5: Fitting GMM (n_components={best_k}) on full dataset")
    gmm, gmm_labels = fit_gmm(X_pca, best_k)
    gmm_eval = evaluate_clustering(X_pca, gmm_labels, "GMM")

    print("\nStep 5b: Fitting DBSCAN (density-based — academic comparison only)")
    print("  Note: DBSCAN excluded from winner selection — no predict() for unseen points")
    _, dbscan_labels, dbscan_eps = fit_dbscan(X_pca)
    dbscan_eval = evaluate_clustering(X_pca, dbscan_labels, "DBSCAN")
    print(f"  eps={dbscan_eps:.4f}  noise={dbscan_eval['noise_pct']:.1f}%  clusters={dbscan_eval['n_clusters']}")

    print("\nStep 6: Selecting best model")
    winner = select_best_model(km_eval, gmm_eval)
    winner_model  = kmeans   if winner == "kmeans" else gmm
    winner_labels = km_labels if winner == "kmeans" else gmm_labels
    winner_eval   = km_eval   if winner == "kmeans" else gmm_eval
    print(f"  Winner: {winner.upper()}  (KMeans sil={km_eval['silhouette']:.4f}  GMM sil={gmm_eval['silhouette']:.4f})")

    # Assign cluster labels to ALL tracks (including outliers) via winner predict
    X_pca_full = pca.transform(X_full)
    df["cluster_label"] = winner_model.predict(X_pca_full)

    unique_clusters = sorted(set(winner_labels) - {-1})
    centroids_original = np.array([
        df_clean[[c.replace("_scaled", "") for c in SCALED_FEATURE_COLS]].values[winner_labels == cid].mean(axis=0)
        for cid in unique_clusters
    ])
    joblib.dump(centroids_original, f"{MODEL_DIR}/cluster_centroids.pkl")

    print("\nStep 7: Building cluster metadata")
    metadata = build_cluster_metadata(df_clean, winner_labels, winner_eval, km_eval=km_eval, gmm_eval=gmm_eval, dbscan_eval=dbscan_eval)
    metadata["tsne_available"] = True

    print("\nStep 8: Saving models")
    save_models(winner_model, centroids_original, metadata, MODEL_DIR)
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
    print(f"  Winner     : {winner.upper()}")
    print(f"  Silhouette : {winner_eval['silhouette']:.4f}")
    print(f"  Clusters   : {winner_eval['n_clusters']}")
