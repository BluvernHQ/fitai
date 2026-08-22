import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Home } from "lucide-react";
import { getProgram, getStudentWorkouts } from "../api/backend";
import { resolvePlan } from "../lib/programView";
import { ProgramView } from "./ProgramView";

export const WorkoutDetail = () => {
  const { id, assessmentId } = useParams();
  const navigate = useNavigate();
  const [workout, setWorkout] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const targetId = parseInt(assessmentId, 10);
    getStudentWorkouts(id)
      .then(async (data) => {
        const found = (data || []).find(
          (w) => w.assessment_id === targetId || w.id === targetId,
        );
        if (found) {
          setWorkout(found);
          return;
        }
        try {
          setWorkout(await getProgram(id, targetId));
        } catch {
          setError("Workout not found for this assessment.");
        }
      })
      .catch((err) => {
        console.error("Failed to load workout", err);
        setError("Could not load workouts.");
      })
      .finally(() => setLoading(false));
  }, [id, assessmentId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center text-zinc-500">
        Loading Report...
      </div>
    );
  }

  if (error || !workout) {
    return (
      <div className="min-h-screen bg-[#050505] flex flex-col items-center justify-center text-zinc-500">
        <p className="mb-4">{error || "Data unavailable"}</p>
        <button onClick={() => navigate(-1)} className="text-white hover:underline">
          Go Back
        </button>
      </div>
    );
  }

  const plan = resolvePlan(workout);

  return (
    <div className="min-h-screen bg-[#050505] pt-24 pb-20 px-4 md:px-6 max-w-[1120px] mx-auto">
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={() => navigate(`/coach/student/${id}/progress`)}
          className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to History</span>
        </button>
        <button
          onClick={() => navigate("/coach/dashboard")}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm"
        >
          <Home className="w-4 h-4" />
          Dashboard
        </button>
      </div>
      <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 mb-2">
        {(workout.status || "approved").replace("_", " ")}
        {workout.created_at ? ` · ${new Date(workout.created_at).toLocaleDateString()}` : ""}
      </p>
      <h1 className="text-3xl md:text-4xl font-bold text-white leading-tight mb-3">
        {plan.week_title || "Past session"}
      </h1>
      <p className="text-zinc-400 max-w-2xl mb-8 leading-relaxed">
        {plan.needs_summary || workout.coach_summary}
      </p>
      <ProgramView plan={plan} />
    </div>
  );
};
