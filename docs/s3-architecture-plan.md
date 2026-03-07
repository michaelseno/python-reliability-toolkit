# S3 Architecture Plan

This plan adds persistent reliability history and a continuously updated dashboard.

## Goal

- Persist CI run outputs outside ephemeral runners
- Generate a durable dashboard from accumulated history
- Start with public-read S3, migrate later to private bucket + CloudFront

## Target Flow

1. CI runs tests and writes `.reliabilitykit/` locally
2. CI uploads canonical run outputs to S3
3. S3 event triggers dashboard build (Lambda)
4. Lambda rebuilds `dashboard.html` from full history in S3
5. Static dashboard is served from S3 website endpoint
6. SNS/SES notifies on new run ingestion and dashboard build status

## S3 Layout (suggested)

- `s3://<bucket>/reliabilitykit/runs/YYYY/MM/DD/<run_id>/run.json`
- `s3://<bucket>/reliabilitykit/index/runs_index.jsonl`
- `s3://<bucket>/reliabilitykit/dashboard.html`
- `s3://<bucket>/reliabilitykit/metadata/latest.json`

## Implementation Phases

### Phase 1: Persistence

- Add AWS OIDC auth in GitHub Actions
- Sync `.reliabilitykit/` to S3 after each scheduled run
- Keep GitHub artifact upload as backup

### Phase 2: Automated Dashboard Build

- Create Python Lambda that rebuilds dashboard from S3 history
- Trigger on `run.json` object create events
- Publish dashboard to S3 static location

### Phase 3: Notifications

- SNS topic for ingest/build events
- Email subscription via SES/SNS

### Phase 4: Security Hardening

- Move from public-read bucket to private bucket + CloudFront
- Use Origin Access Control and signed access policy as needed

## Operational Notes

- Add workflow concurrency guard to avoid overlapping writes.
- Enable S3 versioning and lifecycle policies.
- Keep HTML cache TTL low; historical run objects can be immutable.
