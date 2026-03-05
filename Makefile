PYTHON := .venv/bin/python
PLAYWRIGHT_DOWNLOAD_HOST ?= https://playwright.azureedge.net

.PHONY: venv install browsers test test-unit test-e2e run run-chaos-latency run-chaos-fault inspect trend report

venv:
	uv venv

install:
	uv pip install -e .

browsers:
	PLAYWRIGHT_DOWNLOAD_HOST=$(PLAYWRIGHT_DOWNLOAD_HOST) $(PYTHON) -m playwright install chromium

test: test-unit

test-unit:
	$(PYTHON) -m pytest tests/unit

test-e2e:
	$(PYTHON) -m pytest tests/e2e

run:
	$(PYTHON) -m reliabilitykit.cli.main run -- tests/e2e

run-chaos-latency:
	$(PYTHON) -m reliabilitykit.cli.main run --chaos latency_light --seed 21 -- tests/e2e -m chaos

run-chaos-fault:
	$(PYTHON) -m reliabilitykit.cli.main run --chaos checkout_fault --seed 7 -- tests/e2e -m chaos

inspect:
	$(PYTHON) -m reliabilitykit.cli.main inspect --last 20

trend:
	$(PYTHON) -m reliabilitykit.cli.main trend --window-days 14

report:
	@echo "Usage: make report RUN_ID=<run_id>"
	@if [ -n "$(RUN_ID)" ]; then \
		$(PYTHON) -m reliabilitykit.cli.main report --run-id $(RUN_ID); \
	fi
