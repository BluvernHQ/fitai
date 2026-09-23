import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, AlertCircle, Loader2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { register, logout } from "../firebase/auth";
import { registerCoach } from "../api/coach";
import { BrandMark, FieldShell } from "./ui";

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
      transition={{ duration: 0.7 }}
      className="auth-stage relative flex-1 w-full flex flex-col items-center justify-center px-4 py-10"
      style={{
        paddingTop: "max(2.5rem, env(safe-area-inset-top))",
        paddingBottom: "max(2.5rem, env(safe-area-inset-bottom))",
      }}
    >
      <div className="w-full max-w-md">
        <Link to="/" className="btn-ghost mb-6 -ml-1">
          <ArrowLeft className="w-4 h-4" />
          Back
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="mb-8 text-center"
        >
          <BrandMark size="lg" className="block mb-4" />
          <p className="text-zinc-400 text-base md:text-lg leading-relaxed">
            Create your coach workspace and start building smarter programs.
          </p>
        </motion.div>

        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12, duration: 0.5 }}
          onSubmit={handleSubmit}
          className="space-y-3"
        >
          {[
            { type: "text", placeholder: "Full name", value: name, set: setName, auto: "name" },
            {
              type: "email",
              placeholder: "Email",
              value: email,
              set: setEmail,
              auto: "email",
              mode: "email",
            },
            {
              type: "password",
              placeholder: "Password",
              value: password,
              set: setPassword,
              auto: "new-password",
            },
            {
              type: "password",
              placeholder: "Confirm password",
              value: confirmPassword,
              set: setConfirmPassword,
              auto: "new-password",
            },
          ].map((field) => (
            <FieldShell key={field.placeholder}>
              <input
                type={field.type}
                placeholder={field.placeholder}
                required
                autoComplete={field.auto}
                inputMode={field.mode}
                value={field.value}
                onChange={(e) => field.set(e.target.value)}
                className="w-full h-14 bg-transparent px-5 text-base outline-none text-white placeholder:text-zinc-600 rounded-2xl"
              />
            </FieldShell>
          ))}

          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="flex items-center gap-2 text-red-400 bg-red-500/10 border border-red-500/20 p-4 rounded-2xl"
            >
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span className="text-sm font-medium">{error}</span>
            </motion.div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="group btn-primary w-full min-h-14 text-base !rounded-full"
            >
              {isLoading ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <>
                  <span>Create account</span>
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
