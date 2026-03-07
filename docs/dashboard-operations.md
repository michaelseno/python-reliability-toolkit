# Dashboard Operations

The unified dashboard is generated from stored run JSON data.

## Generate Dashboard

```bash
reliabilitykit dashboard
reliabilitykit dashboard --window-days 30
make dashboard
```

Default output path:

- `.reliabilitykit/dashboard.html`

## View Dashboard Locally

If the dashboard is opened with `file://`, browser fetch restrictions can block lazy loading
of `run.json` files.

Serve the storage directory over HTTP:

```bash
python -m http.server -d .reliabilitykit 8000
# open http://localhost:8000/dashboard.html
```

## Data Dependencies

Dashboard content depends on:

- `.reliabilitykit/runs/**/run.json`
- `.reliabilitykit/index/runs_index.jsonl`

## CI vs Local

- Local: history accumulates in your workspace unless cleaned.
- CI: runner is ephemeral, so dashboard only reflects data present in that job unless prior
  history is restored from persistent storage first.

## Troubleshooting

- Empty history: verify `.reliabilitykit/index/runs_index.jsonl` exists.
- Missing per-test details under xdist runs: verify plugin collection behavior when workers are enabled.
- Stale UI: regenerate dashboard after new runs.
