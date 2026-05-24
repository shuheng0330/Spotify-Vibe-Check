import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime

import pandas as pd
import streamlit as st

from app.components.playlist_store import delete as delete_playlist, load_all
from app.components.audio_radar import radar_chart

st.set_page_config(page_title="Saved Playlists", layout="wide")

st.title("Saved Playlists")

playlists = load_all()

if not playlists:
    st.info("No saved playlists yet. Go to **Vibe Check**, build a playlist, and hit **Save Playlist**.")
    st.stop()

st.caption(f"{len(playlists)} saved playlist(s) — newest first")

for entry in playlists:
    cluster_name = entry.get("cluster", {}).get("cluster_name", "Unknown")
    track_count  = len(entry.get("tracks", []))
    saved_raw    = entry.get("saved_at", "")
    try:
        saved_display = datetime.fromisoformat(saved_raw).strftime("%b %d %Y, %H:%M")
    except Exception:
        saved_display = saved_raw

    cover_path = entry.get("cover_path")
    pid        = entry["id"]

    with st.container(border=True):
        img_col, info_col, action_col = st.columns([1, 4, 1])

        with img_col:
            if cover_path and cover_path.exists():
                st.image(str(cover_path), use_container_width=True)
            else:
                st.markdown("🎵", help="No album cover saved")

        with info_col:
            st.markdown(f"### {cluster_name}")
            st.caption(f"{track_count} tracks  |  Saved {saved_display}")

        with action_col:
            if st.button("Delete", key=f"del_{pid}", type="secondary"):
                delete_playlist(pid)
                st.rerun()

        tracks = entry.get("tracks", [])
        if tracks:
            with st.expander("Show tracks"):
                df = pd.DataFrame(tracks)
                display_cols = [c for c in
                    ["track_name", "artist_name", "popularity",
                     "energy", "valence", "danceability"]
                    if c in df.columns]
                if "spotify_url" in df.columns:
                    df["open"] = df["spotify_url"].apply(
                        lambda u: f"[Open]({u})" if u else ""
                    )
                    display_cols.append("open")
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        centroid = entry.get("centroid", {})
        radar_feats = {k: v for k, v in centroid.items()
                       if k in ["energy", "valence", "danceability",
                                "acousticness", "instrumentalness",
                                "speechiness", "liveness"]}
        if radar_feats:
            with st.expander("Audio profile"):
                fig = radar_chart(radar_feats, title=cluster_name)
                st.plotly_chart(fig, use_container_width=True,
                                config={"displayModeBar": False})
