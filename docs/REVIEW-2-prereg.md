# Review 2: preregistration audit before freeze (2026-11-01)

Verdict: the estimator is sound, but do not freeze yet. The decision table can read a filler artifact as a reason effect, one rule contaminates three others, one checker does not measure its rule, and the prereg commits to things that do not exist.

Method. Simulations call the repo's own `assign`, `render_file`, `rule_level_estimates`, `by_rule`, `run_level` and `randomization_p`, at 1,200 runs, K=12, POOL.md base rates, run SD 8 points, final-message cluster SD 10 points, slope SD 3 points when a level has an effect.

Simulation coverage. The long batch stopped early and the coordinator asked for the report now. Null: 600 reps per scenario. Reading table: 200 reps (Monte Carlo SE up to 3.5 points). Randomization: 48 reps, 199 permutations (SE about 3 to 7 points, coarse). **Unmeasured:** slope SD 6, sparse slopes, randomization under the full null, the base rates predicted in item 2, 8/4 effect sizes. Scripts: a local scratch directory (not kept) (`sim.py`, `short.py`, `summ.py`).

Pilot data was used for checker behavior and rule presence only. I did not read any pilot wording contrast, and no advice below rests on one. Side effect: I ran `analysis/pool_table.py`, which rewrites `docs/POOL.md`. The code and inputs are deterministic and its printed result matches, but the file is untracked, so I could not diff it byte for byte.

## Must fix before freeze

**1. The decision table reads a filler artifact as a reason effect, and absence of evidence as a content effect.**
- Wrong: rows 1 and 2 rest only on contrasts against one filler sentence, and "None versus filler measures that length effect" assumes that sentence is inert. It calls the rule "one of several notes", which could demote it. Row 2 never tests real against placebo. It concludes from two failures to reject.
- Measured, probability of each reading:

| True effect, points | "Form" (row 1) | "Content" (row 2) | Null (row 3) | Inconclusive |
|---|---|---|---|---|
| All zero | 0.2% | 2.0% | 94.7% | 3.2% |
| Filler 3 below all others, no reason effect | **30.0%** | **12.0%** | 15.0% | 43.0% |
| Real 5, placebo 5 | 51.0% | 8.5% | 2.0% | 38.5% |
| Real 5, placebo 3 (keeps 60%) | 6.0% | **34.5%** | 5.0% | 54.5% |
| Real 5, placebo 2 | 0.5% | 61.5% | 6.0% | 32.0% |
| Real 5, placebo 0 | 0.0% | 78.0% | 6.5% | 15.5% |
| Real 3, placebo 3 | 9.5% | 13.0% | 17.5% | 60.0% |

- Fix: add two registered conditions, no new runs. Row 1 also needs real > none and placebo > none. Row 2 also needs real > placebo, two-sided at .05. Measured with them: row 1 falls from 30.0% to 0.5% under the filler artifact and only from 51.0% to 46.0% when real. Row 2 falls from 34.5% to 14.5% at 60% retention and from 78.0% to 72.0% when real. Drop "whatever it says" from row 1 unless the TOST passes. Add the reading to code so nobody applies the table by hand.

**2. `short_final` contaminates three other rules, so the pool rule does not transport to the fielded file.**
- Wrong: the pool gates were measured with `short_final` co-shown about 40% of the time (K=12 of 28). At 12 of 15 it is co-shown 11/14 of the time. A short message passes digit, first person and contraction checks mechanically, so those rules lose their room to move.
- Measured, K=12 pilots, presence only, pooled over wording, with `short_final` shown versus not: `final_no_digits` 19/20 vs 3/23; `final_no_first_person` 20/20 vs 8/24; `final_no_contractions` 12/12 vs 12/14. Rule unshown: 9/23 vs 0/32, 3/24 vs 0/32, 12/14 vs 1/20. Arithmetic prediction at 12 of 15: digits 0.77 shown, 0.34 no rule (POOL.md 0.51, 0.16); first person 0.86, 0.11 (0.64, 0.05); contractions 0.97, 0.74 (0.92, 0.38), which **fails both pool gates**. Cell counts are small.
- Fix: drop `short_final`, take K=12 of 14 or K=11 of 14, and regenerate both manifests. Then run about 60 pilot runs on the final mix and reapply the pool rule to pooled compliance only, before the freeze. `final_no_digits` at 3/23 may then be near the 0.10 floor, so let the gate decide.

