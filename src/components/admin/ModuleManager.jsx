import { useState } from "react";
import { patchAdminModule } from "../../api/backend";
import { useModules } from "../../context/ModuleContext";

const CATEGORY_LABEL = {
  coach: "Coach features",
  admin: "Admin panel",
  platform: "Platform / beta",
};

export function ModuleManager() {
  const { modules, refresh } = useModules();
  const [busy, setBusy] = useState(null);
  const [message, setMessage] = useState(null);

  const grouped = modules.reduce((acc, mod) => {
    const key = mod.category || "platform";
    if (!acc[key]) acc[key] = [];
    acc[key].push(mod);
    return acc;
  }, {});

  const toggle = async (mod) => {
    setBusy(mod.id);
    setMessage(null);
    try {
      await patchAdminModule(mod.id, { enabled: !mod.enabled });
      await refresh();
      setMessage(`${mod.name} ${mod.enabled ? "disabled" : "enabled"}.`);
    } catch (err) {
      setMessage(err.message || "Update failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold mb-1">Plug & play modules</h2>
        <p className="text-sm text-zinc-400 max-w-2xl">
          Turn platform features on or off instantly. To add a new module, register it in{" "}
          <code className="text-zinc-300">src/modules/registry.js</code> and seed it in{" "}
          <code className="text-zinc-300">src/logic/modules.py</code> on the API.
        </p>
        {message && <p className="text-sm text-lime-300 mt-3">{message}</p>}
      </div>

      {Object.entries(grouped).map(([category, rows]) => (
        <section key={category}>
          <h3 className="text-xs uppercase tracking-widest text-zinc-500 mb-3">
            {CATEGORY_LABEL[category] || category}
          </h3>
          <div className="space-y-3">
            {rows.map((mod) => {
              const Icon = mod.icon;
              return (
                <div
                  key={mod.id}
                  className="rounded-2xl border border-white/8 bg-white/3 p-4 md:p-5 flex flex-col sm:flex-row sm:items-center gap-4"
                >
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    {Icon && (
                      <div className="p-2 rounded-xl bg-white/5 text-lime-400 shrink-0">
                        <Icon className="w-5 h-5" />
                      </div>
                    )}
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-semibold">{mod.name}</p>
                        {mod.badge && (
                          <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-400/15 text-amber-200 border border-amber-400/20">
                            {mod.badge}
                          </span>
                        )}
                        <span className="text-[10px] text-zinc-600 font-mono">{mod.id}</span>
                      </div>
                      <p className="text-sm text-zinc-400 mt-1">{mod.description}</p>
                      <p className="text-xs text-zinc-600 mt-1">
                        v{mod.version} · {mod.scope}
                        {mod.embedded ? " · embedded in workflow" : mod.path ? ` · ${mod.path}` : ""}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    disabled={busy === mod.id}
                    onClick={() => toggle(mod)}
                    className={`min-h-11 px-5 py-2.5 rounded-xl text-sm font-semibold shrink-0 transition-colors ${
                      mod.enabled
                        ? "bg-lime-400 text-black hover:bg-lime-300"
                        : "bg-white/10 text-zinc-300 hover:bg-white/15"
                    }`}
                  >
                    {busy === mod.id ? "Saving…" : mod.enabled ? "Enabled" : "Disabled"}
                  </button>
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
