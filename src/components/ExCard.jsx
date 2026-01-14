import { motion } from "framer-motion";

export const ExCard = ({ exercise, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      viewport={{ once: true }}
      className="flex flex-col h-full p-8 rounded-[2rem] bg-zinc-900/50 border border-white/5 hover:border-lime-500/30 transition-colors group relative overflow-hidden"
    >
      {/* Background Ambience */}
      <div className="absolute -right-20 -top-20 w-64 h-64 bg-lime-500/5 rounded-full blur-3xl group-hover:bg-lime-500/10 transition-colors duration-700" />

      <div className="relative z-10 flex flex-col h-full">
        <div className="flex justify-between items-start mb-6">
          <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-white/5 border border-white/10 text-sm font-bold brand-font text-white">
            {index + 1}
          </span>
          <span className="text-xs font-bold tracking-widest uppercase text-lime-400/80 bg-lime-900/20 px-3 py-1 rounded-full border border-lime-500/20">
            {exercise.tag}
          </span>
        </div>

        <h3 className="text-3xl font-medium text-white mb-2 leading-tight">
          {exercise.name}
        </h3>

        <div className="mt-auto space-y-6 pt-8">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl bg-black/20 border border-white/5">
              <p className="text-xs text-zinc-500 mb-1 uppercase tracking-wider font-bold">
                Sets / Reps
              </p>
              <p className="text-lg text-white font-medium brand-font">
                {exercise.sets_reps || exercise.rx}
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-black/20 border border-white/5">
              <p className="text-xs text-zinc-500 mb-1 uppercase tracking-wider font-bold">
                Tempo
              </p>
              <p className="text-lg text-white font-medium brand-font">
                {exercise.tempo}
              </p>
            </div>
          </div>

          <div className="pl-4 border-l-2 border-lime-500/30">
            <p className="text-sm text-zinc-400 italic leading-relaxed">
              "{exercise.coach_tip}"
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
