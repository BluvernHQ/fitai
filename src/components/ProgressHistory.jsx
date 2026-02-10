import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  ChevronRight,
  Calendar,
  Clock,
  Activity,
  AlertCircle,
} from "lucide-react";
import { getAssessments } from "../api/backend";

export const ProgressHistory = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getAssessments(id)
      .then((data) => {
        // Sort by date descending
        const sorted = (data || []).sort((a, b) => {
          const dateA = new Date(a.generated_at || a.created_at || 0);
          const dateB = new Date(b.generated_at || b.created_at || 0);
          return dateB - dateA;
        });
        setAssessments(sorted);
      })
      .catch((err) => {
        console.error("Failed to load assessments", err);
        setError("Could not load history.");
      })
      .finally(() => setLoading(false));
  }, [id]);

  const formatDate = (isoStr) => {
    if (!isoStr) return "N/A";
    return new Date(isoStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatTime = (isoStr) => {
    if (!isoStr) return "N/A";
    return new Date(isoStr).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center text-zinc-500 font-bold uppercase tracking-widest text-xs">
        Loading History...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white pt-24 pb-20 px-6">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate(`/coach/student/${id}`)}
          className="flex items-center gap-2 text-zinc-500 hover:text-white mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Profile</span>
        </button>

        <div className="mb-12">
          <h1 className="text-3xl font-bold text-white mb-2">
            Progress History
          </h1>
          <p className="text-zinc-400">
            Past assessments and generated workouts.
          </p>
        </div>

        {error ? (
          <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center gap-3">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        ) : assessments.length === 0 ? (
          <div className="text-center py-20 bg-white/2 rounded-3xl border border-white/5 border-dashed">
            <HistoryIcon className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-zinc-400 mb-2">
              No history found
            </h3>
            <p className="text-zinc-600 max-w-sm mx-auto">
              Complete an FMS assessment to see results here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {assessments.map((item, i) => (
              <motion.button
                key={item.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                onClick={() =>
                  navigate(`/coach/student/${id}/workout/${item.id}`)
                } // Navigate to Detail View
                className="w-full group flex items-center justify-between p-6 bg-white/3 border border-white/5 hover:bg-white/6 hover:border-white/10 rounded-2xl transition-all"
              >
                <div className="flex items-center gap-6">
                  <div className="w-12 h-12 rounded-xl bg-lime-400/10 flex items-center justify-center text-lime-400 font-bold border border-lime-400/20">
                    {i + 1}
                  </div>
                  <div className="text-left">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="text-lg font-bold text-white">
                        Assessment #{String(item.id).substring(0, 6)}
                      </h3>
                      {/* If you have difficulty in assessment or associated workout, show it here */}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-zinc-500">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5" />
                        {formatDate(item.generated_at || item.created_at)}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5" />
                        {formatTime(item.generated_at || item.created_at)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span className="text-sm font-bold text-zinc-500 group-hover:text-white transition-colors">
                    View Results
                  </span>
                  <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-lime-400 transition-colors" />
                </div>
              </motion.button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const HistoryIcon = ({ className }) => (
  <svg
    className={className}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);
