# Deviations from the preregistrations

Everything that changed after a freeze, with its date and reason. The registered analysis is still what gets reported.

## Both studies

**2026-11-01 23:02 CST. A bug in the frozen analysis, found on first reading Study 2's output, fixed.** `by_rule` returned a NaN p-value
when every rule or target agreed exactly, which happens at a floor or ceiling, and the NaN corrupted Holm for the rest of the family (C4 at
+51 points showed an adjusted p of 1.000). A zero SE now gives p = 1 for a zero estimate and p = 0 otherwise. It changes results only where
such a tie exists. Study 2's first printout had the bug; the numbers reported are from the fixed code.

## Study 1, frozen at `prereg-study1`

**2026-11-01 22:10 CST. Study 1 runs swept into the Study 2 freeze commit.** `git add -A` at the Study 2 tag also committed
about 154 partial Study 1 runs. Nobody had read a contrast, and the final data commit supersedes them.

**2026-11-01 22:15 CST. Audit sampler brought in line with the plan.** The registration says 100 focal observations. The
sampler as frozen drew from every shown rule, so it now draws from focal rules only. It also gives the reader a diff, because
many rules apply only to lines the agent added and the final file alone does not show which those are.

**2026-11-01 22:40 CST. A checker fault found by an early blind audit, fixed and rescored.** With about 260 runs in, before any
contrast, a fresh reader checked 36 extra observations with no arm labels (`docs/audit/early-report.md`). It agreed with 34 and
found one fault. `write_tool` failed a run for `cat >>` onto a file the repo already had, which the rule does not cover. The
checker now ignores a redirect onto a file that existed at the base commit. The registered audit of 100 observations still runs on
the finished batch. Every verdict is computed from traces, so all runs are rescored by rerunning the analysis.

**Harness edits after the tag, none of which touch a run's behavior.** The leak scan's `agent-memory` needle became `agent-memory/`,
because a public skill in the Study 2 library has that name. `run_agent` gained a `probe` parameter for Study 2. `run_row`,
`read_claude_stream` and the `command` option were factored out so a stand-in or another agent can use the same path. Kept
request samples now drop `metadata`, which holds account and device ids (see below). The wrapper shell is written once rather than
before each run. The batch that produced the data loaded the code as frozen plus the first two edits.
