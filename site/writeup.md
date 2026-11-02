# What makes Claude Code follow its instructions

Anyone who uses Claude Code ends up writing instructions for it, and there's plenty of advice about how to word them. Put it in capitals, say IMPORTANT, say you must, explain why. I wanted to know which of that changes what the agent does, so I ran three preregistered randomized experiments on Claude Code 2.1.303 with Sonnet 5.5 and scored every run with code instead of a model.

The rule you pick, and whether you write it at all, matters far more than how you phrase it, though that comparison is exploratory. Giving a reason, the question I went in for, came back inconclusive. And the largest effect I found comes from a limit in the CLI, which drops long skill descriptions before the model reads them.

You can look at the rules, the arms and the transcripts behind each number in the [explorer](https://abhaymettu.github.io/because/).

## Which rule it is matters far more than the wording

Study 1 gave the agent coding tasks in two synthetic repos, 1,000 runs and 7,072 focal observations, with a `CLAUDE.md` holding a random mix of rules. Each rule's wording was drawn on its own, so a single file can compare a reason on one rule against no reason on the next.

Compliance across the nine rules runs from 0.09 to 0.93. Tell the agent to create new Python files with its Write tool and it complies in 0.93 of runs. Tell it to keep digits out of its final message and it complies in 0.09. Having a rule at all adds 54.2 points [+33.1, +75.2] over having no rule. Both of those comparisons are exploratory.

Against that, no wording factor survives correction across the nine registered contrasts. Capitals come nearest, at +2.5 points [+0.2, +4.9], raw p 0.039, Holm p 0.353.

## Reasons came back inconclusive

Explaining why is the advice the study was built around. It traces to Langer, Blank and Chanowitz (1978), the copier study, where a "because" with no content worked for a small favor. That paradigm is contested, Folkes (1985) reports studies that did not replicate it, and I treated this as an analogue instead of a replication.

A reason written for the rule, the "real" arm, is +0.2 points [-5.2, +5.7] against a filler sentence of matched length. A placebo like "because that is just how this particular part of the project is" gets +1.1 [-1.2, +3.5]. The registered reading is the word inconclusive. Before the first run I set the bar for calling this a null at both upper bounds under 5 points, and the real arm reached 5.7. It missed, so I'm not calling it a null.

The data does support two narrower claims. There's no effect above about 6 points, and real and placebo are equivalent within 5 points (TOST p 0.040, a registered sensitivity check). The placebo effect from the copier study doesn't reproduce here. Below that I can't say much, because simulated power at 5 points is 0.56 with a slope SD of 3 points across rules and 0.34 with 6.

## Skill descriptions do move loading

Study 2 moved to skills, where the agent decides whether to load one from a line of text. With the description in view, a trigger list ("Use when ...") loads a skill more often than one short sentence, +17.6 points [+6.3, +29.0], Holm p 0.023.

"ALWAYS invoke" and a "Not for" clause showed nothing, but both sat at a limit. Trigger lists already loaded at 1.00 in those cells, and decoy prompts loaded a skill at a rate of 0.007. A ceiling and a floor can't show an effect, so this is no evidence that those wordings do nothing.

## The listing budget decides what the model sees

This part I didn't go in looking for. A pilot looked inconsistent, with late-named skills keeping their description in one run and losing it in the next, and when I went through the captured requests the listing turned out to follow an exact rule.

Claude Code 2.1.303 gives the skill listing a budget of 30,000 characters. I measured that with no model judgment, and a replay of the rule predicts all 4,915 [listing entries](docs/LISTING-MECHANISM.md) I compared. Under the budget every skill keeps its description. Past it, skills rank by past use on the account, ties go by name, and each one keeps its description only if it still fits in what's left, or else it shows as a bare name.

At 300 skills an early name adds 51.3 points [+37.7, +64.8] over a late one, and the long trigger list that wins below the budget loses past it. Study 2's registered test of that reversal was too wide to read, at -27.1 [-67.1, +13.0], so I preregistered Study 2b to settle it, using late names with no usage history.

| Wording | Load rate at 50 skills | Load rate at 300 skills | Description reached the model at 300 |
|---|---|---|---|
| `Reconciles ledgers.` | 0.953 | 0.511 | 0.526 |
| `Use when reconciling ledgers.` | 1.000 | 0.500 | 0.338 |
| Long trigger list | 0.978 | 0.211 | 0.000 |

At 300 skills the short plain description beats the long list by +29.8 points [+19.2, +40.3], and the short description in trigger form beats it by +29.4 [+20.5, +38.4]. At 50 skills, below the budget, the short trigger is +2.1 [-2.5, +6.7] against the long list, so it costs nothing I can measure.

When the description is gone the agent mostly does the job with no skill, 0.72 of runs in Study 2b against 0.18 when the description is kept. It loads some other skill instead in only 0.02. That breakdown is exploratory.

## What I'd do with this

I think you should spend your effort on which rules you write and on whether a rule fits how the agent already works. The Write tool rule and the digits rule both sit at 0.00 with no rule, so the agent does neither unprompted, and yet one reaches 0.93 and the other 0.09. My read is that picking a tool at the moment you create a file is easy to change, and rewriting how the agent reports its results isn't. That's my interpretation of an exploratory comparison, since rule identity wasn't randomized.

Keep skill descriptions short. The trigger form is worth keeping, as long as it stays short.

## How I ran it

The design is a split-plot factorial. Each run is one `claude -p` on one task, wording is drawn independently for each rule inside a file, and file length and user pressure are set per run. The comparator for a reason is a filler sentence of the same length, like "This note is one of several notes kept here in this section", because a reason clause adds length as well as meaning.

Code computes every verdict from the trace and the repo, and no model scores an outcome. Naming the rule in the prompt gives 0.653 (n 72) against 0.038 (n 1856) with no rule, so the assay can detect change. The false positive rate of the registered test is 0.053 over 1000 simulations on the real assignment.

Each run gets a clean room, and I measured that instead of assuming it. [`make isolation`](docs/ISOLATION.md) scans the outgoing requests for my own instruction files and skill names, with a plain `claude -p` as the negative control. The same scan runs on every request of every run.

Before computing any contrast I had fresh model readers, with no arm labels, check 100 focal observations against the checkers. They agreed on 92 of 100 with no qualification. The other eight all turn on one question, whether a rule's "you write" reaches throwaway code that never lands in the repo, and I wrote that decision down [before any contrast](docs/audit/report.md). An earlier blind audit found one checker fault, which I fixed before rescoring every run.

`make replay` checks the harness, the checkers and the analyses in about 40 s with no subscription, and `make reproduce` regenerates [every reported number](results/NUMBERS.md) from the raw traces.

## What this doesn't settle

This is one model on one CLI version, nine rules picked off the ceiling in pilots, and two synthetic repos. The preregistered tests are claims about rules like these. The `aa-` and `zz-` prefixes are artificial, I wrote the skill targets, and the real reasons are plausible rationales the agent can't check. The listing rule is a fact about 2.1.303 and can change with any release.

I rewrote the history once before making the repo public, to remove account and device identifiers from the sample captures, so commit and tag hashes changed. The preregistration files hash to the same git blobs at the new tags, but the order of events rests on commit dates and push history, and I used no timestamping service. I also fixed a bug in the frozen analysis after Study 2's first printout, and Study 2b stopped 41 runs short on its registered quota stop. All of it is in the [deviations log](docs/DEVIATIONS.md).

## Prior work

A literature review on 2026-11-01 found no preregistered randomized test of a reason or placebo reason on a real coding agent, and a [census of instruction files](https://www.alphaxiv.org/abs/2610.31715) says "Whether reasons or emphasis change what agents do remains open." Absence after a search isn't proof, and this field moves weekly. Practitioner tests exist, including an [informal Inferal post](https://inferal-com.pages.dev/blog/instruction-adherence-research), whose sample I could not verify, claiming that a consequences strategy did not improve adherence.

Position and file size repeat tests by [McMillan](https://www.alphaxiv.org/abs/2605.10039), who ran both on Claude Code and found nulls, and neither survives correction here. The effect of library size on skill loading belongs to [2610.18522](https://www.alphaxiv.org/abs/2610.18522). What's new here is randomizing the target skill's own description on real Claude Code, crossed with library size.

The distractor library comes from [`alirezarezvani/claude-skills`](https://github.com/alirezarezvani/claude-skills) (MIT), and the repo is MIT too.
