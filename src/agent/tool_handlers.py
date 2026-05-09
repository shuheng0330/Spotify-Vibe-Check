"""
Tool handler implementations — called by dj_agent.py when Gemini emits a function_call.
Each handler loads models via ModelLoader (singleton, loaded once at startup).
"""
import os
import random
import numpy as np
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Lazy import to avoid circular dependency; model_loader uses st.cache_resource
_models = None


def _get_models():
    global _models
    if _models is None:
        from src.utils.model_loader import load_all
        _models = load_all()
    return _models


# ---------------------------------------------------------------------------
# Mood word → feature midpoint lookup table
# ---------------------------------------------------------------------------
MOOD_KEYWORDS = {
    # (energy, valence, danceability, acousticness, instrumentalness, speechiness, liveness, tempo, loudness, mode)
    "happy":       (0.75, 0.80, 0.75, 0.2, 0.05, 0.1, 0.15, 125, -6, 1),
    "sad":         (0.25, 0.20, 0.30, 0.7, 0.2,  0.1, 0.1,  80,  -12, 0),
    "energetic":   (0.90, 0.70, 0.80, 0.1, 0.05, 0.1, 0.2,  140, -4, 1),
    "chill":       (0.30, 0.55, 0.45, 0.6, 0.3,  0.05, 0.1, 90,  -10, 1),
    "relaxed":     (0.25, 0.55, 0.35, 0.7, 0.35, 0.05, 0.1, 85,  -11, 1),
    "focus":       (0.45, 0.50, 0.40, 0.4, 0.65, 0.05, 0.1, 110, -8, 1),
    "study":       (0.35, 0.50, 0.35, 0.5, 0.70, 0.05, 0.1, 100, -9, 1),
    "workout":     (0.90, 0.65, 0.80, 0.05, 0.05, 0.1, 0.2, 145, -3, 1),
    "party":       (0.85, 0.80, 0.90, 0.05, 0.03, 0.1, 0.2, 130, -4, 1),
    "romantic":    (0.45, 0.65, 0.55, 0.5,  0.2,  0.05, 0.1, 95, -8, 1),
    "angry":       (0.85, 0.20, 0.60, 0.1,  0.1,  0.15, 0.2, 140, -4, 0),
    "melancholic": (0.30, 0.20, 0.30, 0.65, 0.25, 0.05, 0.1, 78, -11, 0),
    "upbeat":      (0.80, 0.80, 0.80, 0.1,  0.05, 0.1, 0.15, 130, -5, 1),
    "acoustic":    (0.35, 0.60, 0.45, 0.85, 0.3,  0.05, 0.1, 90,  -10, 1),
    "instrumental":(0.50, 0.55, 0.50, 0.4,  0.85, 0.03, 0.1, 110, -8, 1),
    "jazz":        (0.45, 0.60, 0.60, 0.5,  0.6,  0.05, 0.15, 100, -9, 1),
    "classical":   (0.25, 0.55, 0.20, 0.9,  0.95, 0.03, 0.05, 80, -13, 1),
    "hiphop":      (0.70, 0.65, 0.80, 0.1,  0.05, 0.25, 0.15, 95, -6, 0),
    "rap":         (0.70, 0.55, 0.75, 0.1,  0.03, 0.35, 0.15, 90, -6, 0),
    "electronic":  (0.80, 0.65, 0.80, 0.05, 0.5,  0.05, 0.1, 128, -5, 1),
    "rock":        (0.80, 0.55, 0.65, 0.1,  0.1,  0.1,  0.25, 130, -5, 1),
    "metal":       (0.90, 0.25, 0.55, 0.05, 0.15, 0.1,  0.25, 150, -3, 0),
    "country":     (0.55, 0.65, 0.60, 0.55, 0.05, 0.05, 0.1, 110, -7, 1),
    "soul":        (0.55, 0.70, 0.65, 0.4,  0.1,  0.1,  0.15, 100, -7, 1),
    "morning":     (0.40, 0.65, 0.50, 0.6,  0.2,  0.05, 0.1, 95,  -9, 1),
    "night":       (0.50, 0.45, 0.60, 0.3,  0.2,  0.1,  0.1, 105, -8, 0),
    "sunday":      (0.30, 0.60, 0.40, 0.7,  0.25, 0.05, 0.1, 85,  -10, 1),
    "driving":     (0.75, 0.65, 0.70, 0.2,  0.1,  0.1,  0.15, 120, -6, 1),
    "coding":      (0.45, 0.50, 0.40, 0.35, 0.60, 0.05, 0.1, 110, -8, 1),
}

