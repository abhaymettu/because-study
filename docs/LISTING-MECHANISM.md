# Which skills keep their description in the listing

Claude Code 2.1.303, project skills in `.claude/skills`, run through this repo's harness.

Each claim carries one of three labels. **Measured** means a live run or a replay of stored captures. **Binary** means read from the code in the shipped CLI and not tested separately. **Inferred** means neither.

## The rule

If every entry fits in full, every skill keeps its description. The budget is 30000 characters on `claude-haiku-5-5` and `claude-sonnet-5-5`.

Otherwise the CLI does this:

1. Bundled skills always keep their description. In this setup there are 12.
2. Every other skill is charged for its bare name. Each newline between entries costs 1 as well.
3. The remaining skills are sorted by usage score, highest first. Ties keep the listing's base order, which is project skills by name, then `init` and `security-review`.
4. The CLI walks that list once. A skill keeps its description if `len(description) + 2` fits in what is left. If it does not fit, the skill is skipped and the walk continues, so a short description further down can still fit.

The usage score comes from `skillUsage` in the account's global config: `usageCount * max(0.5 ^ (days_since_last_use / 7), 0.1)`. A skill never used scores 0.

So two things can save a skill late in the alphabet: having been invoked before on this account, or having a description short enough for the leftover characters.

## Why the pilot looked inconsistent

All four targets sort last among the project skills. Replay of the stored captures gives the reason for each (**measured**).

| Run | Target | Wording | Prior usage | Characters left at its turn | Cost | Kept |
|---|---|---|---|---|---|---|
| s2pilot-00006 | zz-timezone-audit | minimal | 0 | 5 | 20 | no |
| s2pilot-00008 | zz-log-triage | trigger_not | 0 | 35 | 209 | no |
| s2pilot-00011 | zz-release-notes | minimal | 0 | 60 | 23 | yes, it fit the leftover |
| s2pilot-00015 | zz-ledger-reconcile | padded | 1 | 18063 | 126 | yes, it went first |

`zz-ledger-reconcile` had usage because s2pilot-00001 invoked it 52 seconds earlier.

`results/listing_rule.json` looked like evidence that a zz name always keeps its description. It was written at 21:56:54, after the pilot had invoked `zz-ledger-reconcile` and `zz-log-triage` at 21:54. Those two are the only stems it tested, so every zz row was promoted by usage. A longer target cost a distractor a slot for the same reason: the target was charged first.

## Evidence

**Exact prediction of the whole set (measured).** `analysis/listing_mechanism.py` implements the rule and compares every entry.

| Test | Entries compared | Wrong with the rule | Wrong with usage removed |
|---|---|---|---|
| 16 pilot captures | 2590 | 0 | 28 |
| Live, fresh distractor samples at 120, 200, 300, 300, 388 skills | 1378 | 0 | not run |
| Live, library of 300 plus probes, before and after usage | 947 | 0 | not run |

Earlier result files replay the same way, using only their stored inputs:

- `results/listing_budget.json`: 18 of 18 rows match on count and on the prefix flag, including the False rows at 200 and 388. Those two are the skip in step 4. No usage is needed, because the file predates the pilot.
- `results/listing_rule.json`: 40 of 40 rows match on target and on distractor count with pilot usage, and 22 of 40 without it.

**Usage is the cause (measured).** Same library, same prompt, three never-used probes with descriptions of about 500 characters:

| State | Probe a | Probe b | Probe c |
|---|---|---|---|
| Before any Skill call | bare name | bare name | bare name |
| After one real Skill call each for a and b, two for c | described | described | described |
| Same, with a budget that leaves room for one probe | bare name | bare name | described |

The one-slot row also ranks the factors. Probe b sorts before c and was used last, so name order and recency both favored b. The higher count won. On the original library, adding usage to probe a took the description from three distractors.

**The budget (measured).** A crafted library of 100-character costs followed by 3-character costs reads the budget to within 3. The 3-character tail also shows the skip directly: after the long ones stop fitting, 20 tail skills still fit.

| Setting | Budget read off |
|---|---|
| Haiku 5-5 | 30000 to 30002 |
| Sonnet 5-5 | 30000 to 30002 |
| Haiku 5-5, pilot tools | 30000 to 30002 |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET=12000` | 12000 to 12002 |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET=20000` | 20000 to 20002 |
| `claude-sonnet-4-6` | below 10240, no non-bundled description kept |

