import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getCoachInsights } from "../api/backend";
import { useAuth } from "../context/authContext";

export const CoachInsights = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    getCoachInsights()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((err) => {
        if (cancelled) return;
        const msg = String(err.message || "");
        if (msg.includes("404") || msg.includes("Not Found")) {
          setData({
            kept_often: [],
            emerging: [],
            replaced_often: [],
            disclaimer: "No preference history yet. Approve or edit a few programs first.",
          });
          return;
        }
        setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  return (
    <div className="page-shell page-shell-md text-white">
      <button
        onClick={() => navigate("/coach/dashboard")}
        className="btn-ghost mb-6 -ml-1"
      >
        <ArrowLeft className="w-4 h-4" /> Dashboard
      </button>
      <h1 className="display-title text-3xl md:text-4xl mb-2">Coach learning</h1>
      <p className="text-zinc-400 mb-8 text-sm md:text-base leading-relaxed">
        {data?.disclaimer || "Taste never overrides safety, equipment, or level gates."}
      </p>
      {error && <p className="text-red-300">{error}</p>}
      {!data && !error && <p className="text-zinc-500">Loading…</p>}
      {data && (
        <div className="space-y-8">
          <Section title="Kept often" rows={data.kept_often} />
          <Section title="Emerging signals" rows={data.emerging} />
          <Section title="Replaced often" rows={data.replaced_often} />
        </div>
      )}
    </div>
  );
};

function Section({ title, rows }) {
  if (!rows?.length) {
    return (
      <section>
        <h2 className="text-sm uppercase tracking-widest text-zinc-500 mb-3">{title}</h2>
        <p className="text-zinc-600 text-sm">Not enough similar decisions yet.</p>
      </section>
    );
  }
  return (
    <section>
      <h2 className="text-sm uppercase tracking-widest text-zinc-500 mb-3">{title}</h2>
      <div className="space-y-2">
        {rows.map((row) => (
          <div
            key={`${row.exercise_id}-${row.context_key}`}
            className="rounded-xl border border-white/10 bg-white/3 px-4 py-3"
          >
            <p className="font-medium">{row.exercise_id}</p>
            <p className="text-xs text-zinc-500 mt-1">{row.label}</p>
            <p className="text-xs text-zinc-600">
              shown {row.shown} · kept {row.kept} · replaced {row.replaced}
              {row.applied ? "" : " · not used in ranking"}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
