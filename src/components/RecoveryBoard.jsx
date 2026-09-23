import { Plus, Trash2, HeartPulse, Moon } from "lucide-react";

const SUGGESTIONS = [
  { name: "Easy walk", detail: "20–40 min zone 1", role: "cardio" },
  { name: "Easy bike / assault", detail: "15–30 min easy", role: "cardio" },
  { name: "Mobility flow", detail: "10–15 min", role: "mobility" },
  { name: "Soft tissue", detail: "5–10 min targeted", role: "recovery" },
  { name: "Nasal breathing", detail: "5–8 min", role: "breathing" },
  { name: "Light swim", detail: "20–30 min easy", role: "cardio" },
];

/**
 * Editable active / passive recovery day — title, notes, and coach-added activities.
 */
export function RecoveryBoard({ cell, editable = false, onChange }) {
  if (!cell) return null;
  const activities = Array.isArray(cell.activities) ? cell.activities : [];
  const isActive = cell.kind === "active_recovery";
  const Icon = isActive ? HeartPulse : Moon;

  const patch = (next) => onChange?.({ ...cell, ...next });

  const updateActivity = (idx, fields) => {
    const list = activities.map((row, i) => (i === idx ? { ...row, ...fields } : row));
    patch({ activities: list });
  };

  const removeActivity = (idx) => {
    patch({ activities: activities.filter((_, i) => i !== idx) });
  };

  const addActivity = (seed = null) => {
    const row = seed
      ? { name: seed.name, detail: seed.detail || "", role: seed.role || "recovery", notes: "" }
      : { name: "", detail: "", role: "recovery", notes: "" };
    patch({ activities: [...activities, row] });
  };

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden">
      <div className="p-5 md:p-6 border-b border-white/8">
        <div className="flex items-start gap-4">
          <div
            className={`p-3 rounded-xl shrink-0 ${
              isActive ? "bg-sky-400/15 text-sky-300" : "bg-white/5 text-zinc-300"
            }`}
          >
            <Icon className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 mb-1">
              {cell.weekday} · {(cell.label || cell.kind || "").replaceAll("_", " ")}
            </p>
            {editable ? (
              <input
                value={cell.title || ""}
                onChange={(e) => patch({ title: e.target.value })}
                className="w-full bg-transparent text-2xl font-semibold text-white outline-none border-b border-transparent focus:border-white/20 pb-1"
                placeholder="Recovery title"
              />
            ) : (
              <h2 className="text-2xl font-semibold mb-2">{cell.title || "Recovery"}</h2>
            )}
            {editable ? (
              <textarea
                value={cell.notes || ""}
                onChange={(e) => patch({ notes: e.target.value })}
                rows={3}
                className="mt-3 w-full bg-black/30 border border-white/10 rounded-xl px-3 py-3 text-base text-zinc-300 outline-none focus:border-sky-400/40 resize-y min-h-[4.5rem]"
                placeholder="Coach notes for this recovery day"
              />
            ) : (
              <p className="text-zinc-400 max-w-2xl leading-relaxed mt-2">
                {cell.notes || "No loaded work today."}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="p-4 md:p-6 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-[11px] font-bold tracking-widest text-zinc-500 uppercase">
            Recovery activities
          </p>
          {editable && (
            <button
              type="button"
              onClick={() => addActivity()}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-sky-300 hover:text-sky-200 min-h-11 px-3"
            >
              <Plus className="w-4 h-4" /> Add
            </button>
          )}
        </div>

        {activities.length === 0 && (
          <p className="text-sm text-zinc-500">
            {editable
              ? "No activities yet — add mobility, easy cardio, breathing, or soft tissue."
              : "No programmed recovery activities."}
          </p>
        )}

        <ul className="space-y-2">
          {activities.map((row, idx) => (
            <li
              key={`act-${idx}`}
              className="rounded-xl border border-white/10 bg-black/30 p-3 md:p-4"
            >
              {editable ? (
                <div className="flex gap-2">
                  <div className="min-w-0 flex-1 space-y-2">
                    <input
                      value={row.name || ""}
                      onChange={(e) => updateActivity(idx, { name: e.target.value })}
                      className="w-full bg-transparent text-base font-medium text-white outline-none placeholder:text-zinc-600"
                      placeholder="Activity name"
                    />
                    <input
                      value={row.detail || ""}
                      onChange={(e) => updateActivity(idx, { detail: e.target.value })}
                      className="w-full bg-transparent text-base text-zinc-400 outline-none placeholder:text-zinc-700 py-1"
                      placeholder="Dose — e.g. 20 min easy / 2×8 breaths"
                    />
                    <input
                      value={row.notes || ""}
                      onChange={(e) => updateActivity(idx, { notes: e.target.value })}
                      className="w-full bg-transparent text-base text-zinc-500 outline-none placeholder:text-zinc-700 py-1"
                      placeholder="Optional coach cue"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeActivity(idx)}
                    className="shrink-0 p-2 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 min-h-11 min-w-11 inline-flex items-center justify-center"
                    aria-label="Remove activity"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div>
                  <p className="font-medium text-white">{row.name}</p>
                  {row.detail && <p className="text-sm text-zinc-400 mt-0.5">{row.detail}</p>}
                  {row.notes && <p className="text-xs text-zinc-500 mt-1">{row.notes}</p>}
                </div>
              )}
            </li>
          ))}
        </ul>

        {editable && (
          <div className="pt-2">
            <p className="text-[10px] uppercase tracking-widest text-zinc-600 mb-2">Quick add</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.name}
                  type="button"
                  onClick={() => addActivity(s)}
                  className="min-h-11 px-3 rounded-full text-xs border border-white/10 bg-white/5 text-zinc-300 hover:border-sky-400/40 hover:text-sky-200"
                >
                  + {s.name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
