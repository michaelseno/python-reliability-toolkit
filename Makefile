PYTHON := .venv/bin/python
PLAYWRIGHT_DOWNLOAD_HOST ?= https://playwright.azureedge.net
RUN_PYTEST_ARGS ?= -v
RUN_WORKERS ?= auto
RUN_REPEAT ?= 1
RUN_CHAOS ?=
RUN_SEED ?=
RUN_SURFACE ?= api
RUN_SCAN_PACK ?= core_reliability_scan
CHAOS_PROFILE ?=

.PHONY: venv install browsers test test-unit test-guardrails test-e2e test-api test-legacy-ui run run-serial run-legacy-ui run-chaos-latency run-chaos-fault run-chaos-ci-latency run-chaos-ci-fault chaos-profiles chaos-show inspect trend dashboard clean-data report

venv:
	uv venv

install:
	uv pip install -e .

browsers:
	PLAYWRIGHT_DOWNLOAD_HOST=$(PLAYWRIGHT_DOWNLOAD_HOST) $(PYTHON) -m playwright install chromium

test: test-unit

test-unit:
	$(PYTHON) -m pytest tests/unit

test-guardrails:
	$(PYTHON) -m pytest tests/unit/test_e2e_architecture_guardrails.py

test-e2e:
	$(PYTHON) -m pytest tests/e2e

test-api:
	$(PYTHON) -m pytest tests/api_scenarios/tests

test-legacy-ui:
	$(PYTHON) -m pytest tests/e2e/tests -m legacy_ui

run:
	$(PYTHON) -m reliabilitykit.cli.main run --surface $(RUN_SURFACE) --scan-pack $(RUN_SCAN_PACK) $(if $(RUN_CHAOS),--chaos $(RUN_CHAOS),) $(if $(RUN_SEED),--seed $(RUN_SEED),) --workers $(RUN_WORKERS) --repeat $(RUN_REPEAT) -- $(RUN_PYTEST_ARGS)

run-serial:
	$(PYTHON) -m reliabilitykit.cli.main run --surface $(RUN_SURFACE) --scan-pack $(RUN_SCAN_PACK)

run-legacy-ui:
	$(PYTHON) -m reliabilitykit.cli.main run --surface legacy_ui -- tests/e2e/tests -m legacy_ui -v

run-chaos-latency:
	$(PYTHON) -m reliabilitykit.cli.main run --surface legacy_ui --chaos latency_light --seed 21 -- tests/e2e/tests -m "legacy_ui and chaos"

run-chaos-fault:
	$(PYTHON) -m reliabilitykit.cli.main run --surface legacy_ui --chaos checkout_fault --seed 7 -- tests/e2e/tests -m "legacy_ui and chaos"

run-chaos-ci-latency:
	$(PYTHON) -m reliabilitykit.cli.main run --surface legacy_ui --workers 2 --chaos latency_light --seed 21 -- tests/e2e/tests -m "legacy_ui and chaos" -v

run-chaos-ci-fault:
	$(PYTHON) -m reliabilitykit.cli.main run --surface legacy_ui --workers 2 --chaos checkout_fault --seed 7 -- tests/e2e/tests -m "legacy_ui and chaos" -v

chaos-profiles:
	$(PYTHON) -m reliabilitykit.cli.main chaos list

chaos-show:
	@echo "Usage: make chaos-show CHAOS_PROFILE=<profile_name>"
	@if [ -n "$(CHAOS_PROFILE)" ]; then \
		$(PYTHON) -m reliabilitykit.cli.main chaos show $(CHAOS_PROFILE); \
	fi

inspect:
	$(PYTHON) -m reliabilitykit.cli.main inspect --last 20

trend:
	$(PYTHON) -m reliabilitykit.cli.main trend --window-days 14

dashboard:
	$(PYTHON) -m reliabilitykit.cli.main dashboard --window-days 14

clean-data:
	rm -rf .reliabilitykit

report:
	@echo "Usage: make report RUN_ID=<run_id>"
	@if [ -n "$(RUN_ID)" ]; then \
		$(PYTHON) -m reliabilitykit.cli.main report --run-id $(RUN_ID); \
	fi
