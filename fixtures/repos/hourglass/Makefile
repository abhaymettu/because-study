.PHONY: check lint

check:
	HOURGLASS_ENV=test python3 -m unittest discover -s tests
	@if [ -d qa ]; then HOURGLASS_ENV=test python3 -m unittest discover -s qa; fi

lint:
	python3 tools/lint.py
