import { Navigate } from "react-router-dom";
import { useAdminAuth } from "../../context/AdminAuthContext";
import { useAuth } from "../../context/authContext";

export function AdminGuard({ children }) {
  const { user, loading: authLoading } = useAuth();
  const { unlocked } = useAdminAuth();

  if (authLoading) {
    return (
      <div className="min-h-[40vh] flex items-center justify-center text-zinc-500 text-sm">
        Loading admin…
      </div>
    );
  }

  if (!user || !unlocked) {
    return <Navigate to="/admin/login" replace />;
  }

  return children;
}