FEATURE_ORDER = ["energy", "valence", "danceability", "acousticness",
                 "instrumentalness", "speechiness", "liveness", "tempo", "loudness", "mode"]


def _text_to_feature_vector(text: str, energy_level: str = None, valence_preference: str = None) -> tuple[dict, float]:
    words = text.lower().split()
    matches = [MOOD_KEYWORDS[w] for w in words if w in MOOD_KEYWORDS]

    # Override with explicit parameters
    overrides = {}
    if energy_level == "low":
        overrides["energy"] = 0.25
    elif energy_level == "medium":
        overrides["energy"] = 0.55
    elif energy_level == "high":
        overrides["energy"] = 0.85

    if valence_preference == "sad":
        overrides["valence"] = 0.20
    elif valence_preference == "neutral":
        overrides["valence"] = 0.50
    elif valence_preference == "happy":
        overrides["valence"] = 0.80

    if matches:
        arr = np.mean(matches, axis=0)
        confidence = min(0.95, 0.5 + 0.15 * len(matches))
    else:
        # Fallback: neutral midpoints
        arr = np.array([0.5, 0.5, 0.5, 0.4, 0.2, 0.1, 0.1, 110.0, -8.0, 1.0])
        confidence = 0.3

    fv = dict(zip(FEATURE_ORDER, arr.tolist()))
    for k, v in overrides.items():
        fv[k] = v
        confidence = min(0.95, confidence + 0.1)

    return fv, round(confidence, 2)


# ---------------------------------------------------------------------------
# Handler functions
# ---------------------------------------------------------------------------

def handle_assess_mood(mood_description: str, energy_level: str = None, valence_preference: str = None) -> dict:
    fv, confidence = _text_to_feature_vector(mood_description, energy_level, valence_preference)
    return {
        "feature_vector": fv,
        "confidence_score": confidence,
        "energy_range": [round(max(0, fv["energy"] - 0.2), 2), round(min(1, fv["energy"] + 0.2), 2)],
        "valence_range": [round(max(0, fv["valence"] - 0.2), 2), round(min(1, fv["valence"] + 0.2), 2)],
    }


def handle_find_cluster(
    energy: float, valence: float, danceability: float,
    acousticness: float = 0.4, instrumentalness: float = 0.2,
    speechiness: float = 0.1, liveness: float = 0.1,
    tempo: float = 110.0, loudness: float = -8.0, mode: float = 1.0,
    top_n: int = 1,
) -> dict:
    m = _get_models()
    scaler = m["scaler"]
    pca = m["pca"]
    centroids = m["centroids"]
    metadata = m["metadata"]
    clusters = metadata["clusters"]

    fv_array = np.array([[energy, valence, danceability, acousticness,
                          tempo, loudness, speechiness, instrumentalness,
                          liveness, mode]])
    X_scaled = scaler.transform(fv_array)
    X_pca = pca.transform(X_scaled)

    # Centroids are stored in original feature space; transform them too
    centroids_scaled = scaler.transform(centroids)
    centroids_pca = pca.transform(centroids_scaled)

    dists = np.linalg.norm(centroids_pca - X_pca, axis=1)
    top_n = min(top_n, len(dists))
    top_ids = np.argsort(dists)[:top_n]

    results = []
    for idx in top_ids:
        cid = str(idx)
        cinfo = clusters.get(cid, {})
        results.append({
            "cluster_id": int(idx),
            "cluster_name": cinfo.get("name", f"Cluster {idx}"),
            "match_score": round(1.0 / (1.0 + float(dists[idx])), 4),
            "track_count": cinfo.get("track_count", 0),
            "representative_tracks": cinfo.get("representative_tracks", []),
        })

    if top_n == 1:
        return results[0]
    return {"candidates": results}


