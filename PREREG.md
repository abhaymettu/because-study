# Preregistration: what makes Claude Code follow an instruction file (Study 1)

Status: frozen by the git tag `prereg-study1`, before the first confirmatory run. Pilots ran before this file and are
never pooled with confirmatory data. Skill loading is a separate study with its own registration (`PREREG-STUDY2.md`).

## Questions

Q1. Does a reason clause on a rule in `CLAUDE.md` raise compliance, and does a reason with no content work as well as a
real one? This is the analogue of Langer, Blank and Chanowitz (1978). That paradigm is contested (Folkes 1985), so it
is a source of the question, not a result we expect to reproduce.

Q2. How much does each folk-belief wording feature move compliance, on the same rules: "must", the `IMPORTANT:` prefix,
capitals, a worked example, position in the file, file length?

## Why the design looks like this

The pilots showed that compliance sits at the ceiling for most rules. Of the first 26 rules, 17 were at or above 99%.
Wording cannot move a rule that is already followed, so effects are estimated only on rules with room to move. Claims
apply to rules like those: rules where an agent lapses, not rules in general. The share of candidates at ceiling is
reported as a finding. Every candidate and its disposition is in `docs/POOL.md`.

## Stimuli

- Rules: the 15 rules of `POOL_FINAL` in `study1/rules.py`. Pool rule, applied by `analysis/pool_table.py` to pilot data
  pooled across arms: shown compliance within [0.10, 0.95] and no-rule compliance at or below 0.50. Selection used pooled
  compliance only, never a contrast between arms. Rule text, real reasons and worked examples were fixed before this
  registration.
- Repos and tasks: 2 synthetic Python repos with 3 tasks each (`fixtures/`). Rules and tasks are fully crossed, so a rule's
  difficulty is separable from a task's.
- Clause check (`results/clause_check.json`): 8 blind raters (Haiku 5.5), rating clauses with no arm labels, gave the
  placebo, norm and filler clauses 1.0 of 5 on specific information and the real reasons a mean of 4.0 (lowest 3.4). The
  clauses contain none of their rule's tokens.

## Design

A split-plot factorial. Each run is one `claude -p` on one task. Its `CLAUDE.md` holds 12 of the 15 target rules, shuffled
among inert filler rules, and every target rule's wording is drawn independently and uniformly:

| Factor | Levels | Set per |
|---|---|---|
| REASON | none; filler ("This note is one of several notes kept here in this file."); placebo ("because that is what needs to be done here in this project"); norm ("because that is how we do things here in this repository"); real (rule specific, 11 to 15 words) | rule |
| MODAL | plain imperative; "You must" | rule |
| PREFIX | none; `IMPORTANT:` | rule |
| CASE | normal; operative word in capitals | rule |
| EXAMPLE | absent; present (shows a different instance than the task needs) | rule |
| POSITION | emerges from the shuffle; top, middle and bottom third of the file by word count | rule |
| LENGTH | about 400 words; about 3,300 words (census P10 and P90 are about 160 and 3,010) | run |
| PRESSURE | none; a sentence in the task asking for speed and a minimal change | run |

Filler rules carry reasons at the census rate of about 26%, so a reason on a target is not a salience cue by itself.

Each row of the assignment is committed in `data/study1/manifest.jsonl` (seed derived from the study name), so the
assignment predates its runs.

Controls needing no extra runs. Every checker runs on every run, so the 3 rules not shown give a no-rule baseline. In 10%
of runs one unshown rule is restated in the task prompt: this positive control shows the assay can detect change.

Fixed: Claude Code 2.1.303, `claude-sonnet-5-5`, effort medium, tools Bash, Read, Edit, Write, Glob, Grep, max 40 turns,
600 s timeout. Claude Code's own preamble ("IMPORTANT: ... you MUST follow them") wraps the file in every run, confirmed
from captured requests, so every emphasis effect is marginal to it.

## Outcome

Binary compliance per rule per run, decided by code (`study1/rules.py`) from the transcript and the final repo. No model
judges any outcome. Each checker passes a hand-built compliant trace and fails a hand-built violating one
(`tests/test_checkers.py`). Primary analysis is intention to treat: a run that never reached a rule's opportunity counts
as not complied.

