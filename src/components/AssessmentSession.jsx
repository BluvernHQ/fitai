import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useLocation, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Check, Loader2 } from "lucide-react";
import { getAssessmentBatteries, submitAssessmentSession } from "../api/fms";
import { PageShell, PageHeader, Button, Surface } from "./ui";
import { FMSAssessment } from "./FMSAssessment";
import {
  BeightonForm,
  BreathingForm,
  BunkieForm,
  EnduranceForm,
  McGillForm,
} from "./batteryForms";

const DEFAULT_BATTERIES = [
  { id: "breathing", label: "Breathing Screen", short_label: "Breathing" },
  { id: "beighton", label: "Beighton Score", short_label: "Beighton" },
  { id: "fms", label: "Functional Movement Screen", short_label: "FMS" },
  { id: "mcgill", label: "McGill Torso Endurance", short_label: "McGill" },
  { id: "bunkie", label: "Bunkie Test", short_label: "Bunkie" },
  { id: "muscular_endurance", label: "Muscular Endurance", short_label: "Endurance" },
];

const FORM_BY_ID = {
  breathing: BreathingForm,
  beighton: BeightonForm,
  mcgill: McGillForm,
  bunkie: BunkieForm,
  muscular_endurance: EnduranceForm,
};

export const AssessmentSession = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const studentName = location.state?.studentName || "Athlete";

  const preset = useMemo(() => {
    const raw = searchParams.get("batteries") || location.state?.batteries;
    if (!raw) return ["fms"];
    if (Array.isArray(raw)) return raw;
    return String(raw)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }, [searchParams, location.state]);

  const [catalog, setCatalog] = useState(DEFAULT_BATTERIES);
  const [phase, setPhase] = useState("hub"); // hub | step | review
  const [selected, setSelected] = useState(() => new Set(preset.length ? preset : ["fms"]));
  const [stepIndex, setStepIndex] = useState(0);
  const [batteries, setBatteries] = useState({});
  const [sessionNotes, setSessionNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getAssessmentBatteries()
      .then((data) => {
        if (data?.batteries?.length) setCatalog(data.batteries);
        if (data?.default_selected?.length && selected.size === 0) {
          setSelected(new Set(data.default_selected));
        }
      })
      .catch(() => {});
  }, []);

  const orderedSelected = useMemo(() => {
    const order = catalog.map((b) => b.id);
    return order.filter((bid) => selected.has(bid));
  }, [catalog, selected]);

  const currentId = orderedSelected[stepIndex];
  const currentMeta = catalog.find((b) => b.id === currentId);

  const toggle = (bid) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(bid)) next.delete(bid);
      else next.add(bid);
      return next;
    });
  };

  const start = () => {
    if (!orderedSelected.length) {
      setError("Select at least one battery.");
      return;
    }
    setError(null);
    setStepIndex(0);
    setPhase("step");
  };

  const goNextFromStep = () => {
    if (stepIndex >= orderedSelected.length - 1) {
      setPhase("review");
      return;
    }
    setStepIndex((i) => i + 1);
  };

  const handleGenerate = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        student_id: Number(id),
        selected_batteries: orderedSelected,
        batteries,
        session_notes: sessionNotes,
        use_manual_scores: false,
        athlete_context: location.state?.athleteContext || {},
      };
      const result = await submitAssessmentSession(payload);
      const dest = result?.id
        ? `/coach/student/${id}/program/${result.id}`
        : `/coach/student/${id}/workout/current`;
      navigate(dest, {
        state: { workout: result, programId: result.id, assessmentId: result.assessment_id },
      });
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not generate program.");
    } finally {
      setSubmitting(false);
    }
  };

  if (phase === "step" && currentId === "fms") {
    return (
      <FMSAssessment
        embedded
        initialFms={batteries.fms}
        onComplete={(fmsPayload) => {
          setBatteries((prev) => ({ ...prev, fms: fmsPayload }));
          goNextFromStep();
        }}
        onBack={() => {
          if (stepIndex === 0) setPhase("hub");
          else setStepIndex((i) => i - 1);
        }}
        continueLabel={
          stepIndex >= orderedSelected.length - 1 ? "Review session" : "Next battery"
        }
      />
    );
  }

  return (
    <PageShell size="md">
      <button
        type="button"
        onClick={() => {
          if (phase === "hub") navigate(`/coach/student/${id}`);
          else if (phase === "review") setPhase("step");
          else if (stepIndex === 0) setPhase("hub");
          else setStepIndex((i) => i - 1);
        }}
        className="btn-ghost mb-4 -ml-1"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      {phase === "hub" && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <PageHeader
            eyebrow="Baseline assessment"
            title={studentName}
            accent="session"
            description="Select which batteries to run. FMS is recommended for most athletes — others are optional."
          />
          <div className="space-y-2 mb-6">
            {catalog.map((b) => {
              const on = selected.has(b.id);
              return (
                <button
                  key={b.id}
                  type="button"
                  onClick={() => toggle(b.id)}
                  className={`w-full flex items-center gap-4 p-4 rounded-2xl border text-left transition-colors ${
                    on
                      ? "border-lime-400/40 bg-lime-400/10"
                      : "border-white/10 bg-white/[0.03] hover:border-white/20"
                  }`}
                >
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-md border ${
                      on ? "bg-lime-400 border-lime-400 text-black" : "border-white/20 text-transparent"
                    }`}
                  >
                    <Check className="w-4 h-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="font-display font-medium text-white">{b.label}</p>
                    <p className="text-xs text-zinc-500">{b.short_label}</p>
                  </div>
                  {b.id === "fms" && (
                    <span className="ml-auto text-[10px] uppercase tracking-widest text-lime-400/80">
                      Common
                    </span>
                  )}
                </button>
              );
            })}
          </div>
          <label className="block mb-6">
            <span className="text-xs uppercase tracking-widest text-zinc-500">Session notes</span>
            <textarea
              rows={2}
              value={sessionNotes}
              onChange={(e) => setSessionNotes(e.target.value)}
              className="mt-2 w-full bg-black/40 border border-white/15 rounded-xl px-4 py-3 text-white"
              placeholder="Optional coach notes for this session"
            />
          </label>
          {error && <p className="text-sm text-red-400 mb-3">{error}</p>}
          <Button onClick={start} className="w-full sm:w-auto min-h-12">
            Start assessment ({orderedSelected.length})
          </Button>
        </motion.div>
      )}

      {phase === "step" && currentId && currentId !== "fms" && (
        <motion.div key={currentId} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <p className="eyebrow mb-2">
            Battery {stepIndex + 1} / {orderedSelected.length}
          </p>
          <h1 className="display-title text-3xl md:text-4xl mb-6">{currentMeta?.label}</h1>
          <Surface className="p-5 md:p-6 mb-6">
            {(() => {
              const Form = FORM_BY_ID[currentId];
              if (!Form) return <p className="text-zinc-500">Unknown battery.</p>;
              return (
                <Form
                  value={batteries[currentId] || {}}
                  onChange={(next) => setBatteries((prev) => ({ ...prev, [currentId]: next }))}
                />
              );
            })()}
          </Surface>
          <div className="flex flex-col sm:flex-row flex-wrap gap-3 pb-[env(safe-area-inset-bottom,0px)]">
            <Button variant="secondary" onClick={() => goNextFromStep()} className="w-full sm:w-auto">
              Skip / continue
            </Button>
            <Button onClick={() => goNextFromStep()} className="w-full sm:w-auto">
              {stepIndex >= orderedSelected.length - 1 ? "Review" : "Next"}
            </Button>
          </div>
        </motion.div>
      )}

      {phase === "review" && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <PageHeader
            eyebrow="Review"
            title="Ready to"
            accent="generate"
            description="AI will interpret only the batteries you completed and build the week from that profile."
          />
          <div className="space-y-3 mb-8">
            {orderedSelected.map((bid) => {
              const meta = catalog.find((b) => b.id === bid);
              const hasData = batteries[bid] && Object.keys(batteries[bid]).length > 0;
              return (
                <Surface key={bid} className="p-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">{meta?.label || bid}</p>
                    <p className="text-xs text-zinc-500">{hasData ? "Data captured" : "No inputs yet"}</p>
                  </div>
                  <button
                    type="button"
                    className="text-sm text-lime-400 min-h-11 px-3"
                    onClick={() => {
                      setStepIndex(orderedSelected.indexOf(bid));
                      setPhase("step");
                    }}
                  >
                    Edit
                  </button>
                </Surface>
              );
            })}
          </div>
          {error && <p className="text-sm text-red-400 mb-3">{error}</p>}
          <Button onClick={handleGenerate} disabled={submitting} className="w-full sm:w-auto min-h-12">
            {submitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" /> Generating…
              </>
            ) : (
              "Generate week"
            )}
          </Button>
        </motion.div>
      )}
    </PageShell>
  );
};
