import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import {
  ChevronLeft,
  ChevronRight,
  Activity,
  AlertCircle,
  ArrowLeft,
  MessageSquare,
} from "lucide-react";
import fmsData from "../data/fms-v1.json";
import { submitFMSAssessment } from "../api/fms";
import { getFmsSpec } from "../api/backend";
import { QUALITY_KEYS, isQualityKey, scoreMovement, stampComputedScores } from "../lib/fmsScore";

const shortLabel = (movement) =>
  (movement.short_label || movement.label.split("(")[0] || movement.label).trim();

const chipsFromMovement = (movement) => {
  if (movement.comment_chips?.length) return movement.comment_chips;
  return (movement.sections || [])
    .flatMap((section) => section.observations || [])
    .filter((obs) => obs?.label && !QUALITY_KEYS.has(obs.key) && obs.polarity !== "quality")
    .map((obs) => obs.label)
    .slice(0, 5);
};

const placeholderFromMovement = (movement) => {
  if (movement.comment_placeholder) return movement.comment_placeholder;
  const chips = chipsFromMovement(movement);
  return chips.length
    ? `e.g. ${chips.slice(0, 3).join("; ")}.`
    : "Note side, where it failed, and the main compensation.";
};

const officialScore = (movement, data = {}) =>
  scoreMovement(movement?.id, data).score;

const scoreClass = (score) => {
  if (score === 0) return "bg-red-500 text-white";
  if (score === 1) return "bg-amber-400 text-black";
  if (score === 2) return "bg-zinc-200 text-black";
  return "bg-lime-400 text-black";
};

// Helper to create the EXACT payload structure required by backend
const createInitialState = () => {
    const state = {
      use_manual_scores: false,
    };

    fmsData.movements.forEach((m) => {
      state[m.id] = {
        score: 2,
        comment: "",
        ...(m.score_config?.type === "asymmetrical" && {
          l_score: 2,
          r_score: 2,
        }),
      ...(m.score_config?.clearing_test && { clearing_pain: false }),
      ...(!m.score_config?.clearing_test && { pain: false }),
    };

    // Initialize Sections
    m.sections.forEach((s) => {
      state[m.id][s.id] = {};
      s.observations.forEach((o) => {
        state[m.id][s.id][o.key] = 0; // Default to 0 (integer)
      });
    });
  });

  return state;
};

