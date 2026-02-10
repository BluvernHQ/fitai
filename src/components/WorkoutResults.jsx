import { useLocation, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ExerciseCard } from "./ExerciseCard";
import { ArrowLeft, Clock, BarChart, Home } from "lucide-react";

export const WorkoutResults = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { id } = useParams();

  // Robustly handle missing state (e.g. direct URL access without flow)
  // In a real app, you might want to fetch the latest workout from DB here if state is missing
  const workout = state?.workout;

  if (!workout) {
    return (
      <div className="min-h-screen pt-32 px-6 flex flex-col items-center justify-center text-center">
        <h2 className="text-2xl font-bold text-white mb-4">
          No Workout Data Found
        </h2>
        <p className="text-zinc-400 mb-8">
          Please complete the assessment flow first.
        </p>
        <button
          onClick={() => navigate(`/coach/student/${id}/fms`)}
          className="px-6 py-3 bg-lime-400 text-black font-bold rounded-xl hover:bg-lime-300 transition-colors"
        >
          Start Assessment
        </button>
      </div>
    );
  }

  // Determine difficulty color
  const getDifficultyColor = (color) => {
    const map = {
      green: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
      yellow: "text-amber-400 bg-amber-400/10 border-amber-400/20",
      red: "text-rose-400 bg-rose-400/10 border-rose-400/20",
    };
    return map[color] || map.green;
  };

  return (
    <div className="min-h-screen pt-24 pb-20 px-6 max-w-7xl mx-auto">
      {/* Header / Nav */}
      <div className="flex items-center justify-between mb-8">
        <motion.button
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          onClick={() => navigate(`/coach/student/${id}/scores`)}
          className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Scores</span>
        </motion.button>

        <motion.button
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          onClick={() => navigate("/coach/dashboard")}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg transition-colors text-sm font-medium border border-white/10"
        >
          <Home className="w-4 h-4" />
          <span>Dashboard</span>
        </motion.button>
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
              {workout.session_title || "Generated Session"}
            </h1>

            <div className="flex flex-wrap gap-3 mb-6">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zinc-800/50 border border-white/5 text-zinc-300 text-sm">
                <Clock className="w-4 h-4" />
                <span>{workout.estimated_duration || "45-60 min"}</span>
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
                rx: exercise.sets_reps || exercise.rx, // Handle diverse API names
              }}
              index={i}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
