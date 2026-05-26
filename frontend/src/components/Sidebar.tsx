import { LineChart, Network, BookOpen, Music, Activity } from 'lucide-react';
import { HealthStatus } from '../types';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  modelStatus: string;
  health: HealthStatus | null;
}

export default function Sidebar({ activeTab, setActiveTab, modelStatus, health }: SidebarProps) {
  const navItems = [
    { id: 'vibe_check', label: 'Vibe Check', icon: LineChart },
    { id: 'explore', label: 'Explore Clusters', icon: Network },
    { id: 'academic', label: 'Academic Analysis', icon: BookOpen },
    { id: 'saved_playlists', label: 'Saved Playlists', icon: Music },
  ];

  return (
    <aside className="fixed left-0 top-0 h-full w-[260px] hidden md:flex flex-col bg-[#131313] border-r border-white/10 z-50">
      <div className="flex flex-col h-full py-8">
        <div className="px-6 mb-10">
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded bg-[#1db954] flex items-center justify-center font-bold text-black text-sm">VC</span>
            <h1 className="font-sans text-xl font-black text-[#53e076] tracking-tight">Vibe Check</h1>
          </div>
          <p className="text-[10px] text-[#bccbb9] uppercase tracking-wider font-semibold mt-1">AI Music Analytics</p>
        </div>

        <nav className="flex-1 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id || (item.id === 'saved_playlists' && activeTab === 'playlist_detail');
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 py-3 px-6 transition-all border-l-4 text-left ${
                  isActive
                    ? 'border-[#53e076] bg-white/5 text-white font-semibold'
                    : 'border-transparent text-[#bccbb9] hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-[#53e076]' : ''} />
                <span className="text-sm font-sans">{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="px-6 mt-auto">
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="flex items-center gap-2 mb-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#53e076] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#53e076]"></span>
              </span>
              <span className="text-[10px] uppercase tracking-wider font-bold text-[#53e076]">Model Status: {modelStatus}</span>
            </div>
            <p className="text-xs text-[#bccbb9] leading-relaxed">
              {health?.models_loaded
                ? `${health.track_count.toLocaleString()} tracks, ${health.cluster_count} clusters, ${health.selected_algorithm} selected.`
                : 'Start the FastAPI backend to load model diagnostics.'}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
