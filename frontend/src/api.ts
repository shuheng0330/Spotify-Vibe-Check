import {
  AnalysisPayload,
  AudioCentroid,
  BackendTrack,
  ChatResponse,
  Cluster,
  ClusterPoint,
  FeatureDistributionsPayload,
  HealthStatus,
  Playlist,
  SavePlaylistPayload,
  Track,
} from './types';
import { averageTrackFeaturePercent } from './savedPlaylistUtils';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const FALLBACK_COVER =
  'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&q=80&w=400&h=400';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { ...((init?.headers as Record<string, string>) || {}) };
  if (init?.body) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers,
    ...init,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Keep the generic message when the server does not return JSON.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

function cleanArtist(value?: string): string {
  if (!value) return 'Unknown Artist';
  return value.replace(/^\[/, '').replace(/\]$/, '').replaceAll("'", '').trim();
}

function formatDuration(durationMs?: number): string {
  if (!durationMs) return '--:--';
  const totalSeconds = Math.max(0, Math.round(durationMs / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = `${totalSeconds % 60}`.padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function percent(value?: number): number {
  return Math.round(Math.max(0, Math.min(1, value || 0)) * 100);
}

function resolveUrl(value?: string | null): string | undefined {
  if (!value) return undefined;
  if (value.startsWith('http://') || value.startsWith('https://')) return value;
  return `${API_BASE_URL}${value}`;
}

export function apiUrl(path?: string | null): string {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return `${API_BASE_URL}${path}`;
}

export function mapTrack(track: BackendTrack): Track {
  return {
    id: track.track_id || `${track.track_name}-${track.artist_name}`,
    title: track.track_name || 'Unknown Track',
    artist: cleanArtist(track.artist_name),
    albumArt: track.artwork_url || FALLBACK_COVER,
    popularity: Math.round(track.popularity || 0),
    energy: Number(track.energy || 0),
    valence: Number(track.valence || 0),
    danceability: Number(track.danceability || 0),
    acousticness: Number(track.acousticness || 0),
    duration: formatDuration(track.duration_ms),
    spotifyUrl: track.spotify_url,
    tempo: track.tempo,
  };
}

export function mapSavedPlaylist(raw: any): Playlist {
  const centroid: AudioCentroid = raw.centroid || {};
  const clusterName = raw.cluster?.cluster_name || 'Saved Playlist';
  const savedDate = raw.saved_at
    ? new Date(raw.saved_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : 'Unknown date';
  const tracks = (raw.tracks || []).map(mapTrack);
  const firstArtwork = tracks.find((track) => track.albumArt)?.albumArt;

  return {
    id: raw.id,
    name: clusterName,
    tag: clusterName,
    tagColor: raw.cluster?.cluster_id === 0 ? 'secondary' : raw.cluster?.cluster_id === 2 ? 'tertiary' : 'primary',
    savedDate,
    trackCount: tracks.length,
    tracks,
    energy: averageTrackFeaturePercent(tracks, centroid, 'energy'),
    valence: averageTrackFeaturePercent(tracks, centroid, 'valence'),
    danceability: averageTrackFeaturePercent(tracks, centroid, 'danceability'),
    acousticness: averageTrackFeaturePercent(tracks, centroid, 'acousticness'),
    bpm: Math.round(centroid.tempo || 0),
    imageUrl: resolveUrl(raw.cover_url) || firstArtwork || FALLBACK_COVER,
    description: `${clusterName} saved from the real clustering pipeline with ${tracks.length} recommended tracks.`,
    prompt: raw.cover_prompt || raw.prompt_used || undefined,
    cluster: raw.cluster,
    centroid,
  };
}

export function playlistFromCluster(cluster: Cluster, tracks: BackendTrack[], coverUrl?: string | null): Playlist {
  const mappedTracks = tracks.map(mapTrack);
  const firstArtwork = mappedTracks.find((track) => track.albumArt)?.albumArt;
  return {
    id: `cluster-${cluster.id}`,
    name: cluster.name,
    tag: cluster.name,
    tagColor: cluster.id === 0 ? 'secondary' : cluster.id === 2 ? 'tertiary' : 'primary',
    savedDate: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    trackCount: mappedTracks.length,
    tracks: mappedTracks,
    energy: percent(cluster.centroid.energy),
    valence: percent(cluster.centroid.valence),
    danceability: percent(cluster.centroid.danceability),
    acousticness: percent(cluster.centroid.acousticness),
    bpm: Math.round(cluster.centroid.tempo || 0),
    imageUrl: coverUrl || firstArtwork || FALLBACK_COVER,
    description: `${cluster.name} contains ${cluster.track_count.toLocaleString()} tracks with a centroid shaped by the trained clustering model.`,
    prompt: coverUrl || undefined,
    cluster: { cluster_id: cluster.id, cluster_name: cluster.name, track_count: cluster.track_count },
    centroid: cluster.centroid,
  };
}

export const api = {
  health: () => request<HealthStatus>('/api/health'),
  clusters: async () => (await request<{ clusters: Cluster[] }>('/api/clusters')).clusters,
  clusterPlaylist: (clusterId: number, nTracks = 10) =>
    request<{ playlist: BackendTrack[]; cluster_id: number; cluster_name: string; n_tracks: number }>(
      `/api/clusters/${clusterId}/playlist?n_tracks=${nTracks}`
    ),
  clusterMap: async (minPopularity = 0, maxPopularity = 100) =>
    (
      await request<{ points: ClusterPoint[] }>(
        `/api/cluster-map?min_popularity=${minPopularity}&max_popularity=${maxPopularity}`
      )
    ).points,
  analysis: () => request<AnalysisPayload>('/api/analysis'),
  featureDistributions: () => request<FeatureDistributionsPayload>('/api/feature-distributions'),
  chat: (message: string) =>
    request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
  resetChat: () => request<{ ok: boolean }>('/api/chat/reset', { method: 'POST' }),
  albumCover: (payload: {
    cluster_name: string;
    energy?: number;
    valence?: number;
    acousticness?: number;
    instrumentalness?: number;
    tempo?: number;
  }) =>
    request<{ image_url: string; prompt_used: string }>('/api/album-cover', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  savedPlaylists: async () =>
    (await request<{ playlists: any[] }>('/api/saved-playlists')).playlists.map(mapSavedPlaylist),
  savePlaylist: (payload: SavePlaylistPayload) =>
    request<{ id: string }>('/api/saved-playlists', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  deletePlaylist: (id: string) => request<{ ok: boolean }>(`/api/saved-playlists/${id}`, { method: 'DELETE' }),
};
