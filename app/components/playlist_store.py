import json
import re
import shutil
from datetime import datetime
from pathlib import Path

STORE_DIR = Path("data/saved_playlists")


def _slug(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-")[:40]


def _make_id(cluster_name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{_slug(cluster_name)}"


def save(
    cluster: dict,
    centroid: dict,
    tracks: list[dict],
    cover_bytes: bytes | None,
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
            "track_count": cluster.get("track_count", 0),
        },
        "centroid": centroid,
        "tracks": tracks,
        "has_cover": cover_bytes is not None,
    }

    with open(folder / "playlist.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    if cover_bytes is not None:
        (folder / "cover.png").write_bytes(cover_bytes)

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
            data["cover_path"] = cover_path if cover_path.exists() else None
            entries.append(data)
        except Exception:
            continue

    entries.sort(key=lambda e: e.get("saved_at", ""), reverse=True)
    return entries


def delete(playlist_id: str) -> None:
    shutil.rmtree(STORE_DIR / playlist_id, ignore_errors=True)