**3. Filler and placebo are one string each, repeated verbatim, while real reasons are unique.**
- Wrong: an oddity of one sentence shifts every rule's H1 and H2 together, and the across-rule t interval cannot see it, because clause wording is not sampled (the language-as-fixed-effect problem; Clark 1973, from memory, verify). Repetition is also confounded with content: a boilerplate placebo may be discounted as boilerplate, which is not an effect of having no content.
- Measured in `data/study1/manifest.jsonl`: 72.3% of files hold the placebo at least twice, 44.2% at least three times; filler and norm match (72.1%, 72.6%). H1 and H2 estimates correlate 0.33 to 0.47 through the shared filler.
- Fix: write 4 paraphrases each for filler, placebo and norm, none repeated within a file, and record the variant in the manifest. Rerun `analysis/clause_check.py`. Add a second rater question on how strongly the clause asserts obligation, because "what needs to be done" presses without informing and the current scale cannot see that (all 8 raters gave 1).

**4. The `no_chain` checker does not measure its rule.**
- Wrong: the rule says "Do not join shell commands with `&&`; run each one as its own call". The checker tests only for `&&`, so `;` passes.
- Measured, p3, rule shown: 20 of 25 pass, and 0 of those 20 ran single commands; every one joined with `;`, outside quotes and heredocs. Strict scoring gives 0/25, under the pool floor. `;` use is near universal either way (34/35 unshown, 25/25 shown).
- Fix: make the rule literal ("Do not use `&&` in any shell command"), and rewrite its example and real clause, which promise separate calls ("misses anything joined"). The alternative is to score `;` and let the floor drop the rule.

**5. A run that hits 40 turns is rerun as if it were an infrastructure error.**
- Wrong: the prereg excludes nothing but API and infrastructure errors. The 2.1.303 bundle emits `is_error:!0` with `subtype:"error_max_turns"`, `harness/agent_run.py:258` maps that to `error`, and `harness/batch.py:100-104` requeues the row until it finishes. That is selection on a post-treatment outcome, and it could differ by arm.
- Measured: 0 of 215 pilot runs hit the limit (maximum 25 turns), so current impact is small, but the final pool is harder. Also, `counters["lost"] > 25` stops the batch, which is an unregistered stopping rule.
- Fix: read `subtype`; give `error_max_turns` status `max_turns`, keep it in like a timeout, and report it by arm. Register the lost-run stop or remove it.

**6. Every request shows the study's hypothesis word and a study run id.**
- Wrong: the model sees `/private/tmp/because-runs/p3-00000/hourglass/CLAUDE.md`, in both the file header and the working directory line. Confirmatory runs will show `study1-NNNNN`. It is constant across arms, but it can prime "because" and signal a test, which could interact with REASON.
- Measured: 2 occurrences in a captured p3 first request; the path also appears in assistant text in 7 of 160 runs. No visible text mentions an experiment, but thinking blocks are empty in the raw logs, so demand cannot be audited there.
- Fix: set `RUN_ROOT` to a neutral path, name run directories by a hash of `run_id`, and update the strip at `agent_run.py:191`.

