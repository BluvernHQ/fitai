import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Activity,
  History,
  ChevronRight,
  BarChart,
} from "lucide-react";
import { getStudent, getLiftMaxHistory, updateStudent, getStudentWorkouts } from "../api/backend";

const LIFT_KEYS = ["back_squat", "deadlift", "bench_press", "row"];
const SOURCE_OPTIONS = [
  { id: "coach", label: "Coach" },
  { id: "test", label: "Test" },
  { id: "estimated", label: "Estimated" },
];

function formatLift(key) {
  return String(key || "").replaceAll("_", " ");
}

function formatWhen(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

const KIT_OPTIONS = [
  "bodyweight",
  "band",
  "dumbbell",
  "kettlebell",
  "barbell",
  "trap_bar",
  "cable",
  "trx",
  "box",
  "medball",
  "landmine",
  "wall",
];

export const StudentProfile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [maxes, setMaxes] = useState({
    back_squat: "",
    deadlift: "",
    bench_press: "",
    row: "",
  });
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("male");
  const [injuries, setInjuries] = useState("");
  const [days, setDays] = useState(3);
  const [kit, setKit] = useState([]);
  const [saving, setSaving] = useState(false);
  const [saveNote, setSaveNote] = useState(null);
  const [liftSource, setLiftSource] = useState("coach");
  const [liftHistory, setLiftHistory] = useState([]);

  const [latestDraft, setLatestDraft] = useState(null);
  const [retestDue, setRetestDue] = useState(false);

  const loadHistory = () =>
    getLiftMaxHistory(id)
      .then((data) => setLiftHistory(data?.history || []))
      .catch(() => setLiftHistory([]));

  useEffect(() => {
    getStudent(id)
      .then((data) => {
        setStudent(data);
        setName(data.name || "");
        setAge(data.age ?? "");
        setGender(data.gender || "male");
        setInjuries(data.injuries || "");
        setDays(data.days_per_week || 3);
        setKit(Array.isArray(data.equipment) ? data.equipment : []);
        setMaxes({
          back_squat: data.lift_maxes?.back_squat || "",
          deadlift: data.lift_maxes?.deadlift || "",
          bench_press: data.lift_maxes?.bench_press || "",
          row: data.lift_maxes?.row || "",
        });
      })
      .catch((err) => console.error("Failed to load student", err))
      .finally(() => setLoading(false));
    loadHistory();
    getStudentWorkouts(id)
      .then((rows) => {
        const draft = (rows || []).find((r) => r.status === "draft");
        setLatestDraft(draft || (rows || [])[0] || null);
        setRetestDue(Boolean((rows || []).some((r) => r.mesocycle?.retest_due)));
      })
      .catch(() => {});
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 text-zinc-500">Loading...</div>
    );
  }

  if (!student) {
    return (
      <div className="flex items-center justify-center py-24 text-zinc-500">
        Student not found.
      </div>
    );
  }

  return (
    <div className="px-4 md:px-6 py-5 md:py-10 pb-8">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate("/coach/dashboard")}
          className="flex items-center gap-2 text-zinc-500 hover:text-white mb-5 min-h-11 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setSaving(true);
            setSaveNote(null);
            try {
              const trimmed = name.trim();
              if (!trimmed) {
                setSaveNote("Name is required.");
                setSaving(false);
                return;
              }
              const lift_maxes = Object.fromEntries(
                Object.entries(maxes)
                  .filter(([, v]) => v !== "" && v != null)
                  .map(([k, v]) => [k, Number(v)]),
              );
              const updated = await updateStudent(id, {
                name: trimmed,
                age: age === "" || age == null ? null : Number(age),
                gender,
                injuries,
                days_per_week: Number(days),
                equipment: kit,
                lift_maxes,
                lift_max_source: liftSource,
              });
              setStudent(updated);
              setName(updated.name || trimmed);
              setAge(updated.age ?? "");
              setGender(updated.gender || gender);
              setInjuries(updated.injuries || "");
              await loadHistory();
              setSaveNote("Saved. Name, age, and notes update now. Days, kit, and 1RMs apply on the next generate.");
            } finally {
              setSaving(false);
            }
          }}
        >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900/50 border border-white/5 rounded-3xl p-5 md:p-8 mb-6"
        >
          <div className="flex flex-col gap-5">
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 mb-3">Athlete details</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="text-xs uppercase tracking-widest text-zinc-400">Name</label>
                  <input
                    type="text"
                    autoComplete="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="mt-2 w-full bg-black/40 border border-white/15 rounded-xl px-4 py-3.5 text-white"
                  />
                </div>
                <div>
                  <label className="text-xs uppercase tracking-widest text-zinc-400">Age</label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    inputMode="numeric"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    className="mt-2 w-full bg-black/40 border border-white/15 rounded-xl px-4 py-3.5 text-white"
                  />
                </div>
                <div>
                  <label className="text-xs uppercase tracking-widest text-zinc-400">Gender</label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="mt-2 w-full bg-black/40 border border-white/15 rounded-xl px-4 py-3.5 text-white appearance-none"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="text-xs uppercase tracking-widest text-zinc-400">
                    Injuries / notes
                  </label>
                  <textarea
                    rows={3}
                    value={injuries}
                    onChange={(e) => setInjuries(e.target.value)}
                    placeholder="Optional. Coach notes for this athlete."
                    className="mt-2 w-full bg-black/40 border border-white/15 rounded-xl px-4 py-3.5 text-white resize-y min-h-[5.5rem]"
                  />
                </div>
                <button
                  type="submit"
                  disabled={saving}
                  className="md:col-span-2 min-h-12 py-3 rounded-xl bg-white/10 font-medium"
                >
                  {saving ? "Saving..." : "Save athlete details"}
                </button>
                {saveNote && (
                  <p className="md:col-span-2 text-sm text-lime-300/90">{saveNote}</p>
                )}
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={() =>
                  navigate(`/coach/student/${id}/fms`, {
                    state: { studentName: name || student.name },
                  })
                }
                className="w-full min-h-12 py-3 px-6 rounded-xl bg-lime-400 text-black font-bold hover:bg-lime-300 transition-colors flex items-center justify-center gap-2"
              >
                <Activity className="w-4 h-4" />
                {retestDue ? "Retest now" : "New Assessment"}
              </button>
              {latestDraft?.id && (
                <button
                  type="button"
                  onClick={() => navigate(`/coach/student/${id}/program/${latestDraft.id}`)}
                  className="w-full min-h-12 py-3 px-6 rounded-xl bg-white/10 font-medium"
                >
                  Open latest program
                </button>
              )}
            </div>
          </div>
        </motion.div>

        <div className="mb-6 p-5 md:p-6 rounded-3xl bg-white/3 border border-white/5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <h2 className="text-lg font-semibold text-white">Plan inputs</h2>
            <p className="text-sm text-zinc-400 mt-1">
              Days, kit, and 1RMs feed the next generate. Saving does not rewrite an already generated week.
            </p>
          </div>
          <div>
            <label className="text-xs uppercase tracking-widest text-zinc-500">
              Days / week
            </label>
            <input
              type="number"
              min="2"
              max="6"
              inputMode="numeric"
              value={days}
              onChange={(e) => setDays(e.target.value)}
              className="mt-2 w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3.5"
            />
          </div>
          <div className="md:col-span-2">
            <label className="text-xs uppercase tracking-widest text-zinc-500">
              Equipment — leave empty for bodyweight / band only
            </label>
            <div className="mt-3 flex flex-wrap gap-2">
              {KIT_OPTIONS.map((item) => {
                const on = kit.includes(item);
                return (
                  <button
                    key={item}
                    type="button"
                    onClick={() =>
                      setKit((prev) =>
                        prev.includes(item) ? prev.filter((x) => x !== item) : [...prev, item],
                      )
                    }
                    className={`min-h-10 px-3.5 py-2 rounded-full text-xs capitalize border ${
                      on
                        ? "bg-lime-400 text-black border-lime-400"
                        : "bg-white/5 text-zinc-400 border-white/10 hover:text-white"
                    }`}
                  >
                    {item.replace("_", " ")}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="md:col-span-2">
            <label className="text-xs uppercase tracking-widest text-zinc-500">
              1RM source for this save
            </label>
            <div className="mt-3 flex flex-wrap gap-2">
              {SOURCE_OPTIONS.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => setLiftSource(option.id)}
                  className={`min-h-10 px-3.5 py-2 rounded-full text-xs border ${
                    liftSource === option.id
                      ? "bg-lime-400 text-black border-lime-400"
                      : "bg-white/5 text-zinc-400 border-white/10 hover:text-white"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          {LIFT_KEYS.map((lift) => (
            <div key={lift}>
              <label className="text-xs uppercase tracking-widest text-zinc-500">
                {formatLift(lift)} 1RM (kg)
              </label>
              <input
                type="number"
                inputMode="decimal"
                value={maxes[lift]}
                onChange={(e) =>
                  setMaxes((prev) => ({ ...prev, [lift]: e.target.value }))
                }
                className="mt-2 w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3.5"
              />
            </div>
          ))}
          <button
            type="submit"
            disabled={saving}
            className="md:col-span-2 min-h-12 py-3 rounded-xl bg-white/10 font-medium"
          >
            {saving ? "Saving..." : "Save profile & 1RMs"}
          </button>
          {saveNote && (
            <p className="md:col-span-2 text-sm text-lime-300/90">{saveNote}</p>
          )}
        </div>
        </form>

        <div className="mb-6 p-5 md:p-6 rounded-3xl bg-white/3 border border-white/5">
          <h2 className="text-lg font-semibold text-white">1RM log</h2>
          <p className="text-sm text-zinc-400 mt-1 mb-4">
            Strength history lives here. Progress History still holds FMS screens and workouts only.
          </p>
          {liftHistory.length === 0 ? (
            <p className="text-sm text-zinc-500">No 1RM changes logged yet. Save a new number to start the log.</p>
          ) : (
            <ul className="space-y-2">
              {liftHistory.map((row) => (
                <li
                  key={row.id || `${row.lift_key}-${row.recorded_at}`}
                  className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 text-sm border-b border-white/5 pb-2"
                >
                  <span className="text-white capitalize">{formatLift(row.lift_key)}</span>
                  <span className="text-zinc-300">
                    {row.previous_one_rm != null ? `${row.previous_one_rm} → ` : ""}
                    {row.one_rm} kg
                    <span className="text-zinc-500"> · {row.source || "coach"}</span>
                  </span>
                  <span className="text-zinc-500 text-xs">{formatWhen(row.recorded_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-6">
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            onClick={() => navigate(`/coach/student/${id}/progress`)}
            className="group relative min-h-28 md:h-48 rounded-3xl bg-white/3 border border-white/5 p-5 md:p-8 text-left hover:bg-white/5 transition-all overflow-hidden"
          >
            <div className="relative z-10 h-full flex items-center justify-between md:flex-col md:items-start md:justify-between gap-4">
              <div className="p-3 bg-white/5 w-fit rounded-xl group-hover:bg-lime-400/20 group-hover:text-lime-400 transition-colors">
                <History className="w-6 h-6" />
              </div>
              <div className="flex-1 md:flex-none">
                <h3 className="text-lg md:text-xl font-bold text-white mb-0.5">
                  Assessment History
                </h3>
                <p className="text-zinc-400 text-sm">View past results & trends</p>
              </div>
              <ChevronRight className="w-5 h-5 text-zinc-500 md:hidden" />
            </div>
          </motion.button>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="min-h-24 md:h-48 rounded-3xl bg-white/3 border border-white/5 p-5 md:p-8 flex items-center md:flex-col md:justify-center md:items-center text-left md:text-center gap-4 opacity-50"
          >
            <BarChart className="w-7 h-7 text-zinc-600 shrink-0" />
            <div>
              <h3 className="text-lg font-bold text-zinc-500">Analytics</h3>
              <p className="text-xs text-zinc-600">Coming Soon</p>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};
