import { Routes, Route, Navigate, useLocation } from "react-router-dom";
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
import { AthleteProgramView } from "./components/AthleteProgramView";
import { CoachInsights } from "./components/CoachInsights";
import { useAuth } from "./context/authContext";

const HIDE_TABS = /\/coach\/student\/[^/]+\/(fms|scores|program|workout)/;

export default function App() {
  const { user, loading } = useAuth();
  const { pathname } = useLocation();
  const hideTabs = HIDE_TABS.test(pathname);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center">
        <div className="animate-pulse text-zinc-500 font-bold tracking-widest uppercase text-xs">
          Loading System...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-dvh bg-[#050505] text-white selection:bg-lime-500/30 flex flex-col">
      {user && <Navbar />}
      <div
        className={`flex-1 flex flex-col ${
          user ? `app-pad-top ${hideTabs ? "" : "md:pb-0"}` : ""
        }`}
      >
        <Routes>
          <Route path="/v/:token" element={<AthleteProgramView />} />
          {!user ? (
            <>
              <Route path="/" element={<LoginView />} />
              <Route path="/signup" element={<SignupView />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </>
          ) : (
            <>
              <Route path="/coach/dashboard" element={<StudentsDashboard />} />
              <Route path="/coach/insights" element={<CoachInsights />} />
              <Route path="/coach/student/:id" element={<StudentProfile />} />
              <Route path="/coach/student/:id/progress" element={<ProgressHistory />} />
              <Route
                path="/coach/student/:id/workout/:assessmentId"
                element={<WorkoutDetail />}
              />
              <Route path="/coach/student/:id/fms" element={<FMSAssessment />} />
              <Route path="/coach/student/:id/scores" element={<InputView />} />
              <Route path="/coach/student/:id/workout/current" element={<WorkoutResults />} />
              <Route path="/coach/student/:id/program/:programId" element={<WorkoutResults />} />
              <Route path="*" element={<Navigate to="/coach/dashboard" replace />} />
            </>
          )}
        </Routes>
      </div>
      {!hideTabs && (
        <footer
          className={`mt-auto w-full border-t border-white/5 ${
            user ? "mb-14 md:mb-0" : ""
          }`}
        >
          <div className="flex items-center justify-center gap-2 px-4 py-3 md:py-4">
            <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-600 uppercase">
              Powered by
            </span>
            <img src={blueLogo} alt="Bluvern" className="h-4 md:h-5 opacity-80" />
          </div>
        </footer>
      )}
    </div>
  );
}
