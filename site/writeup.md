# What makes Claude Code follow its instructions

Anyone who uses Claude Code ends up writing instructions for it, and there's plenty of advice about how to word them. Put it in capitals, say IMPORTANT, say you must, explain why. I wanted to know which of that changes what the agent does, so I ran four preregistered randomized experiments on Claude Code 2.1.303 with Sonnet 5.5 and scored every run with code instead of a model.

Giving a reason came back inconclusive. No wording factor survives correction on average, though single rules do move in a post hoc look. For skills, the listing budget controls whether a description reaches the model. A long description on a never-used skill that sorts after the budget is spent doesn't arrive. The last study raised the budget, which also showed every other skill's description, and that skill went from a load rate of 0.292 to 0.990, +69.8 points [+53.7, +85.8].

Every number here is on the [numbers page](results/NUMBERS.md) unless it links to its own report, and anything exploratory or post hoc says so. The [explorer](https://abhaymettu.github.io/because/) shows the rules, arms and transcripts behind the numbers, and the [paper](paper/because.pdf) has the full methods.

## Reasons came back inconclusive

Explaining why is the advice the first study was built around. Anthropic's [prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) gives that advice and says "Claude can generalize from the explanation." The older version of the idea is Langer, Blank and Chanowitz (1978), the copier study, where a "because" with no content worked for a small favor. That paradigm is contested, Folkes (1985) reports studies that did not replicate it, and I treated this as an analogue instead of a replication.

Study 1 gave the agent coding tasks in two synthetic repos, 1,000 runs and 7,072 focal observations, with a `CLAUDE.md` holding a random mix of rules. Each rule's wording was drawn on its own, so a single file can compare a reason on one rule against no reason on the next.

A reason written for the rule, the "real" arm, is +0.2 points [-5.2, +5.7] against a filler sentence of matched length. A placebo like "because that is just how this particular part of the project is" gets +1.1 [-1.2, +3.5]. The registered reading is the word inconclusive. Before the first run I set the bar for calling this a null at both upper bounds under 5 points, and the real arm reached 5.7, so I'm not calling it a null.

Averaged across these nine rules, the 95% interval against filler stops at +5.7. Single rules are less certain. `final_no_first_person` reads +15.8, post hoc, and the prediction interval for a new rule is about plus or minus 12, [-11.6, +11.9], also post hoc. Simulated power at 5 points is 0.56 with a slope SD of 3 points across rules and 0.34 with 6, and anything smaller could easily go unseen.

Real minus placebo is -0.9 [-5.6, +3.8]. It passes an equivalence test at 5 points, TOST p 0.040, a registered sensitivity check, and the pass is narrow. It fails at 4.5 (p 0.058, post hoc), and the same test passed 20% of the pre-freeze simulations with a true gap of 5, because ceilings shrink the gap it sees. The placebo effect from the copier study doesn't reproduce here.

Also, this design scores literal compliance only, and the guide's claim is about generalizing past the literal rule, which I didn't test. The reason I wrote for `final_no_digits` is a voice assistant that stumbles over numerals, close to the guide's own text-to-speech example. It reads +2.9 post hoc, and all that says is whether digits showed up.

## No wording factor survives correction on average

Capitals come nearest of the nine registered contrasts, at +2.5 points [+0.2, +4.9], raw p 0.039, Holm p 0.353.

Single rules do move, in a look nobody registered, so all of this paragraph is exploratory and post hoc. Two of the 72 rule-by-level cells survive Holm, a worked example on `final_no_first_person` at +26.9 and `IMPORTANT:` on `reverse_imports` at +9.8. A worked example adds specification as well as form and has no length-matched control, so I wouldn't read +26.9 as form alone. Adding position, file length and user pressure makes 99 cells and five more survive, the largest being a user in a hurry on `one_blank` at -24.5. The [numbers page](results/NUMBERS.md) has the table.

## With the description in view, a trigger list loads at least as well

Study 2 moved to skills, where the agent decides whether to load one from a line of text. With the description in view, a trigger list ("Use when ...") loads a skill more often than one short sentence, +17.6 points [+6.3, +29.0], Holm p 0.023. That contrast pools libraries of 0 and 50 skills with 300-skill runs that have an early name, and those 300-skill runs hold 7 of the short sentence's 12 misses. Strictly below the budget it's +12.4 [+1.5, +23.2] in Study 2 and +3.5 [-10.0, +16.9] in Study 2b at 50 skills, both post hoc.

"ALWAYS invoke" and a "Not for" clause showed nothing, but both sat at a limit. Trigger lists already loaded at 1.00 in those cells, and decoy prompts loaded a skill at a rate of 0.007. A ceiling and a floor can't show an effect, so this is no evidence that those wordings do nothing.

## The listing budget decides what the model sees

The [Claude Code skills docs](https://code.claude.com/docs/en/skills) already describe the limit. They say the budget scales at 1% of the model's context window, that descriptions get dropped starting with the skills you invoke least, and how to raise it. I read that page on 2026-11-02 and it isn't pinned to a version. I went to measure the rule behind it on 2.1.303, and what I found beyond the docs is the exact walk, the skip, the tie order and how much it costs you.

If everything fits, every skill keeps its description. Otherwise bundled skills keep theirs, every other skill is charged for its bare name, and the rest sort by past use on the account, with ties in name order. Then the CLI walks that list once. A skill keeps its description if its length plus 2 fits in what's left, and if it doesn't, the walk skips it and keeps going, so a shorter description further down can still fit. In the pilot, `zz-timezone-audit` had 5 characters left at its turn and lost a description costing 20, and `zz-release-notes` had 60 left and kept one costing 23. The [full rule](docs/LISTING-MECHANISM.md) is in the repo, measured from captured requests with no model judgment.

The budget is `context_window * chars_per_token * 0.01` in the binary. I measured 30,000 characters on `claude-haiku-5-5` and `claude-sonnet-5-5`, and below 10,240 on `claude-sonnet-4-6`.

A replay of the rule predicts all 4,915 listing entries I compared. You can't rerun those from a clean checkout, because the pilot captures aren't in the repo and the rest come from live runs. This narrower check takes about a second with no agent.

```
.venv/bin/python -m analysis.listing_check data/study2 data/study2b data/study2c
```

It predicts whether each run's target kept its description and compares that with what the run's capture recorded, and it's right in all 1,519 runs of the three skill studies. It uses the manifests, the fixtures, the stored widths of the bundled skills, the run times in each `batch.log` and the usage the account held when each batch began. With no usage counted it gets 583 of 600, 426 of 535 and 361 of 384. Nobody registered this check.

The scope is narrow. What loses its description is a long description on a never-used skill that sorts after the budget is spent. At 300 skills early names and used skills keep theirs, and in Study 2 every wording with an `aa-` name reached the model in 1.000 of runs.

An early name adds 51.3 points [+37.7, +64.8] over a late one at 300 skills. That average covers a wide spread by wording, raw `aa` minus `zz` running from +12.2 for the short sentence to +76.5 for the trigger list, post hoc. The prefixes force name order, so these are sizes at an extreme.

Study 2's registered test of the reversal was too wide to read, at -27.1 [-67.1, +13.0], so I preregistered Study 2b to settle it, using late names with no usage history.

| Wording | Load rate at 50 skills | Load rate at 300 skills | Description reached the model at 300 |
|---|---|---|---|
| `Reconciles ledgers.` | 0.953 | 0.511 | 0.526 |
| `Use when reconciling ledgers.` | 1.000 | 0.500 | 0.338 |
| Long trigger list | 0.978 | 0.211 | 0.000 |

At 300 skills the short plain description beats the long list by +29.8 points [+19.2, +40.3], and the short description in trigger form beats it by +29.4 [+20.5, +38.4]. At 50 skills, below the budget, the short trigger is +2.1 [-2.5, +6.7] against the long list, and the registered reading says it costs under 10 points. Those cells sit near the ceiling and 11 of 12 targets tie at zero, so the data can't separate a cost of a few points from none.

When the description is gone the agent mostly does the job with no skill, 0.721 of Study 2b runs at 300 skills against 0.178 when the description is kept. That split is exploratory, since whether a description fits wasn't randomized and the comparison mixes wordings and targets.

## Raising the budget brings the long description back

That still left a gap, and I didn't find it myself. A hostile review by a fresh model session with no part in the build ([Review 3](docs/REVIEW-3-final.md), item S3) pointed out that no arm had ever changed the budget, so "past the budget" had always meant "300 skills". Study 2c's frozen registration came from that item. It has 384 runs at 300 skills with late names and no usage, and it sets the budget at the CLI's own 30,000 characters or at 100,000 through `SLASH_COMMAND_TOOL_CHAR_BUDGET`. The two wordings are the minimal sentence, a mean of 21 characters, and the trigger list, a mean of 140. Every raised run carried the description, and each cell has 96 runs.

| Load rate | Own budget | Raised |
|---|---|---|
| Minimal | 0.531 | 0.823 |
| Trigger list | 0.292 | 0.990 |

All four registered contrasts pass Holm. For the trigger list, raised minus the CLI's own budget is +69.8 [+53.7, +85.8]. For minimal the same contrast is +29.2 [+6.1, +52.2]. With the budget raised, trigger minus minimal is +16.7 [+0.7, +32.7], and the interaction is +40.6 [+22.7, +58.6]. The registered reading that fired is "the budget causes the reversal: with the budget raised a long trigger list recovers and is within 10 points of a short description or above it", and this is the cleanest result in the repo.

It costs money. A run cost $0.134 with the budget raised, against $0.061 for minimal and $0.060 for the trigger list at the CLI's own budget, at API-equivalent prices. Raising the budget also shows every distractor's description, so this tests the budget, which is what you'd get if you raised it, and not the target's description alone.

## Rule identity and having a rule, exploratory

Compliance across the nine rules runs from 0.09 to 0.93. I chose that band, since the pool rule kept rules at 0.10 to 0.95 in pilots and 42 of the 59 candidates sat at or above 0.95, so the range is there by construction. Rule identity isn't randomized, and it isn't a lever you can pull, because you write a rule to get that behavior. Having a rule adds 54.2 points [+33.1, +75.2] over having no rule, which is close to saying a rule works better than no rule.

## What I'd do with this

This applies to new project skills, since no target had usage history and only project skills and built-ins loaded.

If you have many skills, check whether the listing is past its budget. The docs say `--debug` logs a warning when it is, and the Skills row in `/context` shows the listing's size after the budget. If it's past, raising the budget is what the data backs, and in Study 2c that took a run from about $0.06 to $0.134.

If you can't raise it, a late never-used skill needs a description of about 25 characters to keep it. The characters left at its turn had a median of 24 to 29, a p90 of 63 to 68 and a max of 80 to 92 across the three skill studies, and those sizes belong to this library. When a description fits, a trigger list loads at least as well as a short sentence.

For a rule that matters, I think you should test it on your own agent, because no wording factor survives correction on average and single rules moved by up to 27 points, post hoc. The harness takes another agent's command line and transcript reader, and the checkers work unchanged.

## How I ran it

The design is a split-plot factorial. Each run is one `claude -p` on one task, wording is drawn independently for each rule inside a file, and file length and user pressure are set per run. The comparator for a reason is a filler sentence of the same length, like "This note is one of several notes kept here in this section", because a reason clause adds length as well as meaning.

Code computes every verdict from the trace and the repo, and no model scores an outcome. Naming the rule in the prompt gives 0.653 (n 72) against 0.038 (n 1856) with no rule, so the assay can detect a large change, and a contrast that size says nothing about sensitivity at 5 points. The false positive rate of the registered test is 0.053 over 1000 simulations on the real assignment.

Each run gets a clean room, and I measured that instead of assuming it. [`make isolation`](docs/ISOLATION.md) scans the outgoing requests for my own instruction files and skill names, with a plain `claude -p` as the negative control. The same scan runs on every request of every run.

Before computing any contrast I had three fresh model readers, with no arm labels, check 100 focal observations against the checkers. Each item showed the checker's verdict, so the agreement is anchored. They agree on 92 of 100, including one item a reader flagged. Seven are unclear and one disagrees, and those eight all turn on one question, whether a rule's "you write" reaches throwaway code that never lands in the repo. I wrote that decision down [before any contrast](docs/audit/report.md). An earlier blind audit found one checker fault, which I fixed before rescoring every run.

`make replay` checks the harness, the checkers and the analyses with no subscription, 60 s on a fresh clone and 36 s after that, and it covers all four studies. `make reproduce` regenerates the registered results and the [numbers page](results/NUMBERS.md) from the raw traces in 24 s, while `make calibration` and `make robust` write their own files. `make rerun` repeats the runs into a fresh folder, and it needs Claude Code 2.1.303 and a subscription.

## What this doesn't settle

This is one model on one CLI version, nine rules picked off the ceiling in pilots, and two synthetic repos. The preregistered tests are claims about rules like these. Nothing here describes a skill already in use. The `aa-` and `zz-` prefixes are artificial, the size of Study 2c's effect belongs to a library of this size and to `zz-` names with no usage, I wrote the skill targets, and the real reasons are plausible rationales the agent can't check. The listing sizes belong to this library of 81 to 675 character descriptions, and the rule is a fact about 2.1.303 and can change with any release. I also ran the first study's design on Haiku and read it for sign only. Real against filler is -0.9 [-5.2, +3.4] and placebo against filler is +0.3 [-3.3, +3.9]. The signs are mixed, and sign is all this batch is read for.

The strongest timing evidence is for Study 2c. GitHub Actions created a run on the tagged commit at 2026-11-02T07:46:31Z, before the first run, which you can verify once the repo is public, and [`batch.log`](data/study2c/batch.log), my own record, shows the runs after it. For Study 1, GitHub reports the repo created at 03:52:50 UTC, one second after the freeze commit date. The rest of the order of events rests on commit dates and push history, and I used no timestamping service.

I rewrote the history once before making the repo public, to remove account and device identifiers from the sample captures, so commit and tag hashes changed. The preregistration files hash to the same git blobs at the new tags. I also fixed a bug in the frozen analysis after Study 2's first printout, added registered secondaries after reading the family results, and Study 2b stopped 41 runs short on its registered quota stop. Most exploratory analyses the first registration lists weren't run. All of it is in the [deviations log](docs/DEVIATIONS.md).

## Prior work

A literature review on 2026-11-01 and 14 searches on 2026-11-02, logged in [Review 3](docs/REVIEW-3-final.md), found no preregistered randomized test of a reason or placebo reason on a real coding agent, and a [census of instruction files](https://www.alphaxiv.org/abs/2610.31715) says "Whether reasons or emphasis change what agents do remains open." Absence after a search isn't proof, and this field moves weekly.

Practitioner tests exist. An [Inferal post](https://inferal-com.pages.dev/blog/instruction-adherence-research) reports that a consequences strategy did not improve adherence, from 9 to 10 runs per strategy on one project with Sonnet. [CLAUDE.md Under Test](https://leanpub.com/claude-md-under-test) ran 39 trials on rule presence and burial on Claude Code 2.1.246, and its public description, the part I read, lists no reason arm.

Position and file size repeat tests by [McMillan](https://www.alphaxiv.org/abs/2605.10039), who ran both on Claude Code and found nulls, and neither survives correction here. [SkillClash](https://www.alphaxiv.org/abs/2610.25064) reports that worked examples inside skills drive which rules get followed when two skills clash, which bears on the post hoc +26.9. The effect of library size on skill loading belongs to [2610.18522](https://www.alphaxiv.org/abs/2610.18522). The part I didn't find elsewhere is the target skill's own description randomized on real Claude Code, crossed with library size.

Three reviews are in the repo, on [novelty and design](docs/REVIEW-1-novelty-design.md), [the preregistration](docs/REVIEW-2-prereg.md) and [the final draft](docs/REVIEW-3-final.md). Fresh model sessions wrote all three, and no person has reviewed this. The last one was hostile, and it drove the final changes to this page and a whole study.

The distractor library comes from [`alirezarezvani/claude-skills`](https://github.com/alirezarezvani/claude-skills) (MIT), and the repo is MIT too.
