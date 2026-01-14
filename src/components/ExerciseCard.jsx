import { motion } from "framer-motion";
import { Timer, Repeat, Trophy } from "lucide-react";

export const ExerciseCard = ({ exercise, index }) => {
  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: index * 0.1 }}
      className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden hover:border-cyan-500/30 transition-all group"
    >
      <div className="p-1 bg-linear-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="px-2 py-1 bg-cyan-950/50 border border-cyan-500/20 rounded text-[10px] font-mono text-cyan-400 uppercase tracking-widest">
            {exercise.tag}
          </div>
        </div>

        <h4 className="text-xl font-bold text-white mb-6 font-sans tracking-wide">
          {exercise.name}
        </h4>

        <div className="space-y-3 mb-6">
          <div className="flex items-center gap-3 text-sm text-slate-300">
            <Repeat className="w-4 h-4 text-slate-500" />
            <span className="font-mono">{exercise.rx}</span>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-300">
            <Timer className="w-4 h-4 text-slate-500" />
            <span className="font-mono">{exercise.tempo}</span>
          </div>
        </div>

        <div className="p-4 bg-slate-900/50 rounded-lg border-l-2 border-orange-500">
          <p className="text-xs text-orange-200/80 italic leading-relaxed">
            <span className="font-bold text-orange-500 not-italic mr-2">
              COACH:
            </span>
            "{exercise.coach_tip}"
          </p>
        </div>
      </div>
    </motion.div>
  );
};
