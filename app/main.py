import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="Spotify Vibe Check",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load models once for the entire app session
@st.cache_resource(show_spinner="Loading models...")
def _load_models():
    from src.utils.model_loader import load_all
    return load_all()


def main():
    st.title("Spotify Vibe Check")
    st.caption("Unsupervised Audio-Feature Clustering with a Conversational DJ Agent")

    with st.sidebar:
        st.subheader("Navigation")
        st.page_link("app/pages/01_vibe_check.py",    label="Vibe Check (DJ Chat)")
        st.page_link("app/pages/02_explore_clusters.py", label="Explore Clusters")
        st.page_link("app/pages/03_academic_analysis.py", label="Academic Analysis")
        st.divider()

        try:
            models = _load_models()
            n_tracks = len(models["tracks_df"])
            n_clusters = len(models["metadata"].get("clusters", {}))
            st.success("Models loaded")
            st.caption(f"{n_tracks:,} tracks  |  {n_clusters} clusters")
        except FileNotFoundError as e:
            st.error("Models not found")
            st.caption(str(e))

    st.markdown("""
**Welcome.** This application maps songs into acoustic clusters using PCA and K-Means clustering,
then lets you discover playlists through a conversation with a Dynamic DJ agent.

**How to use:**
1. Go to **Vibe Check** and describe your mood or listening context.
2. The DJ agent will find the best-matching cluster and build a playlist for you.
3. Explore the **Cluster Map** and **Academic Analysis** pages to understand the underlying ML model.
""")


if __name__ == "__main__":
    main()
