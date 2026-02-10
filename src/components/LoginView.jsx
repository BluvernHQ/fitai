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
      // AuthProvider will detect change and App will re-render
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
      className="relative min-h-screen flex flex-col items-center justify-center px-6"
    >
      <div className="w-full max-w-md">
        {/* Sign Up Link */}
        <Link
          to="/signup"
          className="absolute top-8 right-8 text-zinc-400 hover:text-white transition-colors text-sm font-medium"
        >
          Sign Up
        </Link>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-12 text-center"
        >
          <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-4 block brand-font">
            System Access
          </span>
          <h1 className="text-5xl md:text-6xl font-medium tracking-tight mb-4 leading-[0.9]">
            Welcome <br /> <span className="text-zinc-600">Back.</span>
          </h1>
          <p className="text-zinc-400 text-lg">
            Sign in to continue your programming.
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
                    Enter System
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
