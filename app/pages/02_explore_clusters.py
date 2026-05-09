import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from app.components.cluster_plot import scatter_2d
from app.components.audio_radar import radar_chart

st.set_page_config(page_title="Explore Clusters", layout="wide")


@st.cache_resource(show_spinner="Loading models...")
def _load_models():
    from src.utils.model_loader import load_all
    return load_all()


AUDIO_FEATURES = ["energy", "valence", "danceability", "acousticness",
                   "tempo", "speechiness", "instrumentalness"]


def main():
    st.title("Explore Clusters")

    try:
        models = _load_models()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    df = models["tracks_df"]
    metadata = models["metadata"]
    tsne_2d = models.get("tsne_2d")
    tsne_indices = models.get("tsne_indices")
    clusters = metadata.get("clusters", {})
    cluster_names = {cid: info["name"] for cid, info in clusters.items()}

    if "cluster_label" not in df.columns:
        st.warning("Run train_pipeline.py first to assign cluster labels.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Cluster Map", "Cluster Profiles", "Feature Distributions"])

    # ---- Tab 1: Cluster Map ----
    with tab1:
        st.subheader("2D Cluster Map (t-SNE)")

        if tsne_2d is None or tsne_indices is None:
            st.info("t-SNE coordinates not found. Re-run train_pipeline.py to generate them.")
        else:
            df_tsne = df.iloc[tsne_indices].reset_index(drop=True)
            labels = df_tsne["cluster_label"].values

            col1, col2 = st.columns([3, 1])
            with col2:
                min_pop, max_pop = st.slider(
                    "Popularity range", 0, 100, (0, 100), step=5
                )
            mask = (df_tsne["popularity"] >= min_pop) & (df_tsne["popularity"] <= max_pop)
            X_plot = tsne_2d[mask]
            lbl_plot = labels[mask]
            names_plot = df_tsne.loc[mask, "track_name"].tolist()
            artists_plot = df_tsne.loc[mask, "artist_name"].tolist()

            fig = scatter_2d(X_plot, lbl_plot, names_plot, artists_plot,
                             cluster_names=cluster_names, title="t-SNE Cluster Map")
            with col1:
                st.plotly_chart(fig, use_container_width=True)

    # ---- Tab 2: Cluster Profiles ----
    with tab2:
        st.subheader("Cluster Profile")

        options = {f"{v} (id {k})": k for k, v in cluster_names.items()}
        selected_label = st.selectbox("Select a cluster", list(options.keys()))
        selected_id = options[selected_label]

        cinfo = clusters.get(str(selected_id), {})
        centroid = cinfo.get("centroid", {})

        c1, c2 = st.columns([1, 1])
        with c1:
            if centroid:
                radar_feats = {k: v for k, v in centroid.items()
                               if k in ["energy", "valence", "danceability",
                                        "acousticness", "instrumentalness", "speechiness", "liveness"]}
                fig_radar = radar_chart(radar_feats, title=cinfo.get("name", ""))
                st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

        with c2:
            st.markdown(f"**Track count:** {cinfo.get('track_count', 'N/A')}")
            top_artists = cinfo.get("top_artists", [])
            if top_artists:
                st.markdown("**Top artists:**")
                for a in top_artists:
                    st.markdown(f"- {a}")

        rep_tracks = cinfo.get("representative_tracks", [])
        if rep_tracks:
            st.markdown("**Representative tracks:**")
            st.dataframe(pd.DataFrame(rep_tracks), use_container_width=True, hide_index=True)

    # ---- Tab 3: Feature Distributions ----
    with tab3:
        st.subheader("Audio Feature Distributions by Cluster")

        available_features = [f for f in AUDIO_FEATURES if f in df.columns]
        selected_features = st.multiselect(
            "Select features to display",
            available_features,
            default=available_features[:4],
        )

        if not selected_features:
            st.info("Select at least one feature.")
        else:
            df_plot = df[df["cluster_label"] != -1].copy()
            df_plot["Cluster"] = df_plot["cluster_label"].astype(str).map(
                lambda x: cluster_names.get(x, f"Cluster {x}")
            )
            n = len(selected_features)
            ncols = 2
            nrows = (n + 1) // ncols
            fig, axes = plt.subplots(nrows, ncols, figsize=(12, 4 * nrows))
            axes = np.array(axes).flatten()

            for i, feat in enumerate(selected_features):
                sns.boxplot(data=df_plot, x="Cluster", y=feat, ax=axes[i],
                            palette="Set2", flierprops=dict(marker="o", markersize=2, alpha=0.3))
                axes[i].set_title(feat.capitalize())
                axes[i].tick_params(axis="x", rotation=30, labelsize=8)
                axes[i].set_xlabel("")

            for j in range(len(selected_features), len(axes)):
                axes[j].set_visible(False)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)


main()
