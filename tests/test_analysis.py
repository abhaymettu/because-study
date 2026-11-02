"""The registered analyses, run on outcomes we made up, so a right answer is known. Uses the real assignment, no real outcome."""

import unittest

import numpy as np

from analysis.study1 import by_rule, contrast, holm, randomization_p, reading, rule_level_estimates, run_level
from analysis.study2 import contrast as s2_contrast, loaded, visible
from analysis.study2b import reading as s2b_reading
from analysis.synthetic import RULES, assignment, simulate
from study2.design import assign_followup, target_name

OBS = assignment()


class PlantedEffects(unittest.TestCase):
    def test_every_factor_recovers_its_own_effect_and_no_other(self):
        plant = {("reason", "real"): 0.12, ("reason", "placebo"): 0.06, ("modal", "must"): 0.08, ("prefix", "important"): -0.08,
                 ("case", "upper"): 0.05, ("example", "present"): 0.15, ("position", "top"): 0.10}
        est = rule_level_estimates(simulate(OBS, plant, seed=1), RULES)
        for key, want in plant.items():
            self.assertAlmostEqual(float(np.mean(est[key])), want, delta=0.05, msg=str(key))
        for key in (("reason", "norm"), ("reason", "none"), ("position", "bottom")):
            self.assertAlmostEqual(float(np.mean(est[key])), 0.0, delta=0.05, msg=str(key))

    def test_filler_is_the_reference_so_a_shift_in_filler_moves_every_other_arm(self):
        est = rule_level_estimates(simulate(OBS, {("reason", "filler"): -0.10}, seed=2), RULES)
        for level in ("none", "placebo", "norm", "real"):
            self.assertAlmostEqual(float(np.mean(est[("reason", level)])), 0.10, delta=0.05, msg=level)

    def test_top_versus_bottom_is_the_difference_of_two_position_terms(self):
        est = rule_level_estimates(simulate(OBS, {("position", "top"): 0.10, ("position", "bottom"): -0.10}, seed=3), RULES)
        self.assertAlmostEqual(float(np.mean(contrast(est, ("position", "top"), ("position", "bottom")))), 0.20, delta=0.06)

    def test_a_run_level_factor_is_recovered(self):
        r = run_level(simulate(OBS, {("pressure", "urgent"): 0.12}, seed=4), RULES, "pressure", "urgent", "none")
        self.assertAlmostEqual(r["estimate"], 0.12, delta=0.05)
        self.assertGreater(r["se"], 0)
        self.assertLess(r["ci"][0], r["ci"][1])

    def test_randomization_test_separates_a_large_effect_from_none(self):
        hit = simulate(OBS, {("reason", "real"): 0.15}, seed=5)
        self.assertLess(randomization_p(hit, RULES, "real", "filler", "reason", perms=99), 0.05)
        none = simulate(OBS, {}, seed=6)
        self.assertGreater(randomization_p(none, RULES, "placebo", "filler", "reason", perms=99), 0.05)


class Calibration(unittest.TestCase):
    def rate(self, plant, slope_sd, sims=60):
        hits = 0
        for seed in range(sims):
            est = rule_level_estimates(simulate(OBS, plant, seed=100 + seed, slope_sd=slope_sd), RULES)
            hits += by_rule(est[("reason", "real")])["p"] < 0.05
        return hits / sims

    def test_false_positive_rate_with_no_effect_is_near_alpha(self):
        self.assertLessEqual(self.rate({}, slope_sd=0.0), 0.15)

    def test_a_large_effect_with_varying_slopes_is_usually_found(self):
        self.assertGreaterEqual(self.rate({("reason", "real"): 0.12}, slope_sd=0.03, sims=30), 0.8)


