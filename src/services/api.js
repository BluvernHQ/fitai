export const generateWorkoutPlan = async (scores) => {
  try {
    // Map internal IDs to API expected keys
    const payload = {
      deep_squat: scores.squat,
      hurdle_step: scores.hurdle,
      inline_lunge: scores.lunge,
      shoulder_mobility: scores.shoulder,
      active_straight_leg_raise: scores.leg_raise,
      trunk_stability_pushup: scores.pushup,
      rotary_stability: scores.rotary,
    };

    // Use the proxy path /api which redirects to https://fms-rag-app.onrender.com
    const response = await fetch("/api/generate-workout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to generate workout:", error);
    throw error;
  }
};
