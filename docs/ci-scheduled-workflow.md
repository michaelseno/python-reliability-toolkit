# Scheduled CI Workflow

This document describes `.github/workflows/ci-scheduled.yml` behavior.

## Trigger Model

- Scheduled cron: `0 0,5,10,15,20 * * *`
- Manual trigger: `workflow_dispatch`
- Manual input: `seed_strategy` (`daily` or `fixed`)

## Execution Flow

1. Setup Python, uv, and Playwright Chromium
2. Decide chaos campaign (`enable/profile/seed`) in shell step
3. Run baseline reliability campaign
4. Optionally run chaos campaign
   - fixed lane uses Make targets with stable seeds
   - daily lane uses deterministic date+profile-derived seed
5. Generate trend report (`reliabilitykit trend --window-days 30`)
6. Upload run artifacts to GitHub Actions artifacts

## Artifact Location

Artifacts are uploaded via `actions/upload-artifact` with name:

- `reliability-artifacts-${{ github.run_id }}`

Uploaded paths:

- `.reliabilitykit/`
- `artifacts/`
- `.pytest_cache/`

To inspect results, open the specific GitHub Actions run and download the artifact bundle.

## Seed Lanes

- `fixed`: reproducible lane (`latency_light=21`, `checkout_fault=7`)
- `daily`: deterministic rotating lane based on UTC date and profile

## Current Limitation

Each runner is ephemeral. Without external persistence, history is fragmented per run artifact.
See `docs/s3-architecture-plan.md` for persistent dashboard strategy.
