# Review 3: final hostile review before publishing (2026-11-02)

Verdict: the data, the registered readings and the arithmetic hold, and the prose outruns them in the first screen of the README. Do not publish until the nine must-fix items below are closed. None of them needs an agent run beyond the Haiku batch already in progress. Seven are wording, citation or reporting changes on data already in the repo, one is code, and one is the publishing checklist.

A senior reader would respect the design and the audit trail. That reader would then find a false section heading, a +27-point effect that the page never mentions, and a "discovery" the vendor documents. Those three are what to fix first.

Method. I read the README, the write-up, the site metadata, the paper, the three registrations, the deviations log, the audit files and the earlier reviews. I recomputed Studies 1 and 2b with my own code, importing nothing from `analysis/`. I ran the make targets, using an isolated copy for anything that writes to `results/`. I started no agent runs and did not touch `data/study1haiku`, so `make isolation` and the Haiku data are unreviewed.

Labels. "Measured" means computed from the committed data or read from a file. "Simulated" means my own implementation of the listing rule, run on draws from the fixture library. "Inferred" means reasoned from those. "Post hoc" marks a look nobody registered, and a post hoc p-value is uncorrected unless the row says otherwise. My scripts are not in the repo, so each finding says what they did.

## Must-fix, most embarrassing first

### M1. The listing budget reads as a discovery, and the vendor documents it

