# Preregistration: what makes Claude Code follow an instruction file (Study 1)

Status: frozen by the git tag `prereg-study1`, before the first confirmatory run. Pilots ran before this file and are never
pooled with confirmatory data. Skill loading is a separate study with its own registration, written before its runs.

## Questions

Q1. Does a reason clause on a rule in `CLAUDE.md` raise compliance, and does a reason with no content work as well as a real
one? This is the analogue of Langer, Blank and Chanowitz (1978). That paradigm is contested (Folkes 1985), so it is a source
of the question, not a result we expect to reproduce.

Q2. How much does each folk-belief wording feature move compliance, on the same rules: "must", the `IMPORTANT:` prefix,
capitals, a worked example, position in the file, file length?

## Why the design looks like this

Compliance sits at the ceiling for most rules. Across pilots, most of the 59 candidates were at or near 100% regardless of
wording, and wording cannot move a rule already followed. Effects are estimated only on rules with room to move. Claims apply
to rules like those: rules an agent lapses on, not rules in general. The share at ceiling is reported as a finding. Every
candidate and its disposition is in `docs/POOL.md`.

## Stimuli

- Focal rules: the 9 rules of `FOCAL` in `study1/rules.py`. All claims are about these.
- Ballast: the other 5 rules of `POOL_FINAL`. They were at the ceiling in the final-mix pilot, stay in the files so the
  fielded mix is the piloted mix, and are reported descriptively only.
- Pool rule, applied by `analysis/pool_table.py` to compliance pooled across arms, never to a contrast between arms: shown
  compliance within [0.10, 0.95] and no-rule compliance at or below 0.50, first across pilots 1 to 3, then again on pilot 5,
  which used the exact fielded mix. Manual steps before the gates, all named in `analysis/pool_table.py` and all taken without
  reference to arms: `line_length` dropped as a weaker form of `line_60`; `short_final` dropped because a short message passes
  three other rules mechanically; `one_blank` and `no_chain` reworded so that the rule says what the checker measures.
- Real reasons are invented and plausible. No such voice assistant or ticket importer exists in the repos, so this arm tests a
  specific plausible rationale, not a true one. Each shares no content word with its rule (`tests/test_design.py`).
- Generic clauses: 6 paraphrases each of filler, placebo and norm, dealt without repeats within a file, recorded in the manifest.
- Repos and tasks: 2 synthetic Python repos with 3 tasks each (`fixtures/`). Rules and tasks are fully crossed.
- Clause check (`results/clause_check.json`): 8 blind raters (Haiku 5.5), no arm labels, mean ratings out of 5:

| Arm | Specific information | Asserts obligation |
|---|---|---|
| filler | 1.0 | 1.0 |
| placebo | 1.0 | 1.8 |
| norm | 1.0 | 2.9 |
| real | 4.9 | 2.2 |

An earlier placebo set rated 3.9 on obligation, so it was rewritten before this freeze. Norm carries some obligation; that is
disclosed, and it is why norm is a separate arm from placebo.

## Design

A split-plot factorial. Each run is one `claude -p` on one task. Its `CLAUDE.md` holds 11 of the 14 rules, shuffled among inert
filler rules, and every shown rule's wording is drawn independently and uniformly:

| Factor | Levels | Set per |
|---|---|---|
| REASON | none; filler (a non-reason sentence of matched length); placebo (a content-free "because"); norm ("because that is how we do things"); real (rule specific, 11 to 15 words) | rule |
| MODAL | plain imperative; "You must" | rule |
| PREFIX | none; `IMPORTANT:` | rule |
| CASE | normal; operative word in capitals | rule |
| EXAMPLE | absent; present | rule |
| POSITION | emerges from the shuffle; top, middle and bottom third of the file by word count | rule |
| LENGTH | short, mean 514 words (450 to 569); long, mean 3,526 words (3,427 to 3,583) | run |
| PRESSURE | none; a sentence in the task asking for speed and a minimal change | run |

