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
   - fixed lane uses direct CLI command with stable per-profile seeds
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

- `fixed`: reproducible lane with per-profile stable seeds:
  - `latency_light=21`
  - `checkout_fault=7`
  - `rate_limit_burst=31`
  - `auth_expired=41`
  - `malformed_json=51`
  - `timeout_hang=61`
  - `resource_block=71`
  - `fail_hard=99`
- `daily`: deterministic rotating lane based on UTC date and profile

## Chaos Profile Rotation

Scheduled chaos campaign randomly selects one profile from the configured CI set:

- `latency_light`
- `checkout_fault`
- `rate_limit_burst`
- `auth_expired`
- `malformed_json`
- `timeout_hang`
- `resource_block`
- `fail_hard`

## Current Limitation

Each runner is ephemeral. Without external persistence, history is fragmented per run artifact.
See `docs/s3-architecture-plan.md` for persistent dashboard strategy.
