import { Suspense } from "react";
import { Navigate } from "react-router-dom";
import { useModules } from "../../context/ModuleContext";

export function ModuleRoute({ moduleId, fallback = "/coach/dashboard" }) {
  const { isEnabled, getModule, isAdmin, loading } = useModules();
  const mod = getModule(moduleId);

  if (loading) {
    return (
      <div className="min-h-[40vh] flex items-center justify-center text-zinc-500 text-sm">
        Loading…
      </div>
    );
  }

  if (!isEnabled(moduleId)) {
    return <Navigate to={fallback} replace />;
  }

  if (mod?.adminOnly && !isAdmin) {
    return <Navigate to={fallback} replace />;
  }

  const Component = mod?.component;
  if (!Component) {
    return <Navigate to={fallback} replace />;
  }

  return (
    <Suspense
      fallback={
        <div className="min-h-[40vh] flex items-center justify-center text-zinc-500 text-sm">
          Loading module…
        </div>
      }
    >
      <Component />
    </Suspense>
  );
}
