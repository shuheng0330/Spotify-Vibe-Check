"""
Member A — Run once to collect and preprocess the full dataset.

Usage:
    python scripts/collect_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.spotify_collector import collect_all_tracks
from src.data.preprocessor import preprocess

PLAYLIST_FILE = "data/playlists/seed_playlists.txt"
RAW_CSV = "data/raw/tracks_raw.csv"
PROCESSED_CSV = "data/processed/tracks_features.csv"
SCALER_PATH = "models/scaler.pkl"

if __name__ == "__main__":
    print("Step 1: Collecting tracks from Spotify...")
    df_raw = collect_all_tracks(PLAYLIST_FILE, RAW_CSV)
    print(f"  Raw dataset: {df_raw.shape[0]} tracks\n")

    print("Step 2: Preprocessing features...")
    df_processed, scaler = preprocess(RAW_CSV, PROCESSED_CSV, SCALER_PATH)
    print(f"  Processed dataset: {df_processed.shape[0]} tracks")
    print(f"  Null count: {df_processed.isnull().sum().sum()}")
    print("\nDone. Share data/processed/tracks_features.csv and models/scaler.pkl with the team.")