Census P10 and P90 of real instruction files are about 160 and 3,010 words (arXiv 2610.31715). Filler rules carry reasons at
about 26%, the census rate. Each row of the assignment is committed in `data/study1/manifest.jsonl`, seed derived from the study
name, so the assignment predates its runs.

Controls needing no extra runs. Every checker runs on every run, so the rules not shown give a no-rule baseline. That baseline is
not a clean "no instruction" state, because other rules are present. In about 10% of runs one unshown rule is restated in the task
prompt. Positive control criterion: named-in-prompt compliance must exceed no-rule compliance by at least 30 points on focal rules.
If it does not, the assay has failed and no contrast below is read.

Fixed and enforced: the batch aborts on any Claude Code version other than 2.1.303 or a model other than `claude-sonnet-5-5`. Effort
medium, tools Bash, Read, Edit, Write, Glob, Grep, max 40 turns, 600 s timeout. Claude Code's own preamble ("IMPORTANT: ... you MUST
follow them") wraps the file in every run, confirmed from captured requests, so every emphasis effect is marginal to it.

## Outcome

Binary compliance per rule per run, decided by code (`study1/rules.py`) from the transcript and the final repo. No model judges any
outcome. Every checker passes a hand-built compliant trace and fails a hand-built violating one (`tests/test_checkers.py`). Primary
analysis is intention to treat: a run that never reached a rule's opportunity counts as not complied.

## Sample size and stopping

1,000 runs, about 7,070 focal observations. Simulated with `analysis/power.py` from final-mix pilot rates, at alpha .05 and at the
worst case of Holm across two tests:

| True slope mean, points | Slope SD 3 points | Slope SD 6 points |
|---|---|---|
| 5 | 0.62 (Holm 0.49) | 0.40 (0.26) |
| 8 | 0.94 (0.84) | 0.74 (0.59) |

So the study is well powered for about 8 points and underpowered for 5. Nine rules limit this more than runs do: 1,500 runs gain
little. Ceilings also shrink a nominal slope on rules near the top, so realized effects are smaller than nominal ones. A small true
effect may therefore read as inconclusive, and that reading is registered below.

There are no interim looks at any contrast. During the run only status, cost, leak flags and quota are read. The batch stops early
only if it has used 15 points of the account's seven-day window, or the account reads below 25%. It pauses if more than 25 rows are lost
to infrastructure, for diagnosis, and then resumes. None of these depends on outcomes. Whatever exists at a stop is analyzed as registered.

## Exclusions

- A run with an API or infrastructure error is rerun, blind to arm, decided from the error alone. Reruns are logged.
- A run whose captured requests trigger the leak scan is excluded and reported.
- A run that times out or reaches the turn limit stays in, with whatever it did. Counts are reported by arm.
- Nothing else is excluded.

## Estimands and analysis

One command: `make reproduce`. Code: `analysis/study1.py`, frozen at this tag.

Estimator. OLS on the probability scale with run fixed effects, rule intercepts and a separate coefficient for each rule and factor
level. Each contrast yields one estimate per focal rule; the reported effect is their equal-weighted mean, with a t interval across rules
(df = 8). That interval is the claim about new rules like these. Finite-population sensitivity: a studentized randomization test on
these rules and tasks, 2,000 permutations within rule among rows holding the two labels. Run-level factors cannot use run fixed effects;
their SE is by-run variance plus across-rule variance beyond its sampling part.

Confirmatory family 1, two-sided, Holm across the two:

- H1. real versus filler.
- H2. placebo versus filler.

Filler is the comparator because a clause changes a rule's length as well as its meaning. Filler might not be inert, so the reading below
also requires an advantage over no clause at all.

Gated test H3, only if H1 is significant and positive: placebo keeps at least half the real effect (placebo minus half of real, relative
to filler, above zero, one-sided at .05). Reported in all cases: real minus placebo, with a TOST at plus or minus 5 points as a sensitivity.

