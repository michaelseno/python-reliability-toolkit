# ReliabilityKit

[![PR CI](https://github.com/michaelseno/python-reliability-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelseno/python-reliability-toolkit/actions/workflows/ci.yml)
[![Scheduled CI](https://github.com/michaelseno/python-reliability-toolkit/actions/workflows/ci-scheduled.yml/badge.svg)](https://github.com/michaelseno/python-reliability-toolkit/actions/workflows/ci-scheduled.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)

ReliabilityKit is a local-first reliability execution layer for Python Playwright + pytest.
It wraps test execution and emits structured run records, artifacts, failure classifications,
and HTML reports so every run becomes analyzable data.

## Project Status

- **Status:** MVP complete and actively evolving
- **Execution engine:** CLI-first with importable core modules
- **Storage:** local-first run records and artifacts (`.reliabilitykit/`), S3 backend scaffolded
- **Test coverage:** 51 POM-based Playwright e2e scenarios on `https://practicesoftwaretesting.com`
- **Quality gates:** unit tests, golden snapshot tests, architecture guardrails, PR CI, and scheduled CI
- **Next milestones:** richer trend analytics, expanded failure classification, and production-ready S3 backend

## Quickstart (uv + venv)

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

Install Chromium (uses Playwright CDN mirror by default):

```bash
make browsers
```

Run tests via ReliabilityKit:

```bash
make run
```

`make run` executes e2e with pytest-xdist (`--workers auto`) for parallelism.
Use `make run-serial` if you need deterministic single-worker execution.

The default e2e suite targets `https://practicesoftwaretesting.com` and currently contains 51 scenarios
covering positive, negative, and edge cases.

E2E tests follow a Page Object Model structure under `tests/e2e/` with separate `pages/`, `components/`,
`flows/`, `assertions/`, and `data/` modules to keep tests DRY and maintainable.

See `CONTRIBUTING.md` for the e2e architecture checklist and guardrails.

Run chaos profiles:

```bash
make run-chaos-latency
make run-chaos-fault
```

You can also control workers directly:

```bash
python -m reliabilitykit.cli.main run --workers 4 -- tests/e2e
python -m reliabilitykit.cli.main run --workers auto -- tests/e2e
```

Inspect and report:

```bash
make inspect
make trend
make report RUN_ID=<run_id>
```

All run outputs are written to `.reliabilitykit/` by default.

## CI Notes

Run records automatically include basic CI metadata when `CI` or `GITHUB_ACTIONS` is present.

- PR CI: `.github/workflows/ci.yml` runs unit tests on pull requests.
- Scheduled CI: `.github/workflows/ci-scheduled.yml` runs full Playwright e2e daily.

## Current Test Layout

- Unit tests: `tests/unit/` (includes golden snapshots and e2e architecture guardrails)
- E2E tests: `tests/e2e/tests/` (POM-driven, 51 scenarios)
- POM layers:
  - `tests/e2e/pages/`
  - `tests/e2e/components/`
  - `tests/e2e/flows/`
  - `tests/e2e/assertions/`
  - `tests/e2e/data/`
