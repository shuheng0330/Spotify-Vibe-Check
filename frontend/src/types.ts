export interface HealthStatus {
  models_loaded: boolean;
  track_count: number;
  cluster_count: number;
  selected_algorithm: string;
  tsne_available: boolean;
  error?: string;
}

export interface AudioCentroid {
  energy?: number;
  valence?: number;
  danceability?: number;
  acousticness?: number;
  tempo?: number;
  speechiness?: number;
  instrumentalness?: number;
  mode?: number;
}

export interface BackendTrack {
  track_id?: string;
  track_name?: string;
  artist_name?: string;
  album_name?: string;
  popularity?: number;
  energy?: number;
  valence?: number;
  danceability?: number;
  acousticness?: number;
  tempo?: number;
  duration_ms?: number;
  spotify_url?: string;
  artwork_url?: string;
}

export interface Track {
  id: string;
  title: string;
  artist: string;
  albumArt: string;
  popularity: number;
  energy: number;
  valence: number;
  danceability: number;
  acousticness: number;
  duration: string;
  spotifyUrl?: string;
  tempo?: number;
}

export interface Cluster {
  id: number;
  name: string;
  track_count: number;
  centroid: AudioCentroid;
  top_artists: string[];
  representative_tracks: BackendTrack[];
}

export interface Playlist {
  id: string;
  name: string;
  tag: string;
  tagColor: string;
  savedDate: string;
  trackCount: number;
  tracks: Track[];
  energy: number;
  valence: number;
  danceability: number;
  acousticness: number;
  imageUrl: string;
  bpm: number;
  description: string;
  prompt?: string;
  cluster?: ClusterSummary;
  centroid?: AudioCentroid;
}

export interface ClusterSummary {
  cluster_id: number;
  cluster_name: string;
  track_count?: number;
  match_score?: number;
  representative_tracks?: BackendTrack[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'dj';
  text: string;
  timestamp: string;
  isAiOptimized?: boolean;
}

export interface ClusterPoint {
  x: number;
  y: number;
  cluster_id: number;
  cluster_name: string;
  track_id: string;
  track_name: string;
  artist_name: string;
  popularity: number;
}

export interface DiagnosticPlot {
  title: string;
  available: boolean;
  url: string;
}

export interface CohesionSeparationRow {
  cluster_id: number;
  cluster_name: string;
  'cohesion (avg intra-dist)': number;
  'separation (min inter-dist)': number;
  'ratio (sep/coh)': number;
}

export interface FeatureDistributionRow {
  cluster_id: number;
  cluster_name: string;
  count: number;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  mean: number;
}

export interface FeatureDistributionsPayload {
  features: string[];
  distributions: Record<string, FeatureDistributionRow[]>;
}

export interface AnalysisPayload {
  evaluation: {
    algorithm?: string;
    silhouette?: number;
    davies_bouldin?: number;
    n_clusters?: number;
    kmeans?: Record<string, number>;
    gmm?: Record<string, number>;
    dbscan?: Record<string, number>;
  };
  pca_report: {
    individual?: number[];
    cumulative?: number[];
    n_components?: number;
  };
  k_eval: Record<string, { inertia: number; silhouette: number }>;
  clusters: Record<string, Cluster>;
  tsne_available: boolean;
  diagnostic_plots: Record<string, DiagnosticPlot>;
  cohesion_separation: CohesionSeparationRow[];
  analysis_report: string;
}

export interface ChatResponse {
  message: string;
  current_cluster: ClusterSummary | null;
  playlist: BackendTrack[] | null;
  cover_url: string | null;
  tool_log: unknown[];
}

export interface SavePlaylistPayload {
  cluster: ClusterSummary;
  centroid: AudioCentroid;
  tracks: BackendTrack[];
  cover_url?: string | null;
  cover_prompt?: string | null;
}
