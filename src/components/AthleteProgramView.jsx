import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { publicFetch } from "../api/clients";
import { resolvePlan } from "../lib/programView";
import { ProgramView } from "./ProgramView";

export const AthleteProgramView = () => {
  const { token } = useParams();
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    publicFetch(`/public/programs/${token}`)
      .then((data) => setPlan(resolvePlan(data)))
      .catch((err) => setError(err.message || "Share not found"));
  }, [token]);

  if (error) {
    return (
      <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center px-6">
        <p className="text-zinc-400">{error}</p>
      </div>
    );
  }
  if (!plan) {
    return (
      <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center">
        Loading program…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white px-4 py-10 max-w-[1120px] mx-auto">
      <p className="text-[10px] uppercase tracking-[0.25em] text-zinc-500 mb-2">Your week</p>
      <h1 className="text-3xl md:text-4xl font-bold mb-2 leading-tight">{plan.week_title}</h1>
      <p className="text-zinc-400 mb-8 max-w-2xl leading-relaxed">{plan.needs_summary}</p>
      <div className="mb-6 flex gap-3 print:hidden">
        <button
          onClick={() => window.print()}
          className="px-4 py-2 rounded-xl bg-white/10 text-sm"
        >
          Print / Save PDF
        </button>
      </div>
      <ProgramView plan={plan} />
    </div>
  );
};
