import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Clock, BarChart, Calendar, Home } from "lucide-react";
import { getStudentWorkouts } from "../api/backend";
// Note: User flow says /coach/student/:id/workout/:assessmentId.

import { ExerciseCard } from "./ExerciseCard";

export const WorkoutDetail = () => {
  const { id, assessmentId } = useParams();
  const navigate = useNavigate();
  const [workout, setWorkout] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 1. Fetch all workouts for student (since we don't have a single GET endpoint yet)
    getStudentWorkouts(id)
      .then((data) => {
        // 2. Find the one matching the assessmentId
        // The URL param is called assessmentId, but it might be the row ID from history list.
        // Let's match against both to be safe, or check how we linked it (ProgressHistory links to item.id).
        // ProgressHistory item.id is the ASSESSMENT ID (from getAssessments).
        // So we should find the workout where w.assessment_id === item.id
        const targetId = parseInt(assessmentId, 10);

        const found = (data || []).find(
          (w) => w.assessment_id === targetId || w.id === targetId,
        );

        if (found) {
          setWorkout(found);
        } else {
          setError("Workout not found for this assessment.");
        }
      })
      .catch((err) => {
        console.error("Failed to load workout", err);
        setError("Could not load workouts.");
      })
      .finally(() => setLoading(false));
  }, [id, assessmentId]);

  const getDifficultyColor = (color) => {
    const map = {
      green: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
      yellow: "text-amber-400 bg-amber-400/10 border-amber-400/20",
      red: "text-rose-400 bg-rose-400/10 border-rose-400/20",
    };
    return map[color] || map.green;
  };

  if (loading)
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center text-zinc-500">
        Loading Report...
      </div>
    );

  if (error || !workout) {
    return (
      <div className="min-h-screen bg-[#050505] flex flex-col items-center justify-center text-zinc-500">
        <p className="mb-4">{error || "Data unavailable"}</p>
        <button
          onClick={() => navigate(-1)}
          className="text-white hover:underline"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] pt-24 pb-20 px-6 max-w-7xl mx-auto">
      {/* Header / Nav */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/coach/student/${id}/progress`)}
            className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to History</span>
          </button>
        </div>

        <div className="flex items-center gap-4">
          {/* Date */}
          <div className="text-zinc-500 text-sm">
            {workout.created_at &&
              new Date(workout.created_at).toLocaleDateString()}
          </div>

          <button
            onClick={() => navigate("/coach/dashboard")}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg transition-colors text-sm font-medium border border-white/10"
          >
            <Home className="w-4 h-4" />
            <span>Dashboard</span>
          </button>
        </div>
      </div>

      {/* Read-Only Banner */}
      <div className="bg-lime-400/5 border border-lime-400/20 text-lime-400 px-4 py-2 rounded-lg text-sm font-bold mb-8 w-fit">
        READ ONLY MODE
      </div>

      {/* Main Content */}
      <div className="grid lg:grid-cols-[400px_1fr] gap-12">
        {/* Sidebar: Session Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          <div>
            <h1 className="text-4xl font-bold text-white leading-tight mb-4">
              {workout.session_title || "Past Session"}
            </h1>

            <div className="flex flex-wrap gap-3 mb-6">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zinc-800/50 border border-white/5 text-zinc-300 text-sm">
                <Clock className="w-4 h-4" />
                <span>{workout.estimated_duration || "N/A min"}</span>
              </div>
              {workout.difficulty_color && (
                <div
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm border ${getDifficultyColor(workout.difficulty_color)}`}
                >
                  <BarChart className="w-4 h-4" />
                  <span className="capitalize">
                    {workout.difficulty_color} Intensity
                  </span>
                </div>
              )}
            </div>

            <div className="p-6 rounded-2xl bg-zinc-900/50 border border-white/5 leading-relaxed text-zinc-300">
              <h3 className="text-white font-bold mb-2 text-sm uppercase tracking-wider">
                Coach Summary
              </h3>
              <p>{workout.coach_summary}</p>
            </div>
          </div>
        </motion.div>

        {/* Exercises Grid */}
        <div className="space-y-6">
          {workout.exercises?.map((exercise, i) => (
            <ExerciseCard
              key={i}
              exercise={{
                ...exercise,
                rx: exercise.sets_reps || exercise.rx,
              }}
              index={i}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
