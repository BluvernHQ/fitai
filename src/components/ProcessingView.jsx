import { motion } from "framer-motion";
import { Dna } from "lucide-react";

export const ProcessingView = () => {
  return (
    <motion.div
      key="processing"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-40 flex flex-col items-center justify-center bg-[#050505]"
    >
      <div className="relative w-32 h-32 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="absolute inset-0 border-t-2 border-l-2 border-lime-500 rounded-full"
        />
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
          className="absolute inset-4 border-b-2 border-r-2 border-white/20 rounded-full"
        />
        <Dna className="w-10 h-10 text-white/50 animate-pulse" />
      </div>
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-12 text-2xl font-light text-zinc-400"
      >
        Analyzing <span className="text-white font-medium">Biomechanics</span>
      </motion.h2>
    </motion.div>
  );
};
