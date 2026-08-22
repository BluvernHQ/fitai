import { useState } from "react";
import { ChevronDown, Repeat } from "lucide-react";
import { loadLine, rxLine, sectionLabel, sectionOrder, whyText } from "../lib/programView";

const CellInput = ({ value, onChange, className = "", type = "text", placeholder = "—" }) => (
  <input
    type={type}
    value={value ?? ""}
    placeholder={placeholder}
    onChange={(e) =>
      onChange(type === "number" && e.target.value !== "" ? Number(e.target.value) : e.target.value)
    }
    className={`w-full bg-transparent border-0 px-0 py-0.5 text-sm text-white placeholder:text-zinc-700 focus:outline-none focus:bg-white/5 rounded tabular-nums ${className}`}
  />
);

export function SessionBoard({
  plan,
  day,
  editable = false,
  candidatesFor = () => [],
  onPatch,
  onSwap,
}) {
  if (!day) return null;
  const order = sectionOrder(plan);

  return (
    <div className="space-y-4">
      <header className="px-1">
        <p className="text-[10px] uppercase tracking-[0.22em] text-lime-400 mb-1">
          Day {day.day}
          {plan?.ui?.circuit?.block_rest_sec ? ` · circuit rest ${plan.ui.circuit.block_rest_sec}s` : ""}
        </p>
        <h2 className="text-xl sm:text-2xl font-semibold leading-tight">{day.title}</h2>
        <p className="text-xs text-zinc-500 mt-1 capitalize">
          {(day.emphasis || []).join(" · ") || "Full session"}
        </p>
      </header>

      {order.map((block) => {
        const items = day.blocks?.[block] || [];
        if (!items.length) return null;
        const meta = day.block_meta?.[block] || {};
        const isCircuit = meta.format === "circuit";
        return (
          <section
            key={block}
            className="rounded-2xl border border-white/10 bg-black/40 overflow-hidden"
          >
            <div className="flex items-center justify-between gap-3 px-4 py-2.5 bg-lime-400/10 border-b border-lime-400/10">
              <p className="text-[11px] font-bold tracking-widest text-lime-400 uppercase">
                {sectionLabel(day, block)}
              </p>
              {isCircuit && (
                <span className="text-[10px] uppercase tracking-widest text-lime-400/80">
                  Circuit
                </span>
              )}
            </div>
            <ol className="divide-y divide-white/6">
              {items.map((item, itemIdx) => (
                <ExerciseRow
                  key={`${item.exercise_id || "u"}-${itemIdx}`}
                  item={item}
                  index={itemIdx}
                  circuit={isCircuit}
                  editable={editable}
                  swaps={candidatesFor(item).filter((c) => c.exercise_id !== item.exercise_id)}
                  onPatch={(patch) => onPatch?.(block, itemIdx, patch)}
                  onSwap={(candidate) => onSwap?.(block, itemIdx, candidate)}
                />
              ))}
            </ol>
          </section>
        );
      })}
    </div>
  );
}

function ExerciseRow({ item, index, circuit, editable, swaps, onPatch, onSwap }) {
  const [open, setOpen] = useState(false);
  const load = loadLine(item);

  return (
    <li
      className={`px-4 py-3 ${item.circuit_end ? "border-b-lime-400/20" : ""} ${
        item.unfilled ? "bg-amber-400/5" : ""
      }`}
    >
      <div className="flex items-start gap-3">
        {circuit && (
          <span className="mt-0.5 w-6 h-6 rounded-full bg-white/8 text-[11px] font-bold text-zinc-400 flex items-center justify-center shrink-0">
            {index + 1}
          </span>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
              {item.role || item.tag}
            </span>
            {item.unfilled && (
              <span className="text-[10px] uppercase tracking-widest text-amber-300">Unfilled</span>
            )}
          </div>
          {editable ? (
            <CellInput
              value={item.name}
              onChange={(value) => onPatch({ name: value })}
              className={`font-medium text-base ${item.unfilled ? "text-amber-200" : ""}`}
            />
          ) : (
            <p className={`font-medium ${item.unfilled ? "text-amber-200" : ""}`}>{item.name}</p>
          )}
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <RxChip label="Rx" value={rxLine(item)} />
            {load ? <RxChip label="Load" value={load} /> : null}
            {item.rest ? <RxChip label="Rest" value={item.rest} /> : null}
            {item.tempo ? <RxChip label="Tempo" value={item.tempo} /> : null}
          </div>
          {item.unfilled && (
            <p className="text-[11px] text-amber-200/80 mt-2">
              {(item.unfilled_reasons || []).join(" · ")}
            </p>
          )}
        </div>
        {(editable || whyText(item) || item.coach_note) && (
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="shrink-0 p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5"
            aria-label="Show details"
          >
            <ChevronDown className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        )}
      </div>

      {open && (
        <div className="mt-3 pl-0 sm:pl-9 space-y-3">
          {editable && (
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
              <Field label="Role">
                <CellInput
                  value={item.role || item.tag}
                  onChange={(value) => onPatch({ role: value, tag: value })}
                  className="uppercase"
                />
              </Field>
              <Field label="Sets">
                <CellInput type="number" value={item.sets ?? ""} onChange={(value) => onPatch({ sets: value })} />
              </Field>
              <Field label="Reps-RPE">
                <CellInput value={item.reps_rpe || ""} onChange={(value) => onPatch({ reps_rpe: value })} />
              </Field>
              <Field label="% 1RM">
                <CellInput
                  type="number"
                  value={item.percent_1rm ?? ""}
                  onChange={(value) => onPatch({ percent_1rm: value })}
                />
              </Field>
              <Field label="1RM">
                <CellInput type="number" value={item.one_rm ?? ""} onChange={(value) => onPatch({ one_rm: value })} />
              </Field>
              <Field label="Load">
                <CellInput
                  type="number"
                  value={item.load ?? item.load_kg ?? ""}
                  onChange={(value) => onPatch({ load: value })}
                />
              </Field>
              <Field label="Rest">
                <CellInput value={item.rest || ""} onChange={(value) => onPatch({ rest: value })} />
              </Field>
            </div>
          )}
          {swaps?.length > 0 && editable && (
            <label className="block">
              <span className="text-[10px] uppercase tracking-widest text-zinc-600 flex items-center gap-1 mb-1">
                <Repeat className="w-3 h-3" /> Swap
              </span>
              <select
                className="w-full max-w-md bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-300"
                defaultValue=""
                onChange={(e) => {
                  const candidate = swaps.find((c) => c.exercise_id === e.target.value);
                  if (candidate) onSwap(candidate);
                  e.target.value = "";
                }}
              >
                <option value="">Replace with…</option>
                {swaps.slice(0, 8).map((c) => (
                  <option key={c.exercise_id} value={c.exercise_id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          {(whyText(item) || item.coach_note) && (
            <p className="text-[12px] text-zinc-500 leading-relaxed">
              {whyText(item) || item.coach_note}
            </p>
          )}
        </div>
      )}
    </li>
  );
}

function RxChip({ label, value }) {
  return (
    <span className="inline-flex items-baseline gap-1.5 rounded-lg bg-white/5 border border-white/8 px-2 py-1">
      <span className="text-[9px] uppercase tracking-widest text-zinc-600">{label}</span>
      <span className="tabular-nums text-zinc-200">{value}</span>
    </span>
  );
}

function Field({ label, children }) {
  return (
    <label className="rounded-xl bg-white/4 border border-white/8 px-3 py-2">
      <span className="block text-[9px] uppercase tracking-widest text-zinc-600 mb-0.5">{label}</span>
      {children}
    </label>
  );
}
