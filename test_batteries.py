"""Unit tests for modular batteries, fusion, and load calculator."""

import unittest

from src.logic.assessment_fusion import analyze_assessment_session, normalize_session
from src.logic.batteries import (
    score_beighton,
    score_breathing,
    score_bunkie,
    score_mcgill,
    score_muscular_endurance,
)
from src.logic.load_calculator import estimate_1rm, percent_1rm_for, pro_rata_maxes


class BatteryScorerTests(unittest.TestCase):
    def test_breathing_bands(self):
        red = score_breathing({"bolt_seconds": 20, "tlc_seconds": 30})
        self.assertEqual(red["bolt_band"], "red")
        self.assertEqual(red["tlc_band"], "red")
        self.assertEqual(red["band"], "red")
        green = score_breathing({"bolt_seconds": 70, "tlc_seconds": 100})
        self.assertEqual(green["band"], "green")

    def test_beighton_hypermobile(self):
        data = {k: 1 for k in [
            "little_finger_rt", "little_finger_lt", "thumb_rt", "thumb_lt",
            "elbow_rt", "elbow_lt", "knee_rt", "knee_lt", "straight_leg",
        ]}
        result = score_beighton(data, age=25)
        self.assertEqual(result["total"], 9)
        self.assertTrue(result["hypermobile"])
        self.assertIn("stability", result["needs_hints"])

    def test_mcgill_ratios(self):
        result = score_mcgill({
            "flexor_seconds": 120,
            "extensor_seconds": 90,
            "lateral_right_seconds": 80,
            "lateral_left_seconds": 40,
        })
        self.assertGreaterEqual(result["ratios"]["flexion_extension"], 1.0)
        self.assertIn("lateral_asymmetry", result["flags"])
        self.assertIn("stability", result["needs_hints"])

    def test_bunkie_asymmetry_and_weak(self):
        result = score_bunkie({
            "anterior_power": {"left": 45, "right": 50},
            "lateral_power": {"left": 40, "right": 42},
            "posterior_power": {"left": 20, "right": 26},
            "posterior_stabilizing": {"left": 48, "right": 28},
            "medial_stabilizing": {"left": 47, "right": 30},
        })
        self.assertGreaterEqual(result["weak_line_count"], 1)
        self.assertIn("asymmetry", result["needs_hints"])

    def test_muscular_endurance_low(self):
        result = score_muscular_endurance(
            {"push_ups": 8, "squats": 40, "calf_raises": {"left": 10, "right": 12}},
            gender="male",
        )
        lows = [t for t in result["tests"] if t.get("low")]
        self.assertTrue(lows)
        self.assertIn("endurance", result["needs_hints"])


class FusionTests(unittest.TestCase):
    def test_legacy_fms_normalizes(self):
        profile = {k: {"score": 3} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        session = normalize_session(profile)
        self.assertEqual(session["selected_batteries"], ["fms"])
        self.assertIn("fms", session["batteries"])
        analysis = analyze_assessment_session(profile, use_manual_scores=True)
        self.assertEqual(analysis["total_score"], 21)
        self.assertIn("fms", analysis["battery_results"])

    def test_fms_plus_bunkie(self):
        fms = {k: {"score": 2} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        payload = {
            "selected_batteries": ["fms", "bunkie"],
            "batteries": {
                "fms": fms,
                "bunkie": {
                    "posterior_power": {"left": 15, "right": 16},
                    "anterior_power": {"left": 40, "right": 41},
                    "lateral_power": {"left": 40, "right": 40},
                    "posterior_stabilizing": {"left": 35, "right": 35},
                    "medial_stabilizing": {"left": 30, "right": 30},
                },
            },
            "use_manual_scores": True,
        }
        analysis = analyze_assessment_session(payload)
        self.assertIn("bunkie", analysis["battery_results"])
        self.assertIn("fms", analysis["battery_results"])
        self.assertTrue(any("Bunkie" in f or "Posterior" in f for f in analysis["findings"]))

    def test_without_fms_still_programs(self):
        payload = {
            "selected_batteries": ["beighton", "mcgill"],
            "batteries": {
                "beighton": {
                    "little_finger_rt": 1, "little_finger_lt": 1, "thumb_rt": 1, "thumb_lt": 1,
                    "elbow_rt": 0, "elbow_lt": 0, "knee_rt": 0, "knee_lt": 0, "straight_leg": 0,
                },
                "mcgill": {
                    "flexor_seconds": 100,
                    "extensor_seconds": 60,
                    "lateral_right_seconds": 50,
                    "lateral_left_seconds": 50,
                },
            },
        }
        analysis = analyze_assessment_session(payload, athlete_context={"age": 30})
        self.assertNotIn("fms", analysis["battery_results"])
        self.assertIn(analysis["status"], {"MOBILITY", "STABILITY", "STRENGTH", "PATTERN"})
        self.assertEqual(len(analysis["effective_scores"]), 7)


class LoadCalculatorTests(unittest.TestCase):
    def test_percent_table(self):
        self.assertEqual(percent_1rm_for(1, 10), 1.0)
        self.assertAlmostEqual(percent_1rm_for(5, 10), 0.863, places=3)

    def test_estimate_1rm(self):
        # 95kg × 5 @ RPE10 ≈ 95 / 0.863
        result = estimate_1rm(95, 5, 10)
        self.assertEqual(result["method"], "sheet_reps_rpe")
        self.assertGreater(result["estimated_1rm"], 100)

    def test_pro_rata(self):
        maxes = pro_rata_maxes(100, "back_squat")
        self.assertEqual(maxes["back_squat"], 100)
        self.assertEqual(maxes["front_squat"], 85.0)
        self.assertEqual(maxes["bench_press"], 75.0)


if __name__ == "__main__":
    unittest.main()
