import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Check,
  ChevronDown,
  Download,
  Home,
  Moon,
  MoreHorizontal,
  Printer,
  RefreshCw,
  Share2,
  X,
} from "lucide-react";
import {
  createShare,
  downloadExport,
  getBlockWeek,
  getProgram,
  reviewProgram,
} from "../api/backend";
import {
  exportCsv,
  gymDayForCell,
  isTrainingKind,
  LOAD_INCREMENT,
  reorderCalendarCells,
  resolvePlan,
  snapshotLine,
} from "../lib/programView";
import { WeekStrip } from "./WeekStrip";
import { SessionBoard } from "./SessionBoard";

function applyPatch(item, patch) {
  const next = { ...item, ...patch };
  if ("reps" in patch || "rpe" in patch) {
    const primary = String(next.reps || "").split("-")[0].trim();
    const rpe = next.rpe === "" || next.rpe == null ? "" : next.rpe;
    next.reps_rpe = rpe === "" ? primary : `${primary}-${rpe}`;
    next.intensity_label = next.reps_rpe || next.intensity_label;
  }
  if ("reps_rpe" in patch && typeof patch.reps_rpe === "string") {
    const [repsPart, rpePart] = patch.reps_rpe.split("-");
    if (repsPart) next.reps = repsPart.trim();
    if (rpePart) next.rpe = Number(rpePart);
  }
  if ("percent_1rm" in patch || "one_rm" in patch) {
    const pct = Number(next.percent_1rm);
    const orm = Number(next.one_rm);
    if (pct > 0 && orm > 0) {
      next.load = Math.round((orm * (pct / 100)) / LOAD_INCREMENT) * LOAD_INCREMENT;
      next.load_kg = next.load;
      next.intensity = pct / 100;
    }
  }
  if ("load" in patch) {
    const value = patch.load === "" || patch.load == null ? null : Number(patch.load);
    next.load = Number.isNaN(value) ? null : value;
    next.load_kg = next.load;
  }
  return next;
}

