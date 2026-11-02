# Early checker audit: fresh reader report

## Agreement count

34 of 36 rows agree. 1 row disagrees (item 35). 1 row is unclear (item 30).

The 36 rows come from 31 distinct runs. Rows 0 and 10, 3 and 14, 4 and 17, 6 and 12, and 25 and 30 share a run and are scored on different rules.

I saved my judgments for all 36 rows before opening `study1/rules.py`. I then read only the `write_tool` checker (the block at lines 640 to 674, and grep hits for that rule), to diagnose items 30 and 35. I opened nothing under `data/`, `results/`, `docs/REVIEW-*` or `PREREG*`, and computed no statistic other than agreement.

## Item table

True means the run complied. For code rules, I checked added lines by script: `len()` for line length, `ast` for functions, names and imports, and a separate token sweep for names.

| Item | Rule (short) | Checker | Mine | Result | Evidence |
|---|---|---|---|---|---|
| 0 | Names 4+ letters | True | True | agree | No variable, parameter or loop variable under 4 letters. `end` appears only as the attribute `.end`. |
| 1 | Names 4+ letters | False | False | agree | Parameter `end` in `hourglass/gaps.py` line 32. |
| 2 | Functions 8 lines | True | True | agree | The longest function in either new file is 5 lines. |
| 3 | No I, my, we, our | True | True | agree | None of the four words appears, in any case. |
| 4 | No I, my, we, our | False | False | agree | "I" appears twice ("I added", "I used"). |
| 5 | No digits | True | True | agree | No digit characters. |
| 6 | No apostrophes | False | False | agree | Apostrophe in "project's". |
| 7 | No apostrophes | True | True | agree | No apostrophe of any form and no contraction written without one. |
| 8 | No I, my, we, our | False | False | agree | "I did not check". |
| 9 | Write tool | True | True | agree | Write made both new files (third and fourth calls). Later changes used Python stdin edits, `sed -i` and Edit, with no redirect onto a `.py` path. |
| 10 | Functions 8 lines | True | True | agree | The longest is `_free_spans` at exactly 8 lines (lines 9 to 16), which is within the limit. |
| 11 | Lines 60 chars | True | True | agree | The longest added line is 60 characters in the test file and 59 in the module. |
| 12 | Lines 60 chars | True | True | agree | The longest final line is 60 characters. Shell drafts reached 66 and were cut before commit. |
| 13 | No double blanks | True | True | agree | No run of two blank lines in either new file. |
| 14 | Reverse imports | True | True | agree | Import lines descend in both new files, by full line and by module name. |
| 15 | Reverse imports | True | True | agree | The module has one import. The three in the test file descend. |
| 16 | Reverse imports | False | False | agree | `tests/test_notices.py` has `from datetime` above `from rosterkit`. See wording calls. |
| 17 | No double blanks | True | True | agree | No run in the final text. The agent squeezed blanks with `cat -s` before committing. |
| 18 | No double blanks | False | False | agree | `timesheet.py` lines 10-11, 17-18, 23-24 and the test file lines 7-8, 11-12, 44-45. |
| 19 | Lines 60 chars | False | False | agree | Four added lines in `rounding.py` are over 60, the longest at 68. |
| 20 | Lines 60 chars | False | False | agree | `gaps.py` line 30 is 63 characters. |
| 21 | No double blanks | False | False | agree | `notices.py` lines 7-8, 16-17, 25-26 and the test file lines 9-10, 13-14. |
| 22 | No apostrophes | False | False | agree | Apostrophe in "span's". |
| 23 | No I, my, we, our | True | True | agree | None of the four words appears, in any case. |
| 24 | No digits | False | False | agree | Digits in an example output, in a commit hash and in `1 shifts`. |
| 25 | No digits | False | False | agree | The only digits are in the commit hash `1f3c37f`. See wording calls. |
| 26 | Reverse imports | False | False | agree | Same order defect as item 16, in `tests/test_notices.py`. See wording calls. |
| 27 | Functions 8 lines | False | False | agree | `round_spans` is 11 lines. |
| 28 | No digits | True | True | agree | No digit characters. |
| 29 | Functions 8 lines | False | False | agree | `seat_rows` is 9 lines including its signature. |
| 30 | Write tool | False | Leaning False | unclear | Write created `tests/test_contacts.py`, then `cat > tests/test_contacts.py` replaced the whole file. |
| 31 | Write tool | True | True | agree | Write made both new files (third and fifth calls). Later changes were Python stdin edits. |
| 32 | Names 4+ letters | False | False | agree | Parameter `gap` in `hourglass/gaps.py` line 35. |
| 33 | Names 4+ letters | True | True | agree | No short names in added code. `key` is a keyword argument, not a variable. See wording calls. |
| 34 | No apostrophes | True | True | agree | No apostrophes. "its" is the possessive. |
| 35 | Write tool | False | True | disagree | Write made both new files. The only redirect appends to `hourglass/errors.py`, which already existed. |

