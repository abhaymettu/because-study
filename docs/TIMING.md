# Timing record, self-reported

The work ran in a private repo before this one existed. That repo's commits from before the history rewrite still hold account and device identifiers awaiting removal, so it stays private, and you can't inspect the GitHub entries below. This is my copy of them, read from GitHub's API on 2026-11-02, so treat it as my statement. What you can inspect is the git record here, the tags and commit dates, and an author can set those.

This is a selection. The log's other entries are pushes at 06:12:40, 06:48:21, 06:53:07, 08:16:00, 08:41:34, 09:10:46 and 15:00:57. Entries that name a commit from before the rewrite are given without that hash. All times are UTC on 2026-11-02.

| Time | GitHub entry | What it marks |
|---|---|---|
| 03:52:50 | Repo created | `prereg-study1` has commit date 03:52:49 |
| 03:52:55 | Branch `main` created by a push | Study 1 freeze, before the rewrite |
| 04:10:07 | Push to `main` | Study 2 freeze, before the rewrite. `prereg-study2` has commit date 04:10:05 |
| 05:04:14 | Push to `main` | Study 2b freeze, before the rewrite. `prereg-study2b` has commit date 05:04:13 |
| 06:11:06 | Force push to `main` | The history rewrite |
| 07:46:29 | Push to `main`, head `c22f089` | Study 2c freeze. `prereg-study2c` has commit date 07:46:28 |
| 07:46:31 | Actions run 41408469178, workflow `Site`, event push, head `c22f089`, concluded failure | The run failed at its Pages step, because Pages was off |

[`data/study2c/batch.log`](../data/study2c/batch.log) is my own record too. Its first line is at 01:46:48 CST, or 07:46:48 UTC, and the earliest start, by finish time minus duration, is about 07:46:40 UTC.
