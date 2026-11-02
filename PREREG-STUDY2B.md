# Preregistration: the reversal past the budget (Study 2b)

Status: frozen by the git tag `prereg-study2b`, before its first run. Written after reading Study 2, whose registered test of this
question (C5) came out at -27 points with an interval from -67 to +13. The point of this study is to resolve that interval, so its
hypotheses come from Study 2 and none of its data was seen when they were set.

## Why this study

Study 2 found that with a skill's description in view, a trigger list ("Use when ...") loaded the skill more often than one short
sentence. It also found that past the budget, with a late-sorted name, the order looked reversed: minimal 0.61, trigger 0.24, directive
0.36, and only minimal ever kept its description (65% of runs against 0%). Few runs fell in those cells, with 8 of 12 targets estimable,
so the registered contrast could not separate the two wordings. The listing rule in `docs/LISTING-MECHANISM.md` predicts this reversal
from length alone.

The practical advice this points at is to write short descriptions, and that raises a question Study 2 did not ask. Does a short
description that still says when to use the skill keep the benefit of each? So this study adds one wording.

## Questions

Q1. Past the budget, for a late-sorted skill with no usage history, does a short plain description beat a long trigger list?

Q2. Does a short description in trigger form beat the long trigger list past the budget, and what does it cost below the budget?

## Stimuli

As in Study 2: the 12 targets with their bodies and prompts, the workbench, and the distractors from `alirezarezvani/claude-skills` (MIT).
One new field per target, `short_when`, written before any run and holding the same content as `job` ("Reconciles ledgers." becomes "Use
when reconciling ledgers."). Wordings:

| Wording | Example | Length |
|---|---|---|
| minimal | Reconciles ledgers. | mean 21 characters |
| short_trigger | Use when reconciling ledgers. | mean 32 characters |
| trigger | Use when reconciling a ledger or bookkeeping CSV against a bank statement, ... | mean 140 characters |

Each is the wording of that name from Study 2 except short_trigger, which is new.

## Design

Each run is one `claude -p` with one target. Names are `zz-` only, and run numbers start at 10000, so no target shares a name with a
Study 2 target and none starts with usage.

| Factor | Levels | Set how |
|---|---|---|
| WORDING | minimal, short_trigger, trigger | fixed count per cell |
| LIBRARY | 300 distractors; 50 distractors | 12 runs per target and wording at 300, 4 at 50 |
| TARGET | 12 | fully crossed |
| PROMPT | keyword, generic, indirect | independent and uniform |

Decoy prompts are dropped because Study 2 put false loads at 0.7%, which leaves nothing to learn here. The size of 50 stands in for "below the
budget" because a library of 0 leaves nothing to choose among, and Study 2 had every wording near 1.0 there.

Total 576 runs. Assignment committed in `data/study2b/manifest.jsonl`, seed derived from the study name. Fixed and enforced as in Study 2:
Claude Code 2.1.303, `claude-sonnet-5-5`, effort medium, tools Skill, Bash, Read, Edit, Write, Glob, Grep, max 6 turns, same isolation.

Past invocations on the account carry into later runs, so distractors invoked in Study 2 hold rank here. As of this freeze that is three
names: `month-end-close` (5), `sql-database-assistant` (1), `changelog-generator` (1). Their rank is the same across arms. Any further ones
are recorded.

## Outcome

Code only, as in Study 2: a load is a Skill tool call naming the target, or a Read of its `SKILL.md`. Whether the target's description
reached the model is recorded per run from the captured request.

## Sample size and stopping

576 runs. With 12 runs per cell, a within-cell rate near 0.3, and a spread of 10 to 20 points between targets, the interval across 12 targets has an SE of 6 to 8
points. Power to detect 30 points at the worst case of Holm over four tests is 0.76 to 0.94, and for 20 points 0.37 to 0.60; both figures assume that spread. No
interim looks at any contrast. The batch stops early only at 6 points of the account's seven-day window or below 25% remaining. Whatever exists is
analyzed. Infrastructure errors rerun blind. A turn-limit run stays in.

## Analysis

`analysis/study2b.py`, frozen at this tag. Contrasts per target, averaged with equal weight, with a t interval across 12 targets (df = 11). Holm across:

- D1. minimal minus trigger, library 300. Predicted positive. Replicates C5 of Study 2.
- D2. short_trigger minus trigger, library 300. Predicted positive.
- D3. short_trigger minus minimal, library 300. No directional prediction.
- D4. short_trigger minus trigger, library 50. Predicted at or below zero.

How the outcomes read, decided now and applied by `reading()` in the code:

| Result | Reading |
|---|---|
| D1 significant and positive | Past the budget a short plain description beats a long trigger list |
| D2 significant and positive, and D4's lower bound above -10 points | A short description that says when to use the skill beats a long one past the budget and costs under 10 points below it |
| Neither | Inconclusive |

Secondary: description rate by wording; the same contrasts within each prompt type. Exploratory and labeled so: load rate by whether the description
reached the model within a wording, which is not randomized, since fit depends on which distractors a run drew.

## Limits, stated now

Everything in Study 2's limits applies. In addition, `short_trigger` is a mechanical rewrite of `job`, and a person writing a short trigger by hand might do better.
A target's name stays informative even with no description, so a load past the budget can come from the name alone. Only `zz-` names run here, so
this says nothing new about name order. The budget and the ranking belong to this CLI version.

## Deviations

Logged in `docs/DEVIATIONS.md` with date and reason; the registered analysis is still reported.
