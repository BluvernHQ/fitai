export const BLOCK_ORDER = ["ramp", "activation", "block_a", "block_b", "accessories"];
export const LOAD_INCREMENT = 2.5;
export const DEFAULT_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export const TONE_STYLES = {
  accent: {
    chip: "bg-lime-400 text-black",
    card: "border-lime-400/30 bg-lime-400/8 hover:border-lime-400/50",
    selected: "ring-2 ring-lime-400 border-lime-400",
  },
  info: {
    chip: "bg-sky-400/20 text-sky-200 border border-sky-400/30",
    card: "border-sky-400/20 bg-sky-400/5 hover:border-sky-400/40",
    selected: "ring-2 ring-sky-300 border-sky-300/60",
  },
  calm: {
    chip: "bg-violet-400/20 text-violet-200 border border-violet-400/30",
    card: "border-violet-400/20 bg-violet-400/5 hover:border-violet-400/40",
    selected: "ring-2 ring-violet-300 border-violet-300/60",
  },
  muted: {
    chip: "bg-zinc-800 text-zinc-400 border border-white/10",
    card: "border-white/8 bg-white/3 hover:border-white/15",
    selected: "ring-2 ring-zinc-400 border-zinc-400/50",
  },
  warn: {
    chip: "bg-amber-400/20 text-amber-200 border border-amber-400/30",
    card: "border-amber-400/20 bg-amber-400/5",
    selected: "ring-2 ring-amber-300",
  },
  alert: {
    chip: "bg-red-500/20 text-red-200 border border-red-500/30",
    card: "border-red-500/30 bg-red-500/8",
    selected: "ring-2 ring-red-400",
  },
};

export function normalizePlan(raw) {
  if (!raw) return raw;
  const days = (raw.days || []).map((day) => {
    const src = day.blocks || {};
    if (src.block_a || src.block_b) return day;
    return {
      ...day,
      title: day.title || `DAY ${day.day}`,
      blocks: {
        ramp: src.ramp || [],
        activation: src.activation || [],
        block_a: src.main || [],
        block_b: src.backdown || [],
        accessories: src.accessories || [],
      },
    };
  });
  return { ...raw, days };
}

export function resolvePlan(program) {
  if (!program) return null;
  const candidates = [program.coach_plan, program.ai_plan, program.workout, program];
  const withDays = candidates.find((p) => p && Array.isArray(p.days) && p.days.length);
  return normalizePlan(withDays || candidates.find(Boolean) || null);
}

export function sectionOrder(plan) {
  return plan?.ui?.section_order || BLOCK_ORDER;
}

export function sectionLabel(day, key) {
  return day?.block_meta?.[key]?.label || String(key).replaceAll("_", " ");
}

export function toneStyle(cell) {
  return TONE_STYLES[cell?.tone] || TONE_STYLES.muted;
}

export function dayExerciseCount(day, order = BLOCK_ORDER) {
  return order.reduce((sum, key) => sum + ((day?.blocks?.[key] || []).length), 0);
}

export function isTrainingKind(kind) {
  return kind === "gym" || kind === "deload";
}

export function calendarWeekdays(plan) {
  const fromUi = plan?.ui?.weekdays;
  if (Array.isArray(fromUi) && fromUi.length) return fromUi;
  return DEFAULT_WEEKDAYS;
}

/** Move a calendar cell; weekday labels follow slot index (Mon–Sun). */
export function reorderCalendarCells(calendar, fromIdx, toIdx, weekdays = DEFAULT_WEEKDAYS) {
  if (!calendar?.length || fromIdx === toIdx) return calendar;
  if (fromIdx < 0 || toIdx < 0 || fromIdx >= calendar.length || toIdx >= calendar.length) {
    return calendar;
  }
  const next = calendar.map((cell) => ({ ...cell }));
  const [moved] = next.splice(fromIdx, 1);
  next.splice(toIdx, 0, moved);
  return next.map((cell, i) => ({
    ...cell,
    weekday: weekdays[i] || cell.weekday,
  }));
}

export function gymDayForCell(cell, days) {
  if (!cell?.day && cell?.day !== 0) {
    if (isTrainingKind(cell?.kind)) return (days || [])[0] || null;
    return null;
  }
  const want = Number(cell.day);
  return (days || []).find((d) => Number(d.day) === want) || null;
}

export function shortDayTitle(day, cell) {
  if (day?.emphasis?.length) {
    return day.emphasis
      .map((p) => String(p).replace(/_/g, " "))
      .join(" · ");
  }
  const raw = day?.title || cell?.title || "";
  const parts = raw.split("|").map((s) => s.trim()).filter(Boolean);
  if (parts.length > 2) return parts.slice(0, 2).join(" · ");
  return raw;
}

export function rxLine(item) {
  const sets = item?.sets != null && item.sets !== "" ? `${item.sets}` : "";
  const reps = item?.reps_rpe || item?.reps || "";
  if (sets && reps) return `${sets} × ${reps}`;
  return sets || reps || "—";
}

export function loadLine(item) {
  if (item?.load != null && item.load !== "") return `${item.load} kg`;
  if (item?.load_kg != null && item.load_kg !== "") return `${item.load_kg} kg`;
  if (item?.percent_1rm) return `${item.percent_1rm}%`;
  return "";
}

export function exportCsv(plan) {
  const headers = [
    "Day", "Title", "Section", "Role", "Exercise", "Sets", "Reps-RPE",
    "%1RM", "1RM", "Load", "Rest", "Why",
  ];
  const rows = [headers];
  for (const day of plan.days || []) {
    for (const section of sectionOrder(plan)) {
      for (const item of day.blocks?.[section] || []) {
        rows.push([
          day.day, day.title || "", sectionLabel(day, section),
          item.role || item.tag || "", item.name || "", item.sets ?? "",
          item.reps_rpe || "", item.percent_1rm ?? "", item.one_rm ?? "",
          item.load ?? item.load_kg ?? "", item.rest || "",
          item.why || item.coach_note || "",
        ]);
      }
    }
  }
  const csv = rows
    .map((row) => row.map((cell) => `"${String(cell ?? "").replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${(plan.week_title || "program").replace(/\s+/g, "_")}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export function whyText(item) {
  const parts = item?.why_parts;
  if (!parts) return item?.why || "";
  const lines = [];
  if (parts.methodology) lines.push(`Methodology: ${parts.methodology}`);
  if (parts.needs?.length) lines.push(`Needs: ${parts.needs.join(", ")}`);
  if (parts.faults?.length) lines.push(`Faults: ${parts.faults.join(", ")}`);
  if (parts.taste) lines.push(parts.taste_applied ? `Taste: ${parts.taste}` : `Taste (not ranked): ${parts.taste}`);
  return lines.join(" · ") || item?.why || "";
}

export function snapshotLine(snapshot) {
  if (!snapshot) return "";
  const days = snapshot.days_per_week;
  const kit = Array.isArray(snapshot.equipment) ? snapshot.equipment : [];
  const maxes = snapshot.lift_maxes || {};
  const parts = [];
  if (days) parts.push(`${days} gym days`);
  if (kit.length) parts.push(kit.map((k) => String(k).replaceAll("_", " ")).join(", "));
  else parts.push("bodyweight / band kit");
  const loads = ["back_squat", "deadlift", "bench_press", "row"]
    .filter((k) => maxes[k] != null && maxes[k] !== "")
    .map((k) => `${k.replaceAll("_", " ")} ${maxes[k]} kg`);
  if (loads.length) parts.push(loads.join(" · "));
  return parts.join(" · ");
}
