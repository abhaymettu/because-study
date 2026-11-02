# because: design draft (pre-review, 2026-11-01 20:10 CST)

Not yet the preregistration. Written to be attacked.

## Questions

Q1. Does a reason clause raise an agent's compliance with a rule in its instruction file (CLAUDE.md), and does a
placebo reason (length-matched, information-free, "because that is how we do it in this repository") work as well
as a real one? This is the agent analogue of Langer, Blank and Chanowitz (1978), the copy-machine study.

Q2. Which of the folk-belief wording features move compliance, and by how much, on the same rules: reason,
"must" modal, capitals / "IMPORTANT:", position in the file, file length, a concrete example.

Q3 (second study, same harness). With the skill body fixed, does the wording of a skill's description (minimal,
trigger list, trigger list plus a "Not for ..." clause, length-matched padding) change whether Claude Code loads
the skill, and does library size (0 / ~50 / ~300 distractor skills) change that?

## Study 1 design (rules)

- Items: about 24 to 30 rules that are checkable by code and cut against the model's defaults (nonstandard test
  command, commit-message prefix, never-edit path, changelog entry, stdlib-only, file header, logging helper,
  final-message format, and so on). Each rule has a tiny synthetic repo and a task that gives it a chance to
  apply without naming it.
- Unit of randomization: one `claude -p` run. Each run draws every factor independently (conjoint-style,
  within rule):
  - REASON in {none, real, placebo}
  - MODAL in {plain imperative, "must"}
  - CAPS in {off, on} ("IMPORTANT:" prefix and capitalised modal)
  - POSITION in {top, middle, bottom} of the CLAUDE.md
  - LENGTH in {short (about 8 other rules), long (about 60 other rules plus prose)}
  - EXAMPLE in {absent, present}
  - plus a NO-RULE control (rule absent) on a fixed share of runs, to show the rule is not the default.
- Outcome: binary compliance, decided by a checker per rule on the final repo state and the trace (commands run,
  files touched, final message). No model judges anything.
- Secondary: task success (repo tests pass), turns, tokens.
- Estimand: AMCE on the probability scale. Primary estimator: linear probability model with rule fixed effects;
  CIs by cluster bootstrap over rules; p-values by randomization inference (permute each factor within rule).
  Holm across the confirmatory family. Robustness: logistic GLMM (lme4) with rule random intercepts and slopes.
- Placebo test: superiority of placebo over none, and equivalence of placebo to real by TOST with a margin of
  plus or minus 10 points.
- Pilot gate: compliance must sit off the ceiling for most rules; rules outside a 10 to 90 percent band in the
  bare condition are rewritten or dropped before the preregistration freezes. Pilot data are never analysed
  with the confirmatory data.

## Isolation

`claude -p` with `--setting-sources project`, `--strict-mcp-config --mcp-config '{"mcpServers":{}}'`,
`--settings '{"claudeMdExcludes":[home/**],"autoMemoryEnabled":false}'`, `--tools Bash,Read,Edit,Write,Skill`,
`--no-session-persistence`, a run directory with no instruction files in any ancestor, neutral git identity.
Proof: a local forwarding proxy (`harness/capture_proxy.py`) records each request body sent to the model, and a
leak scan runs on every captured request (no user CLAUDE.md, skills, hooks, memory, MCP).

## Model

Pinned Claude Code version (2.1.303) and an explicit `--model`. Which model is a pilot decision (Sonnet 5.5 is
cheaper; Opus 5.5 is what many users run).

## Open risks I already see

- Ceiling: single-rule compliance is reported near 93 to 99 percent elsewhere.
- Placebo text that accidentally carries information.
- Reason quality varies by rule; the real-reason effect is an average over these reasons.
- One model family; claims are "Claude Code, version X, model Y".
- Quota: the subscription's weekly window bounds the run count.
