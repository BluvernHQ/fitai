import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { AlertCircle, ArrowRight, KeyRound, Loader2, Shield } from "lucide-react";
import { login } from "../../firebase/auth";
import { useAdminAuth } from "../../context/AdminAuthContext";
import { useAuth } from "../../context/authContext";
import { useModules } from "../../context/ModuleContext";

export function AdminLoginView() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { unlocked, unlock } = useAdminAuth();
  const { refresh } = useModules();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [gateSecret, setGateSecret] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  if (unlocked) {
    return <Navigate to="/admin" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await unlock({ email, password, gateSecret, loginFn: login });
      await refresh();
      navigate("/admin", { replace: true });
    } catch (err) {
      console.error(err);
      const msg = String(err.message || "");
      if (msg.includes("Admin gate") || msg.includes("gate")) {
        setError("Invalid admin gate key.");
      } else if (msg.includes("not an admin") || msg.includes("Admin access")) {
        setError("This account is not an admin.");
      } else if (msg.includes("auth/") || msg.includes("credential") || msg.includes("password")) {
        setError("Invalid email or password.");
      } else {
        setError(msg || "Admin sign-in failed.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="relative flex-1 w-full flex flex-col items-center justify-center px-4 py-10 min-h-dvh bg-[#050505]"
      style={{
        paddingTop: "max(2.5rem, env(safe-area-inset-top))",
        paddingBottom: "max(2.5rem, env(safe-area-inset-bottom))",
      }}
    >
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_top,_rgba(163,230,53,0.08),_transparent_55%)]" />
      <div className="relative w-full max-w-md">
        <div className="flex items-center justify-between mb-10">
          <span className="text-lg font-bold tracking-tighter brand-font flex items-center gap-2">
            <Shield className="w-5 h-5 text-lime-400" />
            FIT.AI <span className="text-lime-400">ADMIN</span>
          </span>
          <Link
            to={user ? "/coach/dashboard" : "/"}
            className="text-zinc-500 hover:text-white transition-colors text-sm min-h-11 inline-flex items-center"
          >
            {user ? "Coach app" : "Coach login"}
          </Link>
        </div>

        <div className="mb-8">
          <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-3 block">
            Separate auth gate
          </span>
          <h1 className="text-4xl sm:text-5xl font-medium tracking-tight mb-3 leading-[0.95]">
            Platform <br />
            <span className="text-zinc-600">control.</span>
          </h1>
          <p className="text-zinc-400 text-sm md:text-base">
            Admin access requires an admin account plus the platform gate key.
            Coach login alone cannot open this panel.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="group relative bg-white/3 border border-white/5 rounded-2xl p-1 focus-within:border-lime-400/30">
            <input
              type="email"
              placeholder="Admin email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full h-14 bg-transparent px-5 text-base outline-none text-white placeholder:text-zinc-600 rounded-2xl"
            />
          </div>
          <div className="group relative bg-white/3 border border-white/5 rounded-2xl p-1 focus-within:border-lime-400/30">
            <input
              type="password"
              placeholder="Password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full h-14 bg-transparent px-5 text-base outline-none text-white placeholder:text-zinc-600 rounded-2xl"
            />
          </div>
          <div className="group relative bg-white/3 border border-lime-400/15 rounded-2xl p-1 focus-within:border-lime-400/40">
            <div className="absolute left-5 top-1/2 -translate-y-1/2 text-lime-400/70">
              <KeyRound className="w-4 h-4" />
            </div>
            <input
              type="password"
              placeholder="Admin gate key"
              required
              autoComplete="off"
              value={gateSecret}
              onChange={(e) => setGateSecret(e.target.value)}
              className="w-full h-14 bg-transparent pl-11 pr-5 text-base outline-none text-white placeholder:text-zinc-600 rounded-2xl"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-400 bg-red-500/10 p-4 rounded-2xl">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span className="text-sm font-medium">{error}</span>
            </div>
          )}

          <div className="pt-3">
            <button
              type="submit"
              disabled={isLoading}
              className="group inline-flex items-center gap-3 min-h-14 px-8 py-4 bg-lime-400 text-black rounded-full hover:bg-lime-300 disabled:bg-zinc-800 disabled:text-zinc-500 w-full justify-center font-bold"
            >
              {isLoading ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <>
                  Unlock admin
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  );
}
