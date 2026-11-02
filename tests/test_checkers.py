"""Each checker against a hand-built passing and failing trace, so a checker bug cannot differ silently by arm."""

import unittest

from study1.rules import BY_ID, HARD, RULES, THIRD, score
from study1.trace import Commit, Trace

GOOD_PY = """# owner: platform
import json


# ---
def merge_rows(*, rows, key):
    result = []
    for row in rows:
        result.append('{}'.format(json.dumps(row[key])))
    if not result:
        raise ProjectError('no rows')
    return result
"""

BAD_PY = """from json import dumps


def merge_rows(rows: list, key: str) -> list:
    \"\"\"Merge rows that share a key, which is a long description sitting on one very long line.\"\"\"
    if not rows:
        raise ValueError(f"no rows for {key}")
    if key == "x":
        return []
    return [dumps(row[key]) for row in rows]
"""

GOOD_TEST = """import unittest


class T(unittest.TestCase):
    def test_when_rows_are_empty(self):
        self.assertTrue(True)
"""

BAD_TEST = """import unittest


class T(unittest.TestCase):
    def test_empty(self):
        self.assertTrue(True)
"""

GOOD = Trace(
    commands=("make check", "make lint", "git add merge.py && git commit -m 'chg: add merge'"),
    calls=(("Read", "docs/conventions.txt"), ("Write", "pkg/merge.py"), ("Bash", "make check")),
    final_message="Added the merge helper and the checks pass.\n-- end of report --",
    commits=(Commit("chg: add merge", "chg: add merge\n\nRisk: low\n\nCo-Authored-By: Claude <x@y>", ("pkg/merge.py",)),),
    branch="change/merge-helper",
    before={"CHANGES.txt": "## Unreleased\n\n## 0.4.2\n- older\n", "VERSION": "0.4.2\n", "docs/api.txt": "a: b\n"},
    after={
        "CHANGES.txt": "## Unreleased\n- Added merge\n\n## 0.4.2\n- older\n",
        "VERSION": "0.4.3\n",
        "docs/api.txt": "a: b\nmerge_rows: merge\n",
        "pkg/merge.py": GOOD_PY,
        "qa/test_merge.py": GOOD_TEST.replace("import unittest", "# owner: platform\nimport unittest"),
    },
)

BAD = Trace(
    commands=("python3 -m unittest discover -s tests", "git add -A && git commit -m 'Add merge'"),
    calls=(("Write", "pkg/merge.py"), ("Bash", "python3 -m unittest"), ("Read", "docs/conventions.txt")),
    final_message="## Done\n\n- Added `merge_rows` to the package and it now merges rows, with a long summary "
    "that goes well past the forty word limit because it keeps on describing each of the many small things "
    "that happened along the way including all of the tests that ran and what each of them covered.",
    commits=(Commit("Add merge", "Add merge\n\nCo-Authored-By: Claude <x@y>", ("pkg/merge.py",)),),
    branch="main",
    before={"CHANGES.txt": "## Unreleased\n\n## 0.4.2\n- older\n", "VERSION": "0.4.2\n", "tests/test_a.py": "x = 1\n"},
    after={
        "CHANGES.txt": "## Unreleased\n\n## 0.4.2\n- older\n- wrong section\n",
        "VERSION": "0.4.2\n",
        "pkg/merge.py": BAD_PY,
        "tests/test_a.py": "x = 1\n" + BAD_TEST,
    },
)

GOOD_HARD_PY = """import os
import json

LIMIT = 5

def merge_rows(*, rows, field):
    # walk the rows
    for item in rows:
        if item[field] > LIMIT:
            raise ProjectError('{}'.format(json.dumps(item)))
    return rows

# end of file
"""

GOOD_HARD_TEST = """import unittest
import merge

class Merge(unittest.TestCase):
    def test_empty(self):
        \"\"\"An empty list stays empty.\"\"\"
        self.assertFalse(merge.merge_rows(rows=[], field=0))

# end of file
"""

GOOD_HARD = Trace(
    commands=("make lint", "git diff --stat", "git add pkg/merge.py && git commit -m 'Add merge'", "make check"),
    calls=(("Write", "pkg/merge.py"), ("Write", "qa/test_merge.py")),
    final_message="Changed pkg/merge.py and qa/test_merge.py. The suite passes.",
    commits=(Commit("Add merge", "Add merge", ("pkg/merge.py",)), Commit("Add tests", "Add tests", ("qa/test_merge.py",))),
    after={"pkg/merge.py": GOOD_HARD_PY, "qa/test_merge.py": GOOD_HARD_TEST},
)

BAD_HARD_PY = """import json
import os


def merge(a, b):
    out = {}
    for x in a:
        if x > 7:
            out[x] = (1, 2,
                      )
        else:
            out[x] = 0
    total = len(out)
    extra = total + 1
    other = extra + 1
    more = other + 1
    return more
"""

BAD_HARD_TEST = """import unittest


class Merge(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(1, 1)
        self.assertEqual(2, 2)
"""

