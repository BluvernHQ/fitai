import { motion } from "framer-motion";
import { Check, AlertCircle, X } from "lucide-react";

export const MetricInput = ({ id, label, value, onChange, index }) => {
  const options = [
    { start: 0, label: "Pain", color: "bg-red-500", text: "text-red-500" },
    {
      start: 1,
      label: "Poor",
      color: "bg-orange-500",
      text: "text-orange-500",
    },
    { start: 2, label: "OK", color: "bg-yellow-500", text: "text-yellow-500" },
    { start: 3, label: "Perfect", color: "bg-lime-400", text: "text-lime-400" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.5, ease: "easeOut" }}
      viewport={{ once: true }}
      className="group relative flex flex-col md:flex-row md:items-center justify-between p-6 md:p-8 rounded-3xl bg-white/[0.03] hover:bg-white/[0.05] border border-white/5 transition-colors"
    >
      <div className="mb-6 md:mb-0 md:mr-8 flex-1">
        <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-2 block brand-font">
          0{index + 1}
        </span>
        <h3 className="text-2xl md:text-3xl font-medium text-white group-hover:text-lime-400 transition-colors">
          {label}
        </h3>
      </div>

      <div className="relative flex items-center gap-2 bg-black/40 p-1 rounded-2xl border border-white/5">
        {options.map((opt) => {
          const isActive = value === opt.start;
          return (
            <button
              key={opt.start}
              onClick={() => onChange(id, opt.start)}
              className={`relative w-16 h-14 md:w-20 md:h-16 rounded-xl flex flex-col items-center justify-center transition-all duration-300 overflow-hidden ${
                isActive ? "bg-zinc-800" : "hover:bg-zinc-900"
              }`}
            >
              <div
                className={`absolute inset-0 opacity-20 transition-opacity duration-300 ${
                  isActive ? opt.color : "bg-transparent"
                }`}
              />

              <span
                className={`text-xl font-bold z-10 ${
                  isActive ? "text-white" : "text-zinc-500"
                }`}
              >
                {opt.start}
              </span>

              {isActive && (
                <motion.div
                  layoutId={`active-glow-${id}`}
                  className={`absolute bottom-0 left-0 right-0 h-1 ${opt.color} shadow-[0_0_15px_rgba(0,0,0,0.5)]`}
                />
              )}
            </button>
          );
        })}
      </div>
    </motion.div>
  );
};
