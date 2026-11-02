PY := .venv/bin/python

.PHONY: setup test reproduce replay rerun isolation

setup: .venv/.done
.venv/.done: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip -q install -r requirements.txt
	touch $@

test: setup
	$(PY) -m unittest discover -s tests -t .

# Every number from the raw traces. No subscription needed.
reproduce: setup
	$(PY) -m analysis.study1 data/study1 --perms 2000 --out results/study1.json

# The same pipeline on a committed sample of runs, for a check in under a minute.
replay: setup
	$(PY) -m analysis.study1 data/study1 --perms 100

# Repeats the runs themselves. Needs Claude Code and a subscription.
rerun: setup
	$(PY) -m harness.batch data/study1/manifest.jsonl --workers 5

isolation: setup
	$(PY) -m harness.prove_isolation
