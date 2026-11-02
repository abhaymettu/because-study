import unittest
from collections import Counter

from study1.design import FILLER, K, NORM, PLACEBO, assign, core, render_file, render_prompt, render_rule
from study1.rules import ALL_RULES, BY_ID, RULES


class Wording(unittest.TestCase):
    def test_modal_and_case_cross_for_both_polarities(self):
        do, dont = BY_ID["version_bump"], BY_ID["no_annotations"]
        self.assertEqual(core(do, "plain", "normal"), "Increase the patch number in `VERSION` with every change")
        self.assertEqual(core(do, "plain", "upper"), "INCREASE the patch number in `VERSION` with every change")
        self.assertEqual(core(do, "must", "normal"), "You must increase the patch number in `VERSION` with every change")
        self.assertEqual(core(do, "must", "upper"), "You MUST increase the patch number in `VERSION` with every change")
        self.assertEqual(core(dont, "plain", "normal"), "Do not add type annotations to new code")
        self.assertEqual(core(dont, "plain", "upper"), "DO NOT add type annotations to new code")
        self.assertEqual(core(dont, "must", "normal"), "You must not add type annotations to new code")
        self.assertEqual(core(dont, "must", "upper"), "You MUST NOT add type annotations to new code")

    def test_fully_treated_rule_reads_in_slot_order(self):
        t = {"reason": "real", "modal": "must", "case": "upper", "prefix": "important", "example": "present"}
        self.assertEqual(
            render_rule(BY_ID["version_bump"], t),
            "IMPORTANT: You MUST increase the patch number in `VERSION` with every change, because the deployment "
            "script skips any build number it has seen before. For example: `1.2.3` becomes `1.2.4`.",
        )

    def test_reason_clauses_are_matched_in_length(self):
        counts = [len(r.real.split()) for r in ALL_RULES]
        self.assertGreaterEqual(min(counts), 11)
        self.assertLessEqual(max(counts), 15)
        for clause in (PLACEBO, NORM, FILLER):
            self.assertTrue(10 <= len(clause.split()) <= 13, clause)

    def test_no_clause_contains_its_rules_tokens(self):
        for r in ALL_RULES:
            tokens = [w.strip("`,.:;") for w in r.rest.split() if w.startswith("`")]
            for tok in filter(None, tokens):
                self.assertNotIn(tok, r.real, r.id)


class Assignment(unittest.TestCase):
    def test_same_study_gives_the_same_manifest(self):
        self.assertEqual(assign("x", 20), assign("x", 20))

    def test_rules_are_balanced_and_never_repeat_in_a_run(self):
        rows = assign("x", 130)
        seen = Counter()
        for row in rows:
            ids = [t["rule"] for t in row["targets"]]
            self.assertEqual(len(set(ids)), K)
            self.assertNotIn(row["control_rule"], ids)
            seen.update(ids)
        self.assertLessEqual(max(seen.values()) - min(seen.values()), 2)

    def test_file_lengths_sit_near_the_census_tails(self):
        short = next(r for r in assign("x", 20) if r["length"] == "short")
        long = next(r for r in assign("x", 20) if r["length"] == "long")
        _, _, short_words = render_file(short)
        _, depth, long_words = render_file(long)
        self.assertTrue(250 <= short_words <= 550, short_words)
        self.assertTrue(2600 <= long_words <= 3800, long_words)
        self.assertEqual(set(depth), {t["rule"] for t in long["targets"]})
        self.assertTrue(all(0 <= d <= 1 for d in depth.values()))

    def test_every_target_appears_in_its_file_and_unshown_rules_do_not(self):
        row = assign("x", 1)[0]
        text, _, _ = render_file(row)
        for t in row["targets"]:
            self.assertIn(render_rule(BY_ID[t["rule"]], t), text)
        shown = {t["rule"] for t in row["targets"]}
        for r in RULES:
            if r.id not in shown:
                self.assertNotIn(r.rest, text)

    def test_control_rule_is_named_in_the_prompt(self):
        row = next(r for r in assign("x", 100) if r["control_rule"])
        self.assertIn(BY_ID[row["control_rule"]].rest, render_prompt(row))


if __name__ == "__main__":
    unittest.main()
