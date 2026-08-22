import { useState } from "react";
import {
  Activity,
  Check,
  Dumbbell,
  GripVertical,
  HeartPulse,
  Moon,
  TriangleAlert,
} from "lucide-react";
import {
  calendarWeekdays,
  dayExerciseCount,
  gymDayForCell,
  isTrainingKind,
  sectionOrder,
  shortDayTitle,
  toneStyle,
} from "../lib/programView";

const KIND_ICON = {
  gym: Dumbbell,
  deload: TriangleAlert,
  active_recovery: HeartPulse,
  passive_recovery: Moon,
  rest: Moon,
  referral: TriangleAlert,
};

export function WeekStrip({
  plan,
  selectedIdx = 0,
  onSelect,
  onToggleDone,
  onReorder,
  editable = false,
}) {
  const days = plan?.days || [];
  const calendar = plan?.calendar || [];
  const order = sectionOrder(plan);
  const weekdays = calendarWeekdays(plan);
  const gymTotal = calendar.filter((c) => isTrainingKind(c.kind)).length;
  const gymDone = calendar.filter((c) => isTrainingKind(c.kind) && c.done).length;
  const [dragIdx, setDragIdx] = useState(null);
  const [dropIdx, setDropIdx] = useState(null);

  if (!calendar.length) return null;

  const canDrag = editable && Boolean(onReorder);

  const handleDragStart = (idx, e) => {
    if (!canDrag) return;
    setDragIdx(idx);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", String(idx));
  };

  const handleDragOver = (idx, e) => {
    if (!canDrag || dragIdx === null) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (dropIdx !== idx) setDropIdx(idx);
  };

  const handleDrop = (idx, e) => {
    if (!canDrag) return;
    e.preventDefault();
    const from = Number(e.dataTransfer.getData("text/plain"));
    setDragIdx(null);
    setDropIdx(null);
    if (!Number.isNaN(from) && from !== idx) onReorder(from, idx);
  };

  const handleDragEnd = () => {
    setDragIdx(null);
    setDropIdx(null);
  };

  return (
    <section className="mb-5 md:mb-6">
      <div className="flex items-center justify-between mb-3 px-0.5 gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em] text-zinc-500">This week</p>
          {canDrag && (
            <p className="text-[11px] text-zinc-600 mt-0.5">Drag days to reschedule</p>
          )}
        </div>
        {gymTotal > 0 && (
          <p className="text-xs text-zinc-500 tabular-nums shrink-0">
            {gymDone}/{gymTotal} sessions done
          </p>
        )}
      </div>
      <div className="overflow-x-auto snap-strip no-scrollbar -mx-4 px-4 pb-1 md:mx-0 md:px-0 md:overflow-visible">
        <div className="flex gap-2 md:grid md:grid-cols-7 md:gap-2 min-w-0">
          {calendar.map((cell, idx) => {
            const gymDay = gymDayForCell(cell, days);
            const meta = toneStyle(cell);
            const selected = idx === selectedIdx;
            const Icon = KIND_ICON[cell.kind] || Activity;
            const title = shortDayTitle(gymDay, cell);
            const count = gymDay ? dayExerciseCount(gymDay, order) : 0;
            const isDragging = dragIdx === idx;
            const isDropTarget = dropIdx === idx && dragIdx !== null && dragIdx !== idx;
            const weekdayLabel = weekdays[idx] || cell.weekday;

            return (
              <div
                key={`${weekdayLabel}-${idx}-${cell.day ?? cell.kind}`}
                onDragOver={(e) => handleDragOver(idx, e)}
                onDrop={(e) => handleDrop(idx, e)}
                className={`relative snap-start shrink-0 w-[42vw] min-w-[138px] max-w-[168px] md:w-auto md:min-w-0 md:max-w-none rounded-2xl p-3 text-left min-h-[124px] md:min-h-[132px] border transition-all ${meta.card} ${
                  selected ? meta.selected : ""
                } ${cell.done ? "opacity-75" : ""} ${isDragging ? "opacity-40 scale-[0.98]" : ""} ${
                  isDropTarget ? "ring-2 ring-lime-400/60 border-lime-400/40" : ""
                }`}
              >
                <button
                  type="button"
                  onClick={() => onSelect?.(idx, cell)}
                  className="absolute inset-0 rounded-2xl z-0"
                  aria-label={`${weekdayLabel} ${cell.label || cell.kind}`}
                />
                <div className="relative flex items-center justify-between gap-1 mb-2 z-[1]">
                  <div className="flex items-center gap-1 min-w-0">
                    {canDrag ? (
                      <span
                        draggable
                        onDragStart={(e) => handleDragStart(idx, e)}
                        onDragEnd={handleDragEnd}
                        className="pointer-events-auto shrink-0 p-0.5 -ml-0.5 rounded text-zinc-600 hover:text-zinc-300 cursor-grab active:cursor-grabbing"
                        aria-label={`Drag ${weekdayLabel}`}
                      >
                        <GripVertical className="w-3.5 h-3.5" />
                      </span>
                    ) : null}
                    <span className="text-[11px] font-bold uppercase tracking-widest text-zinc-400 truncate pointer-events-none">
                      {weekdayLabel}
                    </span>
                  </div>
                  {editable ? (
                    <button
                      type="button"
                      aria-label={cell.done ? "Mark not done" : "Mark done"}
                      onClick={() => onToggleDone?.(idx, !cell.done)}
                      className={`pointer-events-auto relative z-10 w-7 h-7 rounded-full border flex items-center justify-center shrink-0 ${
                        cell.done
                          ? "bg-lime-400 border-lime-400 text-black"
                          : "border-white/20 text-transparent hover:border-lime-400/60"
                      }`}
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  ) : (
                    cell.done && (
                      <span className="w-6 h-6 rounded-full bg-lime-400 text-black flex items-center justify-center">
                        <Check className="w-3 h-3" />
                      </span>
                    )
                  )}
                </div>
                <div className="relative z-[1] pointer-events-none">
                  <span
                    className={`inline-flex items-center gap-1 text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded-full mb-2 ${meta.chip}`}
                  >
                    <Icon className="w-3 h-3" />
                    {(cell.label || cell.kind).replace("_", " ")}
                  </span>
                  <p className="text-sm font-semibold leading-snug line-clamp-2 capitalize">
                    {title}
                  </p>
                  {isTrainingKind(cell.kind) && (
                    <p className="text-[11px] text-zinc-500 mt-2 tabular-nums">
                      {count} movements
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
