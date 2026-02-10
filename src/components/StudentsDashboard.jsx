import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { fetchStudents } from "../api/student";
import { StudentCard } from "./StudentCard";
import { EnrollStudentModal } from "./EnrollStudentModal";
import { Loader2, Users, UserPlus } from "lucide-react";

export const StudentsDashboard = () => {
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEnrollOpen, setIsEnrollOpen] = useState(false);

  const loadData = async (isInitial = true) => {
    if (isInitial) setLoading(true);
    try {
      const data = await fetchStudents();
      setStudents(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      setError("Unable to load student roster.");
    } finally {
      if (isInitial) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleEnrollSuccess = () => {
    setIsEnrollOpen(false);
    loadData(false); // Refresh without full page loader
  };

  const handleAssess = (student) => {
    navigate(`/coach/student/${student.id}/fms`, {
      state: { studentName: student.name },
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 min-h-[50vh]">
        <Loader2 className="w-8 h-8 text-lime-400 animate-spin mb-4" />
        <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase">
          Syncing Roster...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-20 min-h-[50vh] text-center">
        <span className="text-red-500 font-medium mb-2">{error}</span>
        <button
          onClick={() => window.location.reload()}
          className="text-sm text-zinc-400 hover:text-white underline underline-offset-4"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <>
      <div className="w-full max-w-7xl mx-auto px-6 py-12 md:py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12 flex items-end justify-between border-b border-white/5 pb-8"
        >
          <div>
            <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-4 block brand-font">
              Coach Dashboard
            </span>
            <h1 className="text-4xl md:text-5xl font-medium tracking-tight leading-[0.9]">
              Active <span className="text-zinc-600">Roster</span>
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-3 px-4 py-2 rounded-full bg-white/5 border border-white/5">
              <Users className="w-4 h-4 text-lime-400" />
              <span className="text-sm font-medium text-white">
                {students.length} Students
              </span>
            </div>

            <button
              onClick={() => setIsEnrollOpen(true)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-lime-400 text-black text-sm font-bold hover:bg-lime-300 transition-all hover:scale-105"
            >
              <UserPlus className="w-4 h-4" />
              <span>Enroll Student</span>
            </button>
          </div>
        </motion.div>

        {students.length === 0 ? (
          <div className="text-center py-20 bg-white/2 rounded-3xl border border-white/5 border-dashed">
            <Users className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-zinc-400 mb-2">
              No Students yet
            </h3>
            <p className="text-zinc-600 max-w-sm mx-auto mb-6">
              Your roster is currently empty. New students will appear here once
              they are enrolled.
            </p>
            <button
              onClick={() => setIsEnrollOpen(true)}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-white/5 text-white text-sm font-medium hover:bg-white/10 transition-colors border border-white/10"
            >
              <UserPlus className="w-4 h-4 text-lime-400" />
              Enroll First Student
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {students.map((student, i) => (
              <StudentCard
                key={student.id}
                student={student}
                index={i}
                onAssess={handleAssess}
              />
            ))}
          </div>
        )}
      </div>

      <EnrollStudentModal
        isOpen={isEnrollOpen}
        onClose={() => setIsEnrollOpen(false)}
        onSuccess={handleEnrollSuccess}
      />
    </>
  );
};
