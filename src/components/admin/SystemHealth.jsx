import { useEffect, useState } from "react";
import { getAdminOverview } from "../../api/backend";

export function SystemHealth() {
  const [stats, setStats] = useState(null);
  const [apiOk, setApiOk] = useState(null);

  useEffect(() => {
    getAdminOverview()
      .then((data) => {
        setStats(data);
        setApiOk(true);
      })
      .catch(() => setApiOk(false));
  }, []);

  const rows = [
    { label: "API", status: apiOk === null ? "checking" : apiOk ? "ok" : "down" },
    { label: "Database", status: stats ? "ok" : apiOk === false ? "unknown" : "checking" },
    { label: "Groq enrichment", status: stats?.integrations?.groq ? "configured" : "off" },
    { label: "Firestore mirror", status: stats?.integrations?.firestore_mirror ? "on" : "off" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold mb-1">System health</h2>
        <p className="text-sm text-zinc-400">Live checks from the admin overview endpoint.</p>
      </div>
      <ul className="space-y-3">
        {rows.map((row) => (
          <li
            key={row.label}
            className="flex items-center justify-between rounded-xl border border-white/8 bg-white/3 px-4 py-3"
          >
            <span>{row.label}</span>
            <StatusPill value={row.status} />
          </li>
        ))}
      </ul>
      {stats?.integrations?.database && (
        <p className="text-xs text-zinc-600">Database target: {stats.integrations.database}</p>
      )}
    </div>
  );
}

function StatusPill({ value }) {
  const tone =
    value === "ok" || value === "configured" || value === "on"
      ? "text-lime-300 bg-lime-400/10 border-lime-400/25"
      : value === "off"
        ? "text-zinc-500 bg-white/5 border-white/10"
        : value === "down"
          ? "text-red-300 bg-red-500/10 border-red-500/25"
          : "text-amber-200 bg-amber-400/10 border-amber-400/25";
  return (
    <span className={`text-xs uppercase tracking-wider px-2.5 py-1 rounded-full border ${tone}`}>
      {value}
    </span>
  );
}
