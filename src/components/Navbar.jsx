export const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-6 flex justify-between items-center pointer-events-none mix-blend-difference">
      <span className="text-xl font-bold tracking-tighter brand-font pointer-events-auto">
        FIT.AI <span className="text-lime-400">PRO</span>
      </span>
      <div className="hidden md:flex items-center gap-6 text-xs font-bold tracking-widest uppercase text-zinc-400">
        <span>System Online</span>
        <span className="w-2 h-2 rounded-full bg-lime-500 animate-pulse" />
      </div>
    </nav>
  );
};