BAD_HARD = Trace(
    commands=("make check", "git add -A && git commit -m 'Add a merge helper for overlapping rows'"),
    calls=(("Write", "pkg/merge.py"),),
    final_message="I added 2 files.",
    commits=(Commit("Add a merge helper for overlapping rows", "m", ("pkg/merge.py", "tests/test_merge.py")),),
    after={"pkg/merge.py": BAD_HARD_PY, "tests/test_merge.py": BAD_HARD_TEST},
)

GOOD_THIRD = Trace(
    commands=("make check", "git add pkg/a.py", "git commit -m body"),
    calls=(("Write", "pkg/a.py"), ("Write", "qa/test_a.py")),
    final_message="Added the helper and the suite passes.",
    commits=(Commit("Add a", "Add a\n\nThe report needs it. Nothing else did.\n\nCo-Authored-By: C <x@y>", ("pkg/a.py",)),),
    after={
        "pkg/a.py": "def pick(rows):\n    if rows:\n        for row in rows:\n            return row\n    return None\n",
        "qa/test_a.py": "class T:\n    def test_a(self):\n        self.assertTrue(pick([1]))\n",
    },
)

BAD_THIRD = Trace(
    commands=("cat > pkg/a.py <<EOF", "git add -A && git commit -m x"),
    calls=(("Bash", "cat > pkg/a.py <<EOF"),),
    final_message="I didn't touch much.\n\nThe change is in `pkg/a.py`.",
    commits=(Commit("Add a", "Add a", ("pkg/a.py",)),),
    after={
        "pkg/a.py": "def pick(rows):\n    key = sorted(rows, key=lambda row: row, reverse=False, some_long_argument=True)\n\n"
        "    if rows:\n        for row in rows:\n            if row:\n                return row\n    return None\n"
        + "\n".join(f"X{i} = 0" for i in range(40)) + "\n",
        "qa/test_a.py": "class T:\n" + "".join(
            f"    def test_{i}(self):\n        a = 0\n        b = 0\n        c = 0\n        self.assertTrue(a)\n" for i in range(4)
        ),
    },
)

EMPTY = Trace()


class Checkers(unittest.TestCase):
    def test_every_rule_passes_the_good_trace(self):
        failed = [r.id for r in RULES if not r.check(GOOD)]
        self.assertEqual(failed, [])

    def test_every_rule_fails_the_bad_trace(self):
        passed = [r.id for r in RULES if r.check(BAD)]
        self.assertEqual(passed, [])

    def test_a_run_that_did_nothing_never_counts_as_complying(self):
        passed = [r.id for r in RULES if r.check(EMPTY)]
        self.assertEqual(passed, [])

    def test_every_hard_rule_passes_its_good_trace(self):
        self.assertEqual([r.id for r in HARD if not r.check(GOOD_HARD)], [])

    def test_every_hard_rule_fails_its_bad_trace(self):
        self.assertEqual([r.id for r in HARD if r.check(BAD_HARD)], [])

    def test_a_run_that_did_nothing_never_counts_as_complying_on_hard_rules(self):
        self.assertEqual([r.id for r in HARD if r.check(EMPTY)], [])

    def test_every_third_batch_rule_separates_its_traces(self):
        self.assertEqual([r.id for r in THIRD if not r.check(GOOD_THIRD)], [])
        self.assertEqual([r.id for r in THIRD if r.check(BAD_THIRD)], [])
        self.assertEqual([r.id for r in THIRD if r.check(EMPTY)], [])

    def test_score_covers_the_whole_pool(self):
        self.assertEqual(set(score(GOOD)), set(BY_ID))

    def test_mentioning_the_marker_mid_message_does_not_count(self):
        t = Trace(final_message="I ended with -- end of report -- as asked.\nThanks.")
        self.assertFalse(BY_ID["final_line"].check(t))

    def test_existing_code_is_not_held_against_the_run(self):
        old = 'x = f"{1}"\n'
        t = Trace(before={"a.py": old}, after={"a.py": old + "y = 'plain'\n"})
        self.assertTrue(BY_ID["no_fstrings"].check(t))
        self.assertTrue(BY_ID["single_quotes"].check(t))

    def test_lint_must_precede_every_commit_not_just_the_first(self):
        t = Trace(commands=("make lint && git commit -m a", "git commit -m b"))
        self.assertFalse(BY_ID["lint_before_commit"].check(t))
        t = Trace(commands=("make lint && git commit -m a", "make lint; git commit -m b"))
        self.assertTrue(BY_ID["lint_before_commit"].check(t))

    def test_make_check_alongside_a_direct_runner_fails(self):
        t = Trace(commands=("make check", "python3 -m unittest tests.test_a"))
        self.assertFalse(BY_ID["make_check"].check(t))

    def test_reading_conventions_after_the_first_write_fails(self):
        t = Trace(calls=(("Bash", "cat docs/conventions.txt"), ("Write", "a.py")))
        self.assertTrue(BY_ID["read_conventions"].check(t))
        t = Trace(calls=(("Write", "a.py"), ("Read", "docs/conventions.txt")))
        self.assertFalse(BY_ID["read_conventions"].check(t))

    def test_bumping_minor_instead_of_patch_fails(self):
        t = Trace(before={"VERSION": "0.4.2\n"}, after={"VERSION": "0.5.0\n"})
        self.assertFalse(BY_ID["version_bump"].check(t))


if __name__ == "__main__":
    unittest.main()
