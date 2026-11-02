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
	$(PY) -m analysis.study2 data/study2 --out results/study2.json

# The harness, the checkers and the analyses with a stand-in agent, for a check in under a minute.
replay: setup
	$(PY) -m harness.replay

# Repeats the runs themselves. Needs Claude Code and a subscription.
rerun: setup
	$(PY) -m harness.batch data/study1/manifest.jsonl --workers 5

isolation: setup
	$(PY) -m harness.prove_isolation