def handle_generate_playlist(cluster_id: int, n_tracks: int = 10, min_popularity: int = 0, sort_by: str = "random") -> dict:
    m = _get_models()
    df = m["tracks_df"]
    metadata = m["metadata"]

    n_tracks = min(max(1, n_tracks), 30)
    subset = df[df["cluster_label"] == cluster_id].copy()

    if min_popularity > 0:
        subset = subset[subset["popularity"] >= min_popularity]

    if len(subset) == 0:
        subset = df[df["cluster_label"] == cluster_id].copy()

    if sort_by == "popularity":
        subset = subset.nlargest(n_tracks, "popularity")
    elif sort_by == "random":
        subset = subset.sample(min(n_tracks, len(subset)), random_state=random.randint(0, 9999))
    else:
        subset = subset.sample(min(n_tracks, len(subset)), random_state=42)

    cols = ["track_id", "track_name", "artist_name", "album_name", "popularity",
            "energy", "valence", "danceability", "acousticness", "tempo"]
    available = [c for c in cols if c in subset.columns]
    playlist = subset[available].round(3).to_dict("records")

    # Enrich with Spotify URLs and artwork via the still-working tracks endpoint
    playlist = _enrich_with_spotify_links(playlist)

    cluster_name = metadata["clusters"].get(str(cluster_id), {}).get("name", f"Cluster {cluster_id}")
    return {
        "cluster_id": cluster_id,
        "cluster_name": cluster_name,
        "n_tracks": len(playlist),
        "playlist": playlist,
    }


def _enrich_with_spotify_links(playlist: list[dict]) -> list[dict]:
    """
    Use the Spotify Web API (sp.tracks — still available with Client Credentials)
    to add spotify_url and artwork_url to each track in the playlist.
    Falls back gracefully if credentials are missing or API call fails.
    """
    track_ids = [t.get("track_id") for t in playlist if t.get("track_id")]
    if not track_ids:
        return playlist

    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        ))
        # Fetch in batches of 50 (API limit for /tracks)
        id_to_meta = {}
        for i in range(0, len(track_ids), 50):
            chunk = track_ids[i:i+50]
            result = sp.tracks(chunk)
            for t in result.get("tracks") or []:
                if not t:
                    continue
                images = t.get("album", {}).get("images", [])
                id_to_meta[t["id"]] = {
                    "spotify_url": t.get("external_urls", {}).get("spotify", ""),
                    "artwork_url": images[0]["url"] if images else "",
                }
        for track in playlist:
            meta = id_to_meta.get(track.get("track_id"), {})
            track["spotify_url"] = meta.get("spotify_url", "")
            track["artwork_url"] = meta.get("artwork_url", "")
    except Exception:
        # Silently skip enrichment if credentials are missing or API fails
        pass

    return playlist


def handle_get_cluster_stats(cluster_id: int) -> dict:
    m = _get_models()
    metadata = m["metadata"]
    cinfo = metadata["clusters"].get(str(cluster_id))
    if not cinfo:
        return {"error": f"Cluster {cluster_id} not found"}
    return {
        "cluster_id": cluster_id,
        "name": cinfo["name"],
        "track_count": cinfo["track_count"],
        "feature_means": cinfo["centroid"],
        "top_artists": cinfo["top_artists"],
        "representative_tracks": cinfo["representative_tracks"],
    }