export const FMSAssessment = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const studentName = location.state?.studentName || "Student";
  const storageKey = `fms_state_${id}`;

  // 1. Initialize State with Full Schema (Persisted)
  const [payload, setPayload] = useState(() => {
    try {
      const saved = sessionStorage.getItem(storageKey);
      return saved ? JSON.parse(saved) : createInitialState();
    } catch (e) {
      console.error("Failed to load FMS state", e);
      return createInitialState();
    }
  });

  const [spec, setSpec] = useState(fmsData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [expandedMovement, setExpandedMovement] = useState(
    fmsData.movements[0].id,
  );
  const stickyRef = useRef(null);
  const cardRefs = useRef({});
  const shouldScrollRef = useRef(false);

  const scrollSectionToTop = (movementId) => {
    const el = cardRefs.current[movementId];
    const sticky = stickyRef.current;
    if (!el) {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      return;
    }
    const offset = (sticky?.getBoundingClientRect().bottom ?? 0) + 8;
    const top = el.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top: Math.max(0, top), left: 0, behavior: "auto" });
  };

  useEffect(() => {
    getFmsSpec()
      .then((data) => {
        if (data?.movements?.length) setSpec(data);
      })
      .catch(() => {});
  }, []);

  const movements = spec?.movements?.length ? spec.movements : fmsData.movements;

  // Persist functionality
  useEffect(() => {
    sessionStorage.setItem(storageKey, JSON.stringify(payload));
  }, [payload, storageKey]);

  // 2. State Update Logic (Deeply Nested)
  const updateObservation = (movementId, sectionId, key, value) => {
    setPayload((prev) => {
      const current = { ...(prev[movementId]?.[sectionId] || {}), [key]: value };
      if (value > 0) {
        const quality = isQualityKey(key);
        Object.keys(current).forEach((other) => {
          if (other === key) return;
          if (isQualityKey(other) !== quality) current[other] = 0;
        });
      }
      return {
        ...prev,
        [movementId]: {
          ...prev[movementId],
          [sectionId]: current,
        },
      };
    });
  };

  const updateTopLevel = (movementId, key, value) => {
    setPayload((prev) => {
      const next = { ...prev[movementId], [key]: value };
      if ((key === "clearing_pain" || key === "pain") && value) {
        next.score = 0;
        if ("l_score" in next) next.l_score = 0;
        if ("r_score" in next) next.r_score = 0;
      }
      return { ...prev, [movementId]: next };
    });
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      // 4. Submit Exact Payload from State
      // Reconstruct payload to ensure key order matches specific requirement (use_manual_scores last)
      const stamped = stampComputedScores(payload, movements);
      const orderedPayload = {
        student_id: id,
        ...stamped,
        use_manual_scores: false,
      };

      console.log("Submitting Payload (Exact Match):", orderedPayload);
      const result = await submitFMSAssessment(orderedPayload);

      sessionStorage.removeItem(storageKey);

      const dest = result?.id
        ? `/coach/student/${id}/program/${result.id}`
        : `/coach/student/${id}/workout/current`;
      navigate(dest, {
        state: {
          workout: result,
          programId: result.id,
          assessmentId: result.assessment_id,
        },
      });
    } catch (err) {
      console.error("Submission failed:", err);
      // 5. Professional Error Handling
      if (err.message?.includes("500") || err.status === 500) {
        setErrorMsg(
          "Workout generation unavailable directly. Try again later.",
        );
      } else {
        setErrorMsg("An error occurred during submission. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const movementIndex = movements.findIndex(
    (m) => m.id === expandedMovement,
  );
  const scores = movements.map((m) => officialScore(m, payload[m.id]));
  const totalScore = scores.reduce((sum, n) => sum + n, 0);
  const painFlags = movements.filter((m) => {
    const data = payload[m.id] || {};
    return officialScore(m, data) === 0 || data.clearing_pain || data.pain === true;
  });
  const commented = movements.filter(
    (m) => (payload[m.id]?.comment || "").trim().length > 0,
  ).length;

  const openMovement = (movementId) => {
    if (!movementId) return;
    shouldScrollRef.current = true;
    setExpandedMovement(movementId);
  };

  const goMovement = (delta) => {
    const next = movementIndex + delta;
    if (next < 0 || next >= movements.length) return;
    openMovement(movements[next].id);
  };

  useEffect(() => {
    if (!shouldScrollRef.current || !expandedMovement) return;
    const run = () => scrollSectionToTop(expandedMovement);
    run();
    const frame = requestAnimationFrame(run);
    const timer = window.setTimeout(() => {
      shouldScrollRef.current = false;
      run();
    }, 50);
    return () => {
      cancelAnimationFrame(frame);
      window.clearTimeout(timer);
    };
  }, [expandedMovement]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="text-white"
    >
      <div className="relative z-10 px-4 md:px-6 pb-28 md:pb-16 max-w-5xl mx-auto">
        <div
          ref={stickyRef}
          className="sticky top-[calc(3.5rem+env(safe-area-inset-top,0px))] z-40 -mx-4 md:-mx-6 px-4 md:px-6 py-3 mb-4 bg-[#050505]/92 backdrop-blur-md border-b border-white/10"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <button
                onClick={() => navigate(`/coach/student/${id}`)}
                className="flex items-center gap-2 text-zinc-500 hover:text-white mb-1 transition-colors text-sm font-medium min-h-10"
              >
                <ArrowLeft className="w-4 h-4" />
                Athlete
              </button>
              <h1 className="text-xl md:text-2xl font-bold text-white mb-0.5">FMS screen</h1>
              <div className="flex flex-wrap items-center gap-2 text-xs md:text-sm text-zinc-400">
                <span className="flex items-center gap-1.5 truncate">
                  <Activity className="w-4 h-4 text-lime-400 shrink-0" />
                  {studentName}
                </span>
                <span className="w-1 h-1 rounded-full bg-zinc-600" />
                <span>{commented}/{movements.length} notes</span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <div
                className={`min-w-[72px] rounded-2xl px-3 py-2 text-center ${
                  painFlags.length
                    ? "bg-red-500/15 border border-red-500/30"
                    : "bg-white/5 border border-white/10"
                }`}
              >
                <p className="text-[10px] uppercase tracking-widest text-zinc-500">Total</p>
                <p className="text-xl font-bold tabular-nums">
                  {totalScore}
                  <span className="text-sm text-zinc-500 font-medium">/21</span>
                </p>
              </div>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className={`hidden md:inline-flex px-5 py-3 rounded-xl text-sm font-bold transition-all ${
                  !isSubmitting
                    ? "bg-lime-400 text-black hover:bg-lime-300"
                    : "bg-white/5 text-zinc-500 cursor-not-allowed"
                }`}
              >
                {isSubmitting ? "Building week..." : "Generate week"}
              </button>
            </div>
          </div>

          <div className="mt-3 flex gap-2 overflow-x-auto snap-strip no-scrollbar -mx-4 px-4 md:mx-0 md:px-0 md:grid md:grid-cols-7 md:overflow-visible">
            {movements.map((movement, idx) => {
              const score = scores[idx];
              const active = expandedMovement === movement.id;
              return (
                <button
                  key={movement.id}
                  onClick={() => openMovement(movement.id)}
                  className={`snap-start shrink-0 w-[4.75rem] md:w-auto rounded-xl px-1 py-2 text-center border transition-all ${
                    active
                      ? "border-lime-400/50 bg-lime-400/10"
                      : "border-white/5 bg-white/3 hover:border-white/15"
                  }`}
                >
                  <span
                    className={`mx-auto mb-1 flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-bold ${scoreClass(score)}`}
                  >
                    {score}
                  </span>
                  <span className="block text-[10px] text-zinc-400 truncate">
                    {shortLabel(movement)}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {painFlags.length > 0 && (
          <div className="mb-6 bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-start gap-3 text-red-300">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold">Pain / clearing fail</p>
              <p className="text-xs text-red-200/80 mt-1">
                {painFlags.map((m) => shortLabel(m)).join(", ")} — no loaded mains will be prescribed.
              </p>
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="mb-6 bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <p className="text-sm font-medium">{errorMsg}</p>
          </div>
        )}

        <div className="space-y-3 pb-4">
          {movements
            .filter((movement) => movement.id === (expandedMovement || movements[0]?.id))
            .map((movement) => {
            const idx = movements.findIndex((m) => m.id === movement.id);
            const movementData = payload[movement.id];
            const scored = scoreMovement(movement.id, movementData);
            const score = scored.score;
            const hasComment = Boolean((movementData.comment || "").trim());
            const isPain = score === 0 || movementData.clearing_pain || movementData.pain;

            return (
              <div
                key={movement.id}
                ref={(node) => {
                  cardRefs.current[movement.id] = node;
                }}
                className={`rounded-2xl border ${
                  isPain
                    ? "border-red-500/30 bg-red-500/5"
                    : "bg-white/3 border-lime-400/25"
                }`}
              >
                <div className="w-full flex items-center justify-between gap-3 p-3.5 md:p-5 text-left min-h-14">
                  <div className="flex items-center gap-3 min-w-0">
                    <span
                      className={`shrink-0 flex h-10 w-10 items-center justify-center rounded-xl text-base font-bold ${scoreClass(score)}`}
                    >
                      {score}
                    </span>
                    <div className="min-w-0">
                      <p className="text-[10px] uppercase tracking-widest text-zinc-500">
                        Screen {idx + 1} / {movements.length}
                      </p>
                      <h3 className="text-base md:text-lg font-medium truncate">
                        {movement.label}
                      </h3>
                      {movement.score_config?.type === "asymmetrical" && (
                        <p className="text-xs text-zinc-500 mt-0.5">
                          L {scored.l_score} · R {scored.r_score}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {hasComment && (
                      <MessageSquare className="w-4 h-4 text-lime-400" />
                    )}
                    {isPain && (
                      <span className="text-[10px] font-bold uppercase tracking-widest text-red-400">
                        Pain
                      </span>
                    )}
                  </div>
                </div>

                <div className="border-t border-white/5">
                  <div className="p-4 md:p-6 pt-2 space-y-6 md:space-y-8">
                        <div className="rounded-xl border border-white/8 bg-black/30 p-4">
                          <div className="flex flex-wrap items-end gap-6">
                            <div>
                              <p className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-2">
                                Official score
                              </p>
                              <span
                                className={`inline-flex h-11 w-11 items-center justify-center rounded-xl text-lg font-bold ${scoreClass(scored.score)}`}
                              >
                                {scored.score}
                              </span>
                            </div>
                            {movement.score_config?.type === "asymmetrical" && (
                              <div className="flex gap-6">
                                {[
                                  ["Left", scored.l_score],
                                  ["Right", scored.r_score],
                                ].map(([label, value]) => (
                                  <div key={label}>
                                    <p className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-2">
                                      {label}
                                    </p>
                                    <span className="inline-flex h-10 min-w-10 items-center justify-center rounded-lg bg-white/8 text-sm font-bold text-white">
                                      {value}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                          <p className="text-[11px] text-zinc-600 mt-3">
                            {scored.source === "pain"
                              ? "Pain / clearing fail"
                              : scored.source === "faults"
                                ? "From faults marked below"
                                : scored.source === "quality"
                                  ? "Clean pattern from observations"
                                  : "Mark observations to score"}
                          </p>
                        </div>
                        <div>
                          <div className="flex items-end justify-between gap-3 mb-2">
                            <div>
                              <p className="text-xs font-bold tracking-widest text-zinc-500 uppercase">
                                Assessor comment
                              </p>
                              <p className="text-[11px] text-zinc-600 mt-1">
                                Capture side, where it failed, and the main
                                compensation. “Left” / “Right” sets L vs R.
                              </p>
                            </div>
                            {(movementData.comment || "").length > 0 && (
                              <span className="text-[10px] text-zinc-600 font-mono">
                                {(movementData.comment || "").length}/280
                              </span>
                            )}
                          </div>
                          <textarea
                            value={movementData.comment || ""}
                            onChange={(e) =>
                              updateTopLevel(
                                movement.id,
                                "comment",
                                e.target.value.slice(0, 280),
                              )
                            }
                            placeholder={placeholderFromMovement(movement)}
                            className="w-full min-h-[88px] bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-base text-white placeholder:text-zinc-600 focus:outline-none focus:border-lime-400/40"
                          />
                          {chipsFromMovement(movement).length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-2">
                              {chipsFromMovement(movement).map(
                                (chip) => {
                                  const active = (movementData.comment || "")
                                    .toLowerCase()
                                    .includes(chip.toLowerCase());
                                  return (
                                    <button
                                      key={chip}
                                      type="button"
                                      onClick={() => {
                                        const current =
                                          movementData.comment || "";
                                        if (
                                          current
                                            .toLowerCase()
                                            .includes(chip.toLowerCase())
                                        ) {
                                          return;
                                        }
                                        const next = current.trim()
                                          ? `${current.trim()}; ${chip}`
                                          : chip;
                                        updateTopLevel(
                                          movement.id,
                                          "comment",
                                          next.slice(0, 280),
                                        );
                                      }}
                                      className={`text-[11px] min-h-9 px-3 py-1.5 rounded-full border transition-colors ${
                                        active
                                          ? "border-lime-400/40 bg-lime-400/10 text-lime-300"
                                          : "border-white/10 text-zinc-400 hover:border-white/25 hover:text-white"
                                      }`}
                                    >
                                      {chip}
                                    </button>
                                  );
                                },
                              )}
                            </div>
                          )}
                        </div>
                        {/* ── PAIN CLEARING ONLY (Top Level) ── */}
                        <div
                          className={`rounded-xl p-5 border mb-2 ${
                            movementData.clearing_pain || movementData.pain
                              ? "bg-red-500/10 border-red-500/30"
                              : "bg-black/40 border-white/5"
                          }`}
                        >
                          <label className="flex items-center gap-3 cursor-pointer group">
                            <input
                              type="checkbox"
                              checked={
                                !!(movement.score_config?.clearing_test
                                  ? movementData.clearing_pain
                                  : movementData.pain)
                              }
                              onChange={(e) =>
                                updateTopLevel(
                                  movement.id,
                                  movement.score_config?.clearing_test
                                    ? "clearing_pain"
                                    : "pain",
                                  e.target.checked,
                                )
                              }
                              className="w-5 h-5 rounded bg-zinc-800 border-zinc-600 text-red-500 focus:ring-red-400 focus:ring-offset-black"
                            />
                            <span
                              className={`text-sm ${
                                movementData.clearing_pain || movementData.pain
                                  ? "text-red-300 font-semibold"
                                  : "text-zinc-300 group-hover:text-white"
                              }`}
                            >
                              {movement.score_config?.clearing_label ||
                                "Pain on this screen"}
                            </span>
                          </label>
                        </div>

                        {/* ── SECTIONS & OBSERVATIONS ── */}
                        {movement.sections.map((section) => (
                          <div key={section.id}>
                            <h4 className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-4 pl-2 border-l-2 border-lime-400/20">
                              {section.label}
                            </h4>
                            <div className="space-y-3">
                              {section.observations.map((obs) => {
                                const currentVal =
                                  movementData[section.id][obs.key];
                                // Default range 0-1 (No/Yes)
                                const range = obs.score_range || [0, 1];

                                return (
                                  <div
                                    key={obs.key}
                                    className="flex items-center justify-between gap-3 p-3 md:p-4 rounded-xl bg-black/40 border border-white/5 hover:border-white/10 transition-colors"
                                  >
                                    <span className="text-zinc-300 text-sm font-medium min-w-0">
                                      {obs.label}
                                    </span>

                                    <div className="flex items-center gap-1 bg-black/40 p-1 rounded-lg border border-white/5 shrink-0">
                                      {range.map((val) => (
                                        <button
                                          key={val}
                                          onClick={() =>
                                            updateObservation(
                                              movement.id,
                                              section.id,
                                              obs.key,
                                              val,
                                            )
                                          }
                                          className={`min-h-11 min-w-11 rounded-md text-sm font-bold transition-all duration-200 ${
                                            currentVal === val
                                              ? "bg-zinc-100 text-black scale-105"
                                              : "text-zinc-600 hover:text-white hover:bg-white/5"
                                          }`}
                                        >
                                          {val}
                                        </button>
                                      ))}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        ))}
                        <div className="flex items-center justify-between pt-2">
                          <button
                            type="button"
                            disabled={idx === 0}
                            onClick={() => goMovement(-1)}
                            className="flex items-center gap-1 min-h-11 px-2 text-sm text-zinc-400 hover:text-white disabled:opacity-30"
                          >
                            <ChevronLeft className="w-4 h-4" /> Previous
                          </button>
                          <button
                            type="button"
                            disabled={idx === movements.length - 1}
                            onClick={() => goMovement(1)}
                            className="flex items-center gap-1 min-h-11 px-2 text-sm text-zinc-400 hover:text-white disabled:opacity-30"
                          >
                            Next <ChevronRight className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="md:hidden fixed bottom-0 inset-x-0 z-50 border-t border-white/10 bg-[#050505]/95 backdrop-blur-md px-4 pt-3 safe-bottom">
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className={`w-full min-h-12 rounded-xl text-sm font-bold transition-all ${
            !isSubmitting
              ? "bg-lime-400 text-black"
              : "bg-white/5 text-zinc-500 cursor-not-allowed"
          }`}
        >
          {isSubmitting ? "Building week..." : "Generate week"}
        </button>
      </div>
    </motion.div>
  );
};
