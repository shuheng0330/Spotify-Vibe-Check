import { BackendTrack, ChatMessage, Cluster, ClusterSummary } from './types';

export interface VibeCheckState {
  chatMessages: ChatMessage[];
  clusterSummary: ClusterSummary | null;
  rawPlaylist: BackendTrack[];
  coverUrl: string | null;
  coverPrompt: string | null;
}

function nowLabel() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function createInitialVibeCheckState(): VibeCheckState {
  return {
    chatMessages: [
      {
        id: 'intro',
        sender: 'dj',
        text: 'Tell me what you want to listen to. I will use the trained backend model to match your mood to a real cluster and build a playlist from it.',
        timestamp: nowLabel(),
        isAiOptimized: true,
      },
    ],
    clusterSummary: null,
    rawPlaylist: [],
    coverUrl: null,
    coverPrompt: null,
  };
}

export function resolveActiveCluster(clusterSummary: ClusterSummary | null, clusters: Cluster[]): Cluster | null {
  if (!clusterSummary) return null;
  return clusters.find((cluster) => cluster.id === clusterSummary.cluster_id) || null;
}
