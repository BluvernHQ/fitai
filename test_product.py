"""Taste, periodization, and comment-NLP unit tests."""

import unittest

from src.logic.needs_engine import parse_comment_needs
from src.logic.periodization import apply_week_progression, mesocycle_envelope
from src.logic.taste import plans_differ_selection, prior_contribution
from src.logic.delivery import athlete_dto, hash_token, mint_share_token


class NeedsCommentTests(unittest.TestCase):
    def test_negation_skips_pain_tag(self):
        needs = parse_comment_needs({"overhead_squat": "no pain, heels lift on the way down"})
        tags = {n.tag for n in needs}
        self.assertNotIn("stop", tags)
        self.assertIn("fix_heels_lift", tags)

    def test_laterality(self):
        needs = parse_comment_needs({"inline_lunge": "left valgus"})
        self.assertTrue(needs)
        self.assertEqual(needs[0].side, "left")


class TasteTests(unittest.TestCase):
    def test_low_evidence_does_not_rank(self):
        out = prior_contribution({"ex|ctx": {"shown": 6, "kept": 6, "replaced": 0}}, "ex", "ctx")
        self.assertFalse(out["applied"])
        self.assertEqual(out["score"], 0.0)

    def test_reject_does_not_equal_every_item(self):
        ai = {"days": [{"blocks": {"block_a": [{"exercise_id": "a"}, {"exercise_id": "b"}]}}]}
        coach = {"days": [{"blocks": {"block_a": [{"exercise_id": "a"}, {"exercise_id": "b"}]}}]}
        self.assertFalse(plans_differ_selection(ai, coach))


class PeriodizationTests(unittest.TestCase):
    def test_week_four_is_deload(self):
        env = mesocycle_envelope("STRENGTH", 4)
        self.assertEqual(env["phase"], "deload")
        self.assertTrue(env["retest_due"])

    def test_lazy_scale_keeps_exercises(self):
        week1 = {
            "status": "STRENGTH",
            "schema_version": 3,
            "days": [
                {
                    "blocks": {
                        "block_a": [
                            {
                                "exercise_id": "squat_a",
                                "name": "Goblet Squat",
                                "sets": 4,
                                "intensity": 0.8,
                                "percent_1rm": 80,
                                "one_rm": 100,
                            }
                        ]
                    }
                }
            ],
            "calendar": [{"kind": "gym", "tone": "accent", "label": "gym"}],
        }
        week4 = apply_week_progression(week1, 4)
        self.assertEqual(week4["days"][0]["blocks"]["block_a"][0]["exercise_id"], "squat_a")
        self.assertLess(week4["days"][0]["blocks"]["block_a"][0]["sets"], 4)
        self.assertEqual(week4["calendar"][0]["kind"], "deload")


class DeliveryTests(unittest.TestCase):
    def test_athlete_dto_strips_candidates(self):
        dto = athlete_dto(
            {
                "week_title": "Test",
                "candidate_exercises": {"x": []},
                "analysis": {"faults": ["secret"]},
                "days": [
                    {
                        "day": 1,
                        "title": "A",
                        "blocks": {
                            "block_a": [
                                {
                                    "exercise_id": "a",
                                    "name": "Squat",
                                    "candidates": ["b"],
                                    "score_breakdown": {"taste": 1},
                                }
                            ]
                        },
                    }
                ],
                "calendar": [{"weekday": "Mon", "kind": "gym"}],
            }
        )
        self.assertNotIn("candidate_exercises", dto)
        self.assertNotIn("analysis", dto)
        self.assertNotIn("score_breakdown", dto["days"][0]["blocks"]["block_a"][0])

    def test_token_hash_is_not_raw(self):
        raw = mint_share_token()
        self.assertNotEqual(raw, hash_token(raw))
        self.assertEqual(len(hash_token(raw)), 64)


if __name__ == "__main__":
    unittest.main()