def _result(h1, h2, h1_p=0.5, h2_p=0.5, h1_ci=(-0.02, 0.02), h2_ci=(-0.02, 0.02), retention_p=0.5, gate=False, rmp=0.0, rmp_p=0.5, tost=0.5,
            real_none=(0.1, 0.01), placebo_none=(0.1, 0.01), control=(0.8, 0.1)):
    return {
        "confirmatory": {
            "real_vs_filler": {"estimate": h1, "p_holm": h1_p, "ci": list(h1_ci)},
            "placebo_vs_filler": {"estimate": h2, "p_holm": h2_p, "ci": list(h2_ci)},
        },
        "retention_placebo_minus_half_real": {"gate_open": gate, "p_one_sided": retention_p},
        "real_minus_placebo": {"estimate": rmp, "p": rmp_p, "tost_p_at_5_points": tost},
        "real_vs_none": {"estimate": real_none[0], "p": real_none[1]},
        "placebo_vs_none": {"estimate": placebo_none[0], "p": placebo_none[1]},
        "positive_control": {"named_in_prompt": control[0], "no_rule": control[1]},
    }


class DecisionTable(unittest.TestCase):
    def test_assay_failure_wins_over_everything(self):
        self.assertIn("assay failed", reading(_result(0.2, 0.2, h1_p=0.001, h2_p=0.001, control=(0.3, 0.1))))

    def test_form(self):
        r = _result(0.1, 0.09, h1_p=0.01, h2_p=0.01, h1_ci=(0.05, 0.15), h2_ci=(0.04, 0.14), gate=True, retention_p=0.01)
        self.assertEqual(reading(r), "the form of a reason moves compliance")

    def test_form_with_equivalence(self):
        r = _result(0.1, 0.09, h1_p=0.01, h2_p=0.01, gate=True, retention_p=0.01, tost=0.01)
        self.assertEqual(reading(r), "the form of a reason moves compliance, and a placebo does about as much as a real reason")

    def test_form_needs_an_advantage_over_no_clause(self):
        r = _result(0.1, 0.09, h1_p=0.01, h2_p=0.01, gate=True, retention_p=0.01, placebo_none=(0.02, 0.4))
        self.assertEqual(reading(r), "inconclusive")

    def test_content(self):
        r = _result(0.1, 0.01, h1_p=0.01, h2_p=0.6, gate=True, retention_p=0.9, rmp=0.09, rmp_p=0.01)
        self.assertEqual(reading(r), "reasons work through their content; a placebo does not substitute")

    def test_content_needs_real_above_placebo(self):
        r = _result(0.1, 0.05, h1_p=0.01, h2_p=0.2, gate=True, retention_p=0.5, rmp=0.05, rmp_p=0.2)
        self.assertEqual(reading(r), "inconclusive")

    def test_practical_null(self):
        self.assertEqual(
            reading(_result(0.01, 0.0, h1_ci=(-0.02, 0.04), h2_ci=(-0.03, 0.03))),
            "a reason clause does not move compliance by a practically useful amount on these rules",
        )

    def test_a_wide_null_is_not_a_null(self):
        self.assertEqual(reading(_result(0.02, 0.01, h1_ci=(-0.02, 0.06), h2_ci=(-0.03, 0.03))), "inconclusive")

    def test_a_significant_negative_is_not_read_as_a_reason_effect(self):
        self.assertEqual(reading(_result(-0.1, -0.1, h1_p=0.01, h2_p=0.01, h1_ci=(-0.15, -0.05), h2_ci=(-0.15, -0.05))), "inconclusive")


class Holm(unittest.TestCase):
    def test_known_values(self):
        self.assertEqual(holm([0.01, 0.04]), [0.02, 0.04])
        self.assertEqual(holm([0.04, 0.01]), [0.04, 0.02])
        self.assertEqual(holm([0.03, 0.02, 0.5]), [0.06, 0.06, 0.5])


    def test_a_zero_interval_at_a_ceiling_does_not_break_the_adjustment(self):
        tied = by_rule(np.zeros(12))
        self.assertEqual(tied["p"], 1.0)
        self.assertEqual(holm([0.001, tied["p"], tied["p"]]), [0.003, 1.0, 1.0])
        self.assertEqual(by_rule(np.full(12, 0.5))["p"], 0.0)