**The code (binary).** The budget is `context_window * chars_per_token * 0.01`. Chars per token is 3 for current models and 4 for a named list of older ones, which includes `claude-sonnet-4-6`. The rule's walk, sort and usage formula are in the same functions. An invocation writes `usageCount + 1` and a new `lastUsedAt`.

## What was ruled out

Each variant below reran the same 300-skill library plus a never-used late probe. All eight gave the identical described set and the identical order (**measured**).

| Candidate | Test |
|---|---|
| Relevance to the prompt | A prompt naming the probe and using its description's words |
| Tool list | `Skill,Read` against `Skill,Bash,Read,Edit,Write,Glob,Grep` |
| Model or context size | Haiku 5-5 against Sonnet 5-5, each tool list. Older models do differ, through the budget above |
| Creation order | Skills created in reverse order |
| mtime | Probe set 10 days newer than the rest, then 10 days older |
| Nondeterminism | Plain repeat |

A hash of the name is ruled out because the rule predicts every entry without one. The distractor sample matters only through its description lengths, and the prediction uses those. Plain alphabetical prefix is wrong because of the skip and the usage sort. Greedy fit is correct, and is part of the rule.

## How to record it per run

Parse the first captured API request of the run, and read the target's line inside the listing block:

```python
from analysis.listing_mechanism import described, listing_block
target_described = described(listing_block(request), target)  # True, False, or None if not listed
```

This reads what the model was actually sent, so it needs no model of the CLI and survives a version change. It anchors on the start of a line inside the listing block, where a search of the whole request could also match other text (**inferred**, no such false match was seen). The stored pilot captures hold this request, so the field can be backfilled with no new calls (**measured**, on all 16).

## What this means for Study 2

- **Runs are not independent (measured).** Any Skill call raises that name's priority for every later run on the account. So a zz target's condition depends on whether an earlier run invoked the same name, and therefore on run order. By the formula the score never decays to 0, so one call outranks every never-used skill indefinitely (**binary**, decay not tested live).
- **`zz` at library 300 does not mean the description is gone (measured).** Contrast C5 in `analysis/study2.py` is named `trigger_vs_minimal_described_gone`, but a minimal wording can fit the leftover, as `zz-release-notes` did. Wording therefore changes whether the description is present, inside the contrast meant to hold it absent.
- **`PREREG-STUDY2.md` and `study2/design.py` state the rule as alphabetical.** That wording is incomplete.
- **Isolating usage per run was not tested.** Neither was any fix. `results/listing_rule.json` should not be cited as evidence for a rule.

The Study 1 batch uses the same config, and these tests did not assess whether it is affected.

## Limits

- **Not tested live (binary only):** the usage decay, the 1536-character cap per description, the `when_to_use` text counted with the description, and width measured with `Bun.stringWidth` rather than characters. Fixture descriptions all have width equal to length, so the last has no effect here.
- **Inferred:** the 1M context window on Haiku and Sonnet 5-5, from the measured 30000 and the formula. `claude-sonnet-4-6` at 8000 is what the formula gives for a 200k window; only "below 10240" was measured.
- **Not located in the binary:** the sort behind the base order. Names sorted ascending in every capture and did not follow creation order. Mixed-case names were not tried.
- **Scope:** only project skills and built-ins load here, because the harness passes `--setting-sources project`. Skills from user settings or plugins were not tested.
- **Why `>` matters:** the listing prints `>` as `&gt;` and leaves `&` alone (**measured**), and the longer form is what gets charged. `<` did not occur in the fixtures.

## Reproduce

```
BECAUSE_ACCOUNT_EMAIL=... .venv/bin/python -m analysis.listing_mechanism
.venv/bin/python -m analysis.listing_mechanism replay
```

The first command makes 29 model calls and writes `results/listing_mechanism.json`. The second makes none and writes `results/listing_replay.json`.

The first command also leaves four `zz-mech-<tag>-*` entries in the account's `skillUsage`, because its usage test makes real Skill calls. Eight are there now from two runs. They affect only skills with those names.
