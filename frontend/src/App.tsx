import { useEffect, useState } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import VibeCheckTab from './components/VibeCheckTab';
import ExploreClustersTab from './components/ExploreClustersTab';
import AcademicAnalysisTab from './components/AcademicAnalysisTab';
import SavedPlaylistsTab from './components/SavedPlaylistsTab';
import PlaylistDetailTab from './components/PlaylistDetailTab';
import { api } from './api';
import {
  AnalysisPayload,
  Cluster,
  ClusterPoint,
  FeatureDistributionsPayload,
  HealthStatus,
  Playlist,
  SavePlaylistPayload,
} from './types';
import { motion, AnimatePresence } from 'motion/react';
import { Sparkles, LineChart, Network, BookOpen, Music } from 'lucide-react';
import { createInitialVibeCheckState, VibeCheckState } from './vibeCheckState';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('vibe_check');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [clusterPoints, setClusterPoints] = useState<ClusterPoint[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisPayload | null>(null);
  const [featureDistributions, setFeatureDistributions] = useState<FeatureDistributionsPayload | null>(null);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<string | null>(null);
  const [vibeCheckState, setVibeCheckState] = useState<VibeCheckState>(() => createInitialVibeCheckState());
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [appError, setAppError] = useState<string | null>(null);

  const modelStatus = health?.models_loaded ? 'Online' : 'Needs setup';

  const navbarTitles: Record<string, string> = {
    vibe_check: 'Spotify Vibe Check | Dashboard',
    explore: 'Explore Clusters | latent audio space',
    academic: 'Academic Analysis | Comparative Matrix',
    saved_playlists: 'Saved Playlists Library',
    playlist_detail: 'Wave Calibration Details',
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const refreshSavedPlaylists = async () => {
    const saved = await api.savedPlaylists();
    setPlaylists(saved);
  };

  useEffect(() => {
    let cancelled = false;
    async function loadDashboard() {
      try {
        const [healthPayload, clusterPayload, analysisPayload, mapPayload, distributionPayload, savedPayload] = await Promise.all([
          api.health(),
          api.clusters(),
          api.analysis(),
          api.clusterMap(0, 100),
          api.featureDistributions(),
          api.savedPlaylists(),
        ]);
        if (cancelled) return;
        setHealth(healthPayload);
        setClusters(clusterPayload);
        setAnalysis(analysisPayload);
        setClusterPoints(mapPayload);
        setFeatureDistributions(distributionPayload);
        setPlaylists(savedPayload);
      } catch (error) {
        if (!cancelled) {
          setAppError(error instanceof Error ? error.message : 'Could not load backend data');
        }
      }
    }

    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSavePlaylist = async (payload: SavePlaylistPayload) => {
    try {
      const result = await api.savePlaylist(payload);
      await refreshSavedPlaylists();
      setSelectedPlaylistId(result.id);
      showToast(`Saved "${payload.cluster.cluster_name}" to your playlist library.`);
      setTimeout(() => setActiveTab('saved_playlists'), 500);
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Could not save playlist.');
    }
  };

  const handleDeletePlaylist = async (id: string) => {
    try {
      await api.deletePlaylist(id);
      setPlaylists((prev) => prev.filter((p) => p.id !== id));
      if (selectedPlaylistId === id) setSelectedPlaylistId(null);
      showToast('Playlist deleted.');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Could not delete playlist.');
    }
  };

  const handleOpenPlaylist = (id: string) => {
    setSelectedPlaylistId(id);
    setActiveTab('playlist_detail');
  };

  const activePlaylist = playlists.find((p) => p.id === selectedPlaylistId) || playlists[0];

  return (
    <div className="min-h-screen flex flex-col relative select-none">
      <div className="fixed top-[-10%] right-[-10%] w-[50%] h-[50%] bg-[#53e076]/5 rounded-full blur-[150px] -z-10 pointer-events-none"></div>
      <div className="fixed bottom-[-10%] left-[-10%] w-[50%] h-[50%] bg-[#37d7ff]/5 rounded-full blur-[150px] -z-10 pointer-events-none"></div>

      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} modelStatus={modelStatus} health={health} />

      <div className="md:ml-[260px] flex-grow flex flex-col pb-24 md:pb-8">
        <Navbar title={navbarTitles[activeTab] || 'Spotify Vibe Check'} />

        <main className="flex-grow p-4 sm:p-6 md:p-8 max-w-[1600px] mx-auto w-full">
          {appError && (
            <div className="mb-6 glass-panel rounded-xl p-4 border border-[#ffb4ab]/30 text-[#ffb4ab] text-sm">
              Backend connection problem: {appError}
            </div>
          )}

          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="w-full h-full"
            >
              {activeTab === 'vibe_check' && (
                <VibeCheckTab
                  clusters={clusters}
                  state={vibeCheckState}
                  onStateChange={setVibeCheckState}
                  onSavePlaylist={handleSavePlaylist}
                  onOpenPlaylist={handleOpenPlaylist}
                />
              )}

              {activeTab === 'explore' && (
                <ExploreClustersTab clusters={clusters} points={clusterPoints} featureDistributions={featureDistributions} />
              )}

              {activeTab === 'academic' && <AcademicAnalysisTab analysis={analysis} health={health} />}

              {activeTab === 'saved_playlists' && (
                <SavedPlaylistsTab
                  playlists={playlists}
                  onDeletePlaylist={handleDeletePlaylist}
                  onOpenPlaylist={handleOpenPlaylist}
                  onAddNewPlaylist={() => setActiveTab('vibe_check')}
                />
              )}

              {activeTab === 'playlist_detail' && activePlaylist && (
                <PlaylistDetailTab
                  playlist={activePlaylist}
                  onBack={() => setActiveTab('saved_playlists')}
                  onEditVibe={() => setActiveTab('vibe_check')}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <nav className="fixed bottom-0 left-0 w-full z-50 md:hidden bg-[#131313]/90 backdrop-blur-xl border-t border-white/10 flex justify-around items-center h-16 pb-safe px-2 shadow-2xl">
        {[
          { id: 'vibe_check', label: 'Vibe', icon: LineChart },
          { id: 'explore', label: 'Clusters', icon: Network },
          { id: 'academic', label: 'Academic', icon: BookOpen },
          { id: 'saved_playlists', label: 'Saved', icon: Music },
        ].map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id || (item.id === 'saved_playlists' && activeTab === 'playlist_detail');
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center justify-center py-2 px-3 transition-all ${
                isActive ? 'text-[#53e076] scale-105 font-bold' : 'text-[#bccbb9] hover:text-white'
              }`}
            >
              <Icon size={18} />
              <span className="text-[10px] uppercase font-mono tracking-wider mt-1">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <AnimatePresence>
        {toastMessage && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed bottom-20 md:bottom-8 right-4 md:right-8 z-50 bg-[#201f1f] border border-[#53e076]/30 px-5 py-3 rounded-xl shadow-2xl max-w-sm flex items-center gap-3 text-white"
          >
            <Sparkles size={16} className="text-[#53e076] animate-pulse flex-shrink-0" />
            <p className="text-xs font-medium leading-relaxed">{toastMessage}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
