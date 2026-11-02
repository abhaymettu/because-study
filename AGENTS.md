# AGENTS.md

A preregistered study of what makes Claude Code follow its instructions. If you are an agent working here, these are the things that are easy to get wrong.

## Layout

- `PREREG.md`, `PREREG-STUDY2.md`, `PREREG-STUDY2B.md`: the frozen plans, each with a git tag. Never edit one. A departure goes in `docs/DEVIATIONS.md`.
- `study1/rules.py`: rules and their code checkers. `study1/design.py`: assignment and rendering. `study2/design.py`: skill wordings and assignment.
- `harness/agent_run.py`: one isolated run. `harness/batch.py`: a resumable manifest run with quota stops. `harness/replay.py`: the pipeline with no subscription.
- `analysis/`: the registered analyses, `study1.py`, `study2.py`, `study2b.py`. Decision tables live in `reading()`, so nobody applies them by hand.
- `data/<batch>/`: `manifest.jsonl` (the assignment, committed before its runs), `traces/` (what checkers read), `raw/` (Claude Code's stream), `captures/` (sample request bodies).
- `explorer/`: the page behind each number. `python -m explorer.build --out explorer/dist`.
- `.github/workflows/site.yml`: every push to `main` runs the tests and the replay, then publishes the explorer to GitHub Pages, so a push to `main` is a publish.

## Commands

- `make test`: unit tests, no subscription.
- `make replay`: harness, checkers and analyses with a stand-in agent, under a minute, no subscription.
- `make reproduce`: every number from the committed traces.
- `make rerun`: repeats the runs. Needs Claude Code and a subscription, and it spends quota.

## Rules

- A checker decides every outcome. No model judges compliance. A checker change means rescoring all runs, and it gets a line in `docs/DEVIATIONS.md`.
- Pool selection reads pooled compliance only, never a contrast between arms.
- Pilot batches are never pooled with confirmatory ones.
- Nothing private goes in the repo: `harness/needles.local` holds your own strings and stays untracked. `python3 -m harness.public_scan --history` must print no real hits before a push to a public remote.
- To point the harness at another agent, pass `command` and `read_stream` in `opts` to `run_agent`. Everything after that reads only the trace and the repo.