export const WorkoutResults = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { id, programId: paramProgramId } = useParams();
  const [program, setProgram] = useState(state?.workout || null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [calIdx, setCalIdx] = useState(0);
  const [dirty, setDirty] = useState(false);
  const [shareUrl, setShareUrl] = useState(null);
  const [exportOpen, setExportOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);

  const programId = paramProgramId || state?.programId || program?.id;

  useEffect(() => {
    const numericId = Number(programId);
    if (!numericId) return;
    getProgram(id, numericId)
      .then((row) => {
        setProgram(row);
        setDirty(false);
      })
      .catch((err) => setMessage(err.message || "Could not refresh this program"));
  }, [id, programId]);

  const plan = useMemo(() => resolvePlan(program), [program]);

  const days = plan?.days || [];
  const calendar = plan?.calendar || [];
  const selectedCell = calendar[calIdx] || calendar[0];
  const selectedGym = gymDayForCell(selectedCell, days);
  const dayIdx = selectedGym ? days.findIndex((d) => d.day === selectedGym.day) : 0;
  const activeDay = selectedGym || days[dayIdx] || days[0];

  useEffect(() => {
    if (!calendar.length) return;
    setCalIdx((current) => {
      if (calendar[current] && isTrainingKind(calendar[current].kind)) return current;
      const firstGym = calendar.findIndex((c) => isTrainingKind(c.kind));
      return firstGym >= 0 ? firstGym : 0;
    });
  }, [calendar.length]);

  if (!plan) {
    return (
      <div className="min-h-screen pt-32 px-6 flex flex-col items-center justify-center text-center">
        <h2 className="text-2xl font-bold text-white mb-4">No program draft</h2>
        <button
          onClick={() => navigate(`/coach/student/${id}/fms`)}
          className="px-6 py-3 bg-lime-400 text-black font-bold rounded-xl"
        >
          Start Assessment
        </button>
      </div>
    );
  }

  const commitPlan = (nextPlan) => {
    setDirty(true);
    setProgram((prev) => ({ ...prev, coach_plan: nextPlan, ...nextPlan }));
  };

  const updateItem = (block, itemIdx, patch) => {
    const next = structuredClone(plan);
    const current = next.days[dayIdx].blocks[block][itemIdx];
    next.days[dayIdx].blocks[block][itemIdx] = applyPatch(current, patch);
    commitPlan(next);
  };

  const updateCalendar = (idx, done) => {
    const next = structuredClone(plan);
    next.calendar[idx] = { ...next.calendar[idx], done };
    commitPlan(next);
  };

  const reorderCalendar = (fromIdx, toIdx) => {
    const next = structuredClone(plan);
    next.calendar = reorderCalendarCells(next.calendar, fromIdx, toIdx);
    commitPlan(next);
    setCalIdx((current) => {
      if (current === fromIdx) return toIdx;
      if (fromIdx < toIdx && current > fromIdx && current <= toIdx) return current - 1;
      if (fromIdx > toIdx && current >= toIdx && current < fromIdx) return current + 1;
      return current;
    });
  };

  const swapExercise = async (block, itemIdx, candidate) => {
    const item = plan.days[dayIdx].blocks[block][itemIdx];
    const next = structuredClone(plan);
    next.days[dayIdx].blocks[block][itemIdx] = applyPatch(item, {
      exercise_id: candidate.exercise_id,
      name: candidate.name,
    });
    commitPlan(next);
    if (!programId) return;
    setSaving(true);
    try {
      const updated = await reviewProgram(id, programId, {
        event_type: "replace_exercise",
        payload: { out_id: item.exercise_id, in_id: candidate.exercise_id, slot: block },
        coach_plan: next,
      });
      setProgram(updated);
      setDirty(false);
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const saveEdits = async () => {
    if (!programId) return;
    setSaving(true);
    try {
      const updated = await reviewProgram(id, programId, {
        event_type: "edit_prescription",
        payload: {},
        coach_plan: plan,
      });
      setProgram(updated);
      setDirty(false);
      setMessage("Draft saved.");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const decide = async (event_type) => {
    if (!programId) return;
    setSaving(true);
    try {
      const updated = await reviewProgram(id, programId, {
        event_type,
        payload: {},
        coach_plan: plan,
      });
      setProgram(updated);
      setDirty(false);
      if (event_type === "approve_as_is") navigate(`/coach/student/${id}`);
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const candidatesFor = (item) => {
    const map = program?.candidate_exercises || plan?.candidate_exercises || {};
    return map[item.exercise_id] || map[`unfilled:${item.section}:${item.role}`] || [];
  };

  const status = (program?.status || "draft").replace("_", " ");

  return (
    <div className="px-4 md:px-6 py-5 md:py-8 pb-32 md:pb-36 max-w-[1120px] mx-auto">
      <div className="flex items-center justify-between mb-5">
        <button
          onClick={() => navigate(`/coach/student/${id}`)}
          className="flex items-center gap-2 text-zinc-400 hover:text-white text-sm min-h-11"
        >
          <ArrowLeft className="w-4 h-4" />
          Profile
        </button>
        <button
          onClick={() => navigate("/coach/dashboard")}
          className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-zinc-800 rounded-lg text-sm min-h-11"
        >
          <Home className="w-4 h-4" /> Dashboard
        </button>
      </div>

      {plan.referral && (
        <div className="mb-6 p-4 rounded-2xl border border-red-500/30 bg-red-500/10 text-red-200 text-sm">
          Pain / score 0. No loaded mains. {plan.needs_summary}
        </div>
      )}

      <header className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="text-[10px] uppercase tracking-[0.2em] px-2 py-1 rounded-full bg-white/8 text-zinc-400">
            {status}
          </span>
          <span className="text-[10px] uppercase tracking-[0.2em] px-2 py-1 rounded-full bg-lime-400/15 text-lime-300">
            {plan.week_type || "build"}
          </span>
          {dirty && (
            <span className="text-[10px] uppercase tracking-[0.2em] px-2 py-1 rounded-full bg-amber-400/15 text-amber-200">
              Unsaved
            </span>
          )}
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-2 leading-tight">{plan.week_title}</h1>
        <p className="text-zinc-400 max-w-2xl text-sm md:text-base leading-relaxed">{plan.needs_summary}</p>
        {snapshotLine(plan.athlete_snapshot) && (
          <p className="text-xs text-zinc-500 mt-2 max-w-2xl">
            Snapshot at generate · {snapshotLine(plan.athlete_snapshot)}
          </p>
        )}
        {plan.mesocycle && (
          <div className="flex flex-wrap gap-2 mt-4">
            {Array.from({ length: plan.mesocycle.length || 4 }, (_, i) => i + 1).map((week) => {
              const phase = (plan.mesocycle.phases || [])[week - 1] || "";
              const current = (plan.week_index || 1) === week;
              return (
                <button
                  key={week}
                  onClick={async () => {
                    if (!plan.block_id) return;
                    const row = await getBlockWeek(id, plan.block_id, week);
                    navigate(`/coach/student/${id}/program/${row.id}`);
                  }}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium capitalize ${
                    current ? "bg-lime-400 text-black" : "bg-white/8 text-zinc-400 hover:text-white"
                  }`}
                >
                  Week {week}
                  {phase ? ` · ${phase}` : ""}
                </button>
              );
            })}
            {plan.mesocycle.retest_due && (
              <button
                onClick={() => navigate(`/coach/student/${id}/fms`)}
                className="px-3 py-1.5 rounded-full text-xs bg-amber-400/20 text-amber-200"
              >
                Retest due
              </button>
            )}
          </div>
        )}
      </header>

      <WeekStrip
        plan={plan}
        selectedIdx={calIdx}
        onSelect={(idx) => setCalIdx(idx)}
        onToggleDone={updateCalendar}
        onReorder={reorderCalendar}
        editable
      />

      {Boolean(activeDay) && (!calendar.length || !selectedCell || isTrainingKind(selectedCell.kind)) ? (
        calendar.length ? (
          <SessionBoard
            plan={plan}
            day={activeDay}
            editable
            candidatesFor={candidatesFor}
            onPatch={updateItem}
            onSwap={swapExercise}
          />
        ) : (
          <div className="space-y-8">
            {days.map((day) => (
              <SessionBoard
                key={day.day}
                plan={plan}
                day={day}
                editable
                candidatesFor={candidatesFor}
                onPatch={updateItem}
                onSwap={swapExercise}
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
        <p className="text-amber-200/80 text-sm mt-4">This program has no session days yet.</p>
      )}

      {message && <p className="text-sm text-zinc-400 mt-4">{message}</p>}

      <div className="fixed bottom-4 left-4 right-4 z-20">
        <div className="max-w-[1120px] mx-auto flex flex-wrap items-center gap-2 p-2.5 rounded-2xl bg-[#0a0a0a]/95 backdrop-blur-md border border-white/10 shadow-2xl">
          <button
            disabled={saving || plan.referral}
            onClick={() => decide("approve_as_is")}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-lime-400 text-black font-bold disabled:opacity-40"
          >
            <Check className="w-4 h-4" /> Approve
          </button>
          <button
            disabled={saving}
            onClick={saveEdits}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 font-medium"
          >
            <RefreshCw className="w-4 h-4" />
            Save{dirty ? " *" : ""}
          </button>
          <div className="relative">
            <button
              onClick={() => setExportOpen((v) => !v)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 font-medium"
            >
              <Download className="w-4 h-4" /> Export
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
            {exportOpen && (
              <div className="absolute bottom-full mb-2 left-0 min-w-[180px] rounded-xl border border-white/10 bg-[#111] p-1 shadow-xl">
                <button
                  className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-white/5"
                  onClick={() => {
                    exportCsv(plan);
                    setExportOpen(false);
                  }}
                >
                  CSV
                </button>
                <button
                  className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-white/5"
                  onClick={() => {
                    downloadExport(id, programId, "xlsx");
                    setExportOpen(false);
                  }}
                >
                  Excel / Sheets
                </button>
                <button
                  className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-white/5 flex items-center gap-2"
                  onClick={() => {
                    window.print();
                    setExportOpen(false);
                  }}
                >
                  <Printer className="w-3.5 h-3.5" /> Print / PDF
                </button>
              </div>
            )}
          </div>
          <button
            disabled={saving || !programId || program?.status !== "approved"}
            onClick={async () => {
              const share = await createShare(id, programId);
              const url = `${window.location.origin}${share.url_path}`;
              setShareUrl(url);
              await navigator.clipboard.writeText(url);
              setMessage("Share link copied");
            }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 font-medium disabled:opacity-40"
          >
            <Share2 className="w-4 h-4" /> Share
          </button>
          <button
            disabled={saving}
            onClick={() => decide("reject_session")}
            className="ml-auto flex items-center gap-2 px-4 py-2.5 rounded-xl text-red-300 hover:bg-red-500/10"
          >
            <X className="w-4 h-4" /> Reject
          </button>
        </div>
        {shareUrl && (
          <p className="max-w-[1120px] mx-auto mt-2 text-[11px] text-zinc-500 break-all px-2">{shareUrl}</p>
        )}
      </div>
    </div>
  );
};
