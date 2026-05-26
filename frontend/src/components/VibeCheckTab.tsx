import { Dispatch, SetStateAction, useMemo, useState } from 'react';
import { Bot, Send, Palette, Plus, ArrowUpRight } from 'lucide-react';
import { api, mapTrack } from '../api';
import { ChatMessage, Cluster, SavePlaylistPayload } from '../types';
import { motion, AnimatePresence } from 'motion/react';
import { resolveActiveCluster, VibeCheckState } from '../vibeCheckState';

interface VibeCheckTabProps {
  clusters: Cluster[];
  state: VibeCheckState;
  onStateChange: Dispatch<SetStateAction<VibeCheckState>>;
  onSavePlaylist: (payload: SavePlaylistPayload) => Promise<void>;
  onOpenPlaylist: (playlistId: string) => void;
}

function nowLabel() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function percent(value?: number) {
  return Math.round(Math.max(0, Math.min(1, value || 0)) * 100);
}

export default function VibeCheckTab({ clusters, state, onStateChange, onSavePlaylist }: VibeCheckTabProps) {
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isGeneratingCover, setIsGeneratingCover] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const { chatMessages, clusterSummary, rawPlaylist, coverUrl, coverPrompt } = state;

  const activeCluster = useMemo(() => resolveActiveCluster(clusterSummary, clusters), [clusterSummary, clusters]);

  const activeTracks = useMemo(() => {
    if (rawPlaylist.length > 0) return rawPlaylist.map(mapTrack);
    return (activeCluster?.representative_tracks || []).map(mapTrack);
  }, [activeCluster, rawPlaylist]);

  const energy = percent(activeCluster?.centroid.energy);
  const valence = percent(activeCluster?.centroid.valence);
  const danceability = percent(activeCluster?.centroid.danceability);
  const acousticness = percent(activeCluster?.centroid.acousticness);
  const bpm = Math.round(activeCluster?.centroid.tempo || 0);
  const imageUrl = coverUrl || activeTracks[0]?.albumArt || 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&q=80&w=400&h=400';

  const handleChatSend = async () => {
    if (!chatInput.trim()) return;

    const userText = chatInput.trim();
    const userMsg: ChatMessage = {
      id: `${Date.now()}-user`,
      sender: 'user',
      text: userText,
      timestamp: nowLabel(),
    };

    onStateChange((prev) => ({ ...prev, chatMessages: [...prev.chatMessages, userMsg] }));
    setChatInput('');
    setIsChatLoading(true);

    try {
      const response = await api.chat(userText);

      onStateChange((prev) => ({
        ...prev,
        clusterSummary: response.current_cluster || prev.clusterSummary,
        rawPlaylist: response.playlist || prev.rawPlaylist,
        coverUrl: response.cover_url || prev.coverUrl,
        chatMessages: [
          ...prev.chatMessages,
          {
            id: `${Date.now()}-dj`,
            sender: 'dj',
            text: response.message,
            timestamp: nowLabel(),
            isAiOptimized: true,
          },
        ],
      }));
    } catch (error) {
      onStateChange((prev) => ({
        ...prev,
        chatMessages: [
          ...prev.chatMessages,
          {
            id: `${Date.now()}-error`,
            sender: 'dj',
            text:
              error instanceof Error
                ? error.message
                : 'The DJ chat service is not configured. Cluster exploration is still available.',
            timestamp: nowLabel(),
          },
        ],
      }));
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleGenerateCover = async () => {
    if (!activeCluster) return;
    setIsGeneratingCover(true);
    try {
      const result = await api.albumCover({
        cluster_name: activeCluster.name,
        energy: activeCluster.centroid.energy,
        valence: activeCluster.centroid.valence,
        acousticness: activeCluster.centroid.acousticness,
        instrumentalness: activeCluster.centroid.instrumentalness,
        tempo: activeCluster.centroid.tempo,
      });
      onStateChange((prev) => ({ ...prev, coverUrl: result.image_url, coverPrompt: result.prompt_used }));
    } catch (error) {
      onStateChange((prev) => ({
        ...prev,
        chatMessages: [
          ...prev.chatMessages,
          {
            id: `${Date.now()}-cover-error`,
            sender: 'dj',
            text: error instanceof Error ? error.message : 'Cover generation failed.',
            timestamp: nowLabel(),
          },
        ],
      }));
    } finally {
      setIsGeneratingCover(false);
    }
  };

  const handleSave = async () => {
    if (!activeCluster) return;
    setIsSaving(true);
    try {
      let tracksToSave = rawPlaylist;
      if (tracksToSave.length === 0) {
        const generated = await api.clusterPlaylist(activeCluster.id, 10);
        tracksToSave = generated.playlist;
        onStateChange((prev) => ({ ...prev, rawPlaylist: tracksToSave }));
      }
      await onSavePlaylist({
        cluster: {
          cluster_id: activeCluster.id,
          cluster_name: activeCluster.name,
          track_count: activeCluster.track_count,
          match_score: clusterSummary?.match_score,
        },
        centroid: activeCluster.centroid,
        tracks: tracksToSave,
        cover_url: coverUrl,
        cover_prompt: coverPrompt,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const eVal = energy / 100;
  const vVal = valence / 100;
  const dVal = danceability / 100;
  const aVal = acousticness / 100;
  const radarPoints = `${50}, ${50 - 42 * eVal} ${50 + 42 * vVal}, ${50} ${50}, ${50 + 42 * dVal} ${50 - 42 * aVal}, ${50}`;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8" id="vibe-check-tab">
      <section className="lg:col-span-5 flex flex-col gap-6">
        <div className="glass-panel rounded-xl p-6 relative overflow-hidden group flex flex-col gap-5">
          <div className="flex justify-between items-start gap-4">
            <div>
              <h2 className="text-[10px] text-[#bccbb9] uppercase tracking-widest font-bold font-mono">Current Cluster</h2>
              <h3 className="text-2xl font-black text-white mt-1">{activeCluster?.name || 'Awaiting vibe'}</h3>
              {!activeCluster && (
                <p className="text-xs text-[#bccbb9] mt-2 max-w-sm">
                  Ask the DJ for a mood or listening context to select a real cluster and generate a playlist.
                </p>
              )}
            </div>
            {clusterSummary?.match_score && (
              <span className="bg-[#53e076]/25 text-[#53e076] px-3 py-1 rounded-full text-[10px] font-bold border border-[#53e076]/30">
                Model selected
              </span>
            )}
          </div>

          <div className="aspect-[4/3] w-full rounded-lg overflow-hidden border border-white/10 shadow-2xl relative">
            <AnimatePresence mode="wait">
              <motion.img
                key={imageUrl}
                initial={{ opacity: 0.8, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0.8, scale: 0.95 }}
                transition={{ duration: 0.4 }}
                alt={`${activeCluster?.name || 'Awaiting vibe'} cover`}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 pointer-events-none"
                src={imageUrl}
              />
            </AnimatePresence>

            {isGeneratingCover && (
              <div className="absolute inset-0 bg-black/70 backdrop-blur-sm flex flex-col items-center justify-center gap-3">
                <span className="relative flex h-8 w-8">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#53e076] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-8 w-8 bg-[#53e076]"></span>
                </span>
                <p className="text-xs font-mono text-[#53e076] tracking-widest uppercase animate-pulse">Generating Cover...</p>
              </div>
            )}
          </div>
        </div>

        <div className="glass-panel rounded-xl p-6 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-white tracking-tight">Audio Feature Profile</h2>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-[#bccbb9]">Tempo:</span>
              <span className="text-xs text-[#53e076] font-bold font-mono">{bpm || '--'} BPM</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 items-center">
            <div className="flex justify-center select-none">
              <div className="relative w-[180px] h-[180px]">
                <svg viewBox="0 0 100 100" className="w-[180px] h-[180px] text-[#53e076]">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" />
                  <circle cx="50" cy="50" r="30" fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" />
                  <circle cx="50" cy="50" r="15" fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" />
                  <line x1="50" y1="5" x2="50" y2="95" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" />
                  <line x1="5" y1="50" x2="95" y2="50" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" strokeDasharray="1 3" />
                  <polygon points={radarPoints} fill="rgba(83, 224, 118, 0.25)" stroke="#53e076" strokeWidth="1.5" />
                  <circle cx="50" cy="50" r="2" fill="white" />
                </svg>
                <div className="absolute top-1 left-1/2 -translate-x-1/2 text-[8px] font-bold text-[#bccbb9] uppercase font-mono tracking-widest">Energy</div>
                <div className="absolute right-1 top-1/2 -translate-y-1/2 text-[8px] font-bold text-[#bccbb9] uppercase font-mono tracking-widest">Valence</div>
                <div className="absolute bottom-1 left-1/2 -translate-x-1/2 text-[8px] font-bold text-[#bccbb9] uppercase font-mono tracking-widest">Dance</div>
                <div className="absolute left-1 top-1/2 -translate-y-1/2 text-[8px] font-bold text-[#bccbb9] uppercase font-mono tracking-widest">Acoustic</div>
              </div>
            </div>

            <div className="space-y-4">
              {[
                ['Energy', energy, '#53e076'],
                ['Valence', valence, '#37d7ff'],
                ['Danceability', danceability, '#53e076'],
                ['Acousticness', acousticness, '#ffffff'],
              ].map(([label, value, color]) => (
                <div className="space-y-1" key={label}>
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-[#bccbb9]">{label}</span>
                    <span className="font-bold" style={{ color: color as string }}>{value}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={value as number}
                    readOnly
                    className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-default"
                    style={{ accentColor: color as string }}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mt-8">
            <button
              onClick={handleGenerateCover}
              disabled={!activeCluster || isGeneratingCover}
              className="py-3 px-4 border border-white/20 rounded-lg font-semibold text-xs text-white hover:bg-white/5 active:scale-95 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Palette size={14} className="text-[#bccbb9]" />
              Generate Cover
            </button>
            <button
              onClick={handleSave}
              disabled={!activeCluster || isSaving}
              className="py-3 px-4 rounded-lg font-bold text-xs flex items-center justify-center gap-2 active:scale-95 transition-all text-black bg-[#53e076] hover:brightness-110 disabled:opacity-50"
            >
              <Plus size={14} />
              {isSaving ? 'Saving...' : 'Save Playlist'}
            </button>
          </div>
        </div>
      </section>

      <section className="lg:col-span-7 flex flex-col gap-8">
        <div className="glass-panel rounded-xl flex flex-col h-[560px] xl:h-[640px]">
          <div className="p-4 border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#53e076]/20 flex items-center justify-center border border-[#53e076]/40">
                <Bot size={18} className="text-[#53e076]" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-white tracking-wide">Dynamic DJ Chat</h3>
                <span className="text-[10px] text-[#bccbb9] uppercase tracking-wider font-semibold font-mono">
                  {isChatLoading ? 'Matching mood...' : 'OpenRouter backed'}
                </span>
              </div>
            </div>
          </div>

          <div className="flex-grow overflow-y-auto p-5 sm:p-6 space-y-5 custom-scrollbar select-text">
            {chatMessages.map((msg) => (
              <div key={msg.id} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                <div
                  className={`max-w-[92%] sm:max-w-[86%] p-4 rounded-2xl border text-sm leading-relaxed select-text ${
                    msg.sender === 'user'
                      ? 'rounded-tr-none border-[#53e076]/40 bg-white/5 text-white'
                      : 'rounded-tl-none border-white/10 bg-[#222] text-white'
                  }`}
                >
                  <p className="whitespace-pre-line text-sm font-sans select-text cursor-text">{msg.text}</p>
                </div>
                <span className="text-[9px] text-[#bccbb9] mt-1 px-1 font-mono select-text">
                  {msg.timestamp} {msg.isAiOptimized && ' - backend response'}
                </span>
              </div>
            ))}
          </div>

          <div className="p-4 border-t border-white/10">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleChatSend();
              }}
              className="relative"
            >
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Describe your mood or listening context..."
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-xs focus:ring-1 focus:ring-[#53e076]/50 focus:border-[#53e076]/50 outline-none pr-12 text-white"
              />
              <button
                type="submit"
                disabled={isChatLoading}
                className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-[#53e076] hover:brightness-110 active:scale-95 transition-all rounded-lg flex items-center justify-center text-black disabled:opacity-50"
              >
                <Send size={14} />
              </button>
            </form>
          </div>
        </div>

        <div className="glass-panel rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">Active Playlist Tracks</h2>
              <p className="text-[10px] text-[#bccbb9] font-mono mt-0.5">
                {rawPlaylist.length > 0
                  ? 'MATCHES DJ CHAT RESPONSE'
                  : activeCluster
                    ? 'REPRESENTATIVE CLUSTER TRACKS'
                    : 'WAITING FOR DJ MATCH'}{' '}
                - {activeTracks.length} TRACKS
              </p>
            </div>
            <span className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-xs font-bold text-white flex items-center gap-1">
              {activeCluster?.name || 'No cluster selected'}
              <ArrowUpRight size={14} />
            </span>
          </div>

          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left font-sans text-xs">
              <thead>
                <tr className="border-b border-white/15 text-[#bccbb9] uppercase font-mono tracking-wider text-[10px]">
                  <th className="pb-3 w-8">#</th>
                  <th className="pb-3">Track Info</th>
                  <th className="pb-3 hidden sm:table-cell">Popularity</th>
                  <th className="pb-3 text-right">Spotify</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {activeTracks.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-xs text-[#bccbb9]">
                      No active playlist yet. Send a message to the DJ to match a cluster and generate tracks.
                    </td>
                  </tr>
                )}
                {activeTracks.slice(0, 8).map((track, i) => (
                  <tr key={`${track.id}-${i}`} className="group hover:bg-white/5 transition-colors">
                    <td className="py-3 text-xs font-mono text-[#bccbb9]">{i + 1}</td>
                    <td className="py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded overflow-hidden flex-shrink-0 bg-white/5 border border-white/10 relative">
                          <img alt={track.title} className="w-full h-full object-cover transition-transform group-hover:scale-105" src={track.albumArt} />
                        </div>
                        <div>
                          <p className="font-bold text-white text-xs leading-none">{track.title}</p>
                          <p className="text-[10px] text-[#bccbb9] mt-1 leading-none">{track.artist}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 hidden sm:table-cell">
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-[#53e076]" style={{ width: `${track.popularity}%` }}></div>
                        </div>
                        <span className="text-[10px] font-mono font-bold text-[#bccbb9]">{track.popularity}</span>
                      </div>
                    </td>
                    <td className="py-3 text-right">
                      {track.spotifyUrl ? (
                        <a href={track.spotifyUrl} target="_blank" rel="noreferrer" className="p-1.5 inline-flex bg-white/5 group-hover:bg-[#53e076]/20 group-hover:text-[#53e076] rounded-full transition-all text-[#bccbb9]">
                          <ArrowUpRight size={14} />
                        </a>
                      ) : (
                        <span className="text-[10px] text-[#bccbb9]">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}