def handle_compare_clusters(cluster_id_a: int, cluster_id_b: int) -> dict:
    stats_a = handle_get_cluster_stats(cluster_id_a)
    stats_b = handle_get_cluster_stats(cluster_id_b)
    if "error" in stats_a or "error" in stats_b:
        return {"error": "One or both cluster ids not found"}

    features = list(stats_a["feature_means"].keys())
    comparison = {}
    for feat in features:
        va = stats_a["feature_means"].get(feat, 0)
        vb = stats_b["feature_means"].get(feat, 0)
        comparison[feat] = {"cluster_a": round(va, 3), "cluster_b": round(vb, 3), "diff": round(va - vb, 3)}

    return {
        "cluster_a": {"id": cluster_id_a, "name": stats_a["name"]},
        "cluster_b": {"id": cluster_id_b, "name": stats_b["name"]},
        "feature_comparison": comparison,
    }


def handle_refine_preferences(ambiguous_features: list, candidate_cluster_ids: list) -> dict:
    FOLLOW_UPS = {
        "energy":           "Would you prefer high-energy music that pumps you up, or something more relaxed and laid-back?",
        "valence":          "Are you in the mood for something uplifting and positive, or more introspective and mellow?",
        "danceability":     "Should the music have a strong beat you can move to, or is it more for listening?",
        "acousticness":     "Do you prefer live acoustic instruments (guitar, piano) or more produced electronic sounds?",
        "instrumentalness": "Would you like music with vocals, or mostly instrumental tracks?",
        "speechiness":      "Are you okay with lots of lyrics and rap, or do you prefer melodic singing or no words at all?",
        "tempo":            "Do you want fast-paced, high-tempo tracks, or a slower, more measured pace?",
        "liveness":         "Would you enjoy a live concert feel with audience energy, or studio-polished recordings?",
    }
    question = FOLLOW_UPS.get(ambiguous_features[0],
                              "Could you describe your ideal mood or listening context in a bit more detail?")
    return {
        "follow_up_question": question,
        "feature_to_probe": ambiguous_features[0],
        "candidate_cluster_ids": candidate_cluster_ids,
    }


def handle_generate_album_cover(
    cluster_name: str, energy: float, valence: float,
    acousticness: float = 0.4, instrumentalness: float = 0.2,
    tempo: float = 110.0, style_hint: str = None,
) -> dict:
    # Build a structured DALL-E prompt from feature values
    energy_desc = "intense and high-energy" if energy > 0.6 else ("calm and peaceful" if energy < 0.4 else "moderately dynamic")
    valence_desc = "bright, optimistic, and uplifting" if valence > 0.6 else ("dark, moody, and introspective" if valence < 0.4 else "balanced and neutral in tone")
    acoustic_desc = "warm acoustic textures, natural wood and string elements" if acousticness > 0.6 else "sleek electronic and digital aesthetic"
    tempo_desc = "fast-paced" if tempo > 120 else ("slow and deliberate" if tempo < 90 else "mid-tempo")
    style = style_hint or "clean and minimal"

    prompt = (
        f"Album cover artwork for a playlist called '{cluster_name}'. "
        f"The visual mood should feel {valence_desc}. "
        f"The composition should be {energy_desc} and {tempo_desc}. "
        f"Use {acoustic_desc}. "
        f"Style: {style}. "
        f"Professional album art, square format, no text, no typography."
    )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set in .env", "prompt_used": prompt}

    client = OpenAI(api_key=api_key)
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    return {
        "image_url": response.data[0].url,
        "revised_prompt": response.data[0].revised_prompt,
        "prompt_used": prompt,
    }


# Dispatch map used by dj_agent.py
TOOL_DISPATCH = {
    "assess_mood":            handle_assess_mood,
    "find_cluster_for_mood":  handle_find_cluster,
    "generate_playlist":      handle_generate_playlist,
    "get_cluster_stats":      handle_get_cluster_stats,
    "compare_clusters":       handle_compare_clusters,
    "refine_preferences":     handle_refine_preferences,
    "generate_album_cover":   handle_generate_album_cover,
}