Write-up line 33 says "This part I didn't go in looking for" and that "the listing turned out to follow an exact rule." The README and the paper never mention that the vendor describes the behavior. The [Claude Code skills page](https://code.claude.com/docs/en/skills) says:

> The listing always contains every skill name, but if you have many skills, Claude Code drops some descriptions to fit the listing's character budget, which removes the keywords Claude needs to match your request. The budget scales at 1% of the model's context window. When the listing overflows, Claude Code drops descriptions starting with the skills you invoke least, so the skills you use most keep their full text.

The same page names `skillListingBudgetFraction`, `SLASH_COMMAND_TOOL_CHAR_BUDGET`, and `"name-only"` in `skillOverrides`. A reader who knows that page will conclude the author did not look. What this repo adds is real: the exact walk, the skip that lets a shorter description further down still fit, the tie order, and the size of the consequence. It has to be presented that way.

The advice under test has the same gap. Write-up line 19 says explaining why "traces to" Langer. The vendor's [prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) says "Providing context or motivation behind your instructions, such as explaining to Claude why such behavior is important, can give Claude more information about your goals and help it deliver more targeted responses." Its example is a text-to-speech engine and ellipses, and it ends "Claude can generalize from the explanation." The real reason on `final_no_digits` is "because the voice assistant reading these reports aloud stumbles over numerals and identifiers", which is nearly that example. It reads +2.9 (se 4.0) here. The vendor's claim is about generalizing past the literal rule. This design scores literal compliance only, so it does not test that claim, and no surface says so.

What I did: ran `git grep` for `code.claude.com`, `docs/en/skills`, `skillListingBudgetFraction`, `platform.claude.com` and `motivation behind` across README, paper, site, docs and results, which returned nothing. I opened both pages and read the quotes from them. Both are current pages, not pinned to 2.1.303. `docs/LISTING-MECHANISM.md` line 73 reads the same 1% from the binary, so the behavior existed at that version (inferred).

Fix: cite both pages on every surface, reword write-up line 33 as measuring the exact rule behind a documented limit, and add a limit that generalization was not tested.

### M2. "Past the listing budget, a long description never reaches the model" is false on the repo's own numbers

This is the README lead (line 5) and a section heading (line 35). Write-up line 5 says the CLI "drops long skill descriptions before the model reads them", and `site/meta.json` repeats it in the gist and the blurb.

`results/NUMBERS.md` line 82 shows that at 300 skills, `300/aa/trigger`, `300/aa/trigger_not` and `300/aa/directive` all reached the model in 1.0 of runs. Those libraries are past the budget. The +51.3 in the same section depends on exactly that. `docs/LISTING-MECHANISM.md` line 20 adds that past use also saves a long description. The true statement is narrower: a long description on a never-used skill that sorts after the budget is spent. That is 0 of 128 in Study 2b (measured). In my simulation at 300, about 28% of skills keep a description and the first skip falls at median position 82 of 300 names, around the letter c.

"Fixed" (README line 5, the gist) is also wrong beyond one model family. Line 73 of the mechanism doc gives the budget as `context_window * chars_per_token * 0.01`, and line 66 onward measures 30,000 on two models and below 10,240 on `claude-sonnet-4-6`.

What I did: read the cells, then replayed the rule with my own implementation against every Study 2 and Study 2b run (see Held up).

Fix: reword the lead, the heading, the write-up and the metadata to name the skill that loses the walk, and replace "fixed" with the model-dependent formula.

### M3. Rule-level wording effects are large, and almost none are reported

The hero alt text says "All estimates sit within 4.3 points of zero" (README line 7, `site/meta.json`). The axis runs to plus or minus 30 only because `analysis/figures.py` line 31 sizes it to the largest per-rule tick, which is a worked example at +26.9. A reader sees that tick at once and finds no sentence about it.

| Rule and factor | Estimate, points | Cluster-robust se | p | Holm across 72 cells |
|---|---|---|---|---|
| Worked example on `final_no_first_person` (raw .196, n 387, to .446, n 399) | +26.9 | 3.4 | 5e-15 | under .001 |
| `IMPORTANT:` on `reverse_imports` | +9.8 | 2.8 | .0004 | .032 |
| Real reason on `final_no_first_person` | +15.8 | 5.6 | .0045 | .312 |
| Capitals on `final_no_contractions` | +7.2 | 2.7 | .007 | .481 |
| No clause on `func_lines` | -14.6 | 5.7 | .011 | .744 |

Other ticks in the figure: user in a hurry reaches -24.5 on `one_blank` (raw .539 to .294), and top against bottom reaches +15.6 on `final_no_first_person`. Two effects survive correction across all 72 rule-by-level cells, while the README lead says wording matters far less than the rule. These are post hoc, and the README limit that an example "adds specification as well as form" is a fair caveat. But the effect itself is never stated, and Review 1 item 14 warned that examples could dominate.

What I did: fit rule-by-factor regressions with run-clustered errors, checked that the rule-level estimates equal the repo's `per_rule` ticks, and applied Holm across the 72 cells. Then I grepped README, paper, write-up and `results/NUMBERS.md` for these values. Only the +15.8 appears as a reported effect, at paper line 152. The +26.9 and the -24.5 appear nowhere.

Fix: report a rule-by-factor table as exploratory on the README and in the paper, and change the alt text to say that means sit within 4.3 points while single rules reach +26.9 and -24.5.

### M4. "There is no effect above about 6 points" is stated flat

README line 25 and write-up line 23 say this with no qualifier. The paper is better. Its abstract and line 152 say "for a real reason on rules like these", and line 152 reports the +15.8 and says "nine rules cannot say whether that spread is signal." It still says "exclude" and omits both "average" and the comparator.

The 5.7 is the upper bound of an equal-weight average across nine selected rules, against filler. Measured against the alternatives:

- Against no clause, the upper bound is 6.8. Leaving one rule out moves it between 1.9 and 7.0.
- On `final_no_first_person`, real against filler is +15.8 (se 5.6, p .0045, Holm across nine .040, Holm across 72 .312). The raw rates are .287 and .388.
- Heterogeneity is not excluded. Cochran Q is 14.91 on 8 df, p .061, with a DerSimonian-Laird tau of 4.41 points.
- The random-effects mean is +0.15, Hartung-Knapp [-5.04, +5.35]. The prediction interval for a new rule is [-11.6, +11.9].

This does not show that a real reason works. The +15.8 is post hoc and could be noise. It shows that the sentence claims more than the interval does. The `inconclusive` reading itself is correct and fairly reported.

What I did: recomputed the nine estimates with my own fixed-effect regression, then ran the leave-one-out, heterogeneity, random-effects and prediction calculations on them.

Fix: "Averaged across these nine rules, the 95% interval against filler stops at +5.7. Single rules are less certain, and one reads +15.8."

### M5. The lead rests on a spread that selection set by construction

"Which rule you write ... matters far more than how you word it" leads the README (line 5), heads the first findings section (line 15), and drives the first piece of advice (line 55). It is labelled exploratory, and it still sits above the registered results.

| Pilot pool, parsed from `docs/POOL.md` | Mean shown | SD | Shown minus no rule |
|---|---|---|---|
| All 59 candidates | .92 | .15 | +69.4 |
| The 50 dropped | .98 | .05 | +72.2 |
| The 9 kept, in pilots | .64 | .22 | +54.3 |
| The 9 kept, in the fielded study | .58 | .29 | +54.2 |

71% of candidates sat at or above .95 and 34 sat at exactly 1.00. The pool rule kept rules between .10 and .95, and the final SD of .294 is above that of a uniform on the band (.245). So the range 0.09 to 0.93 is by construction. The paper says so at line 230, and the README lead does not. Its limits bullet mentions selection only for the preregistered tests.

I tried to break the claim with this and could not break its sign. The unselected SD of .15 is still far above mean wording effects of at most 4.3 points. In the fielded data, rule identity explains R2 .314 of compliance and wording main effects explain .0069. Selection lowers +54.2, it does not inflate it. The attack that holds is on what the comparison means:

- It compares a spread across selected behaviors with a mean contrast inside a rule. Those are different estimands, and M3 shows the within-rule effects are not small.
- Rule identity is not randomized, and it is confounded with checker strictness. One digit anywhere fails `final_no_digits`.
- It is not an "edit" (README line 3). A writer wants a specific behavior and cannot swap digits for Write-tool use to gain 84 points.
- "Whether you write it at all" is close to self-evident.

Fix: lead with the registered results and the listing finding. Keep this as a labelled secondary finding that says the band was chosen and that a writer's rule choice is not a lever.

### M6. Two documented reproduction commands do not work

`make rerun` does nothing on a clean clone. `harness/batch.py` line 79 drops every row whose trace exists, and all 1,000 Study 1 traces are tracked. Applying that filter to the tracked files gives "1000 in manifest, 0 to run". I applied the filter in my own script and did not start the batch, since this review starts no agent runs. README line 3 promises "the harness to rerun every number", line 75 says the target "repeats the runs themselves", and paper line 285 says the same. It also covers Study 1 only, passes no `--expect-cli` although the repo's own finding is that this behavior changes by version, and writes into the committed data folder.

`python -m analysis.listing_mechanism replay`, the "no model calls" command at `docs/LISTING-MECHANISM.md` line 122 and paper line 285, crashes on a clean checkout with `FileNotFoundError: data/s2pilot/captures/s2pilot-00000.json.gz`. Those captures are not tracked and are not in the working tree. `results/listing_rule.json`, which the same function reads at line 217, is not tracked either. So a reader cannot replay the 2,590 pilot entries at all, and the other 2,325 of the 4,915 need live agent runs. The headline "predicts all 4,915" cannot be rechecked offline.

The rule itself holds up, and there is a public route. My own implementation predicted `probe_hit` in 535 of 535 Study 2b runs and 596 of 600 Study 2 runs from committed data.

Fix: give `make rerun` a fresh output folder, a version check and all three manifests. Commit the replay inputs or replace the replay with one over `probe_hit` in Studies 2 and 2b.

### M7. "Real and placebo are equivalent within 5 points" is flat in the README and the write-up

TOST gives p .0398, and it stops passing at a margin of 4.5 (p .058). The 90% interval is [-4.70, +2.87], the 95% interval [-5.6, +3.8] crosses -5, and per-rule gaps run from -8.4 to +12.9. The author's own pre-freeze simulation passed this test 20.0% of the time with a real effect of 5 and a placebo of 0, because ceilings shrink the gap (`docs/REVIEW-2-prereg.md` line 84, which says "Treat it as a sensitivity only"). The paper discloses that at line 152. README line 25 and write-up line 23 do not, and they present it as one of two claims "the data supports".

What I did: recomputed TOST at five margins and confirmed by grep that neither surface mentions the 20.0%.

Fix: copy the paper's sentence, or drop the claim from the README.

### M8. "No measurable cost" contradicts the README's own ceiling sentence

README line 49 says the short trigger "has no measurable cost" at 50 skills, and write-up line 45 says "it costs nothing I can measure". README line 33 rejects the same kind of inference for `ALWAYS` and `Not for`: "A ceiling and a floor cannot show an effect, so this is no evidence of no effect." At 50 skills every arm is near the ceiling (.953, 1.000, .978).

The interval [-2.5, +6.7] comes from one run. Eleven of 12 targets tie at zero, and `license-scan` is +25 from a single miss (`study2b-10434`, trigger, generic). The half-width is exactly t times 25/12. A run-level Newcombe interval on 44/44 and 45/46 is [-6.1, +11.3], and the Clopper-Pearson worst case is -8.0.

The registered reading, under 10 points, is fair and calibrated. My simulation passes it .022 to .039 of the time at a true 10-point cost, across base rates, against a nominal .025. Near the ceiling it also passes .30 at a true cost of 5 and .58 at a true cost of 3, so the data cannot see costs that size. The paper's abstract already says "costing under 10 points".

Fix: use the registered wording on the README, the write-up and the metadata, and add that these prompts sit near the ceiling.

### M9. Stubs and internal files would ship

- `HAIKU_REPLICATION` is at README line 145 and `HAIKUREPLICATION` at paper lines 254 to 255, and the stub is in the tracked `paper/because.pdf`. These are expected while the batch runs, and they block publishing.
- `paper/SUBMIT.md` is tracked and would go public. It says "An agent drafted it", "Nothing here has been uploaded, pushed, committed", and that `paper/counts.json` is untracked. `git ls-files paper` shows all of `paper/` tracked, and `origin/main` is at HEAD, so those statements are stale.
- The explorer link at README line 11 is not live. `gh api repos/.../pages` returns 404 and the repo is private. It needs Pages turned on at the same moment the repo goes public.

## Should-fix, ranked

| # | Finding | What I did to establish it |
|---|---|---|
| S1 | "The long trigger list that wins below the budget" (README 39, write-up 37) overstates. C1 pools in the 300/aa stratum, which is past the budget and holds 7 of minimal's 12 misses. Below the budget the evidence is +12.4 [+1.5, +23.2] in Study 2, and +3.5 [-10.0, +16.9] in Study 2b at 50, where short trigger sits above long. "The gain sits where the prompt does not use the skill's own words" (+46.7) does not repeat in 2b at 50: generic minimal 14/14, trigger 13/14. No surface compares them. C1 itself holds at run level (see Held up), and at library 0 it is +0.0. | Recomputed strata: 0/aa 10/10 vs 6/6, 0/zz 13/13 vs 10/10, 50/aa 10/10 vs 10/14, 50/zz 14/14 vs 11/12, 300/aa 18/18 vs 19/26. The two restricted contrasts are post hoc. |
| S2 | "Keep skill descriptions short" (README 56, write-up 53) is unconditional and hides how short. Where a long list fits, it wins: at 300/aa, 18/18 against 19/26. For a late never-used skill, "short" means about 25 characters. The short trigger "fits the budget" only .338 of the time, below minimal's .526. The 140-character "long" list is shorter than the library's median of 217. The magnitudes also depend on the library. | Measured: leftover at the target's turn from replaying 2b manifests has median 24, p90 63, max 92. Distractors run from 81 to 675 characters. Simulated at 300: baseline minimal .544, short trigger .408. With 5% of distractors at 30 characters, these fall to .26 and .03. 60-character distractors change little. |
| S3 | Nothing manipulates the budget directly. The obvious decisive arm is 300 skills with the budget raised by the documented env var until all fit. "Past the budget" is also confounded with "300 skills": runs with the description kept load .750 and .848, against .953 and 1.000 at 50. | Read the three registrations and cells. Simulated: a budget of 60,000 is still not enough for the trigger list at 300, so the arm needs a larger value. |
| S4 | +51.3 is an average over very different gaps, and the README's limit bullet covers only the prefix. Raw aa minus zz: minimal +12.2, padded +32.1, trigger +76.5, trigger_not +76.2, directive +64.0. | Recomputed from Study 2 traces, which matches the `NUMBERS.md` grid. |
| S5 | "The reversal does not depend on the kind of prompt" (paper 206) and "alike" (README 39) have no interaction test. Within-prompt D1 intervals run from about 26 to 48 points wide. "D3 shows no difference" (paper 206) has an interval of about plus or minus 9. | Read `results/study2b.json`. Direction is stable in all three prompt types. The claim is the word "alike". |
| S6 | The mixed model's fit is singular and the paper does not say so. Run SD is 0 and placebo slope SD is 0. The "prediction interval for a new rule" of [-5.7, +5.1] (paper 250) rests on a slope SD of 2.18 from that fit and on 1.96 rather than a t quantile for nine rules. My random-effects interval, [-11.6, +11.9], is about twice as wide. | Reran `analysis/robust.R` on a copy, output byte-identical, with R printing `boundary (singular) fit`. Read `results/robust.txt` and line 22 of the script, `half <- 1.96 * sqrt(se^2 + sd_slope^2)`. |
| S7 | "The largest effect I found comes from a limit in the CLI" (write-up 5) conflicts with +54.2 on the same page, and +51.3 is an extreme forced by artificial prefixes. | Read across the page. |
| S8 | "Position and length replicate McMillan" and "registered replications" (paper 61, 154). McMillan's bound of about 6 points is on position and architecture, on one trivial rule with Sonnet 4.6. Here top against bottom is [-1.3, +9.0]. The README correctly says "repeat". | Read McMillan's full text and compared. |
| S9 | The Liu sentence splices two baselines (paper 55). 73.6 to 27.4 is the full task set. 63.3 comes from a masking table on a 10-task subset, one run per task and model, whose baseline is 18.3. "Restores it" implies 27.4 to 63.3. | Read the abstract and the masking table in the full text. |
| S10 | The write-up's explanation that "rewriting how the agent reports its results isn't" easy (line 51) is contradicted by its own table. `final_no_contractions` also changes how the agent reports, and it moves from .28 with no rule to .87. | Read `paper/because.tex` line 238 and the write-up. |
| S11 | Audit readers saw the checker's verdict, so "agreed on 92 of 100" is an anchored number. The registration allows this (`PREREG.md` line 175), and the README and write-up never say it. The registration names one reader, three were used, and `docs/DEVIATIONS.md` does not list that. "With no qualification" includes item 5, which Reader 1 flagged. | `docs/audit/sample.json` holds a `checker_verdict` on all 100 items. Recounted the part reports: 33 + 30 + 29 = 92, 3 + 4 = 7 unclear, 1 disagrees. |
| S12 | "`make reproduce` regenerates every number" (README 69, paper 285) is not literally true. It does not touch `robust.txt`, `calibration.json`, `power.*`, `isolation.json`, `listing_*.json` or `clause_check.json`. | Read the Makefile. I ran calibration and the mixed model by hand on a copy, and both are byte-identical, so this is about wording or adding a target. |
| S13 | The README and write-up omit two limits the paper states at line 281: only project skills and built-ins were tested, and no target had usage history, "so nothing here describes a skill already in use." Both change what a reader should do. | Read all three surfaces. |
| S14 | The README's reversal figure has no intervals and no axis values, for the most consequential contrast in the repo. The Study 2 panel in the paper figure pools 300/aa into "description in view". | Counted the SVG elements (8 text, 5 lines, 6 circles), viewed the rendered figure, read `analysis/figures.py` lines 100 to 104. |
| S15 | 0.72 against 0.18 (README 51, write-up 47) is labelled exploratory. The README omits what `PREREG-STUDY2B.md` says, that fit is not randomized, and the comparison mixes wordings and targets. | Read the registration and `results/exploratory.json`. |
| S16 | The integrity log has small flaws. A `docs/DEVIATIONS.md` entry is stamped 00:55 inside a commit dated 00:53:05. `RUN_ROOT` and `TMPDIR` changes are missing from the harness edits (no effect at their default values on a Mac). `PREREG.md` line 103 says "Reruns are logged" while `data/*/batch.log` is gitignored. | `git log`, `git diff prereg-study1 HEAD`, and the logs themselves: 1,000, 600 and 535 lines, none of them other than `ok`, so there were no reruns. Tracking the logs would show the first run 38 s after the tag. GitHub reports the repo created at 03:52:50 UTC, one second after the Study 1 freeze commit date, which is the one third-party time point available and could be cited at README 125. |
| S17 | Prior work is missing relevant items, and paper line 61 cites a 2 November search with no log. | See Novelty. This review's log can serve as that record. |
| S18 | The exploratory list in `PREREG.md` (cost class, polarity, depth, rule by task, paraphrase, two-way interactions, spillover) is not reported or marked as not run. The registration does not require them. A one-line "not run" closes the question. | Grepped every surface for those terms. The only hit is an unrelated paper line. |

## Taste

| Item | What I did |
|---|---|
| `results/NUMBERS.md` still prints the name `C5_..._described_gone`, prints `nan` cells, and prints raw dictionaries with 16 digits, on a page meant for readers. | Read it. |
| `+0.0 [+0.0, +0.0]` with p 1.000 reads as precision. It is a by-target tie at a ceiling. The README explains this and `NUMBERS.md` does not. | Read `analysis/study1.py` `by_rule`. A zero SE gives p 0 for a nonzero tie, and no reported contrast hits that case. |
| `harness/replay.py` lines 58 to 67 skip lists, so `make replay`'s "152 of 152 estimates" does not compare CI or per-rule arrays. | Read the code. |
| The positive control is a 61-point contrast, which says nothing about sensitivity at 5 points. The +26.9 is a better demonstration. | Read README line 100. |
| README line 137 and write-up say they "could not verify" Inferal's sample. The post states it: 9 to 10 runs per strategy, one project, Sonnet. Say that. | Opened the post. |
| The forest plot's caption says "compliance or loading" on a figure with no loading rows. | Viewed it. |
| `docs/LISTING-MECHANISM.md` "What this means for Study 2" predates the freeze. It says `PREREG-STUDY2.md` states the rule as alphabetical, and only `study2/design.py` line 3 still does. | `git grep`. |

## Held up under attack

- The Study 1 reading of `inconclusive` is correct under the registered table.
- Exact sign-flip p .938, Wilcoxon .91, rule bootstrap [-3.7, +4.9] and randomization .917 all agree there is no average effect, so the t interval across rules is not anti-conservative.
- Holm arithmetic and families are correct by hand. TOST arithmetic is correct.
- "Significant" appears on the public surfaces only in "no significance claim".
- C1 is robust at run level: 65/65 against 56/68, Fisher p .0003.
- All interval triples on the README (14), write-up (9), metadata (7) and paper (40) match `results/NUMBERS.md`. The 4,915 sums from its table (2,590 + 1,378 + 947).
- The listing rule, written from the prose alone, predicted `probe_hit` in 535 of 535 Study 2b runs and 596 of 600 Study 2 runs. The 4 misses are all 300/zz/minimal, and my starting usage was empty, which is the inferred cause.
- `probe_hit` is not tripped by a load: trigger reach is 0 of 128 with 27 loads.
- The `zz-` prefix does not drive the reversal. Simulated with real unprefixed names at 300, trigger reach is at most .02 and minimal runs .44 to .69.
- The reversal does not depend on one library size. Simulated reach for minimal, short and trigger: 100 skills .89/.83/.395, 150 .605/.458/0, 300 .583/.448/0, 350 .482/.343/0.
- Carry-over is minor. Only `month-end-close` (9) and `changelog-generator` (2) were invoked in 2b, both pre-listed in the registration. There is no load trend by run quartile. Leftover characters balance across arms (Kruskal p .337).
- The missing 41 are the last manifest rows, not outcome-linked. Trigger at 300 lost 15 against 7 and 8, chi-square p .13.
- Bare-name load rates across all 8 wording cells of both studies are homogeneous (p .641), so the name-only baseline is a fair placebo.
- Preregistration blobs at the tags match HEAD. Tag and commit order is consistent, and the post-freeze diffs in `analysis/` and `study1/` match the log. `fixtures/skills.json` is JSON-equal between the 2b tag and HEAD.
- The audit is blind to arm. None of the 77 real, placebo, norm and filler strings appears verbatim in any of the 100 items. The prose holds 34 uses of "because", and the 14 I read are the agent's own. The early checker fix is disclosed.
- History rewrite and the lack of a timestamping service are disclosed on README 125, write-up 71 and paper 263.
- `harness.public_scan --history` finds only the author's public name, scanner code, and one random message id that happens to match a local needle. Rerun it once the Haiku data lands.
- Selection does not inflate +54.2 (see M5).

## The brief's questions, answered

**Study 1.** "Inconclusive" holds. "No effect above about 6 points" is too strong as written (M4). "Equivalent within 5 points" passes a registered sensitivity by a hair and needs the paper's caveat (M7).

**"Which rule it is" as the lead.** The sign survives selection. The size does not mean what the lead implies, and it should not lead (M5).

**Is the 2b reversal attributable to the budget?** The contrast is a clean randomized effect of wording at 300 skills. Attribution to the budget is mostly supported, not proven.

- Decomposed by whether the description reached the model, D1 is 27.7 through described runs and 2.1 through bare ones. D2 is 22.1 and 7.3.
- Across targets, the contrast tracks reach: r .69 for D1 and r .88 for D2.
- About a quarter of D2 runs through bare-name loads. Short trigger's bare rate is .322 against trigger's .211 (Fisher p .083, by-target +11.1, se 3.5, p .01, both post hoc). The pooled placebo test gives no reason to call that a real leak.
- Only 2 of 27 trigger loads touched a skills path by command, and 8 had a Glob or skills-path call first. I did not inspect Glob contents, so "from the name alone" (paper 206) is likely, not proven.
- Threats tested: prefix, distractor sample and carry-over (Held up), and fit depending on the draw, which is why the 0.72 split is exploratory (S15). The missing test is S3.

**"At no measurable cost below the budget".** Not fair as worded, fair in its registered form (M8).

## Recomputation and commands

| Check | Result |
|---|---|
| Study 2b, own script, nothing imported from the repo | 576 manifest rows, 41 no trace, 1 leak, 534 used, all `ok`, Sonnet 5.5, CLI 2.1.303 |
| D1 | +29.76 [+19.18, +40.34], p .00007, identical to `results/study2b.json` |
| D2 | +29.45 [+20.52, +38.38], p .00002, identical |
| D3 | -0.32 [-9.22, +8.59], p .939, identical |
| D4 | +2.08 [-2.50, +6.67], p .339, identical |
| Study 1 real against filler, own fixed-effect regression | +0.23 [-5.24, +5.71], p .924, largest per-rule gap from committed 0.0 points |
| Own checkers from the rule text on `final_no_digits`, `final_no_contractions`, `final_no_first_person` | Agree with the repo on 786 of 786 each. Renderer and the other six checkers came from `study1/` so all nine rules could be fit. |
| Raw real minus filler from my checkers | Digits +0.3 (se 3.6), contractions -2.6 (3.7), first person +10.1 (5.4) |
| `make test` | 51 tests OK, 4.62 s, exit 0 |
| `make replay` | 35.51 s, exit 0. Study 1 replayed 20 runs, 280 of 280 verdicts match. Study 2 and 2b 10 of 10 each. Estimates 152 of 152, 112 of 112, 92 of 92. Readings printed, Study 1 `inconclusive`. |
| `make reproduce` steps on an isolated copy | About 25 s. 10 of 10 outputs byte-identical. |
| `analysis.calibration` on a copy | 2m44s, byte-identical |
| `analysis/robust.R` on a copy | Byte-identical, singular fit printed |
| `make rerun` | 0 runs to do on a clean clone (M6). Filter applied, batch not started. |
| `python -m analysis.listing_mechanism replay` on a clean checkout | Crashes (M6) |

## Novelty

**Verdict: no scoop found.** I found no preregistered randomized test of a reason or placebo reason on a real coding agent, so the claim stands as worded. Absence after 14 searches is not proof. The claim that needs care is different: the listing behavior is vendor-documented (M1).

Search log, 2 November 2026. orx 0.2.19, telemetry off. `orx discover` and `orx paper` take no `--backend` flag, and no experiment ran.

| Tool | Query |
|---|---|
| orx embedding | does telling a coding agent why a rule exists change whether it follows the rule, randomized experiment |
| orx embedding | justification clause added to a system prompt rule increases compliance of language model agents |
| orx keyword | preregistered randomized "Claude Code" instruction |
| orx keyword | rationale "AGENTS.md" randomized compliance reason |
| orx embedding | mindless compliance placebic explanation Langer copy machine experiment replicated on large language models |
| orx embedding, after 2025-06-01 | A/B test of cursor rules or copilot instructions wording: which phrasing makes the coding assistant adhere |
| orx keyword | skill description truncated listing budget agent never sees description |
| orx embedding, after 2025-01-01 | effect of explaining the reason behind a constraint on LLM constraint satisfaction, controlled factorial |
| orx keyword | "with rationale" "without rationale" rules instruction compliance language model |
| alphaXiv | randomized experiment on whether giving a reason or rationale for a rule in a coding agent's instruction file changes compliance |
| alphaXiv | how the wording or length of an agent skill's description affects whether the skill gets activated, tested with controlled variants |
| Web | experiment does explaining why in CLAUDE.md rule improve Claude Code compliance tested reasons vs no reasons results |
| Web | skill description "Use when" vs directive wording, 650 tests, description budget, SLASH_COMMAND_TOOL_CHAR_BUDGET |
| Web | Anthropic prompting best practices, add context, explain why |

Should cite, all opened:

- [Claude Code skills page](https://code.claude.com/docs/en/skills) and [prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) (M1).
- [CLAUDE.md Under Test](https://leanpub.com/claude-md-under-test). I read its public description only: 39 trials on Claude Code 2.1.246 on rule presence and burial, 0 of 22 attempts with the rule against 17 of 17 without. It describes no reason arm.
- [SkillClash, 2610.25064](https://www.alphaxiv.org/abs/2610.25064). Worked examples inside skills drive which rules get followed. Review 1 lists it, the paper does not, and it bears directly on the +26.9.

Read and not scoops: [2610.21421](https://www.alphaxiv.org/abs/2610.21421) (instruction categories on five Python libraries, no reason arm), [2608.11095](https://www.alphaxiv.org/abs/2608.11095) (why instruction files grow, rationale loss, may merit a mention), [2608.23550](https://www.alphaxiv.org/abs/2608.23550) (written rules against built-in deny controls), [2610.35992](https://www.alphaxiv.org/abs/2610.35992) (when harness guidance arrives, says it is not a randomized experiment of agent outcomes), [2610.06193](https://www.alphaxiv.org/abs/2610.06193) (contribution policies as a benchmark), [2610.13287](https://www.alphaxiv.org/abs/2610.13287) (preregistered, on prompt optimizers, not reasons).

Surfaced and not read: 2610.37332, 2601.10343, 2608.11727 (listed in Review 1). A 650-test practitioner article on `besthub.dev` failed to fetch, so it stays unverified. A `dev.to` post on five patterns has one unmeasured claim on polarity and no reason test.

## Citation spot-check

Papers were read in full with `orx paper --full` unless noted.

| Citation | Checked | Result |
|---|---|---|
| [zarzycki2026](https://www.alphaxiv.org/abs/2610.31715) | 818 files, 74.0%, P10 163, P90 3,010, the quote "Whether reasons or emphasis change what agents do remains open" | Correct |
| [mcmillan2026](https://www.alphaxiv.org/abs/2605.10039) | 1,650 sessions, 25 to 500 lines, audit justification, nulls after correction, bound of about 6 points, T4 vs T5 of 26.2 | Correct. "Replicate" is the problem (S8). |
| [liu2026routing](https://www.alphaxiv.org/abs/2610.18522) | 73.6, 27.4, 63.3, 1,000 skills | Numbers present, baselines spliced (S9). I found no variation of the target's description, consistent with the paper's "never vary". |
| [wang2026evolution](https://www.alphaxiv.org/abs/2610.04832) | +0.23 (+.16 to +.36), +0.017 [+.002, +.034], margin .08 on four open models | Correct |
| [folkes1985](https://doi.org/10.1037/0022-3514.48.3.600) | Abstract through orx: "In Studies 2 and 3 ... Neither study replicated" | Quote correct. Abstract only. |
| [langer1978](https://doi.org/10.1037/0022-3514.36.6.635) | 120 adults, Table 1 .60/.93/.94 and .24/.24/.42, cells of 15, 15, 16 and 25, 25, 24 | Correct, read from a [third-party PDF copy](https://jamesclear.com/wp-content/uploads/2015/03/copy-machine-study-ellen-langer.pdf) |
| [zhang2026guardrails](https://www.alphaxiv.org/abs/2604.11088) | 63.8 | Correct |
| [zhu2026precedent](https://www.alphaxiv.org/abs/2610.38244) | 359/360, 59/60 vs 38/60 | Correct |
| [xu2026stale](https://www.alphaxiv.org/abs/2610.30571) | 90.1, 4.2 to 91.4 | Correct |
| [wang2026advertising](https://www.alphaxiv.org/abs/2605.23916) | Preregistered, two OpenAI models, about 43 points | Correct |
| [zhan2026wording](https://www.alphaxiv.org/abs/2610.05278) | 54.9, 48.2, 36.7, 33.8 | Correct |
| [spence2026](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals) | About 250 invocations, 100% with hooks, Sonnet 4.5 | Correct |
| [inferal](https://inferal-com.pages.dev/blog/instruction-adherence-research) | "Over-explaining rationale (consequences strategy didn't improve adherence)" | Correct. Sample is stated in the post (Taste). |

Not spot-checked: `clark1973`, `judd2012`, `holm1979`, `schuirmann1987`, `zhang2026estimands`, `lauziere2026`.

## Not covered

`make isolation` and the live half of the listing measurements were not rerun, since they start agents. `results/clause_check.json` and the explorer's behavior were not checked. The Haiku section does not exist yet, so its "sign only" reading is unreviewed.
