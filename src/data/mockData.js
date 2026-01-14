export const MOVEMENTS = [
  {
    id: "squat",
    label: "Deep Squat",
    description: "Hips below knees, torso upright",
  },
  {
    id: "hurdle",
    label: "Hurdle Step",
    description: "Step over hurdle, maintain alignment",
  },
  {
    id: "lunge",
    label: "Inline Lunge",
    description: "Heel-to-toe stance, knee touches floor",
  },
  {
    id: "shoulder",
    label: "Shoulder Mobility",
    description: "Fists within one hand length",
  },
  {
    id: "leg_raise",
    label: "Active Straight Leg Raise",
    description: "Ankle posture past mid-thigh",
  },
  {
    id: "pushup",
    label: "Trunk Stability Pushup",
    description: "Spine neutral during pushup",
  },
  {
    id: "rotary",
    label: "Rotary Stability",
    description: "Same side arm/leg touch",
  },
];

export const generatePlan = (scores) => {
  // Mock AI Latency
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        session_title: "Squat Pattern Strength Development",
        coach_summary:
          "Analysis of FMS scores indicates a need for high-threshold motor unit recruitment while maintaining the acceptable mobility baseline established in the squat pattern.",
        exercises: [
          {
            name: "Tempo Goblet Squats",
            tag: "Structural Integrity",
            rx: "4 sets x 8 reps",
            tempo: "3-1-X-1",
            coach_tip:
              "Focus on maintaining spinal rigidity during the eccentric phase. Do not bottom out.",
          },
          {
            name: "Pallof Press ISO",
            tag: "Anti-Rotation",
            rx: "3 sets x 30s / side",
            tempo: "Isometric",
            coach_tip:
              "Resist the band's pull. Imagine your core is made of iron.",
          },
          {
            name: "KB Swing (Hardstyle)",
            tag: "Power Output",
            rx: "5 sets x 10 reps",
            tempo: "Explosive",
            coach_tip:
              "Snap the hips. The bell should float at the top. Maximize hip extension velocity.",
          },
        ],
      });
    }, 2500); // 2.5s simulated think time
  });
};
