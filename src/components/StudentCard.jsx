import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { User, Calendar, Activity } from "lucide-react";

import { useNavigate } from "react-router-dom";

export const StudentCard = ({ student, index }) => {
  const navigate = useNavigate();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
      className="group relative bg-white/[0.03] border border-white/5 rounded-2xl p-6 hover:bg-white/[0.06] transition-all duration-300 hover:border-white/10 flex flex-col"
    >
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-lime-400/10 flex items-center justify-center text-lime-400 border border-lime-400/20 group-hover:scale-110 transition-transform duration-300">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-medium text-white mb-1 group-hover:text-lime-400 transition-colors">
              {student.name}
            </h3>
            <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase brand-font">
              Student ID: #{String(student.id).substring(0, 6)}
            </span>
          </div>
        </div>
        <div className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-zinc-400">
          Active
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-black/20 border border-white/5">
          <div className="flex items-center gap-2 mb-2 text-zinc-500">
            <Activity className="w-3 h-3" />
            <span className="text-xs uppercase tracking-wider font-bold">
              Details
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-zinc-300">
            <span className="capitalize">{student.gender}</span>
            <span className="w-1 h-1 rounded-full bg-zinc-600" />
            <span>{student.age} Yrs</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-black/20 border border-white/5">
          <div className="flex items-center gap-2 mb-2 text-zinc-500">
            <Calendar className="w-3 h-3" />
            <span className="text-xs uppercase tracking-wider font-bold">
              Joined
            </span>
          </div>
          <div className="text-sm text-zinc-300">
            {formatDate(student.created_at)}
          </div>
        </div>
      </div>

      <button
        onClick={() => navigate(`/coach/student/${student.id}`)}
        className="mt-auto w-full py-3 rounded-xl bg-white/5 border border-white/5 text-sm font-bold text-zinc-300 hover:text-white hover:bg-white/10 hover:border-white/10 transition-all flex items-center justify-center gap-2"
      >
        <User className="w-4 h-4 text-lime-400" />
        View Student Profile
      </button>

      <div className="absolute inset-0 border border-white/0 rounded-2xl group-hover:border-lime-400/10 transition-colors duration-500 pointer-events-none" />
    </motion.div>
  );
};