How the outcomes read, decided now and applied by `reading()` in the code:

| Result | Reading |
|---|---|
| Positive control under 30 points | Assay failed; nothing is read |
| H1 and H2 significant and positive, H3 passes, real above none and placebo above none (each p < .05) | The form of a reason moves compliance. "And a placebo does about as much as a real reason" is added only if the TOST passes |
| H1 significant and positive, H2 not, H3 fails, real above placebo (p < .05) | Reasons work through their content; a placebo does not substitute |
| H1 and H2 not significant, both upper CI bounds under 5 points | A reason clause does not move compliance by a practically useful amount on these rules |
| Anything else | Inconclusive, and said so |

Family 2, two-sided, Holm across the nine: norm versus filler, none versus filler, must versus plain, IMPORTANT versus none, capitals versus
normal, example versus absent, top versus bottom third, long versus short, urgent versus none. Position and length replicate McMillan (arXiv
2605.10039), who found nulls for both.

Sensitivity for the two run-level factors: shown minus unshown, because PRESSURE is an instruction as well as pressure ("skip anything not
strictly needed" can shorten code with no rule in play) and LENGTH changes target density as well as length.

Moderator: REASON by PRESSURE, for real, placebo and norm against filler. A loose analogue of Langer's small-favor, big-favor split: favor size
maps to rule cost more than to user urgency. Secondary, reported with intervals, no significance claim.

Robustness, not used for claims: `analysis/robust.R`, a linear mixed model in lme4 with rule random slopes on real and placebo and random
intercepts for run and task, giving slope variance and a prediction interval for a new rule.

## Exploratory, labeled as such wherever reported

Cost class as a between-rule moderator; polarity; relative depth as a continuous covariate and its interaction with length; rule by task
variation; paraphrase variation within an arm; two-way wording interactions; spillover, meaning the effect of the share of other rules carrying a
reason on a focal rule; compliance on ballast rules; effects on tests passing and turn count; the Haiku replication.

Replication: 300 runs of the same design on `claude-haiku-5-5` (`data/study1haiku/manifest.jsonl`), run after the primary batch if quota allows,
read for sign only, no significance claim. Its pool was selected on Sonnet.

## Known limits, stated now

- EXAMPLE adds specification as well as form, and has no length-matched control. None versus filler calibrates the length part. Some examples
  describe a step the task itself needs (`write_tool`, and the ballast rules `no_chain` and `diff_before_commit`).
- Rules interact mechanically: wrapping for `line_60` adds lines against `func_lines`, and long names from `name_length` do too. Independent labels
  keep the own-rule contrast unbiased, but a clause on one rule may spill onto another.
- Final messages sometimes report on other rules, which adds noise and not bias, since wording is independent across rules.
- 60% of shown rules carry "because" against a census rate of 26%, so a single clause may be diluted relative to a file where it stands out.
- One model, one CLI version, nine rules, two synthetic repos. Results read "Claude Code 2.1.303, Sonnet 5.5, on these rules".
- Rules at 0.91 to 0.94 in pilot leave little room, and selection brings some regression to the mean.

## Validity checks

A blind audit, run before any contrast is computed (`analysis/audit_sample.py`): 100 focal observations, stratified by rule and outcome, read by a
fresh model reader who sees the trace, the rule and the verdict but no arm labels. This checks the checkers and decides no outcome. With about 20
items per reason arm it can find a checker fault but cannot show a small difference in error by arm. A fault found is fixed, all data rescored, and
the change logged. The audit's agreement rate is reported.

The leak scan runs on every request of every run. The isolation procedure and proof are in `docs/ISOLATION.md`. Reviews of this design are in
`docs/REVIEW-1-novelty-design.md` and `docs/REVIEW-2-prereg.md`.

## Deviations

Any departure from this file is logged in `docs/DEVIATIONS.md` with its date and reason, and the registered analysis is still reported.
