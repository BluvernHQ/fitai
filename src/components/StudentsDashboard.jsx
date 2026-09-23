import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { fetchStudents } from "../api/student";
import { StudentCard } from "./StudentCard";
import { EnrollStudentModal } from "./EnrollStudentModal";
import { Users, UserPlus } from "lucide-react";
import { PageShell, PageHeader, EmptyState, LoadingState, Button } from "./ui";

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
    loadData(false);
  };

  const handleAssess = (student) => {
    navigate(`/coach/student/${student.id}/assess`, {
      state: { studentName: student.name },
    });
  };

  if (loading) {
    return <LoadingState label="Syncing roster" />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center px-4 py-16 min-h-[50vh] text-center gap-3">
        <span className="text-red-400 font-medium">{error}</span>
        <Button variant="ghost" onClick={() => window.location.reload()}>
          Retry connection
        </Button>
      </div>
    );
  }

  return (
    <>
      <PageShell>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          <PageHeader
            eyebrow="Coach workspace"
            title="Active"
            accent="Roster"
            description={`${students.length} athlete${students.length === 1 ? "" : "s"} ready for assessment and programming.`}
            actions={
              <>
                <div className="hidden md:flex items-center gap-2.5 px-4 py-2.5 rounded-full bg-white/[0.04] border border-white/[0.08]">
                  <Users className="w-4 h-4 text-lime-400" />
                  <span className="text-sm font-semibold text-white tabular-nums">
                    {students.length}
                  </span>
                </div>
                <Button onClick={() => setIsEnrollOpen(true)} className="w-full sm:w-auto">
                  <UserPlus className="w-4 h-4" />
                  Enroll student
                </Button>
              </>
            }
          />

          {students.length === 0 ? (
            <EmptyState
              icon={Users}
              title="No athletes yet"
              description="Enroll your first student to start screening and building programs."
              action={
                <Button onClick={() => setIsEnrollOpen(true)}>
                  <UserPlus className="w-4 h-4" />
                  Enroll first student
                </Button>
              }
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 md:gap-4">
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
        </motion.div>
      </PageShell>

      <EnrollStudentModal
        isOpen={isEnrollOpen}
        onClose={() => setIsEnrollOpen(false)}
        onSuccess={handleEnrollSuccess}
      />
    </>
  );
};
