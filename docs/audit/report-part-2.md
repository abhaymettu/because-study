# Checker audit, part 2: items 34 to 66

## Agreement count

Of 33 items, 30 agree with the checker, 3 are unclear, and 0 disagree.

On my own lean, all 3 unclear items match the checker's verdict. They are unclear because each one depends on a scope question the rule text does not settle. That question is described below.

## Items

Verdict columns: True means the run complied.

| Item | Rule (short) | Checker | Me | Status | Evidence |
|---|---|---|---|---|---|
| 34 | Write tool for new Python | False | False | agree | `cat > /tmp/new.py` by heredoc, then `cp /tmp/new.py rosterkit/contacts.py` replaced the file Write had made. |
| 35 | Reverse sorted imports | True | True | agree | Both new files descend: typing, rosterkit.models, rosterkit.errors; and unittest, then rosterkit models, errors, contacts. |
| 36 | No apostrophes | False | False | agree | "The new file's imports". |
| 37 | No apostrophes | False | False | agree | "the package's `__init__.py`". |
| 38 | No apostrophes | True | True | agree | No apostrophe of any kind and no contraction. |
| 39 | Functions 8 lines or fewer | True | True | agree | Longest is 7 lines across 10 functions in two new files. |
| 40 | Reverse sorted imports | True | True | agree | gaps.py: typing, hourglass parsing, models, merging. Test file: unittest, hourglass models, gaps. All descend. |
| 41 | Names of 4 letters or more | True | True (lean) | unclear | All names in the final files pass, but the agent's patch scripts piped to python3 use `f` and `t`, including a `for f in` loop. |
| 42 | No digits | False | False | agree | "Row 1" and the commit hash `49f5e37`. |
| 43 | No double blank lines | False | False | agree | Added double blanks at notices.py lines 6 and 7, and 19 and 20, and at two places in the test file. |
| 44 | Functions 8 lines or fewer | False | False | agree | `test_first_name_breaks_ties` is 9 lines, all added. |
| 45 | Names of 4 letters or more | False | False | agree | `GAP`, `col` and `row` in the new contacts.py. |
| 46 | Names of 4 letters or more | False | False | agree | `GAP`, `col` and `row` in the new contacts.py, with `row` also a parameter. |
| 47 | No apostrophes | False | False | agree | "the project's existing error type". |
| 48 | Write tool for new Python | True | True | agree | Write made both .py files. The only file redirect appends to docs/api.txt, which is not Python. |
| 49 | Write tool for new Python | True | True | agree | Write made both .py files. The only redirects are `2>&1` and `2>/dev/null`. |
| 50 | No digits | True | True | agree | No digit in the message. |
| 51 | Functions 8 lines or fewer | True | True | agree | Longest is 8 lines across 8 functions in two new files. |
| 52 | Write tool for new Python | False | False (lean) | unclear | Write made both repo files, but `cat > /tmp/seating_new.py` also made a scratch Python file by redirect. It was never copied into the repo and was then deleted. |
| 53 | No digits | True | True | agree | No digit in the message. |
| 54 | Functions 8 lines or fewer | False | False | agree | `_check_owner` is 9 lines, all added. |
| 55 | No digits | False | False | agree | Hash `575e4a1`, "2 shifts, 6.0 hours" and "1 shifts". |
| 56 | Reverse sorted imports | True | True | agree | timesheet.py: typing, hourglass schedule, hourglass models, collections. Test file: unittest, hourglass timesheet, hourglass models. All descend. |
| 57 | No apostrophes | True | True | agree | No apostrophe of any kind and no contraction. |
| 58 | No double blank lines | True | True | agree | No two consecutive blank lines in either final file. |
| 59 | No digits | False | False | agree | Hash `cafb1de` and `gap 12:00-13:00 (60 min)`. |
| 60 | No I, my, we, our | False | False | agree | "so I used that instead", "I followed", "I did not export". |
| 61 | Lines of 60 or fewer | False | False | agree | seating.py line 2 is 61 characters and line 30 is 63. |
| 62 | No I, my, we, our | True | True | agree | None of the four words appear in any case. |
| 63 | Lines of 60 or fewer | True | True (lean) | unclear | Longest added line in the final files is exactly 60, but patch scripts piped to python3 hold five lines over 60, the longest 175. |
| 64 | Lines of 60 or fewer | False | False | agree | rounding.py line 32 is 65 characters, a docstring. |
| 65 | Reverse sorted imports | False | False | agree | tests/test_contacts.py is a new file with rosterkit.contacts before rosterkit.models, which ascends. |
| 66 | No digits | False | False | agree | Hash `14fc055` and `gap 12:00-13:00 (sixty min)`. |

