import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, AlertCircle, Loader2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { register, logout } from "../firebase/auth";
import { registerCoach } from "../api/coach";

export const SignupView = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setIsLoading(true);

    try {
      await register(email, password, name);
      await registerCoach({ name });
      navigate("/");
    } catch (err) {
      console.error(err);
      if (err.code === "auth/email-already-in-use") {
        setError("Email is already in use");
      } else {
        if (!err.code) {
          await logout();
        }
        setError("Failed to create account. Please try again.");
      }
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
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-zinc-400 hover:text-white transition-colors group min-h-11 mb-8"
        >
          <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
          <span className="font-medium">Back to Login</span>
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8 text-left md:text-center"
        >
          <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-3 block brand-font">
            New Account
          </span>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-medium tracking-tight mb-3 leading-[0.95]">
            Join the <br /> <span className="text-lime-400">System.</span>
          </h1>
          <p className="text-zinc-400 text-base md:text-lg">
            Create an account to start your journey.
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
              type="text"
              placeholder="Full Name"
              required
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full h-14 bg-transparent px-5 text-base outline-none text-white placeholder:text-zinc-600 rounded-2xl"
            />
          </div>

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
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full h-14 bg-transparent px-5 text-base outline-none text-white placeholder:text-zinc-600 rounded-2xl"
            />
          </div>

          <div className="group relative bg-white/3 border border-white/5 rounded-2xl p-1 transition-colors hover:bg-white/5 focus-within:bg-white/8 focus-within:border-white/10">
            <input
              type="password"
              placeholder="Confirm Password"
              required
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
                  <span className="text-lg font-bold tracking-tight">Create Account</span>
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
