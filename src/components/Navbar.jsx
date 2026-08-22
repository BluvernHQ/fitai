import { useAuth } from "../context/authContext";
import { Link, NavLink, useLocation } from "react-router-dom";
import { LogOut, Sparkles, Users } from "lucide-react";

const HIDE_TABS = /\/coach\/student\/[^/]+\/(fms|scores|program|workout)/;

export const Navbar = () => {
  const { logout } = useAuth();
  const { pathname } = useLocation();
  const showTabs = !HIDE_TABS.test(pathname);

  return (
    <>
      <header className="app-header fixed top-0 left-0 right-0 z-50 px-4 md:px-6 flex items-center justify-between bg-[#050505]/92 backdrop-blur-md border-b border-white/5">
        <Link
          to="/coach/dashboard"
          className="text-lg md:text-xl font-bold tracking-tighter brand-font"
        >
          FIT.AI <span className="text-lime-400">PRO</span>
        </Link>
        <div className="hidden md:flex items-center gap-6 text-xs font-bold tracking-widest uppercase text-zinc-400">
          <Link to="/coach/insights" className="hover:text-white">
            Insights
          </Link>
          <button
            onClick={logout}
            className="hover:text-red-500 transition-colors uppercase cursor-pointer"
          >
            Disconnect
          </button>
          <span className="w-2 h-2 rounded-full bg-lime-500 animate-pulse" />
        </div>
      </header>

      {showTabs && (
        <nav className="app-tabbar md:hidden fixed bottom-0 inset-x-0 z-50 bg-[#0a0a0a]/95 backdrop-blur-md border-t border-white/10">
          <div className="grid grid-cols-3 h-14">
            <NavLink
              to="/coach/dashboard"
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 text-[10px] font-bold uppercase tracking-widest ${
                  isActive || pathname.startsWith("/coach/student")
                    ? "text-lime-400"
                    : "text-zinc-500"
                }`
              }
            >
              <Users className="w-5 h-5" />
              Roster
            </NavLink>
            <NavLink
              to="/coach/insights"
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 text-[10px] font-bold uppercase tracking-widest ${
                  isActive ? "text-lime-400" : "text-zinc-500"
                }`
              }
            >
              <Sparkles className="w-5 h-5" />
              Insights
            </NavLink>
            <button
              onClick={logout}
              className="flex flex-col items-center justify-center gap-0.5 text-[10px] font-bold uppercase tracking-widest text-zinc-500"
            >
              <LogOut className="w-5 h-5" />
              Sign out
            </button>
          </div>
        </nav>
      )}
    </>
  );
};
