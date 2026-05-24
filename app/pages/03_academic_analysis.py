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
    st.subheader("Model Comparison: K-Means vs GMM vs DBSCAN")
    winner   = eval_info.get("algorithm", "kmeans")
    km       = eval_info.get("kmeans", {})
    gmm      = eval_info.get("gmm", {})
    dbs      = eval_info.get("dbscan", {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("#### K-Means")
        st.metric("Silhouette", f"{km.get('silhouette', 0):.4f}", delta="Winner" if winner == "KMeans" else None)
        st.metric("Davies-Bouldin", f"{km.get('davies_bouldin', 0):.4f}", help="Lower is better")
        st.metric("Clusters", km.get("n_clusters", "N/A"))
        st.metric("Noise %", "0.0%")
    with col2:
        st.markdown("#### GMM")
        st.metric("Silhouette", f"{gmm.get('silhouette', 0):.4f}", delta="Winner" if winner == "GMM" else None)
        st.metric("Davies-Bouldin", f"{gmm.get('davies_bouldin', 0):.4f}", help="Lower is better")
        st.metric("Clusters", gmm.get("n_clusters", "N/A"))
        st.metric("Noise %", "0.0%")
    with col3:
        st.markdown("#### DBSCAN")
        dbs_sil = dbs.get("silhouette", None)
        sil_str = f"{dbs_sil:.4f}" if dbs_sil is not None and dbs_sil > -1 else "N/A"
        st.metric("Silhouette", sil_str)
        st.metric("Davies-Bouldin", f"{dbs.get('davies_bouldin', 0):.4f}", help="Lower is better")
        st.metric("Clusters", dbs.get("n_clusters", "N/A"))
        st.metric("Noise %", f"{dbs.get('noise_pct', 0):.1f}%")
    with col4:
        st.markdown("#### Selected Model")
        st.metric("Algorithm", winner.upper())
        st.metric("Silhouette", f"{eval_info.get('silhouette', 0):.4f}")
        st.metric("Davies-Bouldin", f"{eval_info.get('davies_bouldin', 0):.4f}", help="Lower is better")

    st.divider()

    # ---- Silhouette diagram + Scree plot ----
    st.subheader("Cluster Visualizations")
    diag_col1, diag_col2 = st.columns(2)

    with diag_col1:
        sil_path = "models/silhouette_diagram.png"
        if os.path.exists(sil_path):
            st.image(sil_path, caption="Silhouette Diagram", use_container_width=True)
        else:
            st.info("Silhouette diagram not found. Re-run train_pipeline.py.")

    with diag_col2:
        scree_path = "models/scree_plot.png"
        if os.path.exists(scree_path):
            st.image(scree_path, caption="PCA Scree Plot", use_container_width=True)
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
