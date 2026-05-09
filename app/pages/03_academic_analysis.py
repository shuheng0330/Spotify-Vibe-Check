import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import streamlit as st
import matplotlib
matplotlib.use("Agg")

from app.components.cluster_plot import elbow_plot

st.set_page_config(page_title="Academic Analysis", layout="wide")


@st.cache_resource(show_spinner="Loading models...")
def _load_models():
    from src.utils.model_loader import load_all
    return load_all()


def main():
    st.title("Academic Analysis")
    st.caption("Cluster cohesion evaluation using the Silhouette Coefficient and PCA diagnostics.")

    try:
        models = _load_models()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    df = models["tracks_df"]
    metadata = models["metadata"]
    pca_report = models.get("pca_report", {})
    k_eval = models.get("k_eval", {})
    eval_info = metadata.get("evaluation", {})
    tsne_2d = models.get("tsne_2d")

    # ---- Model comparison metrics ----
    st.subheader("Model Comparison")
    km_sil = eval_info.get("kmeans_silhouette", 0)
    db_sil = eval_info.get("dbscan_silhouette", 0)
    km_db = eval_info.get("kmeans_davies_bouldin", 0)
    db_db = eval_info.get("dbscan_davies_bouldin", 0)
    winner = eval_info.get("winner", "kmeans")

    col1, col2, col3 = st.columns(3)
    col1.metric("KMeans Silhouette", f"{km_sil:.4f}", delta=f"{'Winner' if winner=='kmeans' else ''}")
    col2.metric("DBSCAN Silhouette", f"{db_sil:.4f}", delta=f"{'Winner' if winner=='dbscan' else ''}")
    col3.metric("Selected Model", winner.upper())

    col4, col5 = st.columns(2)
    col4.metric("KMeans Davies-Bouldin", f"{km_db:.4f}", help="Lower is better")
    col5.metric("DBSCAN Davies-Bouldin", f"{db_db:.4f}", help="Lower is better")
    col4.metric("KMeans Clusters", eval_info.get("kmeans_n_clusters", "N/A"))
    col5.metric("DBSCAN Clusters", f"{eval_info.get('dbscan_n_clusters', 'N/A')} (+{eval_info.get('dbscan_noise_pct', 0):.1f}% noise)")

    st.divider()

    # ---- Silhouette diagram + Scree plot ----
    st.subheader("Cluster Visualizations")
    diag_col1, diag_col2 = st.columns(2)

    with diag_col1:
        sil_path = "models/silhouette_diagram.png"
        if os.path.exists(sil_path):
            st.image(sil_path, caption="Silhouette Diagram", use_column_width=True)
        else:
            st.info("Silhouette diagram not found. Re-run train_pipeline.py.")

    with diag_col2:
        scree_path = "models/scree_plot.png"
        if os.path.exists(scree_path):
            st.image(scree_path, caption="PCA Scree Plot", use_column_width=True)
        else:
            st.info("Scree plot not found. Re-run train_pipeline.py.")

    # ---- Elbow curve ----
    st.subheader("Elbow Curve")
    if k_eval:
        fig_elbow = elbow_plot(k_eval)
        st.plotly_chart(fig_elbow, use_container_width=True)
    else:
        st.info("Elbow data not found. Re-run train_pipeline.py.")

    st.divider()

    # ---- Cohesion & Separation table ----
    st.subheader("Cohesion and Separation")
    if tsne_2d is not None and "cluster_label" in df.columns:
        from src.ml.silhouette_analysis import compute_cohesion_separation
        pca = models.get("pca")
        scaler = models.get("scaler")
        from src.ml.dimensionality import SCALED_FEATURE_COLS
        X_scaled = df[SCALED_FEATURE_COLS].values
        X_pca = pca.transform(X_scaled)
        labels = df["cluster_label"].values
        cohesion_df = compute_cohesion_separation(X_pca, labels)
        cluster_names = {int(k): v["name"] for k, v in metadata.get("clusters", {}).items()}
        cohesion_df.insert(1, "cluster_name", cohesion_df["cluster_id"].map(cluster_names))
        st.dataframe(cohesion_df, use_container_width=True, hide_index=True)
    else:
        st.info("Run train_pipeline.py to compute cohesion/separation metrics.")

    st.divider()

    # ---- Academic analysis report ----
    st.subheader("Analysis Report")
    if "cluster_label" in df.columns and tsne_2d is not None:
        from src.ml.dimensionality import SCALED_FEATURE_COLS
        from src.ml.silhouette_analysis import compute_cohesion_separation, generate_analysis_report
        pca = models["pca"]
        X_scaled = df[SCALED_FEATURE_COLS].values
        X_pca = pca.transform(X_scaled)
        labels = df["cluster_label"].values
        cohesion_df = compute_cohesion_separation(X_pca, labels)
        report = generate_analysis_report(eval_info, cohesion_df)
        st.markdown(report)
    else:
        st.info("Run train_pipeline.py to generate the analysis report.")


main()
