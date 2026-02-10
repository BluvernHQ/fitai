import { Routes, Route, Navigate } from "react-router-dom";
import blueLogo from "./assets/blue.svg";
import { Navbar } from "./components/Navbar";
import { LoginView } from "./components/LoginView";
import { SignupView } from "./components/SignupView";
import { StudentsDashboard } from "./components/StudentsDashboard";
import { StudentProfile } from "./components/StudentProfile";
import { ProgressHistory } from "./components/ProgressHistory";
import { WorkoutDetail } from "./components/WorkoutDetail";
import { FMSAssessment } from "./components/FMSAssessment";
import { InputView } from "./components/InputView";
import { WorkoutResults } from "./components/WorkoutResults";
import { useAuth } from "./context/authContext";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center">
        <div className="animate-pulse text-zinc-500 font-bold tracking-widest uppercase text-xs">
          Loading System...
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-[#050505] text-white selection:bg-lime-500/30">
        <Routes>
          <Route path="/" element={<LoginView />} />
          <Route path="/signup" element={<SignupView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-lime-500/30">
      <Navbar />

      <div className="pt-20">
        <Routes>
          <Route path="/coach/dashboard" element={<StudentsDashboard />} />

          {/* Read Flow */}
          <Route path="/coach/student/:id" element={<StudentProfile />} />
          <Route
            path="/coach/student/:id/progress"
            element={<ProgressHistory />}
          />
          <Route
            path="/coach/student/:id/workout/:assessmentId"
            element={<WorkoutDetail />}
          />

          {/* Write Flow */}
          <Route path="/coach/student/:id/fms" element={<FMSAssessment />} />
          <Route path="/coach/student/:id/scores" element={<InputView />} />
          <Route
            path="/coach/student/:id/workout/current"
            element={<WorkoutResults />}
          />

          {/* Fallback route */}
          <Route
            path="*"
            element={<Navigate to="/coach/dashboard" replace />}
          />
        </Routes>

        <footer className="w-full max-w-7xl mx-auto px-6 py-12 mt-auto">
          <div className="flex flex-col items-center justify-center gap-4 pt-8 border-t border-white/5">
            <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-600 uppercase">
              Powered by
            </span>
            <img src={blueLogo} alt="Logo" className="h-8 opacity-80" />
          </div>
        </footer>
      </div>
    </div>
  );
}
