import os
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler

CONTINUOUS_FEATURES = [
    "energy", "valence", "danceability", "acousticness",
    "tempo", "speechiness", "instrumentalness", "mode",
]


def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.drop_duplicates(subset="track_id")
    return df


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    for col in CONTINUOUS_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    too_many_missing = df[CONTINUOUS_FEATURES].isnull().sum(axis=1) > 3
    df = df[~too_many_missing].reset_index(drop=True)
    return df


def detect_outliers(df: pd.DataFrame) -> pd.DataFrame:
    flags = pd.Series(False, index=df.index)
    for col in CONTINUOUS_FEATURES:
        if col not in df.columns:
            continue
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        flags |= (df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)
    df = df.copy()
    df["is_outlier"] = flags
    return df


def normalize_features(df: pd.DataFrame) -> tuple[pd.DataFrame, StandardScaler]:
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[CONTINUOUS_FEATURES])
    scaled_df = pd.DataFrame(scaled, columns=[f"{c}_scaled" for c in CONTINUOUS_FEATURES], index=df.index)
    return scaled_df, scaler


def preprocess(raw_csv: str, output_csv: str, scaler_path: str) -> tuple[pd.DataFrame, StandardScaler]:
    df = load_raw(raw_csv)
    df = handle_missing(df)
    df = detect_outliers(df)

    scaled_df, scaler = normalize_features(df)

    meta_cols = ["track_id", "track_name", "artist_name", "album_name", "popularity", "duration_ms", "is_outlier"]
    # Keep original feature values too (used by agent for readable stats)
    original_feats = df[CONTINUOUS_FEATURES].copy()
    result = pd.concat([df[meta_cols].reset_index(drop=True),
                        original_feats.reset_index(drop=True),
                        scaled_df.reset_index(drop=True)], axis=1)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    result.to_csv(output_csv, index=False)
    os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
    joblib.dump(scaler, scaler_path)
    print(f"Saved {len(result)} processed tracks to {output_csv}")
    print(f"Saved scaler to {scaler_path}")
    return result, scaler
