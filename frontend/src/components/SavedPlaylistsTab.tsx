import { useMemo, useState } from 'react';
import { Trash2, FolderPlus, SlidersHorizontal, ChevronDown, ChevronUp, Play, RotateCcw } from 'lucide-react';
import { Playlist } from '../types';
import {
  DEFAULT_SAVED_PLAYLIST_FILTERS,
  filterSavedPlaylists,
  SavedPlaylistFilters,
} from '../savedPlaylistUtils';

interface SavedPlaylistsTabProps {
  playlists: Playlist[];
  onDeletePlaylist: (id: string) => void;
  onOpenPlaylist: (id: string) => void;
  onAddNewPlaylist: () => void;
}

export default function SavedPlaylistsTab({
  playlists,
  onDeletePlaylist,
  onOpenPlaylist,
  onAddNewPlaylist,
}: SavedPlaylistsTabProps) {
  const [expandedPlaylistId, setExpandedPlaylistId] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SavedPlaylistFilters>(DEFAULT_SAVED_PLAYLIST_FILTERS);

  const categories = useMemo(() => Array.from(new Set(playlists.map((playlist) => playlist.tag))).sort(), [playlists]);
  const visiblePlaylists = useMemo(() => filterSavedPlaylists(playlists, filters), [playlists, filters]);
  const activeFilterCount = [
    filters.category !== 'all',
    filters.featurePreset !== 'all',
    filters.sortBy !== 'newest',
  ].filter(Boolean).length;

  const toggleExpand = (id: string) => {
    setExpandedPlaylistId((prev) => (prev === id ? null : id));
  };

  const exportPlaylist = (playlist: Playlist) => {
    const element = document.createElement('a');
    const file = new Blob([JSON.stringify(playlist, null, 2)], { type: 'application/json' });
    element.href = URL.createObjectURL(file);
    element.download = `${playlist.name.toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'playlist'}.json`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="space-y-8" id="saved-playlists-tab">
      {/* Header bar and button filters */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tight">Saved Playlists</h2>
          <p className="text-sm text-[#bccbb9] mt-0.5">
            {playlists.length} playlists saved from backend file storage
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowFilters((prev) => !prev)}
            className={`border px-4 py-2 rounded-lg font-bold text-xs flex items-center gap-1.5 active:scale-95 transition-all ${
              showFilters || activeFilterCount > 0
                ? 'bg-[#53e076]/15 border-[#53e076]/40 text-[#53e076]'
                : 'bg-[#201f1f] border-white/10 text-white hover:bg-white/5'
            }`}
          >
            <SlidersHorizontal size={14} className="text-[#bccbb9]" />
            Filters
            {activeFilterCount > 0 && (
              <span className="ml-1 rounded-full bg-[#53e076] text-black px-1.5 py-0.5 text-[9px] font-black">
                {activeFilterCount}
              </span>
            )}
          </button>
          <button
            onClick={onAddNewPlaylist}
            className="bg-[#53e076] text-black px-4 py-2 rounded-lg font-black text-xs flex items-center gap-1.5 hover:brightness-110 active:scale-95 transition-all shadow-lg shadow-[#53e076]/10"
          >
            <FolderPlus size={14} />
            Create in Vibe Check
          </button>
        </div>
      </div>

      {showFilters && (
        <section className="glass-panel rounded-xl p-4 sm:p-5 space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-end gap-4">
            <div className="flex-1 min-w-[180px] space-y-2">
              <label className="text-[9px] text-[#bccbb9] uppercase tracking-widest font-mono font-bold">Category</label>
              <select
                value={filters.category}
                onChange={(e) => setFilters((prev) => ({ ...prev, category: e.target.value }))}
                className="w-full bg-[#201f1f] border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-[#53e076]"
              >
                <option value="all">All categories</option>
                {categories.map((category) => (
                  <option value={category} key={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1 min-w-[180px] space-y-2">
              <label className="text-[9px] text-[#bccbb9] uppercase tracking-widest font-mono font-bold">Feature focus</label>
              <select
                value={filters.featurePreset}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, featurePreset: e.target.value as SavedPlaylistFilters['featurePreset'] }))
                }
                className="w-full bg-[#201f1f] border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-[#53e076]"
              >
                <option value="all">Any profile</option>
                <option value="high_energy">High energy</option>
                <option value="positive">Positive valence</option>
                <option value="danceable">Danceable</option>
                <option value="acoustic">Acoustic leaning</option>
              </select>
            </div>

            <div className="flex-1 min-w-[180px] space-y-2">
              <label className="text-[9px] text-[#bccbb9] uppercase tracking-widest font-mono font-bold">Sort</label>
              <select
                value={filters.sortBy}
                onChange={(e) => setFilters((prev) => ({ ...prev, sortBy: e.target.value as SavedPlaylistFilters['sortBy'] }))}
                className="w-full bg-[#201f1f] border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-[#53e076]"
              >
                <option value="newest">Newest saved</option>
                <option value="oldest">Oldest saved</option>
                <option value="name">Name A-Z</option>
                <option value="energy">Highest energy</option>
                <option value="valence">Highest valence</option>
                <option value="danceability">Most danceable</option>
              </select>
            </div>

            <button
              onClick={() => setFilters(DEFAULT_SAVED_PLAYLIST_FILTERS)}
              className="h-9 px-4 rounded-lg border border-white/10 text-white text-xs font-bold hover:bg-white/5 active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              <RotateCcw size={13} />
              Reset
            </button>
          </div>
          <p className="text-[10px] text-[#bccbb9] font-mono">
            Showing <span className="text-white font-bold">{visiblePlaylists.length}</span> of{' '}
            <span className="text-white font-bold">{playlists.length}</span> saved playlists.
          </p>
        </section>
      )}

      {/* Bento Grid */}
      {playlists.length === 0 ? (
        <div className="glass-panel rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-4">
          <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center text-[#bccbb9]">
            <FolderPlus size={24} />
          </div>
          <div>
            <h4 className="text-white font-bold text-sm">No saved playlists</h4>
            <p className="text-xs text-[#bccbb9] mt-1">Calibrate audio features and save them to begin tracking music zones.</p>
          </div>
        </div>
      ) : visiblePlaylists.length === 0 ? (
        <div className="glass-panel rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-4">
          <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center text-[#bccbb9]">
            <SlidersHorizontal size={24} />
          </div>
          <div>
            <h4 className="text-white font-bold text-sm">No playlists match these filters</h4>
            <p className="text-xs text-[#bccbb9] mt-1">Relax one of the filters or reset to view the full library.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-6">
          {visiblePlaylists.map((playlist) => {
            const isExpanded = expandedPlaylistId === playlist.id;
            
            // Adjust dynamic color classes
            let tagColorClass = 'bg-[#53e076]/20 text-[#53e076]';
            if (playlist.tagColor === 'tertiary') tagColorClass = 'bg-[#37d7ff]/20 text-[#37d7ff]';
            if (playlist.tagColor === 'secondary') tagColorClass = 'bg-white/10 text-white';

            return (
              <div key={playlist.id} className="glass-card rounded-xl overflow-hidden flex flex-col justify-between">
                <div className="p-4 flex gap-4">
                  {/* Thumbnail cover trigger */}
                  <div
                    onClick={() => onOpenPlaylist(playlist.id)}
                    className="w-28 h-28 flex-shrink-0 cursor-pointer rounded-lg overflow-hidden border border-white/10 group relative select-none"
                  >
                    <img
                      alt={playlist.name}
                      src={playlist.imageUrl}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute inset-0 bg-black/45 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <Play size={28} className="text-white fill-white" />
                    </div>
                  </div>

                  {/* Vibe calibration stats */}
                  <div className="flex-1 flex flex-col justify-between min-w-0">
                    <div>
                      <div className="flex justify-between items-start gap-1">
                        <h3 className="text-sm font-bold text-white truncate leading-snug">{playlist.name}</h3>
                        <button
                          onClick={() => onDeletePlaylist(playlist.id)}
                          className="text-[#bccbb9] hover:text-[#ffb4ab] transition-colors p-1 rounded hover:bg-white/5 flex-shrink-0"
                          title="Delete saved playlist"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                      <span className={`inline-block px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider mt-1.5 ${tagColorClass}`}>
                        {playlist.tag}
                      </span>
                      <p className="text-[#bccbb9] text-[10px] uppercase font-mono tracking-widest mt-2">{playlist.savedDate} • {playlist.trackCount} Tracks</p>
                    </div>

                    {/* Progress sliders matching average vectors */}
                    <div className="space-y-1.5 mt-3 select-none">
                      <div className="flex items-center gap-2">
                        <span className="text-[8px] text-[#bccbb9] uppercase font-bold w-12 font-mono">Energy</span>
                        <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div className={`h-full ${playlist.tagColor === 'tertiary' ? 'bg-[#37d7ff]' : playlist.tagColor === 'secondary' ? 'bg-white' : 'bg-[#53e076]'}`} style={{ width: `${playlist.energy}%` }}></div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[8px] text-[#bccbb9] uppercase font-bold w-12 font-mono">Valence</span>
                        <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div className={`h-full ${playlist.tagColor === 'tertiary' ? 'bg-[#37d7ff]' : playlist.tagColor === 'secondary' ? 'bg-white' : 'bg-[#53e076]'}`} style={{ width: `${playlist.valence}%` }}></div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[8px] text-[#bccbb9] uppercase font-bold w-12 font-mono">Dance</span>
                        <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div className={`h-full ${playlist.tagColor === 'tertiary' ? 'bg-[#37d7ff]' : playlist.tagColor === 'secondary' ? 'bg-white' : 'bg-[#53e076]'}`} style={{ width: `${playlist.danceability}%` }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="px-4 pb-4 flex gap-2">
                  <button
                    onClick={() => onOpenPlaylist(playlist.id)}
                    className="flex-1 bg-white text-black font-bold py-2 rounded-lg text-xs hover:bg-white/90 active:scale-95 transition-all outline-none"
                  >
                    Open Details
                  </button>
                  <button
                    onClick={() => exportPlaylist(playlist)}
                    className="flex-1 border border-white/20 text-white font-semibold py-2 rounded-lg text-xs hover:bg-white/5 active:scale-95 transition-all outline-none"
                  >
                    Export JSON
                  </button>
                </div>

                {/* Collapsible track drawer details */}
                <details className="group border-t border-white/5" open={isExpanded}>
                  <summary
                    onClick={(e) => {
                      e.preventDefault();
                      toggleExpand(playlist.id);
                    }}
                    className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-white/5 transition-colors list-none select-none"
                  >
                    <span className="text-[9px] text-[#bccbb9] font-bold uppercase tracking-widest font-mono">Representative Tracks</span>
                    {isExpanded ? <ChevronUp size={14} className="text-[#bccbb9]" /> : <ChevronDown size={14} className="text-[#bccbb9]" />}
                  </summary>

                  <div className="px-4 pb-4 space-y-3 font-sans text-xs">
                    {playlist.tracks.slice(0, 3).map((track, i) => (
                      <div key={track.id} className="flex items-center justify-between group/item">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded bg-white/5 border border-white/10 flex items-center justify-center font-mono font-bold text-[#bccbb9] text-[10px]">
                            {i + 1}
                          </div>
                          <div>
                            <p className="text-xs font-bold text-white leading-tight">{track.title}</p>
                            <p className="text-[10px] text-[#bccbb9] mt-0.5 leading-none">{track.artist}</p>
                          </div>
                        </div>

                        {/* Animated Equalizer bar visuals */}
                        <div className="flex items-center gap-3 select-none">
                          <div className="w-10 h-3 bg-white/5 rounded flex items-end justify-center gap-[1px] p-[1.5px]">
                            <span className="w-1 bg-[#53e076] h-[30%] rounded-t"></span>
                            <span className="w-1 bg-[#53e076] h-[75%] rounded-t animate-[pulse_1s_infinite]"></span>
                            <span className="w-1 bg-[#53e076] h-[100%] rounded-t"></span>
                            <span className="w-1 bg-[#53e076] h-[55%] rounded-t animate-[pulse_1.5s_infinite]"></span>
                            <span className="w-1 bg-[#53e076] h-[40%] rounded-t"></span>
                          </div>
                          <span className="text-[9px] text-[#bccbb9] font-mono">{track.duration}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </details>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
