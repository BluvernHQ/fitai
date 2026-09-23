/** Compact forms for non-FMS baseline batteries. */

const fieldClass =
  "mt-2 w-full bg-black/40 border border-white/15 rounded-xl px-4 py-3.5 text-white outline-none focus:border-lime-400/40";

export const BreathingForm = ({ value = {}, onChange }) => {
  const set = (key, v) => onChange({ ...value, [key]: v });
  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">
        BOLT (FRC) and TLC breath-hold times in seconds. Red / yellow / green bands score automatically.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-xs uppercase tracking-widest text-zinc-500">BOLT (seconds)</span>
          <input
            type="number"
            min="0"
            inputMode="decimal"
            value={value.bolt_seconds ?? ""}
            onChange={(e) => set("bolt_seconds", e.target.value)}
            className={fieldClass}
          />
          <span className="text-[11px] text-zinc-600 mt-1 block">Red &lt;35 · Yellow 36–60 · Green &gt;60</span>
        </label>
        <label className="block">
          <span className="text-xs uppercase tracking-widest text-zinc-500">TLC hold (seconds)</span>
          <input
            type="number"
            min="0"
            inputMode="decimal"
            value={value.tlc_seconds ?? ""}
            onChange={(e) => set("tlc_seconds", e.target.value)}
            className={fieldClass}
          />
          <span className="text-[11px] text-zinc-600 mt-1 block">Red &lt;45 · Yellow 45–90 · Green &gt;90</span>
        </label>
      </div>
      <label className="block">
        <span className="text-xs uppercase tracking-widest text-zinc-500">Notes</span>
        <textarea
          rows={3}
          value={value.comment || ""}
          onChange={(e) => set("comment", e.target.value)}
          className={`${fieldClass} resize-y min-h-[5rem]`}
          placeholder="Breathing pattern, nasal vs mouth, etc."
        />
      </label>
    </div>
  );
};

const BEIGHTON_POINTS = [
  { key: "little_finger_rt", label: "Little finger RT" },
  { key: "little_finger_lt", label: "Little finger LT" },
  { key: "thumb_rt", label: "Thumb RT" },
  { key: "thumb_lt", label: "Thumb LT" },
  { key: "elbow_rt", label: "Elbow RT" },
  { key: "elbow_lt", label: "Elbow LT" },
  { key: "knee_rt", label: "Knee RT" },
  { key: "knee_lt", label: "Knee LT" },
  { key: "straight_leg", label: "Trunk / palms floor" },
];

