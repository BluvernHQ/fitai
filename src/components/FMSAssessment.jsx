import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import {
  X,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Activity,
  AlertCircle,
  ArrowLeft,
} from "lucide-react";
import fmsData from "../data/fms-v1.json";
import { submitFMSAssessment } from "../api/fms";

// Helper to create the EXACT payload structure required by backend
const createInitialState = () => {
  const state = {
    use_manual_scores: false,
  };

  fmsData.movements.forEach((m) => {
    state[m.id] = {
      score: 0,
      // Add l_score/r_score if asymmetrical
      ...(m.score_config?.type === "asymmetrical" && {
        l_score: 0,
        r_score: 0,
      }),
      // Add clearing_pain if applicable
      ...(m.score_config?.clearing_test && { clearing_pain: false }),
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

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [expandedMovement, setExpandedMovement] = useState(
    fmsData.movements[0].id,
  );

  // Persist functionality
  useEffect(() => {
    sessionStorage.setItem(storageKey, JSON.stringify(payload));
  }, [payload, storageKey]);

  // 2. State Update Logic (Deeply Nested)
  const updateObservation = (movementId, sectionId, key, value) => {
    setPayload((prev) => ({
      ...prev,
      [movementId]: {
        ...prev[movementId],
        [sectionId]: {
          ...prev[movementId][sectionId],
          [key]: value, // Value is already integer 0-3
        },
      },
    }));
  };

  const updateTopLevel = (movementId, key, value) => {
    setPayload((prev) => ({
      ...prev,
      [movementId]: {
        ...prev[movementId],
        [key]: value,
      },
    }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      // 4. Submit Exact Payload from State
      // Reconstruct payload to ensure key order matches specific requirement (use_manual_scores last)
      const { use_manual_scores, ...movements } = payload;
      const orderedPayload = {
        student_id: id,
        ...movements,
        use_manual_scores: use_manual_scores,
      };

      console.log("Submitting Payload (Exact Match):", orderedPayload);
      const result = await submitFMSAssessment(orderedPayload);

      console.log("API Result:", result);

      // Clear persisted state on success
      sessionStorage.removeItem(storageKey);

      // Navigate to Scores view
      navigate(`/coach/student/${id}/scores`, {
        state: {
          calculated_scores: result.calculated_scores || result.scores,
          raw_inputs: orderedPayload, // Pass the raw inputs for persistence
          session_metadata: result.metadata,
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

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen bg-black text-white"
    >
      <div className="fixed inset-0 z-0 bg-[#050505]" /> {/* Background */}
      <div className="relative z-10 min-h-screen px-6 py-12 max-w-4xl mx-auto pt-24">
        {/* Header */}
        <div className="flex items-center justify-between mb-8 sticky top-20 bg-black/95 py-4 z-40 border-b border-white/10 backdrop-blur-md">
          <div>
            <button
              onClick={() => navigate("/coach/dashboard")}
              className="flex items-center gap-2 text-zinc-500 hover:text-white mb-2 transition-colors text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </button>
            <h1 className="text-2xl font-bold text-white mb-1">
              FMS Assessment
            </h1>
            <div className="flex items-center gap-3 text-sm text-zinc-400">
              <span className="flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-lime-400" />
                {studentName}
              </span>
              <span className="w-1 h-1 rounded-full bg-zinc-600" />
              <span>v1.0 Spec</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className={`px-6 py-2 rounded-xl text-sm font-bold transition-all duration-300 ${
                !isSubmitting
                  ? "bg-lime-400 text-black hover:bg-lime-300 hover:scale-105"
                  : "bg-white/5 text-zinc-500 cursor-not-allowed border border-white/5"
              }`}
            >
              {isSubmitting ? "Submitting..." : "Submit Assessment"}
            </button>
          </div>
        </div>

        {/* Error Banner */}
        {errorMsg && (
          <div className="mb-6 bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <p className="text-sm font-medium">{errorMsg}</p>
          </div>
        )}

        {/* Movements List */}
        <div className="space-y-4 pb-20">
          {fmsData.movements.map((movement) => {
            const isExpanded = expandedMovement === movement.id;
            const movementData = payload[movement.id];

            return (
              <motion.div
                key={movement.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`rounded-2xl border transition-all duration-300 overflow-hidden ${
                  isExpanded
                    ? "bg-white/3 border-lime-400/20"
                    : "bg-black/20 border-white/5 hover:border-white/10"
                }`}
              >
                <button
                  onClick={() =>
                    setExpandedMovement(isExpanded ? null : movement.id)
                  }
                  className="w-full flex items-center justify-between p-6 text-left"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`p-2 rounded-lg transition-colors ${"bg-lime-400/10 text-lime-400"}`}
                    >
                      <Activity className="w-6 h-6" />
                    </div>
                    <div>
                      <h3
                        className={`text-lg font-medium transition-colors ${
                          isExpanded ? "text-white" : "text-zinc-300"
                        }`}
                      >
                        {movement.label}
                      </h3>
                    </div>
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5 text-zinc-500" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-zinc-500" />
                  )}
                </button>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="border-t border-white/5"
                    >
                      <div className="p-6 pt-2 space-y-8">
                        {/* ── PAIN CLEARING ONLY (Top Level) ── */}
                        {movement.score_config?.clearing_test && (
                          <div className="bg-black/40 rounded-xl p-5 border border-white/5 mb-6">
                            <div className="flex flex-col gap-2 justify-end pb-1">
                              <label className="flex items-center gap-3 cursor-pointer group">
                                <input
                                  type="checkbox"
                                  checked={!!movementData.clearing_pain}
                                  onChange={(e) =>
                                    updateTopLevel(
                                      movement.id,
                                      "clearing_pain",
                                      e.target.checked,
                                    )
                                  }
                                  className="w-5 h-5 rounded bg-zinc-800 border-zinc-600 text-lime-400 focus:ring-lime-400 focus:ring-offset-black"
                                />
                                <span className="text-zinc-300 text-sm group-hover:text-white transition-colors">
                                  {movement.score_config.clearing_label}
                                </span>
                              </label>
                            </div>
                          </div>
                        )}

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
                                    className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-black/40 border border-white/5 hover:border-white/10 transition-colors"
                                  >
                                    <span className="text-zinc-300 text-sm font-medium">
                                      {obs.label}
                                    </span>

                                    <div className="flex items-center gap-1 bg-black/40 p-1 rounded-lg border border-white/5">
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
                                          className={`w-10 h-10 rounded-md text-sm font-bold transition-all duration-200 ${
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
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
};
