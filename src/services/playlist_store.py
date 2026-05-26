import json
import math
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

STORE_DIR = Path("data/saved_playlists")


def _sanitize(obj: Any) -> Any:
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def _slug(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-")[:40] or "playlist"


def _make_id(cluster_name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{_slug(cluster_name)}"


def save(
    cluster: dict,
    centroid: dict,
    tracks: list[dict],
    cover_url: str | None = None,
    cover_prompt: str | None = None,
) -> str:
    playlist_id = _make_id(cluster.get("cluster_name", "playlist"))
    folder = STORE_DIR / playlist_id
    folder.mkdir(parents=True, exist_ok=True)

    payload = {
        "id": playlist_id,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "cluster": {
            "cluster_id": cluster.get("cluster_id"),
            "cluster_name": cluster.get("cluster_name", ""),
            "track_count": cluster.get("track_count", len(tracks)),
        },
        "centroid": centroid,
        "tracks": tracks,
        "cover_url": cover_url,
        "cover_prompt": cover_prompt,
        "has_cover": bool(cover_url),
    }

    with open(folder / "playlist.json", "w", encoding="utf-8") as f:
        json.dump(_sanitize(payload), f, indent=2, ensure_ascii=False)

    return playlist_id


def load_all() -> list[dict]:
    if not STORE_DIR.exists():
        return []

    entries = []
    for folder in STORE_DIR.iterdir():
        if not folder.is_dir():
            continue
        json_path = folder / "playlist.json"
        if not json_path.exists():
            continue
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            cover_path = folder / "cover.png"
            if cover_path.exists():
                data["local_cover_path"] = str(cover_path)
                data["cover_url"] = data.get("cover_url") or f"/api/saved-playlists/{folder.name}/cover"
            entries.append(data)
        except Exception:
            continue

    entries.sort(key=lambda e: e.get("saved_at", ""), reverse=True)
    return entries


def get_cover_path(playlist_id: str) -> Path | None:
    cover_path = STORE_DIR / playlist_id / "cover.png"
    return cover_path if cover_path.exists() else None


def delete(playlist_id: str) -> None:
    shutil.rmtree(STORE_DIR / playlist_id, ignore_errors=True)
