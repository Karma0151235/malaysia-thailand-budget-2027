PYTHON ?= .venv/bin/python

.PHONY: all setup run test clean

all: run test

# Uses uv when available, otherwise falls back to the standard library venv.
setup:
	@if command -v uv >/dev/null 2>&1; then \
		uv venv --python 3.11 .venv && uv pip install --python $(PYTHON) -r requirements.txt; \
	else \
		python3 -m venv .venv && $(PYTHON) -m pip install -r requirements.txt; \
	fi

run:
	PYTHONPATH=src $(PYTHON) -m budget_compare

test:
	$(PYTHON) -m pytest -q

clean:
	rm -rf outputs/charts outputs/findings.json .pytest_cache
