import { useState } from "react";
import { AnimatePresence } from "framer-motion";
import { MOVEMENTS } from "./data/mockData";
import { generateWorkoutPlan } from "./services/api";
import { Navbar } from "./components/Navbar";
import { InputView } from "./components/InputView";
import { ProcessingView } from "./components/ProcessingView";
import { ResultsView } from "./components/ResultsView";

export default function App() {
  const [view, setView] = useState("input"); // input | processing | results
  const [scores, setScores] = useState(
    MOVEMENTS.reduce((acc, m) => ({ ...acc, [m.id]: 2 }), {})
  );
  const [workout, setWorkout] = useState(null);

  const handleScoreChange = (id, val) => {
    setScores((prev) => ({ ...prev, [id]: val }));
  };

  const startAnalysis = async () => {
    setView("processing");

    try {
      const data = await generateWorkoutPlan(scores);
      setWorkout(data);
      setView("results");
    } catch (error) {
      // Error is already logged in the service
      alert(
        "Something went wrong. Please check your connection and try again."
      );
      setView("input");
    }
  };

  const reset = () => {
    setView("input");
    setWorkout(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-lime-500/30">
      <Navbar />

      <AnimatePresence mode="wait">
        {view === "input" && (
          <InputView
            scores={scores}
            onScoreChange={handleScoreChange}
            onGenerate={startAnalysis}
          />
        )}

        {view === "processing" && <ProcessingView />}

        {view === "results" && workout && (
          <ResultsView workout={workout} onReset={reset} />
        )}
      </AnimatePresence>
    </div>
  );
}