class Study2(unittest.TestCase):
    NAME = "aa-ledger-00012"

    def test_a_load_is_a_skill_call_or_a_read_of_the_file(self):
        self.assertTrue(loaded({"calls": [["Skill", self.NAME]]}, self.NAME))
        self.assertTrue(loaded({"calls": [["Skill", f"project:{self.NAME}"]]}, self.NAME))
        self.assertTrue(loaded({"calls": [["Read", f"/x/.claude/skills/{self.NAME}/SKILL.md"]]}, self.NAME))
        self.assertTrue(loaded({"calls": [["Bash", f"cat .claude/skills/{self.NAME}/SKILL.md"]]}, self.NAME))

    def test_other_skills_and_listing_the_folder_are_not_a_load(self):
        self.assertFalse(loaded({"calls": [["Skill", "zz-other"]]}, self.NAME))
        self.assertFalse(loaded({"calls": [["Bash", "ls .claude/skills"], ["Read", "ledger.csv"]]}, self.NAME))

    def test_visible_is_set_by_design(self):
        self.assertTrue(visible({"library": 0, "prefix": "zz"}))
        self.assertTrue(visible({"library": 50, "prefix": "zz"}))
        self.assertTrue(visible({"library": 300, "prefix": "aa"}))
        self.assertFalse(visible({"library": 300, "prefix": "zz"}))

    def test_target_names_are_unique_per_run(self):
        self.assertEqual(target_name({"name_prefix": "zz", "stem": "ledger", "run_id": "study2-00031"}), "zz-ledger-00031")

    def test_contrast_is_averaged_over_targets_with_equal_weight(self):
        rows = []
        for stem, a, b in (("x", 0.75, 0.25), ("y", 0.5, 0.5)):
            for w, rate in (("trigger", a), ("minimal", b)):
                # Target x has eight times the runs of y and must not count for more.
                n = 8 if stem == "x" else 1
                for i in range(4 * n):
                    rows.append({"stem": stem, "wording": w, "y": float(i < rate * 4 * n)})
        r = s2_contrast(rows, lambda _: True, lambda r: r["wording"] == "trigger", lambda r: r["wording"] == "minimal")
        self.assertAlmostEqual(r["estimate"], 0.25)
        self.assertEqual(r["g"], 2)


class Study2b(unittest.TestCase):
    def family(self, d1, d2, d4_low):
        row = lambda est, holm_p, low=0.0: {"estimate": est, "p_holm": holm_p, "ci": [low, est + 0.1]}
        return {"D1_minimal_vs_trigger_at_300": row(d1, 0.01 if d1 else 0.5), "D2_short_trigger_vs_trigger_at_300": row(d2, 0.01 if d2 else 0.5),
                "D4_short_trigger_vs_trigger_at_50": row(0.0, 1.0, d4_low)}

    def test_the_decision_table(self):
        self.assertEqual(s2b_reading(self.family(0.3, 0.0, -0.02)), "past the budget a short plain description beats a long trigger list")
        self.assertIn("costs under 10 points", s2b_reading(self.family(0.0, 0.3, -0.02)))
        self.assertEqual(s2b_reading(self.family(0.0, 0.3, -0.2)), "inconclusive")
        self.assertEqual(s2b_reading(self.family(0.0, 0.0, -0.02)), "inconclusive")

    def test_the_assignment_is_balanced_and_never_reuses_a_study_2_name(self):
        rows = assign_followup("study2b")
        self.assertEqual(len(rows), 576)
        self.assertTrue(all(int(r["run_id"].rsplit("-", 1)[1]) >= 10000 and r["name_prefix"] == "zz" for r in rows))
        self.assertEqual(sum(r["library"] == 300 and r["stem"] == "sql-review" and r["wording"] == "minimal" for r in rows), 12)
        self.assertEqual(sum(r["library"] == 50 and r["stem"] == "sql-review" and r["wording"] == "trigger" for r in rows), 4)
        self.assertEqual(len({target_name(r) for r in rows}), 576)
        self.assertTrue(all(len(r["distractors"]) == r["library"] for r in rows))


if __name__ == "__main__":
    unittest.main()