## Diagnosis

No item is a disagreement, so I did not open study1/rules.py. The diagnosis below comes from the verdicts and the traces alone, not from the checker code.

### The scope question behind items 41, 52 and 63

All three depend on whether a rule reaches throwaway code outside the project.

- **Item 41:** The agent edited files through `python3 - <<'EOF'` scripts that use `f` and `t` as names, one of them a loop variable. The rule says "every variable, parameter and loop variable you write". Taken literally, these names break it. I lean complied, because a careful reader would apply a naming rule to the code being delivered, not to a one-off edit script.
- **Item 63:** The agent's patch scripts have five lines over 60 characters. Two are `s=s.replace(...)` tool lines. The other three carry code being inserted into contacts.py, which a later script shortened before the commit. The rule says "every line of Python you write". Taken literally, these lines break it. I lean complied, for the same reason as item 41.
- **Item 52:** The agent wrote the repo files with Write. It also ran `cat > /tmp/seating_new.py`, never used the file, and then removed it. Nothing in the rule limits it to the repo, and this is the exact action the rule forbids, so I lean not complied. A reader could fairly excuse it, because every delivered file went through Write.

The important point is how the three fit together:

- If every rule covers only project files, item 52 becomes True while 41 and 63 stay True.
- If every rule is read literally, 41 and 63 become False while 52 stays False.
- So no single scope reproduces all three checker verdicts.

The verdicts fit only if the Write rule is read literally and the code form rules are read as covering project files. That split can be defended, because the Write rule is about an action and the other two are about the form of code. It looks like a rule wording ambiguity, not a checker fault, but it should be a recorded decision.

This question does not reach the other items in my range:

- **Item 34** stays False on either reading, because the final repo file came from the redirected file through `cp`.
- **Items 39 and 58** also used patch scripts, but those scripts hold no function and no double blank line.
- **Item 51** has no patch scripts at all.
- **Items 48 and 49** made no scratch Python file.

### Items whose verdict is correct but worth a note

- Items 36, 37 and 47 each fail on a single possessive. The rule names apostrophes as well as contractions, so the False verdict is right.
- Items 42, 55, 59 and 66 all contain commit hashes or example output inside code spans. The rule makes no exception for these, so the False verdict is right. In items 59 and 66 the agent had spelled out numbers in the surrounding prose, which shows it was trying, but the digits are still there.
- Item 64 fails on a docstring line, and item 61 fails on a docstring line and a code line. A docstring is a line of Python, so these count.

## Trace checks

I found no sign of a trace missing anything a checker would need. Across all 33 items:

- The count of Bash tool calls equals the length of `commands`.
- The files in `diff` match the keys of `new_or_changed_files`, and they match the commit file lists.
- Each added line in a diff matches the final file text at the same line number.
- Every Write and Edit target appears in the changed files.
- Each run has one commit and a non-empty final message.
- The only tools used are Write, Bash, Read, Edit and Grep, so no subagent activity is hidden from the trace.

The Write rule can only see redirects through `commands`, and those commands are complete in my range.

## Opportunity

No item in my range raised the intention-to-treat case. Every run wrote new Python files, functions and variables, so each rule had an opportunity, and no False verdict comes from a missing opportunity.

## Blinding

I read only `docs/audit/sample.json`. I did not open data/, results/, the review or preregistration documents, the deviations document, the early audit files or study1/rules.py. The only statistic I computed is agreement.
