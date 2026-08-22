import unittest

from src.logic.prescription import assemble_weekly_program, load_catalog


class PrescriptionTests(unittest.TestCase):
    def test_catalog_loaded(self):
        catalog = load_catalog()
        self.assertGreaterEqual(len(catalog), 1000)
        self.assertTrue(any(e.get("ramp_role") == "raise" for e in catalog))

    def test_heels_lift_avoids_barbell_main(self):
        profile = {
            "use_manual_scores": False,
            "overhead_squat": {
                "score": 2,
                "comment": "heels lift on the descent",
                "trunk_torso": {"upright_torso": 1, "excessive_forward_lean": 0, "rib_flare": 0, "lumbar_flexion": 0, "lumbar_extension_sway_back": 0},
                "lower_limb": {"knees_track_over_toes": 1, "knee_valgus": 0, "knee_varus": 0, "uneven_depth": 0},
                "feet": {"heels_stay_down": 0, "heels_lift": 1, "excessive_pronation": 0, "excessive_supination": 0},
                "upper_body_bar_position": {"bar_aligned_over_mid_foot": 1, "bar_drifts_forward": 0, "arms_fall_forward": 0, "shoulder_mobility_restriction_suspected": 0},
            },
            "hurdle_step": {"score": 2},
            "inline_lunge": {"score": 2},
            "shoulder_mobility": {"score": 2},
            "active_straight_leg_raise": {"score": 2},
            "trunk_stability_pushup": {"score": 2},
            "rotary_stability": {"score": 2},
        }
        plan = assemble_weekly_program(profile, days_per_week=3)
        self.assertNotEqual(plan["status"], "STOP")
        ramp_names = " ".join(i["name"] for d in plan["days"] for i in d["blocks"]["ramp"]).upper()
        mains = [i for d in plan["days"] for i in d["blocks"].get("block_a", [])]
        plyo = [
            i for d in plan["days"] for i in d["blocks"].get("block_a", [])
            if (i.get("pattern") == "plyo" or "JUMP" in (i.get("name") or "").upper() or "DEPTH" in (i.get("name") or "").upper())
            and not i.get("unfilled")
        ]
        self.assertTrue(ramp_names)
        self.assertTrue(mains)
        self.assertEqual(plyo, [])
        squat_slots = [i for i in mains if "SQUAT" in (i.get("role") or "")]
        for item in squat_slots:
            if item.get("unfilled"):
                continue
            self.assertEqual(item.get("pattern"), "squat")

    def test_pick_does_not_drop_pattern(self):
        from src.logic.prescription import _pick, load_catalog, load_methodology
        catalog = load_catalog()
        selected, _cands, reasons = _pick(
            catalog,
            tags={"pattern_squat"},
            target_level=5,
            priors={},
            ctx="test",
            count=1,
            pattern="squat",
            program_role="main",
        )
        self.assertTrue(selected or reasons)
        if selected:
            self.assertEqual(selected[0][0]["pattern"], "squat")

    def test_session_schema_v2_blocks_and_rpe(self):
        profile = {k: {"score": 2} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        plan = assemble_weekly_program(profile, days_per_week=3, lift_maxes={"back_squat": 100, "deadlift": 140})
        self.assertEqual(plan["schema_version"], 3)
        self.assertEqual(len(plan["days"]), 3)
        self.assertIn("mesocycle", plan)
        roles = [i.get("role") for d in plan["days"] for i in d["blocks"].get("block_a", [])]
        self.assertFalse(any(r == "HIP THRUSTERS" for r in roles))
        self.assertTrue(any(i.get("score_breakdown") for d in plan["days"] for i in d["blocks"].get("block_a", []) if not i.get("unfilled")))
        self.assertEqual(len(plan["calendar"]), 7)
        day = plan["days"][0]
        self.assertGreaterEqual(len(day["blocks"]["block_a"]), 2)
        self.assertGreaterEqual(len(day["blocks"]["block_b"]), 2)
        self.assertTrue(any(i.get("reps_rpe") for i in day["blocks"]["block_a"]))
        loaded = [
            i
            for i in day["blocks"]["block_a"] + day["blocks"]["block_b"]
            if i.get("load")
        ]
        self.assertTrue(loaded)
        self.assertTrue(day["blocks"]["block_a"][-1].get("circuit_end"))
        gym_days = [c for c in plan["calendar"] if c["kind"] == "gym"]
        self.assertEqual(len(gym_days), 3)
        self.assertTrue(all(c.get("tone") for c in plan["calendar"]))

    def test_coach_prior_boosts_rank(self):
        from src.logic.prescription import score_exercise
        ex = {"id": "ex_keep", "tags": ["pattern_squat"], "level": 5}
        tags = {"pattern_squat"}
        base, _ = score_exercise(ex, tags, 5, {}, "ctx")
        boosted, breakdown = score_exercise(
            ex,
            tags,
            5,
            {"ex_keep": {"shown": 20, "kept": 18, "replaced": 0}},
            "ctx",
        )
        self.assertGreater(boosted, base)
        self.assertTrue(breakdown["taste_applied"])
        early, early_break = score_exercise(
            ex,
            tags,
            5,
            {"ex_keep": {"shown": 4, "kept": 4, "replaced": 0}},
            "ctx",
        )
        self.assertEqual(early, base)
        self.assertFalse(early_break["taste_applied"])

    def test_pain_returns_referral(self):
        profile = {k: {"score": 0, "clearing_pain": True} for k in [
            "overhead_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
            "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
        ]}
        profile["use_manual_scores"] = True
        plan = assemble_weekly_program(profile)
        self.assertTrue(plan.get("referral"))
        loaded = [
            item
            for day in plan["days"]
            for key in ("block_a", "block_b")
            for item in day["blocks"].get(key) or []
        ]
        self.assertEqual(loaded, [])
        self.assertTrue(any(day["blocks"].get("ramp") for day in plan["days"]))

    def _names(self, plan):
        out = []
        for day in plan.get("days") or []:
            for items in (day.get("blocks") or {}).values():
                if not isinstance(items, list):
                    continue
                for item in items:
                    if item.get("unfilled"):
                        continue
                    out.append((item.get("name") or "").upper())
        return out

    def _mobility_profile(self):
        return {
            "use_manual_scores": False,
            "overhead_squat": {
                "trunk_torso": {"excessive_forward_lean": 1},
                "feet": {"heels_lift": 1},
                "upper_body_bar_position": {"arms_fall_forward": 1, "shoulder_mobility_restriction_suspected": 1},
            },
            "hurdle_step": {"l_score": 1, "r_score": 2, "stepping_leg": {"toe_drag": 1}, "pelvis_core_control": {"loss_of_balance": 1}},
            "inline_lunge": {"score": 2, "alignment": {"lateral_shift": 1, "excessive_forward_lean": 1}},
            "shoulder_mobility": {"score": 2, "clearing_pain": False, "compensation": {"rib_flare": 1}},
            "active_straight_leg_raise": {"l_score": 1, "r_score": 2, "non_moving_leg": {"foot_lifts_off_floor": 1}},
            "trunk_stability_pushup": {"score": 2, "upper_body": {"uneven_arm_push": 1}},
            "rotary_stability": {"l_score": 1, "r_score": 1, "diagonal_pattern": {"unable_to_complete": 1}},
        }

    def test_empty_kit_excludes_barbell(self):
        plan = assemble_weekly_program(self._mobility_profile(), days_per_week=4, equipment=[])
        names = " ".join(self._names(plan))
        self.assertEqual(plan["status"], "MOBILITY")
        self.assertNotRegex(names, r"\bBB\b|BARBELL|TRAP BAR")
        self.assertNotRegex(names, r"OH BB|MILITARY PRESS|SEATED OH BB")

    def test_arms_fall_blocks_overhead(self):
        plan = assemble_weekly_program(self._mobility_profile(), days_per_week=3, equipment=["band", "bodyweight"])
        names = " ".join(self._names(plan))
        self.assertNotRegex(names, r"OH PRESS|OVERHEAD|MILITARY PRESS|PIKE PUSH|SNATCH|JERK|Z PRESS|PUSH PRESS")

    def test_heels_lift_blocks_jump_raise(self):
        plan = assemble_weekly_program(self._mobility_profile(), days_per_week=4, equipment=[])
        names = " ".join(self._names(plan))
        self.assertNotIn("JUMPING JACKS", names)
        self.assertNotRegex(names, r"BOX JUMP|DEPTH JUMP|HURDLE HOP|POGO")

    def test_ramp_varies_across_days(self):
        plan = assemble_weekly_program(self._mobility_profile(), days_per_week=4, equipment=[])
        raises = []
        for day in plan["days"]:
            for item in day["blocks"].get("ramp") or []:
                if item.get("role") == "RAISE" and not item.get("unfilled"):
                    raises.append(item.get("exercise_id"))
        self.assertGreaterEqual(len(set(raises)), min(2, len(raises)))


if __name__ == "__main__":
    unittest.main()