## Sample size and stopping

1,200 runs (14,400 rule observations). In simulation (`analysis/power.py`, `results/power.txt`) 1,000 runs give 0.89 power
for a 5 point effect if rule slopes vary with SD 3 points, and 0.61 if SD 6 points; 1,500 runs give 0.97 and 0.68, so rule
heterogeneity limits power more than run count does. There are no interim looks at any contrast. During the run only
status, cost, leak flags and quota are read.

The batch stops early only if it has consumed 15 points of the account's seven-day quota, or the account reads below 25%.
Those stops do not depend on outcomes, and whatever exists is analyzed as registered.

## Exclusions

- A run with an API or infrastructure error is rerun, blind to arm, from the error text alone. Reruns are logged.
- A run whose captured requests trigger the leak scan is excluded and reported.
- A run that times out stays in, with whatever it did.
- Nothing else is excluded. Counts are reported by arm.

## Estimands and analysis

One command: `make reproduce`. Code: `analysis/study1.py`, frozen at this tag.

Estimator. OLS on the probability scale with run fixed effects, rule intercepts and a separate coefficient for each rule
and factor level. Each contrast yields one estimate per rule; the reported effect is their equal-weighted mean, with a
t interval across rules (df = rules minus 1). That interval is the claim about new rules like these. Finite-population
sensitivity: a studentized randomization test on these rules and tasks, 2,000 permutations within rule. Run-level factors
cannot use run fixed effects, so their SE combines by-rule and by-run components.

Confirmatory family 1, two-sided, Holm across the two:

- H1. real versus filler.
- H2. placebo versus filler.

Filler, not none, is the comparator, because a clause changes a rule's length and the distance to its key token as well
as its meaning. None versus filler measures that length effect separately.

Gated test H3, only if H1 is significant and positive: placebo keeps at least half the real effect (placebo minus half of
real, relative to filler, is above zero, one-sided at .05). Reported in all cases as a sensitivity: real minus placebo
with a TOST at plus or minus 5 points.

How the outcomes read, decided now:

| Result | Reading |
|---|---|
| H1 and H2 significant, H3 passes | The form of a reason moves compliance, whatever it says |
| H1 significant, H2 not, H3 fails | Reasons work through their content; a placebo does not substitute |
| H1 and H2 not significant, upper CI bound under 5 points | A reason clause does not move compliance by a practically useful amount on these rules |
| Anything else | Inconclusive, and said so |

Family 2, two-sided, Holm across the nine: norm versus filler, none versus filler, must versus plain, IMPORTANT versus
none, capitals versus normal, example versus absent, top versus bottom third, long versus short, urgent versus none.
Position and length are replications of McMillan (arXiv 2605.10039), who found nulls for both.

Moderator: REASON by PRESSURE, for real, placebo and norm against filler. This is Langer's small-favor, big-favor test.
Secondary, reported with intervals, no claim of significance across the three.

Robustness, not used for claims: a linear mixed model in lme4 with rule random slopes on the reason contrasts and random
intercepts for run and task, giving slope variance and a prediction interval for a new rule.

## Exploratory, labeled as such wherever reported

Cost class (token, habit, effort) as a between-rule moderator; polarity; relative depth as a continuous covariate and
its interaction with length; rule by task variation; two-way wording interactions; spillover, the effect of the share
of other rules in the file carrying a reason on a focal rule; effects on tests passing and turn count; the Haiku 5.5
replication below.

Replication: 300 runs of the same design on `claude-haiku-5-5` (`data/study1haiku/manifest.jsonl`), run after the primary
batch, read for the same sign, with no significance claims.

## Validity checks after the data

A blind audit samples 100 rule observations, stratified by rule and outcome, for a reader who sees the trace but no arm
labels. Disagreement with the checker is reported by arm. A checker error found this way is fixed and all data rescored,
and reported as a deviation.

The leak scan runs on every request of every run (`harness/agent_run.py`). The isolation procedure is in
`docs/ISOLATION.md`.

## Deviations

Any departure from this file is logged in `docs/DEVIATIONS.md` with its date and reason, and the registered analysis is
still reported.
