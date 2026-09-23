import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { ArrowLeft, Lock, Shield } from "lucide-react";
import { useModules } from "../../context/ModuleContext";
import { useAdminAuth } from "../../context/AdminAuthContext";

export function AdminShell() {
  const navigate = useNavigate();
  const { adminNav } = useModules();
  const { exitAdmin } = useAdminAuth();

  return (
    <div className="min-h-dvh bg-[#050505] text-white pt-[max(2rem,env(safe-area-inset-top))] md:pt-12 px-4 md:px-6 pb-[max(4rem,env(safe-area-inset-bottom))]">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <button
            type="button"
            onClick={() => navigate("/coach/dashboard")}
            className="flex items-center gap-2 text-zinc-500 hover:text-white min-h-11"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to coach app
          </button>
          <button
            type="button"
            onClick={async () => {
              await exitAdmin({ signOutFirebase: false });
              navigate("/admin/login", { replace: true });
            }}
            className="flex items-center gap-2 text-zinc-500 hover:text-red-400 min-h-11 text-sm"
          >
            <Lock className="w-4 h-4" />
            Lock admin
          </button>
        </div>

        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-8">
          <div>
            <p className="text-[10px] uppercase tracking-[0.25em] text-lime-400/80 flex items-center gap-2">
              <Shield className="w-3.5 h-3.5" />
              Admin gate unlocked
            </p>
            <h1 className="text-3xl md:text-4xl font-bold mt-1">Control center</h1>
            <p className="text-zinc-400 mt-2 max-w-xl text-sm">
              Platform overview and plug-and-play modules. This session is separate from coach login.
            </p>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          <aside className="lg:w-56 shrink-0">
            <nav className="flex lg:flex-col gap-2 overflow-x-auto snap-strip no-scrollbar -mx-4 px-4 lg:mx-0 lg:px-0 pb-2 lg:pb-0">
              {adminNav.map((mod) => {
                const Icon = mod.icon;
                return (
                  <NavLink
                    key={mod.id}
                    to={mod.path}
                    end={mod.path === "/admin"}
                    className={({ isActive }) =>
                      `flex items-center gap-2.5 min-h-11 px-4 py-3 rounded-xl text-sm font-medium whitespace-nowrap border transition-colors shrink-0 ${
                        isActive
                          ? "bg-lime-400/15 border-lime-400/40 text-lime-300"
                          : "bg-white/3 border-white/5 text-zinc-400 hover:text-white hover:border-white/15"
                      }`
                    }
                  >
                    {Icon && <Icon className="w-4 h-4 shrink-0" />}
                    {mod.name}
                  </NavLink>
                );
              })}
            </nav>
          </aside>

          <main className="flex-1 min-w-0">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
