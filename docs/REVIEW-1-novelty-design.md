# Review 1: novelty and design (2026-11-01)

## Verdict

Part (a) survives, (b) as written does not, and (c) survives only in a narrow form. I found no randomized test of a reason or placebo reason on a real coding agent. The census 2610.31715 says: "Whether reasons or emphasis change what agents do remains open." Part (b) is partly scooped: McMillan (2605.10039) already ran position and file size on Claude Code, with nulls, so these two factors become replications. The new parts are reason, placebo, modal, emphasis and example across many rules. Part (c) must drop library size as a contribution (2610.18522 owns it); the new part is randomizing the target skill's own description on real Claude Code, crossed with library size. Practitioner tests exist, so say "no preregistered randomized test found", never "nobody". Before freezing, the design must change the placebo, split CAPS from MODAL, add a length-matched non-reason control, replace the +/-10 margin, resolve the estimand and inference mismatch, add a costly-rule condition (Langer's actual moderator), state a run count, and count no-opportunity runs in the primary outcome. This field is moving weekly, so rerun the search just before posting.

## Closest prior work

Read means the paper text returned by alphaXiv, unless marked.

| Id | Covers | Does not cover |
|---|---|---|
| [2605.10039](https://www.alphaxiv.org/abs/2605.10039) McMillan | Claude Code CLI, 1,650 sessions. Size 25 to 500 lines, 5 positions, architecture, conflict. All null after correction; its text rules out effects above about 6 points on two variables (the passage's start was cut off, confirm which). Task identity gap 26.2 points; no-config baseline 0%; ME-03 compliance 67.7% | One trivial rule (`// @tracked`), always justified as an audit requirement, so reason is held constant. No modal, emphasis, example. One-factor sub-blocks, not conjoint |
| [2610.31715](https://www.alphaxiv.org/abs/2610.31715) census | 74.0% of directives give no reason; median set 818 words (P10 163, P90 3,010) | Nothing causal |
| [2610.04832](https://www.alphaxiv.org/abs/2610.04832) Wang | Rule presence: agent action +0.23. Token mention alone +0.08 to +0.18. Prose-only revisions +0.017, inside a 0.08 margin (4 open models). String grader recall by arm 0.79 vs 0.65 | No reason, placebo or emphasis factor. mini-SWE-agent scaffold, not Claude Code |
| [2608.11727](https://www.alphaxiv.org/abs/2608.11727) Harness-IF | Against-prior accuracy 66.1 to 78.6%; rules moved across surfaces | Holds rule meaning fixed; no wording factors. 86.8% of verdicts use an LLM judge |
| [2610.38244](https://www.alphaxiv.org/abs/2610.38244) Precedent or Intent | Repo precedent beats defaults 359/360; written priority rule 59/60 vs example 38/60 | No reason or emphasis arm; rule vs example only |
| [2610.30571](https://www.alphaxiv.org/abs/2610.30571) stale files | 90.1% of choices follow a stale file over code; one precedence sentence moves code-following from 4.2% to 91.4%. Prints Claude Code's preamble ("IMPORTANT ... you MUST follow them") | Precedence, not reasons |
| [2610.25064](https://www.alphaxiv.org/abs/2610.25064) SkillClash | Rules 93 to 99% alone, 61 to 62% paired; worked examples drive takeover | Output-only model runs, skill files in the system prompt; the 93 to 99% is not an agent figure |
| [2610.33201](https://www.alphaxiv.org/abs/2610.33201) WhoWins | Position, role, label under conflict, 14 open models | Conflicts only; single replies; no reason |
| [2610.05278](https://www.alphaxiv.org/abs/2610.05278) WISE | Verifier-equivalent wording shifts compliance. POS 54.9, longer 48.2, target later 36.7, AVOID 33.8. Holm controlled | Chat replies, not agents. No reason, no instruction file. Authors call for a factorial extension |
| [2603.26830](https://www.alphaxiv.org/abs/2603.26830) IAMs | Regression on crossed prompt components, the nearest factorial method | Toy arithmetic, 2 open models. Names coding agents as future work |
| [2607.05537](https://www.alphaxiv.org/abs/2607.05537) | Order-of-addition prompt experiments (abstract only) | Order only, not agents |
| [2510.04950](https://www.alphaxiv.org/abs/2510.04950), [2512.12812](https://www.alphaxiv.org/abs/2512.12812), [2604.16275](https://www.alphaxiv.org/abs/2604.16275), [2605.29027](https://www.alphaxiv.org/abs/2605.29027) | Politeness and tone on accuracy or quality (abstracts) | Accuracy, not rule compliance; not agents |
| [2507.11538](https://www.alphaxiv.org/abs/2507.11538) IFScale | Instruction density, bias toward earlier instructions (abstract) | Keyword inclusion in reports; not agents |
| Liu et al., Lost in the Middle (TACL 2024) | As described inside 2605.10039: multi-document QA U-curve | Not system prompts; not read directly |
| [Meincke et al. 2025](https://gail.wharton.upenn.edu/research-and-insights/persuading-llms-initial-study/) | Exists. Seven Cialdini principles on objectionable requests. Wharton page: authority 32 to 72%, commitment 19 to 100% | Not agents, not reasons, not repo rules. SSRN paper not read; sample size and model unverified |
| [2610.18522](https://www.alphaxiv.org/abs/2610.18522) | Library size: recall 73.6 to 27.4% at 1,000 distractors. Masking distractor descriptions restores loading (63.3%) | Target description never varied. Open executors in a custom harness, Claude Opus 4.6 as validation |
| [2605.23916](https://www.alphaxiv.org/abs/2605.23916) | Preregistered tool-description praise +43 points; slot effect about 72 points | Tools, two-item lists, OpenAI models; no library size. Registered in the authors' own repo |
| [Spence blog](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals) | Sandboxed activation evals, about 250 calls. Keyword prompts about 100%, generic 20 to 40%, indirect about 0% | Tests hooks, not description wording |
| Directive-description blogs (via search summaries) | "Use when" 77% vs "ALWAYS invoke" 100% in 650 tests | Source fetch failed; unverified. Treat as the folk claim to test |
| [Inferal blog](https://inferal-com.pages.dev/blog/instruction-adherence-research) | Claims a consequences strategy did not improve adherence | Informal; sample unverified. Closest thing to (a); must be cited |

Not read beyond headers: 2604.11088 (Guardrails Beat Guidance, known through the census's one-line summary: negative constraints help, random rules as much as curated). Read it before freezing, since polarity is a likely moderator. Also 2610.11647 (abstract only), 2608.04828 and 2609.38593 (headers only). A DOI-level OpenAlex search failed (empty output), so citation-graph coverage of psychology is thin. Search results for a Langer replication with LLMs: none, but absence after about 29 searches is not proof.

## Design attacks, ranked

1. **The placebo carries information.** "That is how we do it in this repository" is a descriptive norm, the social-proof principle. It says the rule is a live convention. Langer's placebo restated the request ("May I use the xerox machine, because I have to make copies?"). Fix: use a tautological placebo as primary ("because this is the rule here"), and keep the norm text as a separate arm. Have blind raters score real, placebo and filler text for information before the freeze. Ban rule tokens from all clauses (2610.04832: token mention alone moves behaviour).

2. **"No reason" differs in length and salience.** WISE shows a longer form costs 6.7 points and later target placement 18.2. Reason vs none therefore confounds meaning, length and the distance to the key token. Fix: add a length-matched non-reason filler arm ("this applies to every file in the repo"). Make it the primary comparator for the reason effect. Always place the clause after the imperative.

3. **No costly-rule condition, so this is not Langer's test.** In Langer the placebo works only for a small favor and fails for a big one (.24 vs .24). Fix: pre-specify rule cost as a between-rule moderator. Better still, add a within-rule pressure factor: contrary repo precedent or a tedious step. Precedent is a powerful lever (359/360). This also pulls rules off the ceiling honestly, instead of by selecting rules.

4. **The +/-10 margin can pass trivially.** If real minus none is 8 points, placebo "equals" real even if placebo equals none. Also, Wang's 0.08 and McMillan's about 6 points suggest effects may be smaller than the margin. Fix: a retention test (placebo keeps at least 50% of the real effect), gated on real > filler. Add an absolute margin of 5 points as a sensitivity check. State that "neither works" is a different result. Add a positive control (the rule restated in the task prompt) to show the assay detects change.

5. **Estimand and inference disagree.** Rule fixed effects plus within-rule randomization identify the average over these rules. A bootstrap over rules claims new rules. Randomization inference tests a sharp null for these rules. Three different targets. Percentile cluster bootstrap also undercovers at about 25 clusters (statistical judgment from memory, not checked here). Fix: name two claims. Finite-population: studentized randomization inference on these rule-task pairs. Generalization: random-slope model with a prediction interval for a new rule, possibly CR2 or wild cluster with Webb weights. Treat stimuli as random (Clark 1973; Judd, Westfall and Kenny 2012; both from memory, verify). Report slope variance, because the headline may be heterogeneity.

6. **CAPS and MODAL are not crossable as coded.** "Capitalised modal" does not exist for a plain imperative, so CAPS means two things. It also merges two folk beliefs. "Must" does not fit prohibitions. Fix: PREFIX {none, IMPORTANT:} and CASE {normal, upper} on the operative word; MODAL levels per polarity (must / must not). Polarity becomes a stratified covariate. Note that Claude Code's preamble, as printed in 2610.30571, already supplies IMPORTANT and MUST in every run. Confirm from your capture and report that all emphasis effects are marginal to it.

7. **Rule selection by pilot band.** Selecting on 10 to 90% buys regression to the mean and narrows the estimand (Harness-IF admits selection optimism). A pilot of few runs cannot classify a rule. The draft does not define "bare" among 144 cells. Fix: define the reference cell, fix pilot runs per rule, publish the whole candidate pool with dispositions, and state that claims apply to rules off the ceiling. Keep NO-RULE near 0 per rule; drop prior-aligned rules on that test. Expect lower ceilings than feared: 67.7% in McMillan, against 93 to 99% in a non-agent setup.

8. **Post-treatment opportunity.** If a run never reaches the rule's trigger, or asks a question (McMillan: Opus 4.7 produced no code in 18% of with-config trials), dropping it conditions on a post-treatment variable. The critical review 2609.33153 (abstract only) makes the same point about conditioning on a trigger inside the treated run. A prohibition also passes when the agent simply does nothing. Fix: primary outcome is intention to treat (no opportunity counts as not complied), and for prohibitions it is comply AND task complete. Verify in the NO-RULE arm that each task reaches the trigger, and that never-edit tasks produce natural violations. Report opportunity rate as its own outcome, by arm. Fix opportunity count per task, since McMillan's largest effect was within-session decay.

9. **Checker error may differ by arm.** Wang's grader recall moved 0.79 to 0.65 between arms. Fix: test each checker against hand-built passing and failing traces before the freeze. Blind hand audit of a stratified sample after, reported by arm. Do not let a final-message rule pass on mere mention.

10. **Rule and task are one-to-one.** McMillan's task gap beats every structural effect. Rule difficulty cannot be separated from task difficulty, and the reason effect may vary by task. Fix: two tasks per rule where possible, or state the unit as rule-task pair.

11. **LENGTH and POSITION interact by construction.** "Middle" of 8 rules is a few lines; of 60 rules it is deep. McMillan had to fix length to vary position. Fix: define position in tokens as a covariate, pre-specify the interaction, and calibrate lengths to the census (about 160 and 3,000 words). Expect a null; report as replication with an equivalence bound.

12. **Filler rules are a hidden treatment.** If the target is the only rule with a reason, the reason is a salience cue. Fix: filler at census rates (about 26% with reasons), several seeded filler sets, none related to the target; record the set as a covariate.

13. **Multiplicity family undefined.** Three reason contrasts, TOST, five other factors, Q3. Fix: gatekeeping. Primary: real > filler, then placebo > filler, then retention. Equivalence is an intersection-union test and needs no Holm inside. Everything else is a separate Holm family. Q3 is its own study.

14. **EXAMPLE leaks and dominates.** An example adds length and the token itself, and 2610.25064 shows examples dominate. Fix: the example shows a different instance than the task needs, and is length-matched by a non-example filler.

15. **No sample size.** The draft states no run count. My arithmetic for TOST at p = .5, one-sided alpha .05, 90% power, true difference 0: n = 2(.25)(3.29)^2 / d^2, about 541 per arm at +/-10 and about 2,164 at +/-5, before any clustering. Three reason arms therefore need about 1,600 runs at the draft's own margin, so the scout's 800 runs is short. With about 25 rules, heterogeneity raises this further. For scale, McMillan reports at least 98% simulated power at n = 50 per condition for a 15-point shift, on one rule. Fix: simulate from pilot variance with rule slopes, and fix both a target N and a minimum viable N. Randomize run order, so a quota cut leaves a balanced prefix, with no optional stopping. If quota forbids the target, cut factors first, keeping REASON fully powered.

16. **Conjoint averages over an artificial mix.** Uniform assignment gives 50% capitals, unlike real files. Fix: report census-reweighted AMCEs as sensitivity, and label them.

17. **Generality and drift.** A CLI and a model change together (McMillan's Opus 4.7 was uninterpretable). The `--tools` list also changes the system prompt from what users see. Fix: log the returned model id and system prompt hash per run, randomize run order across time, and run a preregistered replication on a second model at the same CLI. Pin effort and thinking. In the only cross-model data read, Claude moved least (2605.23916 exploratory study; WISE keyword, Sonnet 4.6 at 88.0, 88.3, 91.0), so a null may be Claude-specific. Word the claim that way.

18. **Demand and framing.** Tiny synthetic repos may read as tests. Fix: repos with realistic noise, a realism sample with one real repo, and no checker names in the tree. Do not claim "mindlessness": say the response tracks the form of a clause rather than its content.

19. **Q3 specifics.** List position is a confound (slot effect about 72 points in 2605.23916), and large libraries may truncate the listing (unverified; check captures). Randomize target position and record what was sent. Do not kill at the first tool call, as the scout suggests, because late loads count; 2610.18522 measures loads across a run. Stratify prompts by keyword, generic and indirect. Add a directive arm ("ALWAYS invoke"), the live folk claim. Draw distractors from real skills, since masking shows meaning drives interference.

20. **The leak proof cannot attribute captures yet.** `harness/capture_proxy.py` keeps one class-level `out_dir` (lines 28, 82) and names files `pid-counter` (line 69), with no run id. If concurrent runs share a proxy, "a leak scan on every captured request" cannot map a request to its run. Responses are not saved either, only rate-limit headers, so tool calls must come from stream-json. The draft does not state its concurrency, and I did not test the isolation flags on 2.1.303 (unverified). Fix: one proxy per run on port 0 or a per-run directory, plus planted canary strings in the user-level files the scan should never see. Also remove `Skill` from the tool list in Study 1, so an installed-skill path cannot mix with rule compliance.

## Langer 1978 check

Verified from the [paper PDF](https://jamesclear.com/wp-content/uploads/2015/03/copy-machine-study-ellen-langer.pdf) (a third-party copy; text layer read): Langer, Blank and Chanowitz, Journal of Personality and Social Psychology, 1978, Vol. 36, No. 6, 635-642. DOI 10.1037/0022-3514.36.6.635 comes from a catalog result, not the PDF. Experiment 1 had 120 adults at a copier. The placebic wording is verbatim from the PDF text. Half of the sessions were run by a blind experimenter and the rest by one who knew the hypotheses.

| Favor | No info | Placebic | Sufficient |
|---|---|---|---|
| Small (5 pages) | .60 (n 15) | .93 (n 15) | .94 (n 16) |
| Big (20 pages) | .24 (n 25) | .24 (n 25) | .42 (n 24) |

The text layer prints the first n as "IS"; 15 is my reading, and the cells then sum to 120. The famous result rests on about 15 people per cell and disappears for the big favor. Folkes 1985 (JPSP 48(3), 600-604, abstract read): "Neither study replicated Langer et al.'s results" for Studies 2 and 3. Present this as an analogy to a contested paradigm, not a replication target.

## Search log

Saved JSON: a local scratch directory (not kept). About 29 searches, slightly over budget.

- orx embedding: CLAUDE.md wording compliance (2610.30571, 2610.38244, 2610.31715); persuasion principles (2608.16177, none direct); skill description (2610.18522, 2610.34728, 2610.32336); conjoint prompts (2607.05537, tone papers); rationale and instruction following (nothing relevant); explaining why a rule exists (2608.11727, 2607.26819); lost in the middle (2507.11538, 2608.02639); politeness (2510.04950, 2605.29027); skill triggers (2610.18522, 2609.00549); stated justification (nothing relevant); AMCE prompts (2603.26830); negative constraints (none new).
- orx keyword: Langer placebic LLM (2512.06591 and 2605.26770, XAI on humans and judges, no compliance test); capitals and emphasis (none); AGENTS.md rationale (2610.06193, 2607.26819); placebo and emphasis in CLAUDE.md (2610.05278, 2608.23550); skill description variants (2608.04828, 2609.38593, 2610.35434).
- orx openalex: placebic replication (failed, empty output).
- alphaXiv: wording of instruction files (2610.33201, 2606.15828); tool description edits (2605.23916, 2602.20426, 2610.33182).
- Web: Meincke (Wharton page); Langer (PDF, Folkes); placebic LLM (none); skill activation (Spence, directive blogs); IMPORTANT and YOU MUST (found 2605.10039, Inferal).
- GitHub: `gh search repos` "CLAUDE.md compliance benchmark" (0), "agents.md benchmark" (AndreaGriffiths11/agents-md-benchmark-plugin, a measuring plugin with no wording study; description only), "skill description trigger eval claude" (0); `gh search code` "placebo reason" CLAUDE.md (0).

Scout ids checked: 2610.31715 (74.0% confirmed), 2610.04832 (+0.41, +0.23 confirmed), 2610.33201 (replies 1,887,356, scout said 1.89M), 2610.25064 and 2610.18522 confirmed. 2610.34728 abstract only.
