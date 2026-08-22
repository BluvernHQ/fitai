import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { User, ChevronRight } from "lucide-react";
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
    <motion.button
      ref={ref}
      type="button"
      onClick={() => navigate(`/coach/student/${student.id}`)}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
      className="group relative w-full text-left bg-white/[0.03] border border-white/5 rounded-2xl p-4 md:p-6 hover:bg-white/[0.06] transition-all duration-300 hover:border-white/10 flex items-center gap-4"
    >
      <div className="w-12 h-12 rounded-full bg-lime-400/10 flex items-center justify-center text-lime-400 border border-lime-400/20 shrink-0">
        <User className="w-5 h-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-0.5">
          <h3 className="text-base md:text-lg font-medium text-white truncate group-hover:text-lime-400 transition-colors">
            {student.name}
          </h3>
          <span className="hidden sm:inline px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-[10px] font-medium text-zinc-400">
            Active
          </span>
        </div>
        <p className="text-xs text-zinc-500 truncate">
          <span className="capitalize">{student.gender}</span>
          <span className="mx-1.5">·</span>
          <span>{student.age} yrs</span>
          {student.created_at && (
            <>
              <span className="mx-1.5 hidden md:inline">·</span>
              <span className="hidden md:inline">Joined {formatDate(student.created_at)}</span>
            </>
          )}
        </p>
      </div>
      <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-lime-400 shrink-0" />
    </motion.button>
  );
};
