"""Deterministic response text for playlist-generating DJ turns."""

from typing import Any


def _clean_artist(value: Any) -> str:
    text = str(value or "Unknown artist").strip()
    return text.strip("[]").replace("'", "")


def _mean(playlist: list[dict], key: str) -> float | None:
    values = [track.get(key) for track in playlist if isinstance(track.get(key), (int, float))]
    if not values:
        return None
    return sum(values) / len(values)


def _level(value: float | None, low: float, high: float, labels: tuple[str, str, str]) -> str:
    if value is None:
        return labels[1]
    if value < low:
        return labels[0]
    if value > high:
        return labels[2]
    return labels[1]


def _playlist_explanation(playlist: list[dict]) -> tuple[str, str]:
    energy = _mean(playlist, "energy")
    valence = _mean(playlist, "valence")
    danceability = _mean(playlist, "danceability")
    acousticness = _mean(playlist, "acousticness")
    tempo = _mean(playlist, "tempo")

    energy_text = _level(energy, 0.4, 0.7, ("low-energy", "steady-energy", "high-energy"))
    mood_text = _level(valence, 0.4, 0.65, ("more introspective", "balanced in mood", "bright and upbeat"))
    dance_text = _level(danceability, 0.45, 0.7, ("less beat-driven", "moderately groovy", "danceable"))
    texture_text = _level(acousticness, 0.25, 0.6, ("produced/electronic", "mixed-texture", "acoustic-leaning"))

    bpm_text = f"around {round(tempo)} BPM" if tempo else "a mid-tempo pace"
    why = (
        f"{energy_text}, {mood_text}, {dance_text}, and {texture_text}, "
        f"with the playlist sitting {bpm_text}."
    )

    if energy and energy > 0.7 and danceability and danceability > 0.65:
        use_case = "you want momentum, movement, or a more active listening session."
    elif acousticness and acousticness > 0.55:
        use_case = "you want something calmer, warmer, or easier to keep in the background."
    elif valence and valence < 0.4:
        use_case = "you want a more reflective mood without losing musical shape."
    else:
        use_case = "you want a balanced playlist that can sit between focus, casual listening, and light energy."

    return why, use_case


def _track_reason(track: dict) -> str:
    energy = track.get("energy")
    valence = track.get("valence")
    danceability = track.get("danceability")
    acousticness = track.get("acousticness")
    popularity = track.get("popularity")

    reasons = []
    if isinstance(energy, (int, float)):
        reasons.append("strong lift" if energy >= 0.7 else "gentler energy" if energy <= 0.4 else "steady energy")
    if isinstance(danceability, (int, float)) and danceability >= 0.65:
        reasons.append("clear groove")
    if isinstance(valence, (int, float)):
        reasons.append("brighter tone" if valence >= 0.65 else "mellower tone" if valence <= 0.4 else "balanced tone")
    if isinstance(acousticness, (int, float)) and acousticness >= 0.55:
        reasons.append("warmer acoustic texture")
    if isinstance(popularity, (int, float)) and popularity >= 70:
        reasons.append("familiar pick")

    return ", ".join(reasons[:2]) or "fits the cluster profile"


def format_active_playlist_response(
    cluster: dict | None,
    playlist: list[dict],
    assistant_text: str = "",
    max_tracks: int = 5,
) -> str:
    """Build chat text from the exact playlist returned to the frontend.

    The LLM sees both cluster representative tracks and generated playlist tool
    output, so it can accidentally mention tracks that are not in the visible
    active playlist. This formatter makes the visible playlist the source of
    truth for recommendation text.
    """
    if not playlist:
        return assistant_text.strip() or "I found a matching vibe, but no playlist tracks were returned."

    cluster_name = (cluster or {}).get("cluster_name") or "this vibe"
    why, use_case = _playlist_explanation(playlist)

    lines = [
        f"I matched your request to the {cluster_name} cluster and built the active playlist from that exact group.",
        f"Why it fits: {why}",
        f"Use it when: {use_case}",
        "Chosen tracks:",
    ]
    for index, track in enumerate(playlist[:max_tracks], start=1):
        track_name = track.get("track_name") or "Unknown track"
        artist_name = _clean_artist(track.get("artist_name"))
        lines.append(f"{index}. {track_name} - {artist_name} ({_track_reason(track)})")

    if len(playlist) > max_tracks:
        lines.append(f"Plus {len(playlist) - max_tracks} more tracks in the table below.")

    lines.append("The Active Playlist Tracks table shows the same recommendation set.")
    return "\n".join(lines)
