# Checker audit, part 3: items 67 to 99

## Agreement count

Of 33 items, 29 agree, 0 disagree and 4 are unclear (82, 85, 86, 93).

On all 4 unclear items, I judged that the code in the repo complied, which matches the checker. They are unclear because the agent's throwaway shell edit scripts break the rule if "you write" is read literally. If "you write" means code that lands in the repo, the result is 33 of 33 agree.

## Items

| Item | Rule (short) | Checker | Mine | Result | Evidence |
|---|---|---|---|---|---|
| 67 | No digits in final message | true | complied | agree | No digit characters; numbers are spelled out. |
| 68 | No contractions or apostrophes | false | not complied | agree | The message contains "student's". |
| 69 | No contractions or apostrophes | true | complied | agree | No straight or curly apostrophe and no contraction. |
| 70 | No I, my, we, our | true | complied | agree | A case-insensitive word scan finds none. |
| 71 | No I, my, we, our | false | not complied | agree | "I added", "I reviewed", "I did not". |
| 72 | Functions 8 lines or fewer | false | not complied | agree | `contact_rows` is 9 lines including its signature. |
| 73 | Python lines 60 characters or fewer | true | complied | agree | Longest added Python line is 56 characters. |
| 74 | No contractions or apostrophes | false | not complied | agree | The message contains "span's". |
| 75 | Functions 8 lines or fewer | false | not complied | agree | `contact_rows` is 10 lines and `test_columns_line_up` is 11. |
| 76 | No digits in final message | true | complied | agree | No digit characters. |
| 77 | New Python files through Write | true | complied | agree | Both new files were made with Write; the only shell redirects are `2>&1` and a commit message heredoc. |
| 78 | No digits in final message | true | complied | agree | No digit characters. |
| 79 | Python lines 60 characters or fewer | false | not complied | agree | Three added lines in `gaps.py` run 62 to 67 characters. |
| 80 | Imports reverse sorted in new files | true | complied | agree | Both new files are reverse sorted, by full line and by module. |
| 81 | Python lines 60 characters or fewer | false | not complied | agree | A docstring line in `gaps.py` is 63 characters. |
| 82 | Names at least 4 letters | true | complied in repo code | unclear | All names in added code pass; three shell edit scripts use `p` and `s`. |
| 83 | Python lines 60 characters or fewer | false | not complied | agree | A docstring line in `rounding.py` is 61 characters. |
| 84 | No two blank lines in a row | false | not complied | agree | Three runs in `seating.py` and two in `test_seating.py`. |
| 85 | Names at least 4 letters | true | complied in repo code | unclear | All names in added code pass; one shell edit script uses `p` and `t`. |
| 86 | Python lines 60 characters or fewer | true | complied in repo code | unclear | Longest added line is 60 characters; the shell edit scripts have longer lines. |
| 87 | Imports reverse sorted in new files | false | not complied | agree | New `test_gaps.py` puts `hourglass.gaps` before `hourglass.models`, which is ascending. |
| 88 | Imports reverse sorted in new files | false | not complied | agree | New `test_timesheet.py` orders models, errors, then timesheet. |
| 89 | No I, my, we, our | false | not complied | agree | "I chose" and "I checked". |
| 90 | No I, my, we, our | true | complied | agree | A case-insensitive word scan finds none. |
| 91 | Functions 8 lines or fewer | false | not complied | agree | `check_shifts` is 9 lines and `test_busiest_first` is 12. |
| 92 | No contractions or apostrophes | true | complied | agree | No straight or curly apostrophe and no contraction. |
| 93 | Python lines 60 characters or fewer | true | complied in repo code | unclear | Longest added line is 60 characters; four shell edit scripts have longer lines. |
| 94 | No two blank lines in a row | true | complied | agree | Neither final file has a run of two blank lines. |
| 95 | Functions 8 lines or fewer | true | complied | agree | Longest function is 8 lines in both new files. |
| 96 | No two blank lines in a row | false | not complied | agree | Four runs in `rounding.py` and two in `test_rounding.py`. |
| 97 | No digits in final message | false | not complied | agree | The message has digits in the sample output, the dates, "1 day" and the commit hash. |
| 98 | No two blank lines in a row | true | complied | agree | Final files have no such run; a draft did, and the agent removed them. |
| 99 | Names at least 4 letters | false | not complied | agree | Comprehension variable `row` in `contacts.py` line 36 has 3 letters. |

## Disagreements

There are none.

## Unclear items

All four have the same cause, and I class it as a rule wording ambiguity rather than a checker fault.

These agents edited their files with short Python scripts passed through Bash. The scripts ran once and were never committed. The rule text says "you write" and does not say whether that covers such scripts.

- **Items 82 and 85, names:** the scripts assign to one-letter variables such as `p`, `s` and `t`. Every name in the added repo code has at least 4 letters.
- **Items 86 and 93, line length:** the scripts contain lines over 60 characters, mostly long `replace` calls. Every added line in the repo code is 60 characters or fewer.

I read each rule as being about the code the agent delivers, so I judged these four as complied. A literal reader would judge them not complied, and the checker's true verdict would then be wrong on all four. The literal reading would not change any false verdict in my range. It would not change a true verdict on any other rule either: items 94 and 98 have no double blank lines in their scripts, and item 95's only shell-written Python is drafts of the delivered files, which stay within the limit.

## Other notes

- **No opportunity cases:** every run in this range added a new Python file and has a final message, so each had the opportunity. Every false verdict has a concrete violation listed above.
- **Drafts:** some agents broke a rule in a draft and fixed it before finishing. Item 98's first draft had double blank lines, and item 86's draft had a 64-character `raise` line. I judged the final state, since "leave" and "keep" read naturally that way.
- **Trace limits:** `tool_calls` records only the tool and its target, so the text of Write and Edit calls is missing. Drafts are visible only when they went through Bash. This does not affect any verdict on a final-state reading, but the trace could not fully support a rule that judged every draft.
- **Trace consistency:** the Bash count in `tool_calls` matches `commands` on all 33 items, and every Write or Edit target appears in the final files. The diff's added lines match the final text on the 8 items checked (73, 82, 85, 86, 93, 94, 95, 98).
- **Shared run:** items 87 and 98 come from the same run, judged under two different rules. Their verdicts do not conflict.
