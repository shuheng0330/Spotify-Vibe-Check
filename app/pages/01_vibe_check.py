import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from app.components.audio_radar import radar_chart

st.set_page_config(page_title="Vibe Check", layout="wide")


@st.cache_resource(show_spinner="Loading models...")
def _load_models():
    from src.utils.model_loader import load_all
    return load_all()


def _get_agent():
    if "agent" not in st.session_state:
        from src.agent.dj_agent import DynamicDJAgent
        st.session_state.agent = DynamicDJAgent()
    return st.session_state.agent


def _init_state():
    defaults = {
        "messages": [],
        "current_cluster": None,
        "current_playlist": None,
        "cover_url": None,
        "cover_bytes": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def main():
    _init_state()

    try:
        models = _load_models()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    left_col, right_col = st.columns([1, 2], gap="large")

    # ---- Left column: vibe dashboard ----
    with left_col:
        st.subheader("Current Cluster")

        cluster = st.session_state.current_cluster
        if cluster:
            cluster_name = cluster.get("cluster_name", "")
            st.markdown(f"**{cluster_name}**")
            track_count = cluster.get("track_count", "")
            if track_count:
                st.caption(f"{track_count} tracks in this cluster")

            # Radar chart from cluster centroid
            metadata = models["metadata"]
            cid = str(cluster.get("cluster_id", ""))
            centroid = metadata.get("clusters", {}).get(cid, {}).get("centroid", {})
            if centroid:
                fig = radar_chart(centroid, title="Cluster Audio Profile")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("Start a conversation to see your cluster here.")

        if cluster and centroid and st.session_state.current_playlist:
            st.divider()
            if st.button("Generate Album Cover", type="primary", use_container_width=True):
                with st.spinner("Generating album cover… this may take 20–30 seconds"):
                    import requests
                    from src.agent.tool_handlers import handle_generate_album_cover
                    result = handle_generate_album_cover(
                        cluster_name=cluster.get("cluster_name", "My Playlist"),
                        energy=centroid.get("energy", 0.5),
                        valence=centroid.get("valence", 0.5),
                        acousticness=centroid.get("acousticness", 0.4),
                        instrumentalness=centroid.get("instrumentalness", 0.2),
                        tempo=centroid.get("tempo", 110.0),
                    )
                    if "image_url" in result:
                        try:
                            resp = requests.get(result["image_url"], timeout=60)
                            resp.raise_for_status()
                            st.session_state.cover_url = result["image_url"]
                            st.session_state.cover_bytes = resp.content
                        except Exception as e:
                            st.error(f"Image generation failed: {e}")
                    st.rerun()

        if st.session_state.cover_bytes:
            st.subheader("Album Cover")
            st.image(st.session_state.cover_bytes, use_container_width=True)

        if cluster and st.session_state.current_playlist:
            st.divider()
            if st.button("Save Playlist", type="primary", use_container_width=True):
                from app.components.playlist_store import save as save_playlist
                try:
                    save_playlist(
                        cluster=st.session_state.current_cluster,
                        centroid=centroid,
                        tracks=st.session_state.current_playlist,
                        cover_bytes=st.session_state.cover_bytes,
                    )
                    st.success("Playlist saved! View it in Saved Playlists.")
                except Exception as e:
                    st.error(f"Could not save: {e}")

        st.divider()
        if st.button("Start New Session", type="secondary"):
            st.session_state.messages = []
            st.session_state.current_cluster = None
            st.session_state.current_playlist = None
            st.session_state.cover_url = None
            st.session_state.cover_bytes = None
            if "agent" in st.session_state:
                st.session_state.agent.reset()
            st.rerun()

    # ---- Right column: chat ----
    with right_col:
        st.subheader("Chat with Dynamic DJ")

        # Render chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Show current playlist if available
        if st.session_state.current_playlist:
            with st.expander("Current Playlist", expanded=True):
                import pandas as pd
                pl_df = pd.DataFrame(st.session_state.current_playlist)
                # Show Spotify links as clickable if enrichment succeeded
                if "spotify_url" in pl_df.columns and pl_df["spotify_url"].any():
                    pl_df["open"] = pl_df["spotify_url"].apply(
                        lambda u: f"[Open]({u})" if u else ""
                    )
                    display_cols = [c for c in ["track_name", "artist_name", "popularity",
                                                "energy", "valence", "danceability", "open"]
                                    if c in pl_df.columns]
                    st.dataframe(pl_df[display_cols], use_container_width=True, hide_index=True)
                else:
                    display_cols = [c for c in ["track_name", "artist_name", "popularity",
                                                "energy", "valence", "danceability"]
                                    if c in pl_df.columns]
                    st.dataframe(pl_df[display_cols], use_container_width=True, hide_index=True)

        # Chat input
        user_input = st.chat_input("Describe your mood, energy, or what you want to listen to...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        agent = _get_agent()
                        response_text, _ = agent.send(user_input)

                        # Sync cached state from agent
                        if agent.current_cluster:
                            st.session_state.current_cluster = agent.current_cluster
                        if agent.current_playlist:
                            st.session_state.current_playlist = agent.current_playlist
                        if agent.cover_url:
                            st.session_state.cover_url = agent.cover_url
                    except Exception as e:
                        response_text = f"Something went wrong: {e}"

                st.markdown(response_text)

            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()


main()
