interface NavbarProps {
  title: string;
}

export default function Navbar({ title }: NavbarProps) {
  return (
    <header className="sticky top-0 w-full z-45 bg-[#0a0a0af2] backdrop-blur-md border-b border-white/10">
      <div className="flex justify-between items-center h-16 px-6 max-w-[1600px] mx-auto">
        <div className="flex items-center gap-4">
          <span className="text-lg md:text-xl font-bold text-white tracking-tight">{title}</span>
        </div>
      </div>
    </header>
  );
}
