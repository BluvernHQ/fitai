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
      // Register with backend
      await registerCoach({ name });

      // AuthProvider will detect change and App will re-render
      navigate("/");
    } catch (err) {
      console.error(err);
      if (err.code === "auth/email-already-in-use") {
        setError("Email is already in use");
      } else {
        // If it was a backend error (not firebase auth), log them out so they aren't stuck
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
      className="relative min-h-screen flex flex-col items-center justify-center px-6"
    >
      {/* Back to Login Button */}
      <Link
        to="/"
        className="absolute top-8 left-8 text-zinc-400 hover:text-white transition-colors flex items-center gap-2 group"
      >
        <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
        <span className="font-medium">Back to Login</span>
      </Link>

      <div className="w-full max-w-md">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-12 text-center"
        >
          <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-4 block brand-font">
            New Account
          </span>
          <h1 className="text-5xl md:text-6xl font-medium tracking-tight mb-4 leading-[0.9]">
            Join the <br /> <span className="text-lime-400">System.</span>
          </h1>
          <p className="text-zinc-400 text-lg">
            Create an account to start your journey.
          </p>
        </motion.div>

        {/* Form */}
        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          onSubmit={handleSubmit}
          className="space-y-4"
        >
          {/* Name Input */}
          <div className="group relative bg-white/3 border border-white/5 rounded-3xl p-1 transition-colors hover:bg-white/5 focus-within:bg-white/8 focus-within:border-white/10">
            <input
              type="text"
              placeholder="Full Name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full h-16 bg-transparent px-6 text-lg outline-none text-white placeholder:text-zinc-600 rounded-3xl"
            />
          </div>

          {/* Email Input */}
          <div className="group relative bg-white/3 border border-white/5 rounded-3xl p-1 transition-colors hover:bg-white/5 focus-within:bg-white/8 focus-within:border-white/10">
            <input
              type="email"
              placeholder="Email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full h-16 bg-transparent px-6 text-lg outline-none text-white placeholder:text-zinc-600 rounded-3xl"
            />
          </div>

          {/* Password Input */}
          <div className="group relative bg-white/3 border border-white/5 rounded-3xl p-1 transition-colors hover:bg-white/5 focus-within:bg-white/8 focus-within:border-white/10">
            <input
              type="password"
              placeholder="Password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full h-16 bg-transparent px-6 text-lg outline-none text-white placeholder:text-zinc-600 rounded-3xl"
            />
          </div>

          {/* Confirm Password Input */}
          <div className="group relative bg-white/3 border border-white/5 rounded-3xl p-1 transition-colors hover:bg-white/5 focus-within:bg-white/8 focus-within:border-white/10">
            <input
              type="password"
              placeholder="Confirm Password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full h-16 bg-transparent px-6 text-lg outline-none text-white placeholder:text-zinc-600 rounded-3xl"
            />
          </div>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="flex items-center gap-2 text-red-500 bg-red-500/10 p-4 rounded-2xl"
            >
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm font-medium">{error}</span>
            </motion.div>
          )}

          {/* Submit Button */}
          <div className="pt-4 flex justify-center">
            <button
              type="submit"
              disabled={isLoading}
              className="group relative inline-flex items-center gap-4 px-10 py-5 bg-white text-black rounded-full hover:bg-lime-400 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed transition-colors duration-500 w-full justify-center md:w-auto"
            >
              {isLoading ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <>
                  <span className="text-xl font-bold tracking-tight">
                    Create Account
                  </span>
                  <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </div>
        </motion.form>
      </div>
    </motion.div>
  );
};
