PY := .venv/bin/python

CLI := 2.1.303
MODEL := claude-sonnet-5-5
TOOLS := Skill,Bash,Read,Edit,Write,Glob,Grep
TURNS := 6
RERUNS := rerun-study1 rerun-study2 rerun-study2b rerun-study2c rerun-study1haiku

.PHONY: setup test reproduce replay rerun $(RERUNS) isolation calibration robust

setup: .venv/.done
.venv/.done: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip -q install -r requirements.txt
	touch $@

test: setup
	$(PY) -m unittest discover -s tests -t .

# The registered results, the exploratory block, the listing check, the figures and the numbers page, from the raw traces.
# No subscription needed. `make calibration` and `make robust` take longer and write their own files.
reproduce: setup
	$(PY) -m analysis.study1 data/study1 --perms 2000 --out results/study1.json
	$(PY) -m analysis.study2 data/study2 --out results/study2.json
	$(PY) -m analysis.study2b data/study2b --out results/study2b.json
	$(PY) -m analysis.study2c data/study2c --out results/study2c.json
	$(PY) -m analysis.exploratory
	$(PY) -m analysis.listing_check data/study2 data/study2b data/study2c
	$(PY) -m analysis.figures
	$(PY) -m paper.counts > paper/counts.json
	$(PY) -m analysis.numbers > results/NUMBERS.md

# The harness, the checkers and the analyses with a stand-in agent, for a check in under a minute.
replay: setup
	$(PY) -m harness.replay

# False positive rate and power of the registered test on the real assignment. A few minutes.
calibration: setup
	$(PY) -m analysis.calibration

# The mixed model, as a robustness check. Needs R with lme4.
robust: setup
	$(PY) -m analysis.export_long data/study1 data_long.csv
	Rscript analysis/robust.R data_long.csv results/robust.txt
	rm data_long.csv

# Repeats the runs themselves, into data/rerun/<study>, never over the committed traces. Needs Claude Code at the pinned
# version and a subscription. A batch stopped by its quota limit resumes when run again. BATCH_FLAGS=--dry-run starts no agent.
rerun: rerun-study1 rerun-study2 rerun-study2b rerun-study2c

rerun-study1 rerun-study1haiku: TOOLS := Bash,Read,Edit,Write,Glob,Grep
rerun-study1 rerun-study1haiku: TURNS := 40
rerun-study1haiku: MODEL := claude-haiku-5-5

$(RERUNS): rerun-%: setup
	mkdir -p data/rerun/$*
	test -f data/rerun/$*/manifest.jsonl || cp data/$*/manifest.jsonl data/rerun/$*/manifest.jsonl
	$(PY) -m harness.batch data/rerun/$*/manifest.jsonl --workers 5 --expect-cli $(CLI) --model $(MODEL) --effort medium --tools $(TOOLS) --max-turns $(TURNS) $(BATCH_FLAGS)

isolation: setup
	$(PY) -m harness.prove_isolation
