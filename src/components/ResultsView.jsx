import { useRef } from "react";
import { motion } from "framer-motion";
import { Activity, RefreshCcw, Clock } from "lucide-react";
import { ExCard } from "./ExCard";

export const ResultsView = ({ workout, onReset }) => {
  const resultsRef = useRef(null);

  if (!workout) return null;

  return (
    <motion.div
      key="results"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen px-6 pt-32 pb-20"
      ref={resultsRef}
    >
      <div className="max-w-6xl mx-auto">
        <header className="mb-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="max-w-3xl"
          >
            <div className="inline-flex items-center gap-2 mb-6 px-4 py-2 rounded-full border border-lime-500/20 bg-lime-500/10 text-lime-400 text-xs font-bold uppercase tracking-widest">
              <Activity className="w-3 h-3" /> System Optimized
            </div>
            <h1 className="text-5xl md:text-7xl font-medium mb-8 leading-[0.95]">
              {workout.session_title}
            </h1>
            <p className="text-xl text-zinc-400 leading-relaxed border-l-2 border-white/10 pl-6">
              {workout.coach_summary}
            </p>

            {/* New Details: Duration & Difficulty */}
            <div className="flex flex-wrap items-center gap-4 mt-8">
              {workout.estimated_duration && (
                <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10">
                  <Clock className="w-4 h-4 text-lime-400" />
                  <span className="text-sm font-medium text-white">
                    {workout.estimated_duration}
                  </span>
                </div>
              )}

              {workout.difficulty_color && (
                <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{
                      backgroundColor: workout.difficulty_color.toLowerCase(),
                    }}
                  />
                  <span className="text-sm font-medium text-white">
                    {workout.difficulty_color} Tier
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workout.exercises.map((ex, i) => (
            <ExCard key={i} index={i} exercise={ex} />
          ))}
        </div>

        <div className="mt-24 flex justify-center">
          <button
            onClick={onReset}
            className="text-zinc-500 hover:text-white flex items-center gap-3 transition-colors text-sm font-bold uppercase tracking-widest"
          >
            <RefreshCcw className="w-4 h-4" /> Start New Scan
          </button>
        </div>
      </div>
    </motion.div>
  );
};
