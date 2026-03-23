# Scheduled CI Workflow

This document describes `.github/workflows/ci-scheduled.yml` behavior.

## Trigger Model

- Scheduled cron: `0 0,5,10,15,20 * * *`
- Manual trigger: `workflow_dispatch`
- Manual input: `fault_injection_rate` (0-100, default `50`)
- Manual input: `workers` (pytest workers, default `4`)

## Execution Flow

1. Setup Python, uv, and Playwright Chromium
2. Decide run mode with randomized fault injection (`enable/profile/seed`) in shell step
3. Run one API reliability scan campaign (`--surface api --scan-pack core_reliability_scan`)
   - baseline when fault injection is disabled
   - fault-injected when enabled with randomized profile + seed
4. Generate trend and dashboard reports (`--window-days 30`)
5. Upload run artifacts to GitHub Actions artifacts

## Artifact Location

Artifacts are uploaded via `actions/upload-artifact` with name:

- `reliability-artifacts-${{ github.run_id }}`

Uploaded paths:

- `.reliabilitykit/`
- `artifacts/`
- `.pytest_cache/`

To inspect results, open the specific GitHub Actions run and download the artifact bundle.

## Fault Injection Profile Rotation

When enabled, scheduled campaign randomly selects one profile from this CI set:

- `latency_light`
- `checkout_fault`
- `rate_limit_burst`
- `auth_expired`
- `malformed_json`
- `timeout_hang`
- `fail_hard`

## Randomization Logic

- Each scheduled run rolls a random value.
- If roll `< fault_injection_rate`, run is fault-injected.
- If roll `>= fault_injection_rate`, run is baseline.
- Fault-injected runs randomize both profile and seed.

## Current Limitation

Each runner is ephemeral. Without external persistence, history is fragmented per run artifact.
See `docs/s3-architecture-plan.md` for persistent dashboard strategy.

## S3 Lifecycle Retention

For cost control, apply lifecycle policy to expire historical run artifacts while keeping dashboard/index current.

- Recommended retention for `runs/`: 90 days
- Transition `runs/` objects to Standard-IA after 30 days
- Abort incomplete multipart uploads after 7 days

Reference policy file:

- `docs/s3-lifecycle-policy.json`

Apply policy:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket rk-reliability \
  --lifecycle-configuration file://docs/s3-lifecycle-policy.json
```

Note:

- If retention is 90 days, keep trend windows at or below 90 days for complete analytics continuity.
