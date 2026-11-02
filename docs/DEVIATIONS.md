# Deviations from the preregistrations

Everything that changed after a freeze, with its date and reason. The registered analysis is still what gets reported.

## Both studies

**2026-11-01 23:02 CST. A bug in the frozen analysis, found on first reading Study 2's output, fixed.** `by_rule` returned a NaN p-value
when every rule or target agreed exactly, which happens at a floor or ceiling, and the NaN corrupted Holm for the rest of the family (C4 at
+51 points showed an adjusted p of 1.000). A zero SE now gives p = 1 for a zero estimate and p = 0 otherwise. It changes results only where
such a tie exists. Study 2's first printout had the bug; the numbers reported are from the fixed code.

**2026-11-02 00:00 CST. History rewritten once, before the repo went public, to remove account identifiers.** Claude Code tags each request with an account id and a device id, and the sample captures kept them. `git filter-repo` removed that one `metadata` field from every kept capture in every commit, so the commit and tag hashes changed. By my own check, which you can't repeat because the old tags aren't public, dates, messages and every other file are as they were, and the preregistration files hash to the same git blobs at the new tags as at the old ones (`PREREG.md` 2f7f2ff909, `PREREG-STUDY2.md` e6002afada, `PREREG-STUDY2B.md` 4290c9823c). No timestamping service was used.

**2026-11-02 13:07 CST. New repo created for publication.** The work ran in a private repo. Its commits from before the rewrite still hold those ids, awaiting removal, so that repo stays private and this one was created from the rewritten `main` and the four tags, with the same hashes. A reader can inspect the tags and commit dates here, and an author can set those. GitHub's activity log and Actions times for the Study 2c freeze can't be inspected publicly, and [`TIMING.md`](TIMING.md) copies them as a self-reported record. No registration, analysis or result changed.

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

**Harness edits after the tag. None touches the behavior of a Study 1, 2 or 2b run.** The leak scan's `agent-memory` needle became `agent-memory/`,
because a public skill in the Study 2 library has that name. `run_agent` gained a `probe` parameter for Study 2. `run_row`,
`read_claude_stream` and the `command` option were factored out so a stand-in or another agent can use the same path. Kept
request samples now drop `metadata`, which holds account and device ids (see below). The wrapper shell is written once rather than
before each run. The batch that produced the data loaded the code as frozen plus the first two edits. Later edits: `RUN_ROOT` now honors `BECAUSE_RUN_ROOT` and falls back to `/tmp/wk` where `/private/tmp` does not exist, and `TMPDIR` follows its parent (2026-11-01 23:04 CST). At their default values on a Mac these give the frozen `/private/tmp/wk` and `/private/tmp/`, so they have no effect there. `run_agent` gained an `env` option, and `run_row` uses it to pass `SLASH_COMMAND_TOOL_CHAR_BUDGET` for rows with a `list_budget`, which only Study 2c and its pilot have (2026-11-02 01:46 CST). `analysis/study2.py` `load()` gained a `budget` column in the same commit, which the Study 2 and 2b analyses do not read. `harness/batch.py` gained `--dry-run`, which prints the row counts and starts no agent (2026-11-02 02:02 CST).

**2026-11-01 23:56 CST. Scope of "you write" written down after the registered audit, before any contrast.** See `docs/audit/report.md`. No checker changed. A sensitivity with `write_tool` on repo paths only is in `results/exploratory.json`.

**The registered audit used three readers.** `PREREG.md` line 175 names one fresh model reader. Three were used, each on part of the 100 items, because the items were too large for one. Items showed the checker's verdict, as that line allows.

**Exploratory analyses that were not run.** Of those `PREREG.md` lists, relative depth, rule by task, paraphrase variation, two-way wording interactions and spillover were not run. Neither were effects on tests passing and on turn count, which appear only as overall rates. Cost class and polarity were not tested. `results/exploratory.json` holds only a descriptive mean of real vs filler for each, and no surface reports it. None of this was required by the registration.

**Haiku replication stopped once and resumed, 2026-11-02.** The batch stopped at 177 of 300 at 01:07 CST on a 4-point sizing limit set at launch, which is not a registered stop. That counter reads the whole account, and a review was running at the same time. It was resumed with the same command at about 01:42 CST.

**Batch logs are tracked from here on, since `PREREG.md` line 103 says reruns are logged (2026-11-02 02:02 CST).** The confirmatory batches' `batch.log` files left `.gitignore`. Pilot logs stay out, since their leak flags print local needle strings.

**Mixed model restricted to focal rules.** `analysis/export_long.py` exported every shown rule as frozen. The registration's claims are about focal rules, so the export now keeps only those. This is a robustness check and decides nothing.

## Studies 2 and 2b, registered secondaries

**2026-11-02 00:53 CST. Secondaries the registrations name were missing from the frozen code, and were added after the family results were read.** `PREREG-STUDY2.md` asks for C1 minus C5 with its interval, a library-size trend within `aa-`, and prompt type by wording. `PREREG-STUDY2B.md` asks for its contrasts within each prompt type. `analysis/study2.py` and `analysis/study2b.py` as frozen computed none of these except library 300 versus 0. They now do, in the form the registrations describe, with no correction. No family result changes, and these decide nothing.

## Study 2b, frozen at `prereg-study2b`

**2026-11-01 23:54 CST. The batch stopped at 535 of 576 runs on its registered quota stop.** The six-point counter reads the whole account, and Study 1 was running at the same time, which the registration did not anticipate. The registration says whatever exists is analyzed, so the remaining 41 were not run. One further run is excluded by the leak scan, a false positive on the needle `agent-memory/`, which appears in a public skill's text.

## Study 2c, frozen at `prereg-study2c`

**2026-11-02 02:02 CST. An additive edit to the analysis after the tag, before any outcome was read.** Each cell of `grid` in `analysis/study2c.py` gained `target_mean` and `ci`, the mean across targets and its 95% interval, so the budget figure can draw intervals. No family row, secondary or reading changes, which was checked by running the frozen and edited code on a synthetic batch.

## Docstrings

**2026-11-02 02:02 CST.** The docstring of `study2/design.py` no longer calls the listing alphabetical. Nothing that runs changed.
