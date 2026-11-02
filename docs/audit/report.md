# The blind audit

Run on the finished Study 1 batch before any contrast between arms was computed, as registered. `analysis/audit_sample.py` drew 100 focal observations, stratified by rule and outcome, with arm labels removed (`sample.json`). The key linking items to arms was kept outside the repo until the audit closed. Three fresh model readers each took a third of the items and judged them from the rule text and the trace, before opening any checker (`report-part-1.md`, `report-part-2.md`, `report-part-3.md`). Readers decided nothing about outcomes. Their job was to find checker faults.

## Agreement

Of 100 items, 92 agree with the checker with no qualification. Seven are marked unclear, where the reader's own lean matches the checker. One disagrees.

All eight turn on one question: does a rule's "you write" reach throwaway code that never lands in the repo?

- Six unclear items (41, 63, 82, 85, 86, 93) are code-form rules where the agent's edit scripts, piped to `python3` and never committed, break the rule while the committed code keeps it. The checker passes these.
- Two items (26 disagree, 52 unclear) are the Write tool rule, where the delivered files came from Write but a scratch `.py` in `/tmp` came from a shell redirect. The checker fails these.
- Reader 1 also flagged one grouped-imports case (item 5), which agrees under the reading that a file's imports are one list.

## Decision, made before any contrast

No checker changes. A code-form rule scores the code the run leaves in the repo, and the Write tool rule scores the action, including a scratch file, because a new Python file made by redirection is what its text forbids. That split is now stated, not implicit. Because one reader read item 26 the other way, the analysis reports a sensitivity with `write_tool` scored on repo paths only.

A reader also noted that the Write tool pattern cannot see a quoted or variable redirect target. Across all 1,000 runs there are no such commands, so this changes nothing.

## What the audit can and cannot show

With about 20 items per reason arm it can find a checker fault, as the early audit did (`early-report.md`, one fault, fixed). It cannot show a small difference in checker error by arm.
