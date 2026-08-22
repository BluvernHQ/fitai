import { Moon } from "lucide-react";
import { gymDayForCell, isTrainingKind } from "../lib/programView";
import { WeekStrip } from "./WeekStrip";
import { SessionBoard } from "./SessionBoard";
import { useState } from "react";

export function ProgramView({ plan, editable = false, candidatesFor, onPatch, onSwap }) {
  const days = plan?.days || [];
  const calendar = plan?.calendar || [];
  const firstGym = calendar.findIndex((c) => isTrainingKind(c.kind));
  const [calIdx, setCalIdx] = useState(firstGym >= 0 ? firstGym : 0);
  const selectedCell = calendar[calIdx] || calendar[0];
  const selectedGym = gymDayForCell(selectedCell, days);
  const activeDay = selectedGym || days[0];
  const showSession =
    Boolean(activeDay) &&
    (!calendar.length || !selectedCell || isTrainingKind(selectedCell.kind));

  return (
    <div>
      <WeekStrip plan={plan} selectedIdx={calIdx} onSelect={(idx) => setCalIdx(idx)} />
      {showSession ? (
        calendar.length ? (
          <SessionBoard
            plan={plan}
            day={activeDay}
            editable={editable}
            candidatesFor={candidatesFor}
            onPatch={onPatch}
            onSwap={onSwap}
          />
        ) : (
          <div className="space-y-8">
            {days.map((day) => (
              <SessionBoard
                key={day.day}
                plan={plan}
                day={day}
                editable={editable}
                candidatesFor={candidatesFor}
                onPatch={onPatch}
                onSwap={onSwap}
              />
            ))}
          </div>
        )
      ) : (
        <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 md:p-8">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-xl bg-white/5">
              <Moon className="w-5 h-5 text-zinc-300" />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 mb-1">
                {selectedCell?.weekday} · {(selectedCell?.label || selectedCell?.kind || "").replace("_", " ")}
              </p>
              <h2 className="text-2xl font-semibold mb-2">{selectedCell?.title || "Recovery"}</h2>
              <p className="text-zinc-400 max-w-2xl leading-relaxed">
                {selectedCell?.notes || "No loaded work today."}
              </p>
            </div>
          </div>
        </section>
      )}
      {!days.length && (
        <p className="text-zinc-500 text-sm mt-4">No sessions in this program yet.</p>
      )}
    </div>
  );
}
