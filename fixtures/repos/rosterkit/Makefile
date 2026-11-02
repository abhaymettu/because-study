.PHONY: check lint

check:
	ROSTERKIT_ENV=test python3 -m unittest discover -s tests
	@if [ -d qa ]; then ROSTERKIT_ENV=test python3 -m unittest discover -s qa; fi

lint:
	python3 tools/lint.py