export const BeightonForm = ({ value = {}, onChange }) => {
  const toggle = (key) => onChange({ ...value, [key]: value[key] ? 0 : 1 });
  const total = BEIGHTON_POINTS.reduce((sum, p) => sum + (value[p.key] ? 1 : 0), 0);
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-zinc-400">Tap each positive hypermobility sign (max 9).</p>
        <span className="text-lg font-display font-bold tabular-nums text-lime-400">{total}/9</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {BEIGHTON_POINTS.map((p) => {
          const on = Boolean(value[p.key]);
          return (
            <button
              key={p.key}
              type="button"
              onClick={() => toggle(p.key)}
              className={`min-h-12 px-4 rounded-xl text-left text-sm border transition-colors ${
                on
                  ? "bg-lime-400/15 border-lime-400/40 text-lime-200"
                  : "bg-white/[0.03] border-white/10 text-zinc-400 hover:text-white"
              }`}
            >
              {p.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export const McGillForm = ({ value = {}, onChange }) => {
  const set = (key, v) => onChange({ ...value, [key]: v });
  const fields = [
    ["flexor_seconds", "Trunk flexor (sec)"],
    ["lateral_right_seconds", "Lateral R (sec)"],
    ["lateral_left_seconds", "Lateral L (sec)"],
    ["extensor_seconds", "Trunk extensor (sec)"],
  ];
  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">
        Hold times in seconds. Ratios (flex:ext, L:R bridges, side:ext) are computed on generate.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {fields.map(([key, label]) => (
          <label key={key} className="block">
            <span className="text-xs uppercase tracking-widest text-zinc-500">{label}</span>
            <input
              type="number"
              min="0"
              inputMode="decimal"
              value={value[key] ?? ""}
              onChange={(e) => set(key, e.target.value)}
              className={fieldClass}
            />
          </label>
        ))}
      </div>
      <label className="block">
        <span className="text-xs uppercase tracking-widest text-zinc-500">Comments</span>
        <textarea
          rows={3}
          value={value.comment || ""}
          onChange={(e) => set("comment", e.target.value)}
          className={`${fieldClass} resize-y min-h-[5rem]`}
        />
      </label>
    </div>
  );
};

const BUNKIE_LINES = [
  { key: "anterior_power", label: "Anterior Power Line", floor: "30–45s" },
  { key: "lateral_power", label: "Lateral Power Line", floor: "30–45s" },
  { key: "posterior_power", label: "Posterior Power Line", floor: "30–45s" },
  { key: "posterior_stabilizing", label: "Posterior Stabilizing Line", floor: "30–45s" },
  { key: "medial_stabilizing", label: "Medial Stabilizing Line", floor: "25–40s" },
];

export const BunkieForm = ({ value = {}, onChange }) => {
  const setLine = (key, side, v) => {
    const row = { ...(value[key] || {}) };
    row[side] = v;
    onChange({ ...value, [key]: row });
  };
  return (
    <div className="space-y-5">
      <p className="text-sm text-zinc-400">
        Hold each line left and right to fatigue or normative time. Note compensations per line.
      </p>
      {BUNKIE_LINES.map((line) => {
        const row = value[line.key] || {};
        return (
          <div key={line.key} className="surface p-4 space-y-3">
            <div className="flex items-baseline justify-between gap-2">
              <h4 className="font-display font-medium text-white">{line.label}</h4>
              <span className="text-[11px] text-zinc-500">Norm {line.floor}</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {["left", "right"].map((side) => (
                <label key={side} className="block">
                  <span className="text-xs uppercase tracking-widest text-zinc-500">{side}</span>
                  <input
                    type="number"
                    min="0"
                    inputMode="decimal"
                    value={row[side] ?? ""}
                    onChange={(e) => setLine(line.key, side, e.target.value)}
                    className={fieldClass}
                    placeholder="sec"
                  />
                </label>
              ))}
            </div>
            <input
              type="text"
              value={row.comment || ""}
              onChange={(e) => setLine(line.key, "comment", e.target.value)}
              className={fieldClass}
              placeholder="Compensations / notes"
            />
          </div>
        );
      })}
    </div>
  );
};

export const EnduranceForm = ({ value = {}, onChange }) => {
  const set = (key, v) => onChange({ ...value, [key]: v });
  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">Reps in 1 minute (or to form break). Calf raises are side-specific.</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[
          ["push_ups", "Push-ups"],
          ["squats", "Squats"],
          ["pull_ups", "Pull-ups (optional)"],
        ].map(([key, label]) => (
          <label key={key} className="block">
            <span className="text-xs uppercase tracking-widest text-zinc-500">{label}</span>
            <input
              type="number"
              min="0"
              inputMode="numeric"
              value={value[key] ?? ""}
              onChange={(e) => set(key, e.target.value)}
              className={fieldClass}
            />
          </label>
        ))}
      </div>
      <div className="surface p-4">
        <p className="text-xs uppercase tracking-widest text-zinc-500 mb-3">Calf raises</p>
        <div className="grid grid-cols-2 gap-3">
          {["left", "right"].map((side) => (
            <label key={side} className="block">
              <span className="text-xs uppercase tracking-widest text-zinc-500">{side}</span>
              <input
                type="number"
                min="0"
                inputMode="numeric"
                value={value.calf_raises?.[side] ?? ""}
                onChange={(e) =>
                  set("calf_raises", { ...(value.calf_raises || {}), [side]: e.target.value })
                }
                className={fieldClass}
              />
            </label>
          ))}
        </div>
      </div>
      <label className="block">
        <span className="text-xs uppercase tracking-widest text-zinc-500">Notes</span>
        <textarea
          rows={3}
          value={value.comment || ""}
          onChange={(e) => set("comment", e.target.value)}
          className={`${fieldClass} resize-y min-h-[5rem]`}
        />
      </label>
    </div>
  );
};
