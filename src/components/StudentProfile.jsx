import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Activity,
  History,
  ChevronRight,
  User,
  Calendar,
  BarChart,
} from "lucide-react";
import { getStudent } from "../api/backend";

export const StudentProfile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real app, you might also fetch latest stats here
    getStudent(id)
      .then(setStudent)
      .catch((err) => console.error("Failed to load student", err))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center text-zinc-500">
        Loading...
      </div>
    );
  }

  if (!student) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center text-zinc-500">
        Student not found.
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white pt-24 pb-20 px-6">
      <div className="max-w-4xl mx-auto">
        {/* Navigation */}
        <button
          onClick={() => navigate("/coach/dashboard")}
          className="flex items-center gap-2 text-zinc-500 hover:text-white mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        {/* Profile Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900/50 border border-white/5 rounded-3xl p-8 mb-8"
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 rounded-full bg-lime-400/10 flex items-center justify-center text-lime-400 border border-lime-400/20">
                <User className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">
                  {student.name}
                </h1>
                <div className="flex items-center gap-4 text-sm text-zinc-400">
                  <span className="flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5" />
                    ID: {String(student.id).substring(0, 6)}
                  </span>
                  <span className="w-1 h-1 rounded-full bg-zinc-600" />
                  <span>{student.age || "N/A"} Years</span>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-3 min-w-[200px]">
              <button
                onClick={() =>
                  navigate(`/coach/student/${id}/fms`, {
                    state: { studentName: student.name },
                  })
                }
                className="w-full py-3 px-6 rounded-xl bg-lime-400 text-black font-bold hover:bg-lime-300 transition-colors flex items-center justify-center gap-2"
              >
                <Activity className="w-4 h-4" />
                New Assessment
              </button>
            </div>
          </div>
        </motion.div>

        {/* Actions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* View Progress Card */}
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            onClick={() => navigate(`/coach/student/${id}/progress`)}
            className="group relative h-48 rounded-3xl bg-white/3 border border-white/5 p-8 text-left hover:bg-white/5 transition-all overflow-hidden"
          >
            <div className="relative z-10 h-full flex flex-col justify-between">
              <div className="p-3 bg-white/5 w-fit rounded-xl mb-4 group-hover:bg-lime-400/20 group-hover:text-lime-400 transition-colors">
                <History className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white mb-1">
                  Assessment History
                </h3>
                <p className="text-zinc-400 text-sm">
                  View past results & trends
                </p>
              </div>
            </div>
            <div className="absolute top-1/2 right-8 -translate-y-1/2 opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
              <ChevronRight className="w-6 h-6 text-lime-400" />
            </div>
          </motion.button>

          {/* Placeholder for Stats or other features */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="h-48 rounded-3xl bg-white/3 border border-white/5 p-8 flex flex-col justify-center items-center text-center opacity-50 cursor-not-allowed"
          >
            <BarChart className="w-8 h-8 text-zinc-600 mb-4" />
            <h3 className="text-lg font-bold text-zinc-500">Analytics</h3>
            <p className="text-xs text-zinc-600">Coming Soon</p>
          </motion.div>
        </div>
      </div>
    </div>
  );
};
