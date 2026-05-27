import { useState } from 'react';
import { Sparkles, Paintbrush, Activity, ArrowLeft, ArrowUpRight } from 'lucide-react';
import { Playlist } from '../types';

interface PlaylistDetailTabProps {
  playlist: Playlist;
  onBack: () => void;
  onEditVibe?: () => void;
}

function clampUnit(value?: number) {
  return Math.max(0, Math.min(1, value || 0));
}

export default function PlaylistDetailTab({ playlist, onBack }: PlaylistDetailTabProps) {
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const featureScores = [
    { label: 'Energy', axisLabel: 'ENERGY', value: clampUnit(playlist.energy / 100), color: '#53e076' },
    { label: 'Valence', axisLabel: 'VALENCE', value: clampUnit(playlist.valence / 100), color: '#37d7ff' },
    { label: 'Danceability', axisLabel: 'DANCEABILITY', value: clampUnit(playlist.danceability / 100), color: '#53e076' },
    { label: 'Acousticness', axisLabel: 'ACOUSTIC', value: clampUnit(playlist.acousticness / 100), color: '#ffffff' },
    { label: 'Instrumentalness', axisLabel: 'INSTRUMENTAL', value: clampUnit(playlist.centroid?.instrumentalness), color: '#bccbb9' },
    { label: 'Speechiness', axisLabel: 'SPEECH', value: clampUnit(playlist.centroid?.speechiness), color: '#bccbb9' },
  ];
  const CX = 70, CY = 70, R = 52;
  const radarAxes = [
    ...featureScores,
  ];
  const axisPt = (i: number, r: number) => {
    const a = (i * Math.PI * 2) / 6;
    return { x: CX + r * Math.cos(a), y: CY - r * Math.sin(a) };
  };
  const hexRing = (r: number) =>
    [0, 1, 2, 3, 4, 5].map((i) => {
      const p = axisPt(i, r);
      return `${p.x},${p.y}`;
    }).join(' ');
  const radarPoints = radarAxes
    .map((axis, index) => {
      const p = axisPt(index, R * axis.value);
      return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
    })
    .join(' ');
  const labelAnchors = ['start', 'start', 'end', 'end', 'end', 'start'] as const;
  const labelBaselines = ['middle', 'auto', 'auto', 'middle', 'hanging', 'hanging'] as const;

  const handleCopyPrompt = () => {
    if (playlist.prompt) {
      navigator.clipboard.writeText(playlist.prompt);
      setCopiedPrompt(true);
      setTimeout(() => setCopiedPrompt(false), 2000);
    }
  };

  return (
    <div className="space-y-8" id="playlist-detail-tab">
      {/* Back navigation */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#bccbb9] hover:text-white transition-colors bg-white/5 px-3 py-1.5 rounded-lg border border-white/5 active:scale-95 duration-200"
      >
        <ArrowLeft size={14} className="text-[#53e076]" />
        Back to Saved Library
      </button>

      {/* Hero Header Banner */}
      <section>
        <div className="flex flex-col md:flex-row items-end gap-6 bg-gradient-to-t from-[#1c1b1b] to-transparent p-6 sm:p-8 rounded-3xl border border-white/5 relative overflow-hidden select-none">
          {/* background glow ambient tint */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-[#53e076]/5 rounded-full blur-[100px] pointer-events-none"></div>

          <div className="w-full md:w-56 aspect-square shadow-2xl overflow-hidden rounded-2xl flex-shrink-0 group relative">
            <img
              alt={playlist.name}
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              src={playlist.imageUrl}
            />
            <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors"></div>
          </div>

          <div className="flex-1 space-y-3 z-10 w-full">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 bg-[#53e076]/20 text-[#53e076] text-[9px] font-bold uppercase tracking-widest rounded-full border border-[#53e076]/30 animate-pulse">
                Active Cluster
              </span>
              <span className="text-[#bccbb9] text-[10px] uppercase font-mono tracking-widest leading-none">
                {playlist.cluster?.match_score ? `- Match Score: ${Math.round(playlist.cluster.match_score * 100)}%` : '- Saved from backend'}
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-black text-white leading-none tracking-tight">
              {playlist.name}
            </h1>

            <div className="flex items-center gap-3 text-xs text-[#bccbb9] pt-1">
              <span className="font-mono">Generated: <strong className="text-white font-semibold">{playlist.savedDate}</strong></span>
              <span>•</span>
              <span className="font-sans font-medium">{playlist.tracks.length} tracks</span>
            </div>

            <p className="text-xs text-[#bccbb9] leading-relaxed max-w-2xl pt-3">
              Saved playlist detail view with calibrated track features and cluster-level profile.
            </p>
          </div>
        </div>
      </section>

      {/* Main Breakdown Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left column: Full tabular Track List */}
        <div className="lg:col-span-8">
          <div className="glass-panel overflow-hidden rounded-xl">
            <div className="p-5 border-b border-white/10 flex justify-between items-center sm:px-6">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">Calibrated Track Breakdown</h3>
                <p className="text-[10px] text-[#bccbb9] font-mono mt-0.5">ACOUSTIC CLASSIFICATION VECTOR SCORE RATIOS [0.0 - 1.0]</p>
              </div>
            </div>

            <div className="overflow-x-auto custom-scrollbar">
              <table className="w-full text-left font-sans text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-[#bccbb9] font-mono tracking-wider text-[9px] uppercase">
                    <th className="px-5 py-3.5 w-8">#</th>
                    <th className="px-3 py-3.5">TITLE</th>
                    <th className="px-3 py-3.5">POPULARITY</th>
                    <th className="px-3 py-3.5 text-center font-bold text-[#53e076]">ENERGY</th>
                    <th className="px-3 py-3.5 text-center font-bold text-[#37d7ff]">VALENCE</th>
                    <th className="px-3 py-3.5 text-center font-bold text-white">DANCE</th>
                    <th className="px-3 py-3.5 text-right">SPOTIFY</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-[#e5e2e1]">
                  {playlist.tracks.map((track, i) => (
                    <tr key={track.id} className="hover:bg-white/5 group transition-colors">
                      <td className="px-5 py-3 text-xs font-mono text-[#bccbb9]">{i + 1}</td>
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded overflow-hidden flex-shrink-0 bg-white/5 border border-white/10 relative">
                            <img
                              alt={track.title}
                              className="w-full h-full object-cover rounded shadow"
                              src={track.albumArt}
                            />
                          </div>
                          <div className="min-w-0">
                            <p className="font-bold text-white text-xs leading-none truncate">{track.title}</p>
                            <p className="text-[10px] text-[#bccbb9] mt-1 truncate leading-none">{track.artist}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-3 min-w-[90px]">
                        <div className="h-1 w-20 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-[#53e076]" style={{ width: `${track.popularity}%` }}></div>
                        </div>
                      </td>
                      <td className="px-3 py-3 text-center font-mono font-semibold text-[#53e076]">{track.energy.toFixed(2)}</td>
                      <td className="px-3 py-3 text-center font-mono font-semibold text-[#37d7ff]">{track.valence.toFixed(2)}</td>
                      <td className="px-3 py-3 text-center font-mono font-semibold text-white">{track.danceability.toFixed(2)}</td>
                      <td className="px-3 py-3 text-right">
                        <a
                          href={track.spotifyUrl || `https://open.spotify.com/search/${encodeURIComponent(`${track.title} ${track.artist}`)}`}
                          target="_blank"
                          rel="noreferrer"
                          className="p-1.5 inline-flex bg-white/5 group-hover:bg-[#53e076]/20 group-hover:text-[#53e076] rounded-full transition-all text-[#bccbb9]"
                        >
                          <ArrowUpRight size={14} />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right column: Audio Profile charts and prompt parameters */}
        <div className="lg:col-span-4 space-y-6 select-none">
          {/* Audio vector polygon layout */}
          <div className="glass-panel p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-xs font-bold uppercase text-white font-mono tracking-widest">Audio Profile Cluster</h3>
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-[#bccbb9] font-mono">
                  Tempo: <strong className="text-[#53e076]">{playlist.bpm || '--'} BPM</strong>
                </span>
                <Activity size={16} className="text-[#53e076]" />
              </div>
            </div>

            <div className="flex justify-center select-none mb-6">
              <svg viewBox="-28 -18 196 176" className="w-full max-w-[360px] h-[320px]">
                {[R * 0.33, R * 0.66, R].map((r, ringIndex) => (
                  <polygon key={ringIndex} points={hexRing(r)} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="0.5" />
                ))}
                {radarAxes.map((_, index) => {
                  const p = axisPt(index, R);
                  return <line key={index} x1={CX} y1={CY} x2={p.x} y2={p.y} stroke="rgba(255,255,255,0.08)" strokeWidth="0.5" />;
                })}
                <polygon
                  fill="rgba(83,224,118,0.18)"
                  points={radarPoints}
                  stroke="#53e076"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
                {radarAxes.map((axis, index) => {
                  const p = axisPt(index, R * axis.value);
                  return <circle key={`${axis.label}-dot`} cx={p.x} cy={p.y} fill="#53e076" r="2.4" />;
                })}
                <circle cx={CX} cy={CY} r="1.5" fill="rgba(255,255,255,0.4)" />
                {radarAxes.map((axis, index) => {
                  const p = axisPt(index, R + 15);
                  return (
                    <text
                      key={`${axis.label}-label`}
                      x={p.x}
                      y={p.y}
                      fontSize="6.5"
                      fontFamily="monospace"
                      fontWeight="700"
                      fill="#bccbb9"
                      textAnchor={labelAnchors[index]}
                      dominantBaseline={labelBaselines[index]}
                      letterSpacing="0.5"
                    >
                      {axis.axisLabel}
                    </text>
                  );
                })}
              </svg>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-5 gap-y-3 text-xs font-sans">
              {featureScores.map((feature) => (
                <div key={feature.label} className="space-y-1">
                  <div className="flex items-center justify-between gap-2 font-mono text-xs">
                    <span className="text-[#bccbb9]">{feature.label}</span>
                    <span className="font-bold" style={{ color: feature.color }}>
                      {Math.round(feature.value * 100)}%
                    </span>
                  </div>
                  <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${feature.value * 100}%`, backgroundColor: feature.color }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cluster description summary details */}
          <div className="glass-panel p-5 border-l-4 border-l-[#53e076]">
            <div className="flex items-center gap-1.5 mb-2.5">
              <Sparkles size={14} className="text-[#53e076]" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Cluster Definition</h4>
            </div>
            <p className="text-xs text-[#bccbb9] leading-relaxed">
              {playlist.description}
            </p>
          </div>

          {/* Album visual prompt box */}
          {playlist.prompt && (
            <div className="glass-panel p-5 space-y-3">
              <div className="flex items-center gap-1.5">
                <Paintbrush size={14} className="text-[#bccbb9]" />
                <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Visual Cover Prompt</h4>
              </div>
              <div
                onClick={handleCopyPrompt}
                className="bg-black/40 rounded-xl p-3 font-mono text-[9px] leading-relaxed text-[#53e076]/80 cursor-pointer border border-white/5 hover:bg-black/60 active:scale-98 transition-all relative group"
                title="Click to copy Prompt text to clipboard"
              >
                "{playlist.prompt}"
                <span className="absolute bottom-1 right-2 text-[8px] uppercase font-bold text-[#bccbb9]/40 opacity-0 group-hover:opacity-100 transition-opacity">
                  Copy Prompt
                </span>
              </div>
              <p className="text-[8px] text-[#bccbb9] font-mono italic text-right">
                {copiedPrompt ? 'Prompt copied successfully!' : 'Click code block above to copy parameters.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
