"""
Data loading module — reads a pre-downloaded Spotify dataset CSV
and formats it to match the pipeline's expected schema.

Supported dataset schemas
--------------------------
Schema A (original ~89K Kaggle dataset by maharshipandya):
  track_id, track_name, artists, album_name, popularity, duration_ms,
  energy, valence, danceability, acousticness, tempo, loudness,
  speechiness, instrumentalness, liveness, key, mode, time_signature

Schema B (300K dataset with Spotify URIs):
  track_uri, name, artists_names, popularity, duration,
  energy, valence, danceability, acousticness, tempo, loudness,
  speechiness, instrumentalness, liveness, key, mode, time_signature

Save your CSV as:  data/raw/spotify_kaggle.csv
"""
import os
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Schema A — original Kaggle dataset column mapping
_SCHEMA_A = {
    "track_id":         "track_id",
    "track_name":       "track_name",
    "artists":          "artist_name",
    "album_name":       "album_name",
    "popularity":       "popularity",
    "duration_ms":      "duration_ms",
    "energy":           "energy",
    "valence":          "valence",
    "danceability":     "danceability",
    "acousticness":     "acousticness",
    "tempo":            "tempo",
    "loudness":         "loudness",
    "speechiness":      "speechiness",
    "instrumentalness": "instrumentalness",
    "liveness":         "liveness",
    "key":              "key",
    "mode":             "mode",
    "time_signature":   "time_signature",
}

# Schema B — 300K dataset with Spotify URIs
_SCHEMA_B = {
    "track_uri":        "track_id",       # strip "spotify:track:" prefix after rename
    "name":             "track_name",
    "artists_names":    "artist_name",
    "popularity":       "popularity",
    "duration":         "duration_ms",    # already in milliseconds
    "energy":           "energy",
    "valence":          "valence",
    "danceability":     "danceability",
    "acousticness":     "acousticness",
    "tempo":            "tempo",
    "loudness":         "loudness",
    "speechiness":      "speechiness",
    "instrumentalness": "instrumentalness",
    "liveness":         "liveness",
    "key":              "key",
    "mode":             "mode",
    "time_signature":   "time_signature",
}

KAGGLE_CSV = "data/raw/spotify_kaggle.csv"


def _detect_schema(columns: list[str]) -> dict:
    if "track_uri" in columns:
        logger.info("Detected Schema B (300K URI-based dataset)")
        return _SCHEMA_B
    logger.info("Detected Schema A (original Kaggle dataset)")
    return _SCHEMA_A


def load_kaggle_dataset(kaggle_csv: str = KAGGLE_CSV) -> pd.DataFrame:
    if not os.path.exists(kaggle_csv):
        raise FileNotFoundError(
            f"\nDataset not found at '{kaggle_csv}'.\n"
            "Save your CSV file as:  data/raw/spotify_kaggle.csv\n"
        )
    logger.info(f"Loading dataset from {kaggle_csv}...")
    df = pd.read_csv(kaggle_csv)
    logger.info(f"  Loaded {len(df):,} rows, columns: {list(df.columns)}")
    return df


def collect_all_tracks(output_csv: str) -> pd.DataFrame:
    df_raw = load_kaggle_dataset()

    schema = _detect_schema(list(df_raw.columns))
    rename_map = {k: v for k, v in schema.items() if k in df_raw.columns}
    df = df_raw.rename(columns=rename_map)

    # Keep only the columns we need (fill missing optional ones)
    keep_cols = list(schema.values())
    available = [c for c in keep_cols if c in df.columns]
    df = df[available].copy()

    # Schema B: track_id is a full URI — extract the bare ID
    if "track_id" in df.columns and df["track_id"].astype(str).str.startswith("spotify:track:").any():
        df["track_id"] = df["track_id"].astype(str).str.split(":").str[-1]
        logger.info("Extracted bare track IDs from Spotify URIs")

    # album_name is absent in Schema B — fill with empty string
    if "album_name" not in df.columns:
        df["album_name"] = ""

    df = df.dropna(subset=["track_id"])
    df = df.drop_duplicates(subset="track_id")

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved {len(df):,} tracks to {output_csv}")
    return df
