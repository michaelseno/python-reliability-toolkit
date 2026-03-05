# ReliabilityKit

ReliabilityKit is a local-first reliability execution layer for Python Playwright + pytest.
It wraps test execution and emits structured run records, artifacts, failure classifications,
and HTML reports so every run becomes analyzable data.

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

Run chaos profiles:

```bash
make run-chaos-latency
make run-chaos-fault
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
