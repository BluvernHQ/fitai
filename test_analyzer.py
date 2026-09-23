import unittest
from src.logic.fms_analyzer import analyze_fms_profile, calculate_score_from_faults


class AnalyzerTests(unittest.TestCase):
    def test_heels_lift_is_score_two_not_one(self):
        data = {
            "score": 0,
            "trunk_torso": {"upright_torso": 1, "excessive_forward_lean": 0, "rib_flare": 0, "lumbar_flexion": 0, "lumbar_extension_sway_back": 0},
            "lower_limb": {"knees_track_over_toes": 1, "knee_valgus": 0, "knee_varus": 0, "uneven_depth": 0},
            "feet": {"heels_stay_down": 0, "heels_lift": 1, "excessive_pronation": 0, "excessive_supination": 0},
            "upper_body_bar_position": {"bar_aligned_over_mid_foot": 1, "bar_drifts_forward": 0, "arms_fall_forward": 0, "shoulder_mobility_restriction_suspected": 0},
        }
        self.assertEqual(calculate_score_from_faults("overhead_squat", data), 2)

    def test_blank_profile_does_not_stop(self):
        profile = {k: {} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        result = analyze_fms_profile(profile)
        self.assertNotEqual(result["status"], "STOP")
        self.assertEqual(result["total_score"], 0)
        self.assertTrue(result["incomplete_screens"])
        self.assertEqual(len(result["incomplete_screens"]), 7)

    def test_unscored_side_zero_without_pain_is_not_stop_when_omitted(self):
        profile = {k: {"score": 2} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        profile["hurdle_step"] = {"score": 2, "l_score": None, "r_score": None}
        result = analyze_fms_profile(profile, use_manual_scores=True)
        self.assertNotEqual(result["status"], "STOP")
        self.assertEqual(result["effective_scores"]["hurdle_step"], 2)

    def test_quality_observations_are_not_faults(self):
        profile = {
            "overhead_squat": {
                "score": 3,
                "trunk_torso": {"upright_torso": 1},
                "lower_limb": {"knees_track_over_toes": 1},
                "feet": {"heels_stay_down": 1},
                "upper_body_bar_position": {"bar_aligned_over_mid_foot": 1},
            }
        }
        for key in [
            "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]:
            profile[key] = {"score": 3}
        result = analyze_fms_profile(profile)
        fault_names = {f["fault"] for f in result["faults"]}
        self.assertNotIn("upright_torso", fault_names)
        self.assertNotIn("knees_track_over_toes", fault_names)
        self.assertNotIn("heels_stay_down", fault_names)

    def test_score_zero_is_pain(self):
        profile = {k: {"score": 2} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        profile["overhead_squat"] = {"score": 0}
        result = analyze_fms_profile(profile, use_manual_scores=True)
        self.assertEqual(result["status"], "STOP")

    def test_pain_stops(self):
        profile = {k: {"score": 2} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        profile["shoulder_mobility"] = {"score": 0, "clearing_pain": True}
        result = analyze_fms_profile(profile, use_manual_scores=True)
        self.assertEqual(result["status"], "STOP")
        self.assertIn("pain-stop", result["needs"])

    def test_manual_score_cannot_outrank_major_faults(self):
        profile = {k: {"score": 2} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        profile["overhead_squat"] = {
            "score": 2,
            "trunk_torso": {"excessive_forward_lean": 1},
            "feet": {"heels_lift": 1},
            "upper_body_bar_position": {"arms_fall_forward": 1},
        }
        result = analyze_fms_profile(profile, use_manual_scores=True)
        self.assertEqual(result["effective_scores"]["overhead_squat"], 1)
        self.assertNotEqual(result["status"], "STRENGTH")

    def test_min_side_score(self):
        profile = {k: {"score": 3} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        profile["hurdle_step"] = {"score": 3, "l_score": 1, "r_score": 3}
        result = analyze_fms_profile(profile, use_manual_scores=True)
        self.assertEqual(result["effective_scores"]["hurdle_step"], 1)

    def test_fusion_legacy_still_scores_when_manual(self):
        """Manual scores without side nests still work when coach enters them."""
        profile = {k: {"score": 3} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        result = analyze_fms_profile(profile, use_manual_scores=True)
        self.assertEqual(result["total_score"], 21)
        self.assertEqual(result["incomplete_screens"], [])

    def test_left_right_nests_scored_independently(self):
        profile = {k: {"score": 3} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        profile["hurdle_step"] = {
            "left": {
                "pelvis_core_control": {"loss_of_balance": 1},
                "stepping_leg": {"toe_drag": 1},
                "stance_leg": {},
            },
            "right": {
                "pelvis_core_control": {"pelvis_stable": 1},
                "stepping_leg": {"clears_hurdle_smoothly": 1},
                "stance_leg": {},
            },
        }
        profile["inline_lunge"] = {
            "left": {
                "alignment": {},
                "lower_body_control": {},
                "balance_stability": {"stable_throughout": 1},
            },
            "right": {
                "alignment": {"lateral_shift": 1},
                "lower_body_control": {},
                "balance_stability": {},
            },
        }
        result = analyze_fms_profile(profile, use_manual_scores=False)
        self.assertEqual(result["side_scores"]["hurdle_step"]["l"], 1)
        self.assertEqual(result["side_scores"]["hurdle_step"]["r"], 3)
        self.assertEqual(result["effective_scores"]["hurdle_step"], 1)
        self.assertEqual(result["side_scores"]["inline_lunge"]["l"], 3)
        self.assertEqual(result["side_scores"]["inline_lunge"]["r"], 2)
        self.assertEqual(result["effective_scores"]["inline_lunge"], 2)
        self.assertIn("asymmetry", result["needs"])
        left_faults = [f for f in result["faults"] if f.get("side") == "left" and f["test"] == "hurdle_step"]
        self.assertTrue(left_faults)

    def test_asymmetrical_requires_both_sides(self):
        profile = {k: {"score": 3} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        profile["hurdle_step"] = {
            "left": {
                "pelvis_core_control": {"loss_of_balance": 1},
                "stepping_leg": {"toe_drag": 1},
                "stance_leg": {},
            },
            "right": {
                "pelvis_core_control": {},
                "stepping_leg": {},
                "stance_leg": {},
            },
        }
        result = analyze_fms_profile(profile, use_manual_scores=False)
        self.assertIsNone(result["effective_scores"]["hurdle_step"])
        self.assertIn("hurdle_step", result["incomplete_screens"])
        self.assertEqual(result["side_scores"]["hurdle_step"]["l"], 1)
        self.assertIsNone(result["side_scores"]["hurdle_step"]["r"])


if __name__ == "__main__":
    unittest.main()