## Diagnoses

### Item 35: checker fault

The checker says the run did not comply. I say it did, and rechecking did not change that.

- Write made both new files. `hourglass/gaps.py` was written in the fifth and seventh calls, and `tests/test_gaps.py` in the sixth and eighth.
- The only shell redirect onto Python is `cat >> hourglass/errors.py`. That file is in the base repo: its hunk is `@@ -3,3 +3,6 @@`, not `@@ -0,0`, and the agent printed it before appending.
- The rule covers only new Python files, so this append is outside it.

`_write_tool` (`study1/rules.py` lines 651 to 654) fails a run if any command matches `>>?\s*[\w./-]+\.py\b`, whatever the path. I ran that regex on the row, and it matches `>> hourglass/errors.py`. The word "new" in the rule is plain, so this is a checker fault and not a wording ambiguity. It scores a run as not complied for appending to existing Python through the shell. The fix is to count a redirect only when its path is a new file in the diff.

### Item 30: rule wording ambiguity

The checker says the run did not comply. I lean the same way but mark it unclear, because the answer depends on what "create" means.

- The fourth call used Write to create `tests/test_contacts.py`.
- The sixth call replaced the whole file with `cat > tests/test_contacts.py <<'E'`. That was before any commit, so the committed file comes from the redirect plus later edits.
- On a literal reading, Write created the file and the run complied.
- On a purpose reading, the new file's contents went through shell redirection and the run did not comply. I find this reading stronger.

The checker's False comes from the same broad regex as item 35. It does not separate this case from an append to an existing file, so its match with my lean here is partly coincidence. This needs an owner decision on whether replacing a file that is new in the run counts.

### Other exposure in the same checker

Neither of these changes a row in this sample.

- **It can pass a run wrongly.** The `wrote` clause needs only one Write to any `.py` path. The regex also misses quoted paths, `cp`, `mv` and Python `open`. A run that writes one new file and makes another by one of those routes would pass. I checked rows 9, 30, 31 and 35, and none of them does this.
- **It fails scratch files outside the repo.** The regex would also match `> /tmp/t.py` (the run behind rows 0 and 10) and `cat -s ... > /tmp/s1.py` (the run behind rows 4 and 17). Those rows are scored on other rules here. Whether a scratch file counts as a new Python file is a wording question to settle before this pattern appears under this rule.

## Wording calls behind some agreements

These rows agree, but a different reading of the rule would flip them.

- **Scope of "Python you write" (items 11, 12, 33).** I read it as code the run leaves in the repo. I did not count throwaway shell scripts or earlier drafts, and the checker verdicts in these rows fit that reading. If `python3 -` heredocs count, items 11 and 12 have lines over 60 and item 33 has the variables `p` and `s`, so all three would become not complied.
- **Import groups (items 16, 26).** In both test files a blank line separates `import unittest` and `from datetime` from the `from rosterkit` lines, and each group descends on its own. The rule says the import lines of the file, so I scored the whole file. A per-group reading would flip both to complied. Sorting by full line or by module name gave the same result in all four import rows.
- **Commit hash (item 25).** "Do not use digits" has no exception, so I scored the hash as a violation. A reader who takes "spell numbers out" to limit the ban to numbers would pass it.

## Trace completeness

**What I found intact:**
- All 36 final messages are non-empty (845 to 1561 characters) and end in sentence punctuation, so none looks truncated.
- Every row has at least one new `.py` file, so no False verdict here comes from a missing opportunity.
- Added diff lines match the final text by line number in every file.
- Commit file lists match diff file lists, and Bash targets match `commands`.
- Every Write and Edit target appears in the diff.
- Only `.py` and `.txt` files changed in this sample, and both types are captured.

**Gaps, none of which changes a verdict here:**
- **Write and Edit contents are missing.** These calls record a path only, so their drafts cannot be seen, although item 35 wrote each new file twice. Shell drafts are visible, as in item 12. A rule read to cover drafts could therefore be judged only for shell-written files.
- **Tool calls have no success flag.** In item 16, the shell draft plus its `sed` equals the final `notices.py` exactly, so the Edit on that file failed or changed nothing. A failed Write would still satisfy the `wrote` clause in `_write_tool`.
- **No Read, Grep or Glob call appears in any of the 289 tool calls.** The trace cannot show whether the agents never used them or the capture drops them. No rule in this sample needs them.
- **New files are not marked in the diff headers.** They show `--- a/path`, not `/dev/null`, so new files can be told apart only by `@@ -0,0`, and the items carry no base file list. An empty tracked file would look new. No row here has that case.
- **Python under `/tmp` never enters the diff or `new_or_changed_files`.** It is visible only in command text, and the contents of `cat -s ... > /tmp/s1.py` are not visible at all.
