"""
Data loading module — reads a pre-downloaded Kaggle Spotify dataset CSV
and formats it to match the pipeline's expected schema.

Kaggle dataset to download (free, ~5 MB):
  "Spotify Tracks Dataset" by maharshipandya
  https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset
  File to download: dataset.csv  -> save as  data/raw/spotify_kaggle.csv

Background: Spotify deprecated the /v1/recommendations and /v1/audio-features
endpoints for all apps created after November 2024. Using a pre-collected
dataset is the standard academic workaround.
"""
import os
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Columns in the Kaggle dataset that map directly to our pipeline schema
KAGGLE_COLUMNS = {
    "track_id":        "track_id",
    "track_name":      "track_name",
    "artists":         "artist_name",
    "album_name":      "album_name",
    "popularity":      "popularity",
    "duration_ms":     "duration_ms",
    "energy":          "energy",
    "valence":         "valence",
    "danceability":    "danceability",
    "acousticness":    "acousticness",
    "tempo":           "tempo",
    "loudness":        "loudness",
    "speechiness":     "speechiness",
    "instrumentalness":"instrumentalness",
    "liveness":        "liveness",
    "key":             "key",
    "mode":            "mode",
    "time_signature":  "time_signature",
}

KAGGLE_CSV = "data/raw/spotify_kaggle.csv"


def load_kaggle_dataset(kaggle_csv: str = KAGGLE_CSV) -> pd.DataFrame:
    if not os.path.exists(kaggle_csv):
        raise FileNotFoundError(
            f"\nKaggle dataset not found at '{kaggle_csv}'.\n\n"
            "Download it in 3 steps:\n"
            "  1. Go to: https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset\n"
            "  2. Click 'Download' (free Kaggle account required)\n"
            "  3. Extract and save the file as:  data/raw/spotify_kaggle.csv\n"
        )
    logger.info(f"Loading Kaggle dataset from {kaggle_csv}...")
    df = pd.read_csv(kaggle_csv)
    logger.info(f"  Loaded {len(df):,} rows, columns: {list(df.columns)}")
    return df


def collect_all_tracks(output_csv: str) -> pd.DataFrame:
    df_raw = load_kaggle_dataset()

    # Rename columns to our schema
    rename_map = {k: v for k, v in KAGGLE_COLUMNS.items() if k in df_raw.columns}
    df = df_raw.rename(columns=rename_map)

    # Keep only the columns we need
    keep_cols = list(KAGGLE_COLUMNS.values())
    available = [c for c in keep_cols if c in df.columns]
    df = df[available].copy()

    # Drop rows with no track_id
    df = df.dropna(subset=["track_id"])
    df = df.drop_duplicates(subset="track_id")

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved {len(df):,} tracks to {output_csv}")
    return df
