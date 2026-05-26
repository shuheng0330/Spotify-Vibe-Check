import { AudioCentroid, Playlist, Track } from './types';

export interface SavedPlaylistFilters {
  category: string;
  featurePreset: 'all' | 'high_energy' | 'positive' | 'danceable' | 'acoustic';
  sortBy: 'newest' | 'oldest' | 'name' | 'energy' | 'valence' | 'danceability';
}

export const DEFAULT_SAVED_PLAYLIST_FILTERS: SavedPlaylistFilters = {
  category: 'all',
  featurePreset: 'all',
  sortBy: 'newest',
};

export function averageTrackFeaturePercent(
  tracks: Track[],
  centroid: AudioCentroid,
  feature: 'energy' | 'valence' | 'danceability' | 'acousticness'
): number {
  const values = tracks.map((track) => track[feature]).filter((value) => Number.isFinite(value) && value > 0);
  if (values.length > 0) {
    const average = values.reduce((sum, value) => sum + value, 0) / values.length;
    return Math.round(Math.max(0, Math.min(1, average)) * 100);
  }
  return Math.round(Math.max(0, Math.min(1, centroid[feature] || 0)) * 100);
}

function savedDateValue(playlist: Playlist): number {
  const parsed = Date.parse(playlist.savedDate);
  return Number.isFinite(parsed) ? parsed : 0;
}

function median(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) return (sorted[middle - 1] + sorted[middle]) / 2;
  return sorted[middle];
}

export function filterSavedPlaylists(playlists: Playlist[], filters: SavedPlaylistFilters): Playlist[] {
  const categoryFiltered = playlists.filter((playlist) => filters.category === 'all' || playlist.tag === filters.category);
  const thresholds = {
    energy: median(categoryFiltered.map((playlist) => playlist.energy)),
    valence: median(categoryFiltered.map((playlist) => playlist.valence)),
    danceability: median(categoryFiltered.map((playlist) => playlist.danceability)),
    acousticness: median(categoryFiltered.map((playlist) => playlist.acousticness)),
  };

  return playlists
    .filter((playlist) => filters.category === 'all' || playlist.tag === filters.category)
    .filter((playlist) => {
      if (filters.featurePreset === 'high_energy') return playlist.energy >= thresholds.energy;
      if (filters.featurePreset === 'positive') return playlist.valence >= thresholds.valence;
      if (filters.featurePreset === 'danceable') return playlist.danceability >= thresholds.danceability;
      if (filters.featurePreset === 'acoustic') return playlist.acousticness >= thresholds.acousticness;
      return true;
    })
    .sort((a, b) => {
      if (filters.sortBy === 'oldest') return savedDateValue(a) - savedDateValue(b);
      if (filters.sortBy === 'name') return a.name.localeCompare(b.name);
      if (filters.sortBy === 'energy') return b.energy - a.energy;
      if (filters.sortBy === 'valence') return b.valence - a.valence;
      if (filters.sortBy === 'danceability') return b.danceability - a.danceability;
      return savedDateValue(b) - savedDateValue(a);
    });
}
