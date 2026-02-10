import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, ArrowLeft } from "lucide-react";
import { MetricInput } from "./MetricInput";
import { MOVEMENTS } from "../data/mockData";
import { generateWorkoutFromScores } from "../api/fms";
import { saveAssessment, saveWorkout } from "../api/backend";
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

      // 3. Save Assessment (Go) - ORDER CHANGED per User Request
      // Link raw inputs and finalized scores
      console.log("Saving assessment...");

      const studentIdInt = parseInt(id, 10);

      const assessmentPayload = {
        student_id: studentIdInt,
        raw_fms_inputs: location.state?.raw_inputs || {},
        calculated_scores: backendScores,
      };

      const savedAssessment = await saveAssessment(assessmentPayload);
      console.log("Assessment saved:", savedAssessment);

      // Robust Assessment ID Extraction
      let assessmentId =
        savedAssessment.assessment_id ||
        savedAssessment.id ||
        savedAssessment.ID;

      // Handle edge case: Backend returns array [ {id: 1} ]
      if (
        !assessmentId &&
        Array.isArray(savedAssessment) &&
        savedAssessment.length > 0
      ) {
        assessmentId =
          savedAssessment[0].assessment_id ||
          savedAssessment[0].id ||
          savedAssessment[0].ID;
      }

      // Handle edge case: Backend returns { data: { id: 1 } }
      if (!assessmentId && savedAssessment.data) {
        assessmentId =
          savedAssessment.data.assessment_id ||
          savedAssessment.data.id ||
          savedAssessment.data.ID;
      }

      if (!assessmentId) {
        console.warn("Could not find ID in response:", savedAssessment);
        // We will try to proceed, but expect failure downstream if ID is strictly required
        throw new Error(
          `Failed to retrieve Assessment ID. Response keys: ${Object.keys(savedAssessment).join(", ")}`,
        );
      }

      // 4. Generate Workout (Python)
      // Now that we have the assessment saved, generate the content
      console.log("Generating workout...");
      const generatedWorkout = await generateWorkoutFromScores(pythonPayload);
      console.log("Generation complete:", generatedWorkout);

      // 5. Save Workout (Go)
      // Link it to the assessment we just saved.
      console.log("Saving workout...");
      const workoutPayload = {
        student_id: studentIdInt,
        assessment_id: assessmentId,
        ...generatedWorkout, // Persist the entire generated structure
        created_at: new Date().toISOString(),
      };

      const savedWorkout = await saveWorkout(workoutPayload);
      console.log("Workout saved:", savedWorkout);

      // 6. Navigate to Confirmation View
      navigate(`/coach/student/${id}/workout/current`, {
        state: {
          workout: generatedWorkout, // Display the one we just made
          assessmentId: assessmentId, // Context for later
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
      className="relative px-6 pt-24 pb-20 max-w-5xl mx-auto min-h-screen bg-[#050505]"
    >
      {/* Back Button */}
      <button
        onClick={() => navigate(`/coach/student/${id}/fms`)}
        className="mb-8 flex items-center gap-2 text-zinc-500 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Assessment</span>
      </button>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-12 md:text-center"
      >
        <h1 className="text-5xl md:text-7xl font-medium tracking-tight mb-6 leading-[0.9] text-white">
          Review Scores
        </h1>
        <p className="text-lg text-zinc-400 max-w-2xl md:mx-auto leading-relaxed">
          Adjust the calculated scores below if necessary. These values will
          drive the programming logic.
        </p>
      </motion.div>

      <div className="space-y-24">
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
        className="mt-32 flex justify-center pb-20"
      >
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className={`group relative inline-flex items-center gap-4 px-12 py-6 rounded-full transition-all duration-500 ${
            isGenerating
              ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
              : "bg-white text-black hover:bg-lime-400"
          }`}
        >
          <span className="text-xl font-bold tracking-tight">
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
