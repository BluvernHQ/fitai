import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, AlertCircle, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { login } from "../firebase/auth";

export const LoginView = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
    } catch (err) {
      console.error(err);
      setError("Invalid credentials. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8 }}
      className="relative flex-1 w-full flex flex-col items-center justify-center px-4 py-10"
      style={{
        paddingTop: "max(2.5rem, env(safe-area-inset-top))",
        paddingBottom: "max(2.5rem, env(safe-area-inset-bottom))",
      }}
    >
      <div className="w-full max-w-md">
        <div className="flex items-center justify-between mb-10">
          <span className="text-lg font-bold tracking-tighter brand-font">
            FIT.AI <span className="text-lime-400">PRO</span>
          </span>
          <Link
            to="/signup"
            className="text-zinc-400 hover:text-white transition-colors text-sm font-medium min-h-11 inline-flex items-center"
          >
            Sign Up
          </Link>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8 md:mb-12 text-left md:text-center"
        >
          <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-3 block brand-font">
            System Access
          </span>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-medium tracking-tight mb-3 leading-[0.95]">
            Welcome <br /> <span className="text-zinc-600">Back.</span>
          </h1>
          <p className="text-zinc-400 text-base md:text-lg">
            Sign in to continue your programming.
          </p>
        </motion.div>

        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          onSubmit={handleSubmit}
          className="space-y-3"
        >
          <div className="group relative bg-white/3 border border-white/5 rounded-2xl p-1 transition-colors hover:bg-white/5 focus-within:bg-white/8 focus-within:border-white/10">
            <input
              type="email"
              placeholder="Email"
              required
              autoComplete="email"
              inputMode="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full h-14 bg-transparent px-5 text-base outline-none text-white placeholder:text-zinc-600 rounded-2xl"
            />
          </div>

          <div className="group relative bg-white/3 border border-white/5 rounded-2xl p-1 transition-colors hover:bg-white/5 focus-within:bg-white/8 focus-within:border-white/10">
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

          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="flex items-center gap-2 text-red-500 bg-red-500/10 p-4 rounded-2xl"
            >
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span className="text-sm font-medium">{error}</span>
            </motion.div>
          )}

          <div className="pt-3">
            <button
              type="submit"
              disabled={isLoading}
              className="group relative inline-flex items-center gap-3 min-h-14 px-8 py-4 bg-white text-black rounded-full hover:bg-lime-400 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed transition-colors duration-500 w-full justify-center"
            >
              {isLoading ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <>
                  <span className="text-lg font-bold tracking-tight">Enter System</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </div>
        </motion.form>
      </div>
    </motion.div>
  );
};