**7. The prereg commits to things the repo does not contain or the code does not do.**
- Missing: `Makefile` (`make reproduce`), `docs/ISOLATION.md`, `docs/DEVIATIONS.md`, `PREREG-STUDY2.md`, the lme4 model (no R code, not in requirements), a blind audit sampler, counts by arm. The freeze tag has nothing to point at: the repo has no commits.
- Quota: "15 points" is not implemented. `batch.py` stops only below 25% remaining; acct2 read 95%, which allows about 70 points.
- Version: "Fixed: Claude Code 2.1.303" is logged, not enforced. Abort on any mismatch in CLI or model.
- False statements: short files are 542 words on average (472 to 631), not "about 400"; long files are 3,548, not "about 3,300". "The clauses contain none of their rule's tokens" fails for 4 of 15: `reverse_imports` (order), `no_chain` (call, joined), `file_header` (file, line), `no_trailing_comma` (item). "Shows a different instance than the task needs" fails for `no_chain`, `write_tool`, `short_final` and `diff_before_commit`, whose examples are the task's own step.
- Positive control: no pass criterion, so it cannot show anything. Register a threshold and the consequence of missing it.
- Power: 1,200 runs were never simulated and the figures ignore Holm. Measured at 1,200 with slope SD 3: H1 rejects 88% raw, 81% to 88% after Holm. Ceilings also shrink a nominal 5-point slope to 4.05 realized points, so the text should say that.
- Fix: build or delete each, and correct each sentence. Rerun the power figures after item 2.

## Disclose

Ranked. None of these invalidates the primary contrasts.

1. **PRESSURE is an instruction, not only pressure.** "Keep it minimal and skip anything not strictly needed" can shorten code and final messages with no rule shown, so "urgent vs none" mixes behavior change with compliance. "Langer's small-favor, big-favor test" overclaims: favor size maps to rule cost, not user urgency. Fix: add shown minus unshown for both run-level factors as a registered sensitivity, and soften the sentence. Not measured, to stay blind to pilot contrasts.
2. **LENGTH carries more than length.** Long files place target rules under headings like "Glossary" and "Incident history", while short files use "Conventions". Target density is 60% vs 11%. "Because" marks targets in about 89% of its bullets in short files and 40% in long ones (fillers carry it at 10.8%, though `has_reason` is 25.8% as registered). Cheap fix: a "Conventions" subheading before each bullet block.
3. **Run-level SE is conservative by double counting.** Measured under the null: empirical SD 0.76 points, reported SE 0.99 (by rule 0.61, by run 0.77), rejection 0.5% to 0.7% at nominal 5%. Long and urgent lose power. Fix: use by-run variance plus excess across-rule variance over its binomial part, floored at 0. Behavior under real slope variance is unmeasured.
4. **Rules interact, despite "never conflict" in `rules.py`.** `func_lines` passes 4/14 with `line_60` shown vs 6/12 without, and 6/15 with `name_length` vs 15/28 without; `no_trailing_comma` passes 8/9 vs 17/17 with `line_60`. Small cells, but the mechanism is plain: wrapping and long names add lines. Their reasons and wording spill across rules. Independent labels keep the own-rule contrast unbiased, but the no-rule baseline is not a clean "no instruction" state.
5. **Final messages report on other rules.** 27 of 160 mention `CLAUDE.md`, 32 project notes. Quoting "40 lines or fewer" fails the digit check through a different rule's text. This adds noise rather than bias, since wording is independent across rules.
6. **"Real" reasons are invented and uncheckable.** No voice assistant or ticket importer exists in the repos, so the arm tests a specific plausible rationale, not a true one. Say so.
7. **Pool selection limits.** Rules at 0.91 to 0.93 leave at most 9 points of room, and n of 25 to 63 gives wide bounds (0.93 at n 44 reaches about 0.98), so expect regression to the mean. Pilots mixed K=8 and K=12. Manual steps exist (`SUPERSEDED`, `SEPARATE`, `one_blank` reworded after pilot 2); name them in the prereg.
8. **Checker-versus-rule scope.** The example for `name_length` reveals `except ... as error`, which the bare rule does not name, so EXAMPLE adds specification as well as form. Pilots show no failure caused by `except` alone. EXAMPLE also has no length-matched control, which Review 1 item 14 asked for.
9. **The blind audit cannot do its stated job.** 100 observations give about 20 per reason arm, which cannot show a 5-point difference in error by arm. Run it before any contrast is computed, so a checker fix cannot follow a look at the results. Name the reader; "no model judges any outcome" leaves that open.
10. **Randomization test scope.** It permutes all five reason labels, so it tests a sharp null across the whole factor, not real versus filler. Measured at 48 reps with other levels large and real equal to filler: 4.2% rejection as coded, 0.0% restricted to the pair; with real +5: 91.7% as coded, 95.8% restricted, 95.8% by-rule t. No damage seen at this coarse resolution. One-line fix: permute within the rows holding the two labels.
11. **Review 1 follow-ups.** Item 8's "comply AND task complete" for prohibitions is not implemented; low stakes, since all 215 pilot runs committed and passed tests. Item 16's census reweighting is absent, and 60% of targets carry "because" against a 26% census rate, so spillover may dilute one clause. 2604.11088, read as a generated report, finds random rules matching curated ones and a polarity pattern; keep polarity exploratory. One new search found no direct scoop; repeat just before posting.
12. **Small code note.** `analysis.study1 data/p3` crashes with `KeyError: 'unshown'`, because p3 predates that field. On a copy with the field derived it ran end to end. `data/study1/manifest.jsonl` has the field. The Haiku replication uses a pool selected on Sonnet.

