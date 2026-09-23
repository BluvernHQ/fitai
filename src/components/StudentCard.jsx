import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

export const StudentCard = ({ student, index }) => {
  const navigate = useNavigate();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });

  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const initials = String(student.name || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");

  return (
    <motion.button
      ref={ref}
      type="button"
      onClick={() => navigate(`/coach/student/${student.id}`)}
      initial={{ opacity: 0, y: 18 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 18 }}
      transition={{ delay: Math.min(index * 0.04, 0.24), duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="group relative w-full text-left surface-interactive p-4 md:p-5 flex items-center gap-4 focus-visible:outline-offset-4"
    >
      <div className="relative shrink-0">
        <div className="w-12 h-12 rounded-2xl bg-lime-400/10 flex items-center justify-center text-lime-400 border border-lime-400/25 font-display font-bold text-sm tracking-tight">
          {initials || "?"}
        </div>
        <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-lime-400 ring-2 ring-[#050505]" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-0.5">
          <h3 className="text-base md:text-lg font-display font-medium text-white truncate group-hover:text-lime-300 transition-colors">
            {student.name}
          </h3>
          <span className="hidden sm:inline px-2 py-0.5 rounded-md bg-lime-400/10 border border-lime-400/20 text-[10px] font-bold uppercase tracking-wider text-lime-400/90">
            Active
          </span>
        </div>
        <p className="text-xs text-zinc-500 truncate">
          <span className="capitalize">{student.gender}</span>
          <span className="mx-1.5 text-zinc-700">·</span>
          <span>{student.age} yrs</span>
          {student.created_at && (
            <>
              <span className="mx-1.5 text-zinc-700 hidden md:inline">·</span>
              <span className="hidden md:inline">Joined {formatDate(student.created_at)}</span>
            </>
          )}
        </p>
      </div>
      <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-lime-400 group-hover:translate-x-0.5 transition-all shrink-0" />
    </motion.button>
  );
};
