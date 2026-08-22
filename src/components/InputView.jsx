import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, ArrowLeft } from "lucide-react";
import { MetricInput } from "./MetricInput";
import { MOVEMENTS } from "../data/mockData";
import { generateWorkoutFromScores } from "../api/fms";
import { useNavigate, useLocation, useParams } from "react-router-dom";

export const InputView = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();

  // Map backend IDs to frontend display IDs
  const backendToFrontend = {
    overhead_squat: "squat",
    hurdle_step: "hurdle",
    inline_lunge: "lunge",
    shoulder_mobility: "shoulder",
    active_straight_leg_raise: "leg_raise",
    trunk_stability_pushup: "pushup",
    rotary_stability: "rotary",
  };

  // Get initial scores from route state or default to safe fallback
  const getInitialScores = () => {
    const rawScores = location.state?.calculated_scores;
    if (!rawScores) {
      return MOVEMENTS.reduce((acc, m) => ({ ...acc, [m.id]: 2 }), {});
    }

    // Map keys if they match backend format
    const mappedScores = {};
    for (const [key, val] of Object.entries(rawScores)) {
      const frontendKey = backendToFrontend[key] || key;
      mappedScores[frontendKey] = val;
    }
    return mappedScores;
  };

  const [scores, setScores] = useState(getInitialScores());
  const [isGenerating, setIsGenerating] = useState(false);

  const handleScoreChange = (movementId, val) => {
    setScores((prev) => ({ ...prev, [movementId]: parseInt(val, 10) }));
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      // 1. Map frontend IDs to backend required IDs for Python Generator
      const keyMapping = {
        squat: "overhead_squat",
        hurdle: "hurdle_step",
        lunge: "inline_lunge",
        shoulder: "shoulder_mobility",
        leg_raise: "active_straight_leg_raise",
        pushup: "trunk_stability_pushup",
        rotary: "rotary_stability",
      };

      const backendScores = Object.entries(scores).reduce((acc, [key, val]) => {
        const backendKey = keyMapping[key] || key;
        acc[backendKey] = val;
        return acc;
      }, {});

      // 2. Prepare payload for Python API
      const pythonPayload = {
        calculated_scores: backendScores,
        metadata: location.state?.session_metadata || {},
      };

      pythonPayload.student_id = Number(id);
      const generatedWorkout = await generateWorkoutFromScores(pythonPayload);
      const dest = generatedWorkout?.id
        ? `/coach/student/${id}/program/${generatedWorkout.id}`
        : `/coach/student/${id}/workout/current`;
      navigate(dest, {
        state: {
          workout: generatedWorkout,
          programId: generatedWorkout.id,
          assessmentId: generatedWorkout.assessment_id,
        },
      });
    } catch (error) {
      console.error("Workflow failed", error);
      alert("Failed to process request. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  // Group movements for display sections
  const groups = {
    "Mobility & Foundation": MOVEMENTS.filter((m) =>
      ["squat", "shoulder", "leg_raise"].includes(m.id),
    ),
    "Core & Stability": MOVEMENTS.filter((m) =>
      ["pushup", "rotary", "hurdle"].includes(m.id),
    ),
    "Dynamic Control": MOVEMENTS.filter((m) => ["lunge"].includes(m.id)),
  };

  return (
    <motion.div
      key="input"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: -50 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="relative px-4 md:px-6 py-6 md:py-12 pb-28 max-w-5xl mx-auto"
    >
      {/* Back Button */}
      <button
        onClick={() => navigate(`/coach/student/${id}/fms`)}
        className="mb-6 flex items-center gap-2 text-zinc-500 hover:text-white transition-colors min-h-11"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Assessment</span>
      </button>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-8 md:mb-12 md:text-center"
      >
        <h1 className="text-3xl sm:text-5xl md:text-7xl font-medium tracking-tight mb-4 leading-[0.95] text-white">
          Review Scores
        </h1>
        <p className="text-base md:text-lg text-zinc-400 max-w-2xl md:mx-auto leading-relaxed">
          Adjust the calculated scores below if necessary. These values will
          drive the programming logic.
        </p>
      </motion.div>

      <div className="space-y-12 md:space-y-24">
        {Object.entries(groups).map(([groupName, movements]) => (
          <div key={groupName} className="relative">
            <div className="flex items-center gap-4 mb-8">
              <div className="h-px bg-white/10 flex-1 max-w-[50px]" />
              <h2 className="text-sm font-bold tracking-widest uppercase text-zinc-500 brand-font">
                {groupName}
              </h2>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {movements.map((m, i) => (
                <MetricInput
                  key={m.id}
                  index={i}
                  {...m}
                  value={scores[m.id]}
                  onChange={handleScoreChange}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="mt-12 md:mt-24 flex justify-center"
      >
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className={`group relative inline-flex items-center justify-center gap-3 w-full md:w-auto min-h-14 px-8 py-4 md:px-12 md:py-6 rounded-full transition-all duration-500 ${
            isGenerating
              ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
              : "bg-white text-black hover:bg-lime-400"
          }`}
        >
          <span className="text-lg md:text-xl font-bold tracking-tight">
            {isGenerating ? "Processing..." : "Generate Workout"}
          </span>
          {!isGenerating && (
            <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
          )}
        </button>
      </motion.div>
    </motion.div>
  );
};
