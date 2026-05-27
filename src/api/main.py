import os
from functools import lru_cache
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.agent.tool_handlers import (
    handle_generate_album_cover,
    handle_generate_playlist,
)
from src.services import analysis_service
from src.services import playlist_store
from src.utils.model_loader import load_all


app = FastAPI(title="Spotify Vibe Check API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class AlbumCoverRequest(BaseModel):
    cluster_name: str
    energy: float = 0.5
    valence: float = 0.5
    acousticness: float = 0.4
    instrumentalness: float = 0.2
    tempo: float = 110.0
    style_hint: str | None = None


class SavedPlaylistRequest(BaseModel):
    cluster: dict[str, Any]
    centroid: dict[str, Any]
    tracks: list[dict[str, Any]]
    cover_url: str | None = None
    cover_prompt: str | None = None


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


@lru_cache(maxsize=1)
def _models() -> dict:
    return load_all()


@lru_cache(maxsize=1)
def _agent():
    if not os.getenv("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY is not configured. Add it to .env to use DJ chat.")
    from src.agent.dj_agent import DynamicDJAgent

    return DynamicDJAgent()


def _cluster_list() -> list[dict]:
    metadata = _models()["metadata"]
    clusters = []
    for raw_id, info in metadata.get("clusters", {}).items():
        clusters.append(
            {
                "id": int(raw_id),
                "name": info.get("name", f"Cluster {raw_id}"),
                "track_count": info.get("track_count", 0),
                "centroid": info.get("centroid", {}),
                "top_artists": info.get("top_artists", []),
                "representative_tracks": info.get("representative_tracks", []),
            }
        )
    clusters.sort(key=lambda item: item["id"])
    return clusters


@app.get("/api/health")
def health() -> dict:
    try:
        models = _models()
        metadata = models["metadata"]
        tracks_df = models["tracks_df"]
        return {
            "models_loaded": True,
            "track_count": int(len(tracks_df)),
            "cluster_count": len(metadata.get("clusters", {})),
            "selected_algorithm": metadata.get("evaluation", {}).get("algorithm", "unknown"),
            "tsne_available": models.get("tsne_2d") is not None,
        }
    except FileNotFoundError as exc:
        return {
            "models_loaded": False,
            "track_count": 0,
            "cluster_count": 0,
            "selected_algorithm": "unknown",
            "tsne_available": False,
            "error": str(exc),
        }


@app.get("/api/clusters")
def clusters() -> dict:
    return {"clusters": _jsonable(_cluster_list())}


@app.get("/api/clusters/{cluster_id}")
def cluster_detail(cluster_id: int) -> dict:
    for cluster in _cluster_list():
        if cluster["id"] == cluster_id:
            return _jsonable(cluster)
    raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")


@app.get("/api/clusters/{cluster_id}/playlist")
def cluster_playlist(cluster_id: int, n_tracks: int = 10, sort_by: str = "random") -> dict:
    if sort_by not in {"random", "popularity", "match_score"}:
        raise HTTPException(status_code=400, detail="sort_by must be random, popularity, or match_score")
    return _jsonable(handle_generate_playlist(cluster_id=cluster_id, n_tracks=n_tracks, sort_by=sort_by))


@app.get("/api/cluster-map")
def cluster_map(min_popularity: int = 0, max_popularity: int = 100) -> dict:
    models = _models()
    tsne_2d = models.get("tsne_2d")
    tsne_indices = models.get("tsne_indices")
    tracks_df = models["tracks_df"]
    cluster_names = {cluster["id"]: cluster["name"] for cluster in _cluster_list()}

    if tsne_2d is None or tsne_indices is None:
        return {"points": []}

    df_tsne = tracks_df.iloc[tsne_indices].reset_index(drop=True)
    points = []
    popularity_mask = (df_tsne["popularity"] >= min_popularity) & (df_tsne["popularity"] <= max_popularity)
    for row_index, row in df_tsne[popularity_mask].iterrows():
        cluster_id = int(row.get("cluster_label", -1))
        x, y = tsne_2d[row_index]
        points.append(
            {
                "x": float(x),
                "y": float(y),
                "cluster_id": cluster_id,
                "cluster_name": cluster_names.get(cluster_id, f"Cluster {cluster_id}"),
                "track_id": row.get("track_id", ""),
                "track_name": row.get("track_name", ""),
                "artist_name": row.get("artist_name", ""),
                "popularity": int(row.get("popularity", 0)),
            }
        )
    return {"points": _jsonable(points)}


@app.get("/api/analysis")
def analysis() -> dict:
    models = _models()
    metadata = models["metadata"]
    cohesion_rows = analysis_service.cohesion_separation_rows(models)
    return _jsonable(
        {
            "evaluation": metadata.get("evaluation", {}),
            "pca_report": models.get("pca_report", {}),
            "k_eval": models.get("k_eval", {}),
            "clusters": metadata.get("clusters", {}),
            "tsne_available": metadata.get("tsne_available", models.get("tsne_2d") is not None),
            "diagnostic_plots": analysis_service.diagnostic_plots(),
            "cohesion_separation": cohesion_rows,
            "analysis_report": analysis_service.analysis_report(models, cohesion_rows),
        }
    )


@app.get("/api/analysis/plots/{plot_name}")
def analysis_plot(plot_name: str):
    plot_path = analysis_service.get_plot_path(plot_name)
    if plot_path is None:
        raise HTTPException(status_code=404, detail="Analysis plot not found")
    return FileResponse(plot_path, media_type="image/png")


@app.get("/api/feature-distributions")
def feature_distributions() -> dict:
    return _jsonable(analysis_service.feature_distributions(_models()))


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict:
    try:
        agent = _agent()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    response_text, tool_log = agent.send(request.message)
    return _jsonable(
        {
            "message": response_text,
            "current_cluster": agent.current_cluster,
            "playlist": agent.current_playlist,
            "cover_url": agent.cover_url,
            "tool_log": tool_log,
        }
    )


@app.post("/api/chat/reset")
def reset_chat() -> dict:
    try:
        _agent().reset()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"ok": True}


@app.post("/api/album-cover")
def album_cover(request: AlbumCoverRequest) -> dict:
    return _jsonable(handle_generate_album_cover(**request.model_dump()))


@app.get("/api/saved-playlists")
def saved_playlists() -> dict:
    return {"playlists": _jsonable(playlist_store.load_all())}


@app.post("/api/saved-playlists")
def save_playlist(request: SavedPlaylistRequest) -> dict:
    playlist_id = playlist_store.save(
        cluster=request.cluster,
        centroid=request.centroid,
        tracks=request.tracks,
        cover_url=request.cover_url,
        cover_prompt=request.cover_prompt,
    )
    return {"id": playlist_id}


@app.delete("/api/saved-playlists/{playlist_id}")
def delete_playlist(playlist_id: str) -> dict:
    playlist_store.delete(playlist_id)
    return {"ok": True}


@app.get("/api/saved-playlists/{playlist_id}/cover")
def saved_playlist_cover(playlist_id: str):
    cover_path = playlist_store.get_cover_path(playlist_id)
    if cover_path is None:
        raise HTTPException(status_code=404, detail="Cover not found")
    return FileResponse(cover_path)
