import { useAuth } from "../context/authContext";
import { useModules } from "../context/ModuleContext";
import { Link, NavLink, useLocation } from "react-router-dom";
import { LogOut, Users } from "lucide-react";
import { BrandMark } from "./ui";

const HIDE_TABS = /\/coach\/student\/[^/]+\/(assess|fms|scores|program|workout)/;

export const Navbar = () => {
  const { logout } = useAuth();
  const { coachNav, loading } = useModules();
  const { pathname } = useLocation();
  const showTabs = !HIDE_TABS.test(pathname) && !pathname.startsWith("/admin");

  const desktopLinks = coachNav.filter((m) => m.path);
  const mobileModules = coachNav.filter((m) => m.path).slice(0, 2);
  const mobileCols = 2 + mobileModules.length;

  return (
    <>
      <header className="app-header nav-glass fixed top-0 left-0 right-0 z-50 px-4 md:px-6 flex items-center justify-between">
        <Link to="/coach/dashboard" className="shrink-0 focus-visible:outline-offset-4">
          <BrandMark size="md" />
        </Link>
        <div className="hidden md:flex items-center gap-1 text-[11px] font-bold tracking-[0.16em] uppercase text-zinc-400">
          {!loading &&
            desktopLinks.map((mod) => (
              <Link
                key={mod.id}
                to={mod.path}
                className={`px-3 py-2 rounded-lg transition-colors hover:text-white hover:bg-white/5 ${
                  pathname.startsWith(mod.path) ? "text-lime-400 bg-lime-400/10" : ""
                }`}
              >
                {mod.name}
              </Link>
            ))}
          <button
            type="button"
            onClick={logout}
            className="ml-1 px-3 py-2 rounded-lg hover:text-red-400 hover:bg-red-500/10 transition-colors uppercase cursor-pointer"
          >
            Disconnect
          </button>
          <span
            className="ml-2 w-2 h-2 rounded-full bg-lime-400 shadow-[0_0_12px_rgba(163,230,53,0.8)]"
            aria-hidden
          />
        </div>
      </header>

      {showTabs && (
        <nav className="app-tabbar md:hidden fixed bottom-0 inset-x-0 z-50 tab-glass">
          <div
            className="grid min-h-14"
            style={{ gridTemplateColumns: `repeat(${mobileCols}, minmax(0, 1fr))` }}
          >
            <NavLink
              to="/coach/dashboard"
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 min-h-14 text-[10px] font-bold uppercase tracking-widest transition-colors ${
                  isActive || pathname.startsWith("/coach/student")
                    ? "text-lime-400"
                    : "text-zinc-500"
                }`
              }
            >
              <Users className="w-5 h-5" />
              Roster
            </NavLink>
            {!loading &&
              mobileModules.map((mod) => {
                const Icon = mod.icon;
                return (
                  <NavLink
                    key={mod.id}
                    to={mod.path}
                    className={({ isActive }) =>
                      `flex flex-col items-center justify-center gap-0.5 min-h-14 text-[10px] font-bold uppercase tracking-widest transition-colors ${
                        isActive ? "text-lime-400" : "text-zinc-500"
                      }`
                    }
                  >
                    {Icon && <Icon className="w-5 h-5" />}
                    {mod.name.split(" ")[0]}
                  </NavLink>
                );
              })}
            <button
              type="button"
              onClick={logout}
              className="flex flex-col items-center justify-center gap-0.5 min-h-14 text-[10px] font-bold uppercase tracking-widest text-zinc-500"
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
