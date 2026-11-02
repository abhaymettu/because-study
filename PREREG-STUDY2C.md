# Preregistration: raising the listing budget (Study 2c)

Status: frozen by the git tag `prereg-study2c`, before its first run. A 16-run pilot (`data/s2cpilot`) read only status, cost, turns, leak flags and whether the target's description reached the model, by arm. No load was read. Pilot run numbers start at 29000, so no pilot name repeats here.

## Why this study

Study 2b found that at 300 skills a short description beats a long trigger list by about 30 points, and the text attributes that to the CLI's listing budget. A hostile review (`docs/REVIEW-3-final.md`, item S3) pointed out the gap. No arm has ever changed the budget. "Past the budget" has always meant "300 skills", and whether a description fits has depended on the distractors a run drew. Claude Code documents two ways to raise the budget, `skillListingBudgetFraction` and `SLASH_COMMAND_TOOL_CHAR_BUDGET` (https://code.claude.com/docs/en/skills), so the budget can be manipulated directly and nothing else needs to move.

This study was written after reading Studies 2 and 2b. Its hypotheses come from them, and none of its data was seen when they were set.

## Questions

Q1. With 300 skills and everything else fixed, does raising the budget until every description fits bring a long trigger list back?

Q2. With the budget raised, does the reversal close, so that a long trigger list does at least about as well as a short description?

Q3. What does raising the budget cost per run, and does showing every description send the agent to the wrong skill more often?

## Stimuli

As in Study 2b: the 12 targets with their bodies and prompts, the workbench, and the distractors from `alirezarezvani/claude-skills` (MIT). Two wordings, both from Study 2b: minimal ("Reconciles ledgers.", mean 21 characters) and trigger ("Use when reconciling a ledger or bookkeeping CSV against a bank statement, ...", mean 140 characters).

## Design

Each run is one `claude -p` with one target. Names are `zz-` only, and run numbers start at 20000, so no target shares a name with an earlier study and none starts with usage.

| Factor | Levels | Set how |
|---|---|---|
| BUDGET | the CLI's own (30,000 characters on this model); raised to 100,000 by `SLASH_COMMAND_TOOL_CHAR_BUDGET` | fixed count per cell |
| WORDING | minimal, trigger | fixed count per cell |
| TARGET | 12 | fully crossed |
| PROMPT | keyword, generic, indirect | independent and uniform |

8 runs per target, wording and budget, 384 in total. Library is 300 distractors per run, a seeded random sample. Any 300 from the library need at most about 79,000 characters, so 100,000 fits them all.

Assignment committed in `data/study2c/manifest.jsonl`, seed derived from the study name. Fixed and enforced as in Study 2b: Claude Code 2.1.303, `claude-sonnet-5-5`, effort medium, tools Skill, Bash, Read, Edit, Write, Glob, Grep, max 6 turns, same isolation.

Study entries were cleared from the account's usage record on 2026-11-02, before the pilot, so distractor rank starts with no carry-over from earlier studies apart from what the pilot added. Distractors invoked during this batch gain rank for later runs in both arms. That is recorded.

## Manipulation check

Whether the target's description reached the model is recorded per run from the captured request. Pilot: 7 of 7 with the budget raised, 1 of 9 at the CLI's own budget. If under 95% of raised runs carry the description, the manipulation failed and nothing is read.

## Outcome

Code only, as in Studies 2 and 2b: a load is a Skill tool call naming the target, or a Read of its `SKILL.md`, at any point in the run.

## Sample size and stopping

384 runs. The pilot cost $0.065 per run at the CLI's budget and $0.147 raised, so about $41 at API-equivalent prices. No interim looks at any contrast. With 8 runs per cell and the spread between targets seen in Study 2b, the SE across 12 targets is about 6 points for a simple contrast and about 9 for the interaction. That gives power near 1 for a 50-point E1 and about 0.9 for a 35-point E4 at the worst case of Holm over four tests, both assuming that spread.

The batch stops early only below 25% remaining on the account's seven-day window. There is no points counter, because that counter reads the whole account, and it cost Study 2b 41 runs. Whatever exists is analyzed. Infrastructure errors rerun blind. A turn-limit run stays in.

## Analysis

`analysis/study2c.py`, frozen at this tag. Contrasts per target, averaged with equal weight, with a t interval across 12 targets (df = 11). Holm across:

- E1. trigger, raised minus the CLI's own budget. Predicted positive.
- E2. minimal, raised minus the CLI's own budget. Predicted positive and smaller than E1.
- E3. trigger minus minimal, raised. Predicted at or above zero.
- E4. Interaction: (trigger minus minimal, raised) minus (trigger minus minimal, the CLI's own budget). Predicted positive.

How the outcomes read, decided now and applied by `reading()` in the code:

| Result | Reading |
|---|---|
| Under 95% of raised runs carry the description | The manipulation failed; nothing is read |
| E1 and E4 significant and positive, and E3's lower bound above -10 points | The budget causes the reversal: with the budget raised a long trigger list recovers and is within 10 points of a short description or above it |
| E1 significant and positive, otherwise | Raising the budget helps a long trigger list, and the reversal is not shown to close |
| Anything else | Inconclusive |

Secondary: minimal minus trigger at the CLI's own budget, which repeats D1 of Study 2b; E1 within each prompt type; by cell, the load rate, the description rate, the share of runs that load only another skill, the share that load no skill, cost and turns.

## Limits, stated now

Everything in Studies 2 and 2b's limits applies. Raising the budget shows every distractor's description as well as the target's, which is what a person who raises it gets, so this tests the budget and not the target's description alone. The size of the effect belongs to a library of this size and to `zz-` names with no usage. The budget rule and the variable belong to this CLI version.

## Deviations

Logged in `docs/DEVIATIONS.md` with date and reason; the registered analysis is still reported.