## Tried to break it and could not

- **Estimator recovery.** Nominal +5 slopes averaged 4.97; the realized effect after ceilings was 4.05 and the estimate 4.22. Placebo at nominal 3: realized 2.41, estimate 2.59. Null estimates: -0.02 and +0.03.
- **By-rule interval.** Null coverage 94.7% and 95.8% (600 reps), 94.2% and 94.5% with no side effects. Rejection 5.3% (H1), 4.2% (H2); Holm familywise 4.5%. Empirical SD 1.05, mean SE 1.01. Under real effects, coverage of the realized effect was 97.5% to 98%, conservative.
- **TOST and retention arithmetic.** Formulas correct. TOST at +/-5 passes 99.2% under the null and 94.0% with real = placebo = 5. It also passes 20.0% at real 5, placebo 0, because ceilings shrink that gap to 4 points. Treat it as a sensitivity only.
- **Assignment.** Regenerating from the seed reproduces the manifest exactly, with K=12, POOL_FINAL and every rule shown 960 times. Reason cells 168 to 214. Pair co-showing SD 5.2 against 16.7 under binomial. Unshown rule by task, length and pressure: p = 0.61, 0.95, 0.99. Reason by length and pressure: p = 0.23, 0.53. Consecutive runs share fewer unshown rules than independence (0.12 vs 0.60), harmless unless drift is sharp.
- **Position.** Top share by reason arm is 34.6% to 36.4% in short files and 32.5% to 33.6% in long ones, so a clause's length barely moves its position.
- **Treatment fidelity.** Today's `render_file` and `render_prompt` appear verbatim in all 4 captures tested, under 2.1.303, with a single system hash per run in 215 of 215.
- **Clause or example text reaching a checker.** Example text verbatim in the final message: 0 of 868. Three or more real-clause words: 3 of 321. Filler, placebo and norm strings in final messages, code or commits: 0. "Because" in added Python: 0.
- **Regex false positives.** `&&` only inside quotes or heredocs: 0 of 329. `diff_before_commit` with heredocs stripped: 0 disagreements of 160. `git -C` or `--no-pager` forms: 0. Curly apostrophes: 0. Non-pronoun "I": 0. Contraction hits only inside code spans: 0. `reverse_imports` trivial passes: 0 of 37. `file_header` failures from empty files among shown fails: 0 of 9. Only `final_no_digits` has code-span hits (17 of 125), which the rule covers.
- **Final message source.** `result` equals the last assistant text in 160 of 160.
- **Capture race.** Captured requests equal distinct assistant messages in 60 of 60.
- **Leak scan as a post-treatment filter.** Flags occur only in pre-fix batches (pilot1, p2haiku); none of the needles appear in the stimuli.
- **Opportunity.** No pilot run lacked a commit or a new Python file, so intention to treat rarely bites.
- **Selection on arms.** `analysis/pool_table.py` pools over arms and uses no contrast. Filler rules have `has_reason` at 25.8% and concern other stacks, with no keyword overlap that would move a pool checker. Family 2 has the nine registered contrasts; `holm` is correct.
