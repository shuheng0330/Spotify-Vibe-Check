import os
import time
import logging
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

AUDIO_FEATURE_KEYS = [
    "energy", "valence", "danceability", "acousticness",
    "tempo", "loudness", "speechiness", "instrumentalness",
    "liveness", "key", "mode", "time_signature",
]


def get_spotify_client() -> spotipy.Spotify:
    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        )
    )


def fetch_playlist_tracks(sp: spotipy.Spotify, playlist_id: str) -> list[dict]:
    tracks = []
    results = sp.playlist_tracks(
        playlist_id,
        fields="items(track(id,name,artists,album(name),popularity,duration_ms)),next",
        limit=100,
    )
    while results:
        for item in results["items"]:
            track = item.get("track")
            if not track or not track.get("id"):
                continue
            tracks.append({
                "track_id": track["id"],
                "track_name": track["name"],
                "artist_name": track["artists"][0]["name"] if track["artists"] else "",
                "album_name": track["album"]["name"],
                "popularity": track.get("popularity", 0),
                "duration_ms": track.get("duration_ms", 0),
            })
        if results.get("next"):
            time.sleep(0.3)
            results = sp.next(results)
        else:
            break
    return tracks


def fetch_audio_features_batch(sp: spotipy.Spotify, track_ids: list[str]) -> list[dict]:
    features = []
    for i in range(0, len(track_ids), 100):
        chunk = track_ids[i : i + 100]
        retries = 0
        while retries < 3:
            try:
                result = sp.audio_features(chunk)
                features.extend([f for f in result if f is not None])
                time.sleep(0.5)
                break
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 429:
                    wait = int(e.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited, waiting {wait}s")
                    time.sleep(wait)
                    retries += 1
                else:
                    raise
    return features


def collect_all_tracks(playlist_file: str, output_csv: str) -> pd.DataFrame:
    sp = get_spotify_client()

    with open(playlist_file) as f:
        playlist_ids = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    all_tracks: dict[str, dict] = {}
    for pid in playlist_ids:
        logger.info(f"Fetching playlist {pid}")
        try:
            tracks = fetch_playlist_tracks(sp, pid)
            for t in tracks:
                all_tracks[t["track_id"]] = t
            logger.info(f"  -> {len(tracks)} tracks (total unique: {len(all_tracks)})")
        except Exception as e:
            logger.error(f"Failed playlist {pid}: {e}")

    track_list = list(all_tracks.values())
    track_ids = [t["track_id"] for t in track_list]
    logger.info(f"Fetching audio features for {len(track_ids)} tracks")
    features = fetch_audio_features_batch(sp, track_ids)

    feature_map = {f["id"]: f for f in features}
    rows = []
    for t in track_list:
        feat = feature_map.get(t["track_id"])
        if feat is None:
            continue
        row = dict(t)
        for key in AUDIO_FEATURE_KEYS:
            row[key] = feat.get(key)
        rows.append(row)

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved {len(df)} tracks to {output_csv}")
    return df
