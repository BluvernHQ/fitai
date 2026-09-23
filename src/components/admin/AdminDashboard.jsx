import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, Blocks, FileStack, Puzzle, Users, UserSquare2 } from "lucide-react";
import { getAdminOverview } from "../../api/backend";
import { useModules } from "../../context/ModuleContext";

function Stat({ label, value, icon: Icon }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs uppercase tracking-widest text-zinc-500">{label}</p>
        {Icon && <Icon className="w-4 h-4 text-zinc-600" />}
      </div>
      <p className="text-3xl font-bold">{value ?? "—"}</p>
    </div>
  );
}

export function AdminDashboard() {
  const { modules } = useModules();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getAdminOverview()
      .then(setStats)
      .catch((err) => setError(err.message || "Could not load overview"));
  }, []);

  const enabled = modules.filter((m) => m.enabled).length;
  const disabled = modules.length - enabled;

  return (
    <div className="space-y-8">
      {error && <p className="text-red-300 text-sm">{error}</p>}

      <section className="grid grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
        <Stat label="Coaches" value={stats?.coaches} icon={UserSquare2} />
        <Stat label="Students" value={stats?.students} icon={Users} />
        <Stat label="Assessments" value={stats?.assessments} icon={Activity} />
        <Stat label="Programs" value={stats?.programs} icon={FileStack} />
        <Stat label="Blocks" value={stats?.blocks} icon={Blocks} />
        <Stat label="Modules on" value={stats?.enabled_modules ?? enabled} icon={Puzzle} />
      </section>

      <section className="rounded-2xl border border-white/8 bg-white/3 p-5 md:p-6">
        <h2 className="text-lg font-semibold mb-4">Integrations</h2>
        <div className="flex flex-wrap gap-2">
          {[
            { key: "groq", label: "Groq AI notes", on: stats?.integrations?.groq },
            { key: "firestore", label: "Firestore mirror", on: stats?.integrations?.firestore_mirror },
            { key: "db", label: `DB · ${stats?.integrations?.database || "local"}`, on: true },
          ].map((item) => (
            <span
              key={item.key}
              className={`px-3 py-1.5 rounded-full text-xs border ${
                item.on
                  ? "bg-lime-400/15 border-lime-400/30 text-lime-200"
                  : "bg-zinc-800/50 border-white/10 text-zinc-500"
              }`}
            >
              {item.label}
            </span>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-white/8 bg-white/3 p-5 md:p-6">
        <div className="flex items-center justify-between gap-4 mb-4">
          <h2 className="text-lg font-semibold">Module snapshot</h2>
          <Link to="/admin/modules" className="text-sm text-lime-400 hover:text-lime-300">
            Manage modules →
          </Link>
        </div>
        <p className="text-sm text-zinc-400 mb-4">
          {enabled} enabled · {disabled} disabled · plug new features in{" "}
          <code className="text-zinc-300">src/modules/registry.js</code>
        </p>
        <ul className="space-y-2">
          {modules.slice(0, 6).map((mod) => (
            <li
              key={mod.id}
              className="flex items-center justify-between gap-3 text-sm border-b border-white/5 pb-2"
            >
              <span className="text-zinc-300">{mod.name}</span>
              <span className={mod.enabled ? "text-lime-400" : "text-zinc-600"}>
                {mod.enabled ? "On" : "Off"}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
