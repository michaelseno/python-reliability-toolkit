# Implementation Plan

## 1. Feature Overview
Implement the backend/core/reporting/storage/retention portion of the manual/operator-assisted 48-Hour API Reliability Audit MVP.

## 2. Technical Scope
Add audit domain models and fail-closed validation, sanitized check execution metadata, HTML/CSV reporting, private S3 presigned artifact delivery helpers, 90-day retention ledger processing, SMTP environment-variable parsing and delivery, and operator CLI commands. Preserve the existing CLI-first toolkit and do not add customer-facing APIs or landing-page backend behavior.

## 3. Source Inputs
- `docs/architecture/api_reliability_audit_mvp_architecture.md`
- `docs/product/api_reliability_audit_mvp_spec.md`
- `docs/qa/api_reliability_audit_mvp_test_plan.md`
- `docs/release/api_reliability_audit_mvp_implementation_issue.md`
- Existing `reliabilitykit` CLI/core/reporting/storage/test conventions.

## 4. API Contracts Affected
No public or customer-facing backend API contracts are in MVP scope.

Operator-facing CLI commands will be added under `reliabilitykit audit` for validating configs, running one check cycle, generating reports, delivering via private S3 presigned URLs, creating retention records, and processing expired retention records.

## 5. Data Models / Storage Affected
- New audit models: `AuditConfig`, `AuditEndpoint`, `BearerAuthConfig`, `PrivacyPolicy`, `RetentionPolicy`, `EndpointAuditResult`, `AuditResult`, and `RetentionRecord`.
- Local sanitized workspace under `.reliabilitykit/audits/` and `.reliabilitykit/retention/` only.
- CSV contract exactly: `audit_id`, `check_cycle_id`, `endpoint_id`, `method`, `path`, `timestamp`, `status_code`, `available`, `latency_ms`, `expected_latency_ms`, `latency_status`, `error_category`, `error_summary`.
- Private S3 object upload/presign helper; no public ACL or permanent URL behavior.

## 6. Files Expected to Change
- `reliabilitykit/core/audit.py`
- `reliabilitykit/reporting/audit.py`
- `reliabilitykit/storage/local.py`
- `reliabilitykit/storage/s3.py`
- `reliabilitykit/storage/retention.py`
- `reliabilitykit/cli/commands/audit.py`
- `reliabilitykit/cli/main.py`
- Unit tests under `tests/unit/`
- Backend implementation documentation under `docs/backend/`

## 7. Security / Authorization Considerations
Production audits fail closed without waiver and internal approval references. Resilience/burst execution remains outside the standard workflow and is blocked without a separate approval reference. Bearer token values are read from runtime env vars only and are not serialized to models, reports, CSV, logs, S3 keys, emails, or errors. Raw bodies, raw headers, and trace logs are not stored by default; raw storage flags require a documented exception reference.

## 8. Dependencies / Constraints
No new required dependency will be added. S3 support will use optional `boto3` when available or an injected test/client object. SMTP uses Python standard-library `smtplib`/`email` and environment variables defined by the architecture.

## 9. Assumptions
- Initial and retention fallback presigned URL expiration defaults to 7 days where not specified; operators may override per command/helper.
- Latency equal to threshold is treated as `pass` because the observed latency is not greater than the client threshold.
- Endpoint identity normalizes HTTP method to uppercase and uses the provided path string as the path identity.
- Source sanitized metadata is retained after successful retention email because deletion/archive is explicitly open in the design.

## 10. Validation Plan
- `python -m pytest tests/unit/test_api_reliability_audit_mvp.py tests/unit/test_cli_commands.py tests/unit/test_storage_local.py`
- Broader unit suite if feasible: `python -m pytest tests/unit`
