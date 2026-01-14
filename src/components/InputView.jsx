import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { MetricInput } from "./MetricInput";
import { MOVEMENTS } from "../data/mockData";

export const InputView = ({ scores, onScoreChange, onGenerate }) => {
  // Group movements for display sections
  const groups = {
    "Mobility & Foundation": MOVEMENTS.filter((m) =>
      ["squat", "shoulder", "leg_raise"].includes(m.id)
    ),
    "Core & Stability": MOVEMENTS.filter((m) =>
      ["pushup", "rotary", "hurdle"].includes(m.id)
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
      className="relative px-6 pt-32 pb-20 max-w-5xl mx-auto"
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-24 md:text-center"
      >
        <h1 className="text-6xl md:text-8xl font-medium tracking-tight mb-6 leading-[0.9]">
          The Coach <br />{" "}
          <span className="text-zinc-600">That Knows You.</span>
        </h1>
        <p className="text-lg text-zinc-400 max-w-2xl md:mx-auto leading-relaxed">
          Experience a programming system that adapts to your biomechanics in
          real-time. Full movement assessment below.
        </p>
      </motion.div>

      <div className="space-y-24">
        {Object.entries(groups).map(([groupName, movements]) => (
          <div key={groupName} className="relative">
            <div className="flex items-center gap-4 mb-8">
              <div className="h-[1px] bg-white/10 flex-1 max-w-[50px]" />
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
                  onChange={onScoreChange}
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
          onClick={onGenerate}
          className="group relative inline-flex items-center gap-4 px-12 py-6 bg-white text-black rounded-full hover:bg-lime-400 transition-colors duration-500"
        >
          <span className="text-xl font-bold tracking-tight">
            Generate Workout
          </span>
          <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
        </button>
      </motion.div>
    </motion.div>
  );
};
