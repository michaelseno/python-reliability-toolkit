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

## Documentation

- Docs index: `docs/README.md`
- Contributing guide: `docs/contributing.md`
- Scheduled CI workflow: `docs/ci-scheduled-workflow.md`
- Dashboard operations: `docs/dashboard-operations.md`
- Seed strategy: `docs/seed-strategy.md`
- S3 architecture plan: `docs/s3-architecture-plan.md`

Root-level UPPER_SNAKE_CASE files are compatibility stubs that point to canonical docs in `docs/`.

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

You can pass chaos and repeat options directly through `make run`:

```bash
make run RUN_CHAOS=latency_light RUN_SEED=21
make run RUN_REPEAT=5 RUN_PYTEST_ARGS="-m smoke -v"
```

The default e2e suite targets `https://practicesoftwaretesting.com` and currently contains 51 scenarios
covering positive, negative, and edge cases.

E2E tests follow a Page Object Model structure under `tests/e2e/` with separate `pages/`, `components/`,
`flows/`, `assertions/`, and `data/` modules to keep tests DRY and maintainable.

See `docs/contributing.md` for the e2e architecture checklist and guardrails.

Run chaos profiles:

```bash
reliabilitykit chaos list
reliabilitykit chaos show latency_light
reliabilitykit chaos show fail_hard
make chaos-profiles
make chaos-show CHAOS_PROFILE=latency_light
make run-chaos-latency
make run-chaos-fault
make run-chaos-ci-latency
make run-chaos-ci-fault
```

`run-chaos-ci-*` targets are fixed-seed CI lane commands for reproducible chaos triage.
`fail_hard` is an intentionally aggressive profile (`abort`, probability `1.0`) intended for
failure-path validation.

You can also control workers directly:

```bash
python -m reliabilitykit.cli.main run --workers 4 -- tests/e2e
python -m reliabilitykit.cli.main run --workers auto -- tests/e2e
```

Inspect and report:

```bash
make inspect
make dashboard
make trend
make report RUN_ID=<run_id>
make clean-data
```

`make dashboard` is the primary report surface and combines latest-run triage with historical trends.
`make trend` now generates a compatibility redirect to `dashboard.html`.
`make report` remains available for focused single-run deep dives.

Dashboard UX is single-page:

- left sidebar run history with timeframe filters (`7d`, `14d`, `30d`, `90d`, `all`)
- run sidebar pagination (`Load more` in batches of 50)
- top analytics with failure-type donut and trend chart
- least-reliable top 10 table
- selected run test table with expandable error details and screenshots

All run outputs are written to `.reliabilitykit/` by default.

## CLI Usage

ReliabilityKit ships with built-in command help via Typer:

```bash
reliabilitykit --help
reliabilitykit run --help
reliabilitykit dashboard --help
```

Common workflows:

```bash
# baseline run
reliabilitykit run -- tests/e2e

# chaos run
reliabilitykit chaos list
reliabilitykit chaos show latency_light
reliabilitykit run --chaos latency_light --seed 21 -- tests/e2e -m chaos

# inspect latest failed runs
reliabilitykit inspect --status failed --last 20

# inspect as JSON (includes run reliability score)
reliabilitykit inspect --status failed --last 20 --json

# unified dashboard (latest + trends)
reliabilitykit dashboard --window-days 14

# open dashboard automatically
reliabilitykit dashboard --open

# repeat full run N times regardless of pass/fail
reliabilitykit run --repeat 5 -- tests/e2e -m smoke
```

Note: dashboard lazy-loads `run.json` from the run table. If you open dashboard from
`file://`, browser fetch restrictions may block on-demand loading. Serve `.reliabilitykit/`
locally and open dashboard via HTTP:

```bash
python -m http.server -d .reliabilitykit 8000
# then open http://localhost:8000/dashboard.html
```

## Reliability Engine Signals

Trend and dashboard views now include reliability scoring:

- **Run reliability score** (0-100): weighted by run pass rate, test reliability history,
  and failure severity, with extra penalty for chaos-run failures.
- **Test reliability score** (0-100): weighted by historical pass rate, flake rate,
  chaos sensitivity, and duration stability.
- **Flake rate**: percentage of pass/fail status transitions for a test across executions.
- **Chaos sensitivity**: additional failure rate under chaos vs baseline.
- **Failure diversity**: count of distinct failure types seen for the same test.

## Seed Convention

Use a two-lane seed strategy so runs are both reproducible and exploratory:

- **CI lane (fixed seeds):** use stable per-profile seeds for reproducible PR triage.
  - `latency_light -> 21`
  - `checkout_fault -> 7`
  - Make targets: `run-chaos-ci-latency`, `run-chaos-ci-fault`
- **Scheduled lane (rotating deterministic seeds):** use a date-based seed derived from
  `YYYYMMDD + profile` so each day explores a new pattern, but reruns on the same day/profile
  stay reproducible.
- **Local debugging:** pin one seed while diagnosing (`--seed 21`), then vary seed values
  for robustness sweeps (`--seed 22`, `--seed 23`, ...).

Quick examples:

```bash
# reproducible CI-like run
reliabilitykit run --chaos latency_light --seed 21 -- tests/e2e -m chaos

# robustness sweep
reliabilitykit run --chaos latency_light --seed 21 --repeat 3 -- tests/e2e -m chaos
reliabilitykit run --chaos latency_light --seed 22 --repeat 3 -- tests/e2e -m chaos
```

## CI Notes

Run records automatically include basic CI metadata when `CI` or `GITHUB_ACTIONS` is present.

- PR CI: `.github/workflows/ci.yml` runs unit tests on pull requests.
- Scheduled CI: `.github/workflows/ci-scheduled.yml` runs full Playwright e2e and supports
  workflow dispatch seed strategy input (`daily` or `fixed`).

## Current Test Layout

- Unit tests: `tests/unit/` (includes golden snapshots and e2e architecture guardrails)
- E2E tests: `tests/e2e/tests/` (POM-driven, 51 scenarios)
- POM layers:
  - `tests/e2e/pages/`
  - `tests/e2e/components/`
  - `tests/e2e/flows/`
  - `tests/e2e/assertions/`
  - `tests/e2e/data/`
