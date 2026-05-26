import { useMemo, useState } from 'react';
import { Zap, Smile, Gauge, SlidersHorizontal } from 'lucide-react';
import { Cluster, ClusterPoint, FeatureDistributionsPayload } from '../types';

interface ExploreClustersTabProps {
  clusters: Cluster[];
  points: ClusterPoint[];
  featureDistributions: FeatureDistributionsPayload | null;
}

const COLORS = ['#53e076', '#FFD700', '#37d7ff', '#E066FF', '#FF7A45'];

function percent(value?: number) {
  return Math.round(Math.max(0, Math.min(1, value || 0)) * 100);
}

export default function ExploreClustersTab({ clusters, points, featureDistributions }: ExploreClustersTabProps) {
  const [minPopularity, setMinPopularity] = useState(0);
  const [maxPopularity, setMaxPopularity] = useState(100);
  const [selectedClusterId, setSelectedClusterId] = useState<number | null>(clusters[0]?.id ?? null);
  const [hoveredDot, setHoveredDot] = useState<ClusterPoint | null>(null);
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);

  const activeCluster = clusters.find((cluster) => cluster.id === selectedClusterId) || clusters[0];
  const visibleFeatures = selectedFeatures.length
    ? selectedFeatures
    : (featureDistributions?.features || []).slice(0, 4);
  const filteredPoints = useMemo(
    () => points.filter((point) => point.popularity >= minPopularity && point.popularity <= maxPopularity),
    [points, minPopularity, maxPopularity]
  );

  const bounds = useMemo(() => {
    const xs = filteredPoints.map((point) => point.x);
    const ys = filteredPoints.map((point) => point.y);
    return {
      minX: Math.min(...xs, 0),
      maxX: Math.max(...xs, 1),
      minY: Math.min(...ys, 0),
      maxY: Math.max(...ys, 1),
    };
  }, [filteredPoints]);

  const plotPosition = (point: ClusterPoint) => {
    const xRange = bounds.maxX - bounds.minX || 1;
    const yRange = bounds.maxY - bounds.minY || 1;
    return {
      left: `${8 + ((point.x - bounds.minX) / xRange) * 84}%`,
      top: `${8 + ((point.y - bounds.minY) / yRange) * 84}%`,
    };
  };

  const toggleFeature = (feature: string) => {
    setSelectedFeatures((prev) => {
      const current = prev.length ? prev : (featureDistributions?.features || []).slice(0, 4);
      if (current.includes(feature)) return current.filter((item) => item !== feature);
      return [...current, feature];
    });
  };

  return (
    <div className="space-y-8" id="explore-clusters-tab">
      <section className="space-y-6">
        <div>
          <h3 className="text-2xl font-black text-white tracking-tight">Explore Clusters</h3>
          <p className="text-sm text-[#bccbb9] mt-0.5">Real t-SNE projection from the trained backend artifacts</p>
        </div>

        <div className="glass-card rounded-2xl p-5 flex flex-wrap gap-6 items-end">
          <div className="flex-1 min-w-[200px] space-y-2">
            <div className="flex justify-between items-center text-[10px] text-[#bccbb9] uppercase font-bold tracking-wider">
              <span>Popularity Range</span>
              <span className="text-[#53e076] font-mono">
                {minPopularity}-{maxPopularity}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input
                aria-label="Minimum popularity"
                type="range"
                min="0"
                max="100"
                value={minPopularity}
                onChange={(e) => setMinPopularity(Math.min(Number(e.target.value), maxPopularity))}
                className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#53e076]"
              />
              <input
                aria-label="Maximum popularity"
                type="range"
                min="0"
                max="100"
                value={maxPopularity}
                onChange={(e) => setMaxPopularity(Math.max(Number(e.target.value), minPopularity))}
                className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#37d7ff]"
              />
            </div>
          </div>

          <div className="w-64 space-y-2">
            <label className="text-[10px] uppercase tracking-wider text-[#bccbb9] font-bold">Cluster Neighborhood</label>
            <select
              value={selectedClusterId ?? ''}
              onChange={(e) => setSelectedClusterId(Number(e.target.value))}
              className="w-full bg-[#2a2a2a] border border-white/10 text-white rounded-lg py-2 px-3 text-xs focus:ring-1 focus:ring-[#53e076] focus:border-[#53e076] outline-none"
            >
              {clusters.map((cluster) => (
                <option value={cluster.id} key={cluster.id}>
                  {cluster.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-10 gap-6 items-start">
        <div className="lg:col-span-7 glass-card rounded-3xl overflow-hidden flex flex-col h-[525px] relative">
          <div className="p-6 border-b border-white/10 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 bg-[#53e076] rounded-full animate-pulse"></span>
              <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono">t-SNE Coordinate Projection Map</h4>
            </div>
            <div className="flex gap-2">
              <span className="px-2 py-1 bg-white/5 rounded text-[9px] font-mono text-[#bccbb9] border border-white/5">
                {filteredPoints.length} plotted points
              </span>
            </div>
          </div>

          <div className="flex-1 relative bg-[#0e0e0e] overflow-hidden select-none">
            <div
              className="absolute inset-0 opacity-[0.03] pointer-events-none"
              style={{
                backgroundImage: 'radial-gradient(circle at 1.5px 1.5px, #FFFFFF 1.5px, transparent 0)',
                backgroundSize: '20px 20px',
              }}
            ></div>

            <div className="absolute inset-0 p-8">
              {filteredPoints.map((point) => {
                const isSelectedCluster = point.cluster_id === activeCluster?.id;
                const color = COLORS[Math.abs(point.cluster_id) % COLORS.length];
                return (
                  <div
                    key={`${point.track_id}-${point.x}-${point.y}`}
                    onMouseEnter={() => setHoveredDot(point)}
                    onMouseLeave={() => setHoveredDot(null)}
                    className="absolute w-2 h-2 rounded-full cursor-pointer hover:scale-200 hover:shadow-[0_0_12px_rgba(255,255,255,0.9)] transition-all duration-300 z-10"
                    style={{
                      ...plotPosition(point),
                      backgroundColor: color,
                      opacity: isSelectedCluster ? 1 : 0.38,
                      boxShadow: `0 0 8px ${color}66`,
                      transform: isSelectedCluster ? 'scale(1.3)' : 'scale(1)',
                    }}
                  />
                );
              })}

              {hoveredDot && (
                <div
                  className="absolute bg-[#1c1b1b] border border-white/10 rounded-lg p-2.5 shadow-xl pointer-events-none z-50 text-xs w-52"
                  style={{
                    ...plotPosition(hoveredDot),
                    transform: 'translate(12px, -50%)',
                  }}
                >
                  <p className="font-bold text-white truncate leading-snug">{hoveredDot.track_name}</p>
                  <p className="text-[10px] text-[#bccbb9] truncate">{hoveredDot.artist_name}</p>
                  <div className="flex items-center gap-1.5 mt-1.5 pt-1.5 border-t border-white/5">
                    <span
                      className="w-1.5 h-1.5 rounded-full"
                      style={{ backgroundColor: COLORS[Math.abs(hoveredDot.cluster_id) % COLORS.length] }}
                    ></span>
                    <span className="text-[9px] uppercase font-mono tracking-widest text-[#bccbb9]">
                      {hoveredDot.cluster_name}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="absolute bottom-4 left-4 flex flex-wrap gap-3 max-w-md bg-black/40 backdrop-blur-sm p-3 rounded-xl border border-white/5 select-none pointer-events-none">
              {clusters.map((cluster) => (
                <div className="flex items-center gap-1.5 text-[9px] text-[#bccbb9] font-mono" key={cluster.id}>
                  <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: COLORS[Math.abs(cluster.id) % COLORS.length] }}></span>
                  {cluster.name}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-3 glass-card rounded-3xl overflow-hidden flex flex-col h-[525px]">
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[Math.abs(activeCluster?.id || 0) % COLORS.length] }}></span>
              <h4 className="text-base font-black text-white">{activeCluster?.name || 'No cluster selected'}</h4>
            </div>
            <p className="text-[#bccbb9] text-[10px] uppercase font-mono">Centroid profile from model metadata</p>
          </div>

          <div className="flex-grow overflow-y-auto p-6 space-y-6 custom-scrollbar">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-white/5 rounded-xl border border-white/5 flex flex-col justify-between">
                <p className="text-[9px] text-[#bccbb9] uppercase font-mono tracking-wider font-bold">Tracks</p>
                <p className="text-lg font-black text-white mt-1">{activeCluster?.track_count.toLocaleString() || '--'}</p>
              </div>
              <div className="p-3 bg-white/5 rounded-xl border border-white/5 flex flex-col justify-between">
                <p className="text-[9px] text-[#bccbb9] uppercase font-mono tracking-wider font-bold">Avg. BPM</p>
                <p className="text-lg font-black text-white mt-1">{Math.round(activeCluster?.centroid.tempo || 0) || '--'}</p>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-[9px] uppercase tracking-wider text-[#bccbb9] font-mono font-bold">Centroid Dimensions</p>
              <div className="space-y-3">
                {[
                  ['Energy', percent(activeCluster?.centroid.energy), '#53e076'],
                  ['Valence', percent(activeCluster?.centroid.valence), '#37d7ff'],
                  ['Dance', percent(activeCluster?.centroid.danceability), '#ffffff'],
                  ['Acoustic', percent(activeCluster?.centroid.acousticness), '#bccbb9'],
                ].map(([label, value, color]) => (
                  <div key={label as string}>
                    <div className="flex justify-between text-[9px] font-mono text-[#bccbb9] mb-1">
                      <span>{label}</span>
                      <span style={{ color: color as string }}>{value}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                      <div className="h-full" style={{ width: `${value}%`, backgroundColor: color as string }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-[9px] uppercase tracking-wider text-[#bccbb9] font-mono font-bold">Top Artists</p>
              <div className="flex flex-wrap gap-2">
                {(activeCluster?.top_artists || []).map((artist) => (
                  <span key={artist} className="px-2 py-1 rounded-md bg-white/5 border border-white/5 text-[10px] text-white">
                    {artist.replace(/^\[/, '').replace(/\]$/, '').replaceAll("'", '')}
                  </span>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-[9px] uppercase tracking-wider text-[#bccbb9] font-mono font-bold">Representative Tracks</p>
              <div className="space-y-2">
                {(activeCluster?.representative_tracks || []).map((track, index) => (
                  <div key={`${track.track_id}-${index}`} className="flex items-center gap-3 p-2 bg-white/5 rounded-lg border border-white/5">
                    <div className="w-8 h-8 rounded bg-white/10 font-bold text-[10px] font-mono flex items-center justify-center text-white">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold text-white truncate">{track.track_name}</p>
                      <p className="text-[10px] text-[#bccbb9] truncate">{track.artist_name}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card rounded-2xl p-5 space-y-4 h-44 flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <p className="text-[10px] uppercase font-mono tracking-widest text-[#bccbb9] font-bold">Energy</p>
            <Zap size={14} className="text-[#53e076]" />
          </div>
          <p className="text-4xl font-black text-white">{percent(activeCluster?.centroid.energy)}%</p>
        </div>
        <div className="glass-card rounded-2xl p-5 space-y-4 h-44 flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <p className="text-[10px] uppercase font-mono tracking-widest text-[#bccbb9] font-bold">Valence</p>
            <Smile size={14} className="text-[#37d7ff]" />
          </div>
          <p className="text-4xl font-black text-white">{percent(activeCluster?.centroid.valence)}%</p>
        </div>
        <div className="glass-card rounded-2xl p-5 space-y-3 h-44 flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <p className="text-[10px] uppercase font-mono tracking-widest text-[#bccbb9] font-bold">Tempo</p>
            <Gauge size={14} className="text-[#bccbb9]" />
          </div>
          <p className="text-4xl font-black text-white">
            {Math.round(activeCluster?.centroid.tempo || 0)}
            <span className="ml-2 text-xs text-[#bccbb9]">BPM</span>
          </p>
        </div>
      </section>

      <section className="glass-panel rounded-2xl p-6 space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h4 className="text-sm font-black text-white uppercase tracking-wider font-mono">Audio Feature Distributions by Cluster</h4>
            <p className="text-xs text-[#bccbb9] mt-1">Boxplot-ready summaries restored from the Streamlit analysis view</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {(featureDistributions?.features || []).map((feature) => {
              const active = visibleFeatures.includes(feature);
              return (
                <button
                  key={feature}
                  onClick={() => toggleFeature(feature)}
                  className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider border transition-all ${
                    active
                      ? 'bg-[#53e076] text-black border-[#53e076]'
                      : 'bg-white/5 text-[#bccbb9] border-white/10 hover:text-white'
                  }`}
                >
                  {feature}
                </button>
              );
            })}
          </div>
        </div>

        {visibleFeatures.length === 0 ? (
          <div className="rounded-xl border border-white/10 bg-white/5 p-6 text-sm text-[#bccbb9] flex items-center gap-3">
            <SlidersHorizontal size={16} />
            Select at least one feature to display distribution summaries.
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {visibleFeatures.map((feature) => {
              const rows = featureDistributions?.distributions[feature] || [];
              const minValue = Math.min(...rows.map((row) => row.min), 0);
              const maxValue = Math.max(...rows.map((row) => row.max), 1);
              const spread = maxValue - minValue || 1;
              return (
                <div key={feature} className="rounded-xl border border-white/10 bg-white/[0.04] p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h5 className="text-xs font-bold text-white uppercase tracking-wider">{feature}</h5>
                    <span className="text-[9px] text-[#bccbb9] font-mono">
                      {minValue.toFixed(feature === 'tempo' ? 0 : 2)} - {maxValue.toFixed(feature === 'tempo' ? 0 : 2)}
                    </span>
                  </div>
                  <div className="space-y-4">
                    {rows.map((row) => {
                      const color = COLORS[Math.abs(row.cluster_id) % COLORS.length];
                      const q1Left = ((row.q1 - minValue) / spread) * 100;
                      const q3Width = Math.max(((row.q3 - row.q1) / spread) * 100, 1);
                      const medianLeft = ((row.median - minValue) / spread) * 100;
                      const whiskerLeft = ((row.min - minValue) / spread) * 100;
                      const whiskerWidth = Math.max(((row.max - row.min) / spread) * 100, 1);
                      return (
                        <div key={`${feature}-${row.cluster_id}`} className="grid grid-cols-[120px_1fr_54px] items-center gap-3">
                          <div className="min-w-0">
                            <p className="text-[10px] font-bold text-white truncate">{row.cluster_name}</p>
                            <p className="text-[9px] text-[#bccbb9] font-mono">{row.count.toLocaleString()} tracks</p>
                          </div>
                          <div className="relative h-8">
                            <div className="absolute left-0 right-0 top-1/2 h-px bg-white/10"></div>
                            <div
                              className="absolute top-1/2 h-px -translate-y-1/2"
                              style={{ left: `${whiskerLeft}%`, width: `${whiskerWidth}%`, backgroundColor: `${color}99` }}
                            ></div>
                            <div
                              className="absolute top-1/2 h-5 -translate-y-1/2 rounded border"
                              style={{
                                left: `${q1Left}%`,
                                width: `${q3Width}%`,
                                backgroundColor: `${color}33`,
                                borderColor: `${color}aa`,
                              }}
                            ></div>
                            <div
                              className="absolute top-1/2 h-7 w-0.5 -translate-y-1/2 rounded-full"
                              style={{ left: `${medianLeft}%`, backgroundColor: color }}
                            ></div>
                          </div>
                          <p className="text-right text-[10px] text-[#53e076] font-mono">
                            {row.median.toFixed(feature === 'tempo' ? 0 : 2)}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
