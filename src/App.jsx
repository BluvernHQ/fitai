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
import { AdminShell } from "./components/admin/AdminShell";
import { AdminGuard } from "./components/admin/AdminGuard";
import { AdminLoginView } from "./components/admin/AdminLoginView";
import { ModuleRoute } from "./components/modules/ModuleRoute";
import { AssessmentSession } from "./components/AssessmentSession";
import { BrandMark } from "./components/ui";
import { useAuth } from "./context/authContext";
import { MODULE_REGISTRY } from "./modules/registry";

const HIDE_TABS = /\/coach\/student\/[^/]+\/(assess|fms|scores|program|workout)/;
const HIDE_TABS_ADMIN = /^\/admin/;

export default function App() {
  const { user, loading } = useAuth();
  const { pathname } = useLocation();
  const hideTabs = HIDE_TABS.test(pathname) || HIDE_TABS_ADMIN.test(pathname);
  const isAdminLogin = pathname === "/admin/login";
  const showCoachChrome = Boolean(user) && !isAdminLogin && !pathname.startsWith("/admin");

  const coachModuleRoutes = MODULE_REGISTRY.filter((m) => m.path && m.scope === "coach" && !m.adminOnly);

  if (loading) {
    return (
      <div className="min-h-dvh text-white flex flex-col items-center justify-center gap-5 px-6">
        <BrandMark size="md" className="opacity-90" />
        <div className="relative h-9 w-9">
          <span className="absolute inset-0 rounded-full border-2 border-white/10" />
          <span className="absolute inset-0 rounded-full border-2 border-transparent border-t-lime-400 animate-spin" />
        </div>
        <p className="eyebrow text-zinc-500">Preparing workspace</p>
      </div>
    );
  }

  return (
    <div className="min-h-dvh text-white selection:bg-lime-500/30 selection:text-lime-100 flex flex-col">
      {showCoachChrome && <Navbar />}
      <div
        className={`flex-1 flex flex-col ${
          showCoachChrome ? `app-pad-top ${hideTabs ? "" : "app-pad-bottom md:!pb-0"}` : ""
        }`}
      >
        <Routes>
          <Route path="/v/:token" element={<AthleteProgramView />} />
          <Route path="/admin/login" element={<AdminLoginView />} />
          <Route
            path="/admin"
            element={
              <AdminGuard>
                <AdminShell />
              </AdminGuard>
            }
          >
            <Route index element={<ModuleRoute moduleId="admin-dashboard" fallback="/admin/login" />} />
            <Route path="modules" element={<ModuleRoute moduleId="module-manager" fallback="/admin/login" />} />
            <Route path="health" element={<ModuleRoute moduleId="system-health" fallback="/admin/login" />} />
            <Route path="coaches" element={<ModuleRoute moduleId="coach-roster-admin" fallback="/admin/login" />} />
          </Route>

          {!user ? (
            <>
              <Route path="/" element={<LoginView />} />
              <Route path="/signup" element={<SignupView />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </>
          ) : (
            <>
              <Route path="/coach/dashboard" element={<StudentsDashboard />} />
              {coachModuleRoutes.map((mod) => (
                <Route
                  key={mod.id}
                  path={mod.path}
                  element={<ModuleRoute moduleId={mod.id} />}
                />
              ))}
              <Route path="/coach/student/:id" element={<StudentProfile />} />
              <Route path="/coach/student/:id/progress" element={<ProgressHistory />} />
              <Route
                path="/coach/student/:id/workout/:assessmentId"
                element={<WorkoutDetail />}
              />
              <Route path="/coach/student/:id/assess" element={<AssessmentSession />} />
              <Route path="/coach/student/:id/fms" element={<FMSAssessment />} />
              <Route path="/coach/student/:id/scores" element={<InputView />} />
              <Route path="/coach/student/:id/workout/current" element={<WorkoutResults />} />
              <Route path="/coach/student/:id/program/:programId" element={<WorkoutResults />} />
              <Route path="*" element={<Navigate to="/coach/dashboard" replace />} />
            </>
          )}
        </Routes>
      </div>
      {/* Partner credit only on auth — not in coach workspace (avoids floating mid-gap above tab bar). */}
      {!user && !isAdminLogin && (
        <footer className="mt-auto w-full border-t border-white/[0.05]">
          <div className="flex items-center justify-center gap-2.5 px-4 py-3.5 md:py-4">
            <span className="text-[10px] font-bold tracking-[0.22em] text-zinc-600 uppercase">
              Powered by
            </span>
            <img src={blueLogo} alt="Bluvern" className="h-4 md:h-5 opacity-70" />
          </div>
        </footer>
      )}
    </div>
  );
}
