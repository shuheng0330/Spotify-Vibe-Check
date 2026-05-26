import { Bell, Settings, Search } from 'lucide-react';

interface NavbarProps {
  title: string;
  onSearchChange?: (val: string) => void;
  searchValue?: string;
}

export default function Navbar({ title, onSearchChange, searchValue }: NavbarProps) {
  return (
    <header className="sticky top-0 w-full z-45 bg-[#0a0a0af2] backdrop-blur-md border-b border-white/10">
      <div className="flex justify-between items-center h-16 px-6 max-w-[1600px] mx-auto">
        <div className="flex items-center gap-4">
          <span className="text-lg md:text-xl font-bold text-white tracking-tight">{title}</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative hidden sm:block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#bccbb9] w-4 h-4" />
            <input
              type="text"
              placeholder="Search playlists, tracks, vibrations..."
              value={searchValue || ''}
              onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
              className="bg-[#201f1f] border-none text-white text-xs rounded-full pl-9 pr-4 py-2 focus:ring-2 focus:ring-[#53e076]/50 w-64 transition-all placeholder:text-[#bccbb9]/50"
            />
          </div>
          <button className="text-[#bccbb9] hover:text-[#53e076] transition-colors p-1 rounded-full hover:bg-white/5">
            <Bell size={18} />
          </button>
          <button className="text-[#bccbb9] hover:text-[#53e076] transition-colors p-1 rounded-full hover:bg-white/5">
            <Settings size={18} />
          </button>
          <div className="w-8 h-8 rounded-full bg-[#53e076]/20 border border-[#53e076]/40 flex items-center justify-center overflow-hidden">
            <img
              alt="User Profile"
              className="w-full h-full object-cover"
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=150&h=150"
            />
          </div>
        </div>
      </div>
    </header>
  );
}
