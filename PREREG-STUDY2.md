# Preregistration: when a skill's description decides whether it loads (Study 2)

Status: frozen by the git tag `prereg-study2`, before the first confirmatory run of this study. No Study 2 confirmatory or pilot
outcome data existed when the question and design were set. A 16-run pilot (`data/s2pilot`) read only status, cost and overall load rate, and it exposed the usage carry-over that the design now handles.

## What we already measured, with no model judgment

`docs/LISTING-MECHANISM.md` gives the rule for Claude Code 2.1.303, measured on 4,915 listing entries with no errors. If all entries fit in 30,000 characters, every skill keeps its description. Otherwise bundled skills keep theirs, the rest are ranked by past invocations on the account, with ties by name, and each keeps its description if it fits what is left. So a short description sorted late can survive where a long one does not. In a sample from a public library the budget binds somewhere between 100 and 150 skills (`results/listing_budget.json`).

Past invocations carry across runs, so each run's target gets a name unique to that run, and no target starts with usage. A distractor invoked in one run gains rank in later runs; distractor loads are recorded and reported.

## Questions

Q1. With the skill's body fixed, does the wording of its description change whether it loads, when the description is visible?

Q2. Does the folk advice hold: is a directive ("ALWAYS invoke") better than a trigger list, and does a "Not for" clause cut false loads?

Q3. When the library is past the budget, does a skill's place in the alphabet decide whether it loads, and does a long description lose to a short one once it no longer fits?

## Stimuli

- 12 target skills (`fixtures/skills.json`), each with a fixed body and a neutral name. Each has 5 description wordings and 4 prompts.
- Wordings: minimal ("Reconciles ledgers."); padded (minimal plus a content-free sentence, matching a trigger list's length); trigger ("Use when ..."); trigger_not (trigger plus "Not for ..."); directive ("ALWAYS invoke this skill when ... You MUST use it ...").
- Prompts: keyword (the job in the skill's words); generic (the job in other words); indirect (a symptom only); decoy (a nearby request on the same files that does not need the skill).
- Distractors: real skill names and descriptions from `alirezarezvani/claude-skills` (MIT), 388 in `fixtures/distractors.json`. A run's distractors are a seeded random sample.
- Workbench: one small repo holding every target's data files, so the files present do not point at the skill in play.

## Design

Each run is one `claude -p` with one target. All independent and uniform, except library, which puts half of runs at the size where the budget binds:

| Factor | Levels |
|---|---|
| WORDING | minimal, padded, trigger, trigger_not, directive |
| LIBRARY | 0 distractors (25%), 50 (25%), 300 (50%) |
| NAME | `aa-` prefix, `zz-` prefix |
| PROMPT | keyword, generic, indirect, decoy |
| TARGET | dealt evenly across 12 |

Fixed and enforced: Claude Code 2.1.303, `claude-sonnet-5-5`, effort medium, tools Skill, Bash, Read, Edit, Write, Glob, Grep, max 6 turns, same isolation as Study 1. Assignment committed in `data/study2/manifest.jsonl`. Whether the target's description reached the model is recorded for every run from the captured request.

## Outcome

Code only, from the transcript: a load is a Skill tool call naming the target, or a Read of its `SKILL.md`, at any point in the run. On decoy prompts a load is a false load.

Secondary: any Skill call to a distractor, and whether the target's description was in the request.

## Sample size and stopping

600 runs. No interim looks at any contrast. Stops early only at the shared quota limits of Study 1, and whatever exists is analyzed. Infrastructure errors rerun blind; a turn-limit or timeout run stays in.

The cell count is small per target, so effects here are read with wide intervals. Large effects are expected (a recall gap of the size reported in arXiv 2610.18522 and 2605.23916 would be tens of points); small ones are out of reach and not claimed.

## Analysis

`analysis/study2.py`, frozen at this tag. Contrasts are estimated per target and averaged with equal weight, with a t interval across 12 targets (df = 11), on non-decoy prompts unless stated. Estimands by level of LIBRARY and NAME as below. Holm across the family.

Confirmatory family:

- C1. trigger versus minimal, description visible (LIBRARY 0 or 50, any NAME; LIBRARY 300 with `aa-`).
- C2. directive versus trigger, description visible.
- C3. trigger_not versus trigger, false loads on decoy prompts, description visible.
- C4. `aa-` versus `zz-`, at LIBRARY 300, pooled over wordings.
- C5. The same trigger versus minimal contrast at LIBRARY 300 with `zz-`, where the listing rule predicts that short descriptions often fit and long ones often do not. Predicted to differ from C1: the advantage of a trigger list shrinks or reverses here. The recorded description rate by wording is reported beside it, and C1 minus C5 is reported as a secondary with its interval.

Padded versus minimal, library-size trend within `aa-`, and prompt type by wording are secondary. Prompt-type and target variation are exploratory, as is any distractor effect.

## Limits, stated now

The `aa-` and `zz-` prefixes are artificial; they stand in for early and late names. The name itself stays informative for `zz-`, so loads there use the name alone. Targets are written by us and sized for a small job, and distractors come from one public library. The budget is a property of this CLI version.

## Deviations

Logged in `docs/DEVIATIONS.md` with date and reason; the registered analysis is still reported.
