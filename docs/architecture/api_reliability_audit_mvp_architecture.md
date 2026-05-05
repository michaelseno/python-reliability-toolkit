# Technical Design

## 1. Feature Overview

**Title:** 48-Hour API Reliability Audit MVP Technical Design  
**Status:** Authorized for full MVP implementation on branch `feature/api_reliability_audit_mvp`  
**Source Product Spec:** `docs/product/api_reliability_audit_mvp_spec.md`  
**Repository:** `python_reliability_toolkit`  
**Scope Type:** Manual/operator-assisted MVP, not SaaS

This document is the implementation-ready architecture for the API Reliability Audit MVP. It replaces prior planning-only language. Downstream implementation must preserve the manual/operator-assisted service boundary and must not introduce SaaS onboarding, customer accounts, login, payment, backend lead capture, or self-service audit configuration.

The MVP audits up to 10 unique `METHOD + PATH` endpoints over approximately 10 check cycles across 48 hours, produces a static HTML report/dashboard and sanitized CSV export, delivers artifacts through private S3 presigned URLs, retains sanitized metadata for 90 days, then automatically emails a sanitized post-retention CSV through SMTP configured by environment variables.

## 2. Product Requirements Summary

- Standard audit supports up to 10 unique `METHOD + PATH` endpoints.
- Default duration is 48 hours with 5 checks per day, approximately 10 total check cycles; `checks_per_day` is configurable from 1 through 24, values above 5 require an operator/client agreement reference, and expected cycles reconcile to the configured frequency over 48 hours.
- Bearer token authentication is the first supported auth method and bearer tokens must never appear in reports, CSV exports, logs, or customer-facing artifacts.
- Production testing requires written client waiver/agreement and completed internal approval checklist before execution.
- Default persisted data is sanitized metadata only: audit/check identifiers, endpoint identifier, method, path, timestamp, status code, availability result, latency, threshold where provided, latency status where allowed, and sanitized error/category metadata.
- Raw logs, raw responses, raw response bodies, raw headers, trace logs, and stack traces are transient and must not be displayed or persisted by default.
- Raw diagnostic artifact collection, report inclusion/display, or persistence requires explicit written client demand plus written approval/reference and is outside the default workflow.
- Reports consist of a static HTML report/dashboard and sanitized CSV export.
- Report delivery must use private S3 presigned URLs; public permanent report URLs are prohibited.
- Sanitized metadata must be retained for 90 days, then exported to CSV and emailed to the client through automated SMTP environment-variable configuration.
- Resilience/burst testing is optional, outside the standard workflow, and requires separate written approval.
- Phase 1 landing page is static and informational only. CTA text must be exactly `Request a Reliability Audit` and CTA destination must be `#request-audit`.

## 3. Requirement-to-Architecture Mapping

| Product Requirement / Acceptance Criterion | Technical Responsibility |
| --- | --- |
| FR-1, AC-1 endpoint cap and uniqueness | Core audit validator normalizes endpoint identity as uppercase `METHOD + PATH` and fails closed above 10 unique identities. |
| FR-2, AC-12 48-hour schedule | CLI/operator workflow supports configured run metadata for 48 hours, default 5 checks/day, configurable 1-24 checks/day, expected cycles reconciled to frequency, and agreement-reference gating above 5; scheduler remains operator-controlled. |
| FR-3, AC-4 bearer token handling | Core/auth boundary accepts bearer token via sensitive runtime input or secret reference; reporting/storage/logging contracts exclude token values. |
| FR-4, AC-2, AC-3 production authorization | Core validation requires waiver and internal approval references before production execution. |
| FR-5, AC-6 sanitized collection only | Execution derives allowed metadata and discards raw logs, raw responses, body/header/trace data, and stack traces without writing them to local disk, S3, CSV, reports, or logs by default. |
| FR-7, AC-11 latency thresholds | Reporting labels latency pass/fail only when `expected_latency_ms` exists; otherwise it displays observed latency only. |
| FR-8, FR-10, AC-8 report/CSV | Reporting generates static HTML and sanitized CSV using the CSV contract in this document. |
| FR-9, AC-5 private delivery | Storage uploads artifacts to private S3 and returns time-limited presigned URLs only. |
| FR-11, AC-9 retention email | Retention component tracks expiry, exports retained sanitized metadata to CSV, and sends it through SMTP configured by environment variables; failures are surfaced for operator remediation. |
| FR-12, AC-10 optional resilience/burst | Chaos/resilience paths remain outside the standard audit workflow and require separate written approval reference. |
| FR-13, AC-13 static landing page | Static frontend contains required informational sections, exact CTA text, and `#request-audit` href with no backend behavior. |

## 4. Technical Scope

### Current Technical Scope

- Operator-assisted audit configuration, validation, execution metadata, reporting, private delivery, and retention automation.
- CLI/local-first workflow aligned with existing `reliabilitykit` package patterns.
- Data contracts for audit config, endpoint definitions, bearer auth references, privacy policy, sanitized results, report artifacts, retention jobs, and SMTP delivery attempts.
- Static HTML report/dashboard and sanitized CSV generation.
- Private S3 artifact upload and presigned URL generation.
- Automated 90-day post-retention CSV email delivery through SMTP environment variables.
- Static landing page with informational content only and CTA `Request a Reliability Audit` linking to `#request-audit`.

### Out of Scope

- Public/customer backend APIs for intake, lead capture, payment, login, accounts, or self-service audit configuration.
- Landing-page form submission, email submission flow, backend lead capture, or payment initiation.
- Automated contract signing or automated authorization verification.
- Schema validation.
- Non-bearer auth standardization, except manual operator handling outside MVP.
- Default load/resilience/burst testing.
- Public S3 objects or permanent unauthenticated URLs.
- Additional endpoint pricing implementation.

### Future Technical Considerations

- Automated intake UI, customer accounts, payments, and managed monitoring only after MVP validation.
- Expanded auth methods and schema validation if validated by customer demand.
- More formal job queue for retention processing if local scheduler/cron is insufficient.
- Private CloudFront signed URLs/cookies if S3 presigned URLs become operationally limiting.

## 5. Architecture Overview

The MVP is a bounded operator workflow, not a SaaS service:

1. **Static offer discovery:** visitor views static landing page and uses CTA `Request a Reliability Audit` linking to `#request-audit` only.
2. **Manual intake:** operator collects endpoint list, bearer auth details, thresholds, client email, environment, waiver/approval evidence, and optional burst/resilience approval status outside the website.
3. **Audit configuration:** operator creates an `AuditConfig` with endpoint scope, auth reference, schedule, privacy policy, reporting/delivery settings, retention settings, and evidence references.
4. **Pre-run validation:** core validation fails closed for endpoint cap, duplicates, production approval, raw-data exception requirements, and optional resilience/burst approval.
5. **Scheduled execution:** operator-controlled scheduler/cron/manual process runs approximately 10 check cycles. Execution writes sanitized metadata only.
6. **Reporting:** reporting builds a static HTML dashboard and sanitized CSV from sanitized metadata.
7. **Private delivery:** storage uploads artifacts to private S3 keys and generates time-limited presigned URLs for operator/customer delivery.
8. **Retention:** retention records expiry at 90 days from audit completion or configured retention start.
9. **Post-retention export:** retention automation exports retained sanitized metadata to CSV and emails it to the client via SMTP environment variables. If SMTP delivery fails, failure is logged/surfaced without secrets and remains pending for operator remediation.

## 6. System Components

### Backend / CLI Component Responsibilities

#### `reliabilitykit/cli/`

- Provides operator-facing commands for audit configuration validation, check execution orchestration, report generation, private delivery, and retention processing.
- Must not expose public/customer HTTP APIs.
- Must display actionable validation and delivery errors without printing secrets.

#### `reliabilitykit/core/`

- Owns audit-domain contracts and validation: `AuditConfig`, `AuditEndpoint`, `BearerAuthConfig`, `PrivacyPolicy`, result models, endpoint counting, approval gates, latency threshold rules, and no-raw persistence policy.
- Owns execution-facing result normalization and sanitized error categorization.
- Must keep bearer token values out of serializable/customer-facing models.

#### `reliabilitykit/reporting/`

- Generates static HTML report/dashboard and sanitized CSV from sanitized result models only.
- Applies latency labels only when thresholds are present.
- Must not read or render raw response bodies, raw headers, traces, bearer tokens, or secret references.
- Must support both initial CSV export and post-retention CSV export using the same sanitized CSV column contract.

#### `reliabilitykit/storage/`

- Owns local sanitized workspace behavior, private S3 artifact upload, and presigned URL generation.
- Must configure report objects as private and must not use public-read ACLs or public static website URLs.
- Should use immutable object keys including `audit_id` and generation timestamp unless an operator intentionally regenerates artifacts.

#### Retention Automation Boundary

- May be implemented as CLI command plus scheduler/cron, or another repository-local automation entrypoint, but must be automated rather than manually sent.
- Identifies audits whose sanitized metadata retention has expired.
- Generates a sanitized CSV, chooses attachment or private S3 presigned-link delivery based on configured size/operational constraints, sends SMTP email, records delivery status, and surfaces failure for operator remediation.

#### Static Frontend Boundary

- Static landing page only.
- Required sections: hero, value proposition, what is included, privacy/safety guarantees, pricing, how it works, FAQ, and CTA.
- CTA text exactly `Request a Reliability Audit`; href exactly `#request-audit`.
- No forms, no backend API calls, no email submission flow, no login, no payment.

## 7. Data Models

## AuditConfig

### Purpose

Defines one client audit.

### Primary Key

- `audit_id`: unique operator-generated identifier.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Unique audit identifier. |
| `client_name` | string | Client display name. |
| `client_email` | string | Client address for delivery and post-retention CSV. |
| `environment` | enum | `production`, `staging`, `development`, or `other`. |
| `production_waiver_reference` | string/null | Required for production. Reference only; not the waiver contents. |
| `internal_approval_reference` | string/null | Required for production. Reference only. |
| `endpoints` | list[`AuditEndpoint`] | Up to 10 unique endpoint definitions. |
| `auth` | `BearerAuthConfig`/null | Bearer auth reference. |
| `schedule_duration_hours` | integer | Default `48`. |
| `checks_per_day` | integer | Default `5`. |
| `expected_check_cycles` | integer | Default `10`. |
| `check_frequency_agreement_reference` | string/null | Required when `checks_per_day` exceeds default `5`; reference only, not customer-facing. |
| `privacy_policy` | `PrivacyPolicy` | Raw-data and retention policy. |
| `resilience_burst_requested` | boolean | Whether optional add-on was requested. |
| `resilience_burst_approval_reference` | string/null | Required before any optional resilience/burst execution. |
| `report_artifact_prefix` | string | Private S3 prefix for artifacts. |
| `retention` | `RetentionPolicy` | 90-day metadata retention and post-retention delivery settings. |
| `created_at` | datetime | Creation timestamp. |

### Ownership Model

Scoped to one client audit. Operators may access under internal procedures. Customer-facing outputs exclude secrets and raw data.

### Lifecycle

Created during manual intake, validated before execution, used for execution/reporting/delivery/retention, then retained according to policy. Secret values should be runtime-only or stored in an operator-managed secret store, not serialized into reports/CSV.

## AuditEndpoint

### Purpose

Defines one audited endpoint and optional latency threshold.

### Primary Key

- Composite identity: uppercase `method + path` within an audit.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `endpoint_id` | string | Stable row/report identifier. |
| `method` | enum/string | HTTP method; normalized uppercase. |
| `path` | string | Endpoint path. |
| `base_url` | string | Target base URL. |
| `expected_latency_ms` | integer/null | Optional threshold. Null means observed-only reporting. |
| `enabled` | boolean | Included in audit when true. |
| `notes` | string/null | Operator-only, must not include secrets. |

### Ownership Model

Scoped to one `AuditConfig`.

### Lifecycle

Created during intake. Changes after execution starts require operator notation and re-validation.

## BearerAuthConfig

### Purpose

Defines how bearer token auth is provided to runtime checks without exposing token values.

### Primary Key

- Associated with `audit_id` or an operator-managed secret reference.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `auth_type` | enum | Must be `bearer_token` for MVP standard support. |
| `token_secret_reference` | string | Runtime env var name or secret-store reference; never rendered in customer artifacts. |
| `header_name` | string | Default `Authorization`. |
| `token_prefix` | string | Default `Bearer`. |

### Ownership Model

Sensitive operator-held credential scoped to the audit.

### Lifecycle

Provided during intake, used during execution, excluded from reports/CSV/logs, rotated/revoked per client agreement.

## PrivacyPolicy

### Purpose

Captures audit-specific privacy and raw-data exception posture.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `store_raw_bodies` | boolean | Default `false`; true only with written exception. |
| `store_raw_headers` | boolean | Default `false`; true only with written exception. |
| `store_trace_logs` | boolean | Default `false`; true only with written exception. |
| `collect_raw_logs`, `include_raw_logs`, `persist_raw_logs` | boolean | Default `false`; true only with explicit client request and written approval/reference. |
| `collect_raw_responses`, `include_raw_responses`, `persist_raw_responses` | boolean | Default `false`; true only with explicit client request and written approval/reference. |
| `collect_stack_traces`, `include_stack_traces`, `persist_stack_traces` | boolean | Default `false`; true only with explicit client request and written approval/reference. |
| `raw_data_exception_reference` | string/null | Required if any raw storage flag is true. |
| `raw_data_written_demand_reference` | string/null | Required if any raw diagnostic artifact collection, inclusion, or persistence flag is true. |
| `sanitized_metadata_retention_days` | integer | Must be `90`. |

### Ownership Model

Scoped per audit.

### Lifecycle

Created before execution; raw-data flags fail closed unless explicit client request and written approval/reference exist.

## AuditResult / EndpointAuditResult

### Purpose

Stores sanitized observations and report artifact references.

### Primary Key

- `AuditResult`: `audit_id` plus generated run/result identifier.
- `EndpointAuditResult`: `audit_id + check_cycle_id + endpoint_id + timestamp`.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Parent audit. |
| `check_cycle_id` | string/integer | Cycle identifier. |
| `endpoint_id` | string | Endpoint identifier. |
| `method` | string | HTTP method. |
| `path` | string | Endpoint path. |
| `timestamp` | datetime | Observation time. |
| `status_code` | integer/null | HTTP status if available. |
| `available` | boolean | Availability result. |
| `latency_ms` | integer/float/null | Observed latency. |
| `expected_latency_ms` | integer/null | Threshold if provided. |
| `latency_status` | enum/null | `pass`/`fail` only when threshold exists; otherwise blank/`observed_only`. |
| `error_category` | string/null | Sanitized category. |
| `error_summary` | string/null | Sanitized non-sensitive summary. |
| `report_html_s3_key` | string/null | Private S3 key, result-level only. |
| `csv_s3_key` | string/null | Private S3 key, result-level only. |
| `retention_expires_at` | datetime | 90-day expiry. |

### Ownership Model

Scoped to client audit and exportable only if sanitized.

### Lifecycle

Created per check, included in report/CSV, retained for 90 days, then exported through retention workflow.

## CSV Export Contract

### Purpose

Defines both initial and post-retention sanitized CSV exports.

### Fields / Columns

`audit_id`, `check_cycle_id`, `endpoint_id`, `method`, `path`, `timestamp`, `status_code`, `available`, `latency_ms`, `expected_latency_ms`, `latency_status`, `error_category`, `error_summary`.

### Explicitly Excluded

Bearer tokens, authorization headers, raw request/response bodies, raw headers, trace logs, stack traces containing request details, unredacted payloads, and secret references that reveal credential location.

## RetentionRecord

### Purpose

Tracks 90-day retention state and post-retention CSV email automation.

### Primary Key

- `audit_id` plus `retention_expires_at`.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Parent audit. |
| `client_email` | string | Recipient for post-retention CSV. |
| `metadata_location` | string | Sanitized metadata location only. |
| `retention_started_at` | datetime | Usually audit completion time. |
| `retention_expires_at` | datetime | `retention_started_at + 90 days`. |
| `export_csv_path_or_key` | string/null | Generated sanitized post-retention CSV location. |
| `delivery_mode` | enum | `attachment` or `presigned_s3_link`. |
| `delivery_status` | enum | `pending`, `sent`, `failed`, `retry_pending`. |
| `last_attempt_at` | datetime/null | Last SMTP attempt. |
| `last_error_category` | string/null | Sanitized failure category. |
| `attempt_count` | integer | Number of SMTP attempts. |

### Ownership Model

Operator-owned operational metadata scoped to a client audit. Must not contain SMTP password, bearer token, raw API data, or message bodies containing secrets.

### Lifecycle

Created when audit completes. Processed when retention expires. Marked `sent` after SMTP success or `failed`/`retry_pending` after sanitized failure. Source metadata deletion/archive after successful export remains an open operational decision unless separately confirmed.

## SmtpDeliveryConfig

### Purpose

Defines environment-variable based SMTP configuration for automated post-retention CSV delivery.

### Environment Variable Contract

| Environment Variable | Required | Description |
| --- | --- | --- |
| `RELIABILITYKIT_SMTP_HOST` | yes | SMTP server hostname. |
| `RELIABILITYKIT_SMTP_PORT` | yes | SMTP server port, integer. |
| `RELIABILITYKIT_SMTP_USERNAME` | conditional | SMTP username when server requires authentication. |
| `RELIABILITYKIT_SMTP_PASSWORD` | conditional | SMTP password/app password; secret; never logged. |
| `RELIABILITYKIT_SMTP_FROM_EMAIL` | yes | Sender address for retention emails. |
| `RELIABILITYKIT_SMTP_FROM_NAME` | no | Display name; default may be product/service name. |
| `RELIABILITYKIT_SMTP_USE_TLS` | yes | `true`/`false` for STARTTLS. |
| `RELIABILITYKIT_SMTP_USE_SSL` | yes | `true`/`false` for implicit SSL. Must not conflict with TLS. |
| `RELIABILITYKIT_SMTP_TIMEOUT_SECONDS` | no | SMTP connect/send timeout. |
| `RELIABILITYKIT_RETENTION_FAILURE_NOTIFY_EMAIL` | yes | Operator/remediation recipient for delivery failures. |
| `RELIABILITYKIT_RETENTION_MAX_ATTACHMENT_MB` | no | Attachment size threshold; above it use private S3 presigned link. |

### Validation Rules

- Missing required SMTP variables must fail the retention email attempt and surface operator remediation.
- `RELIABILITYKIT_SMTP_PORT` and timeout/size values must parse as positive numbers.
- `RELIABILITYKIT_SMTP_USE_TLS` and `RELIABILITYKIT_SMTP_USE_SSL` must not both be true.
- Authentication credentials must be required only when the chosen SMTP server needs auth; if provided, they are secret values and must be redacted from logs/exceptions.

## 8. API Contracts

No public or customer-facing backend API contracts are in MVP scope. The landing page must not call backend services. Audit operations are CLI/local workflow and external integrations.

### External Integration Contract: Private S3 Presigned Report Delivery

#### Purpose

Privately deliver initial HTML report/dashboard and sanitized CSV artifacts.

#### Authentication / Authorization

- Operator/automation uses AWS credentials with least-privilege permissions for private object upload and presigned URL generation.
- Client access is limited to presigned URL validity.

#### Inputs

- Local sanitized artifact paths.
- Private S3 bucket.
- Object keys under audit-specific prefix.
- Presigned URL expiration duration.

#### Outputs

- Time-limited presigned URL for HTML report.
- Time-limited presigned URL for sanitized CSV.

#### Error Conditions

Missing artifact, upload failure, missing/invalid AWS credentials, insufficient IAM permission, presign failure, expired URL.

#### Side Effects

Writes private S3 objects and produces URLs for delivery.

#### Idempotency / Duplicate Handling

Prefer immutable object keys with `audit_id` and generated timestamp. Re-upload to same key only when operator intentionally regenerates a final artifact.

### External Integration Contract: Post-Retention CSV SMTP Email

#### Purpose

Automatically email the sanitized post-retention CSV to the client after 90-day retention expires.

#### Authentication / Authorization

- SMTP credentials come only from environment variables.
- SMTP password and username are operator/system secrets and must not appear in customer artifacts, CSV, logs, tracebacks, or failure notifications.

#### Inputs

- `RetentionRecord` with expired `retention_expires_at`.
- Sanitized metadata for the audit.
- Client recipient email from `AuditConfig`/`RetentionRecord`.
- SMTP config from `RELIABILITYKIT_*` environment variables.

#### Request / Message Contract

- Recipient: `client_email`.
- Sender: `RELIABILITYKIT_SMTP_FROM_EMAIL` and optional `RELIABILITYKIT_SMTP_FROM_NAME`.
- Subject: must identify the audit and state that the sanitized retention CSV is attached or linked; must not include secrets.
- Body: concise operator-approved text; must not include raw API data, bearer token values, SMTP config, stack traces, or internal secret references.
- Payload: sanitized CSV only, either attached or linked through private S3 presigned URL.

#### CSV Attachment or Link Behavior

- Default delivery mode should be direct CSV attachment when generated CSV size is at or below `RELIABILITYKIT_RETENTION_MAX_ATTACHMENT_MB` or implementation default.
- If CSV exceeds the configured threshold, or if SMTP provider attachment limits are likely to reject it, upload the sanitized CSV to private S3 and email a time-limited presigned URL instead of attaching the file.
- Whether attached or linked, the CSV content must use the same sanitized CSV export contract and must exclude bearer tokens, authorization headers, raw bodies, raw headers, and traces.
- Presigned-link mode must use private S3 objects; public links are prohibited.

#### Success Status

- Mark `RetentionRecord.delivery_status = sent` only after SMTP send succeeds.

#### Error Status / Failure Conditions

- Missing or invalid SMTP config.
- SMTP connection timeout.
- Authentication failure.
- Recipient rejection.
- Attachment size rejection.
- S3 upload/presign failure in link mode.
- Unexpected send error.

#### Failure Surfacing / Logging

- Failures must not silently succeed.
- Log/surface audit ID, recipient domain or redacted recipient, delivery mode, sanitized error category, and remediation hint.
- Do not log SMTP password, full SMTP URL with credentials, bearer token, raw API data, CSV contents, stack traces containing secrets, or full environment dumps.
- Notify or expose failure to `RELIABILITYKIT_RETENTION_FAILURE_NOTIFY_EMAIL` when configured; that notification must contain sanitized diagnostic information only.
- Failed delivery should remain retryable with status `failed` or `retry_pending` and `attempt_count` incremented.

#### Idempotency / Duplicate Handling

- Re-running retention processing for an already `sent` record must not resend unless an explicit operator override is provided.
- Re-running for `failed`/`retry_pending` records may retry using the same sanitized CSV or regenerate it deterministically from retained sanitized metadata.

## 9. Frontend Impact

### Components Affected

- New/static Phase 1 product landing page.
- Generated static HTML audit report/dashboard.

### API Integration

- Landing page: none.
- Report/dashboard: no backend API. CSV is a static artifact link/download from private S3 presigned URL or relative artifact link before upload.

### UI States

#### Landing Page

- Static informational state only.
- Required sections: hero, problem/value proposition, what is included, privacy/safety guarantees, pricing, how it works, FAQ, CTA.
- CTA text exactly `Request a Reliability Audit`.
- CTA href exactly `#request-audit`.
- No loading, authenticated, payment, form-submission, email-submission, or lead-capture state.

#### HTML Report/Dashboard

- Completed audit summary.
- Endpoint-level availability/status/latency tables.
- Observed-only latency state when thresholds are absent.
- Threshold pass/fail labels only when expected thresholds exist.
- Sanitized CSV access.
- No bearer tokens, raw bodies, raw headers, or traces.

## 10. Backend Logic

### Responsibilities

- Validate audit configuration before execution.
- Enforce endpoint cap and uniqueness.
- Enforce production authorization and optional resilience/burst approval gates.
- Execute bounded scheduled checks through operator-run/local tooling.
- Derive and persist sanitized metadata only.
- Generate static HTML and sanitized CSV artifacts.
- Upload artifacts to private S3 and generate presigned URLs.
- Track 90-day retention and automatically email post-retention sanitized CSV via SMTP.

### Validation Flow

1. Load `AuditConfig`.
2. Normalize endpoint identity as uppercase `METHOD + PATH`.
3. Reject more than 10 unique identities.
4. Reject duplicates unless de-duplicated before execution.
5. If `environment = production`, require `production_waiver_reference` and `internal_approval_reference`.
6. If resilience/burst execution is requested, require `resilience_burst_approval_reference`; otherwise keep it out of the standard run path.
7. Validate bearer token is referenced as sensitive runtime input/secret reference and is not serialized into output models.
8. Validate privacy policy: raw bodies, raw headers, traces, raw logs, raw responses, and stack traces default false; any collection, inclusion/display, or persistence flag requires explicit client request and written approval/reference.
9. Validate report delivery bucket/key configuration is private/presigned only.
10. Validate retention email SMTP config before attempting post-retention send.

### Business Rules

- Testing fails closed when production approvals are incomplete.
- Standard audit must not exceed 10 unique `METHOD + PATH` endpoints.
- Default check frequency is 5/day for 48 hours; configurable frequency is bounded to 1-24/day, values above 5/day require an operator/client agreement reference, and expected cycles must match the configured frequency over 48 hours.
- Latency pass/fail labels require client thresholds.
- CSV exports contain sanitized metadata only.
- Reports use private S3 presigned delivery only.
- Post-retention CSV delivery is automated through environment-variable SMTP configuration.

### Persistence Flow

- During execution, write only sanitized metadata.
- Raw logs, raw responses, raw response bodies, raw headers, traces, and stack traces are discarded after deriving allowed fields by default and are not included in reports, CSV exports, local persisted artifacts, S3 artifacts, or retention exports.
- Store finalized report artifacts in private S3.
- Retain sanitized metadata for 90 days.
- At expiry, generate sanitized CSV and deliver via SMTP as attachment or private S3 presigned link.
- Source metadata deletion/archive after successful post-retention email remains an open question because the spec requires export/email after 90 days but does not explicitly define deletion behavior.

### Error Handling

- Configuration validation errors block execution with operator-actionable messages.
- Endpoint check failures become sanitized rows where possible.
- Network timeouts are categorized without storing traces.
- Report generation failures block delivery.
- S3 failures require retry/regeneration by operator/automation.
- SMTP failures must be surfaced in sanitized logs/status and must not expose secrets.

## 11. File Structure

Implementation should extend existing repository boundaries without introducing a SaaS service:

```text
docs/architecture/api_reliability_audit_mvp_architecture.md   # this implementation-ready design
docs/product/api_reliability_audit_mvp_spec.md                # source product spec
reliabilitykit/cli/                                           # operator commands for audit workflow and retention processing
reliabilitykit/core/                                          # audit contracts, validation, execution normalization
reliabilitykit/reporting/                                     # static HTML and sanitized CSV generation
reliabilitykit/storage/                                       # local sanitized workspace, private S3, presigned URLs
.reliabilitykit/                                              # local sanitized run/report workspace; no raw bodies/headers/traces
<static-site-path>/                                           # static landing page location, to follow repo convention
```

## 12. Security

### Authentication

- Bearer token auth is supported first.
- Bearer tokens are confidential secrets and should be provided through runtime environment variable, local secret store, or operator-managed secret reference.
- SMTP credentials are confidential secrets loaded from environment variables only.

### Authorization

- Production testing requires written client waiver and completed internal approval before execution.
- Optional resilience/burst testing requires separate written approval.
- S3 report and retention CSV objects must be private; client access is through presigned URLs only.

### Input Validation

- Validate endpoint count, method/path uniqueness, URL/method shape, threshold type, approval references, raw-data exception references, S3 config, and SMTP config.

### Misuse Risks

- Running against production without approval.
- Leaking bearer tokens via reports, CSV, logs, CLI output, tracebacks, or emails.
- Persisting raw response bodies/headers/traces in local workspace or S3.
- Accidentally using public S3 ACLs or public static website delivery for reports.
- Treating resilience/burst testing as part of the standard audit.
- Emailing post-retention CSV to the wrong address or exposing SMTP secrets in failure handling.

### Required Controls

- Fail-closed pre-run safety checklist.
- Redaction checks for generated HTML, CSV, email body, and logs.
- Private S3 bucket policy and least-privilege IAM.
- Environment-variable secret redaction in all errors/logs.
- Delivery status ledger for initial report delivery and post-retention email.

## 13. Reliability

### Retries

- Endpoint checks should avoid aggressive retries that distort audit measurements; any retry behavior must be visible in reporting if implemented.
- S3 upload/presign and SMTP delivery may retry on transient failures with sanitized failure state.
- Retention retry must not duplicate successful client emails unless explicitly overridden.

### Timeouts

- Endpoint request timeout default remains an implementation-time setting and should be documented in report metadata.
- SMTP timeout should come from `RELIABILITYKIT_SMTP_TIMEOUT_SECONDS` or a safe implementation default.

### Failure Modes

- Missed scheduled cycle: record gap and surface to operator/report summary if material.
- Partial endpoint failure: record sanitized endpoint result without aborting full cycle unless safety requires stop.
- Credential failure: classify as auth failure without token disclosure.
- Report generation failure: block delivery until regenerated.
- Expired S3 URL: regenerate if artifact is still authorized/available.
- Missing SMTP config at retention expiry: mark failed/retry pending and notify/surface operator remediation without secrets.
- SMTP send failure: sanitized failure record and retryable status.

### Logging / Monitoring

- Logs may include audit ID, cycle ID, endpoint ID, status category, delivery mode, and sanitized error category.
- Logs must not include bearer tokens, authorization headers, raw bodies, raw headers, trace logs, SMTP password, full environment dumps, or CSV contents.
- Maintain an operational ledger/checklist for cycle completion, report delivery, retention expiry, and retention email status.

### Performance Considerations

- Bounded workload: up to 10 endpoints x approximately 10 cycles.
- Checks should be sequential or modestly parallel to avoid unintended load.
- Retention CSV size is expected to be small for MVP, but attachment threshold and S3 link fallback are required for safe SMTP operation.

## 14. Dependencies

- Existing ReliabilityKit CLI-first execution model.
- Existing `reliabilitykit/core`, `reporting`, and `storage` modules as implementation boundaries.
- AWS S3 private bucket and IAM permissions for artifact upload and presigned URL generation.
- SMTP provider credentials/configuration supplied via `RELIABILITYKIT_SMTP_*` environment variables.
- Operator-maintained written authorization/checklist storage.
- Static hosting path/framework for landing page, following repository convention.

## 15. Assumptions

### Confirmed Assumptions from Product Spec / User Confirmation

- Full MVP implementation is authorized.
- MVP is manual/operator-assisted, not SaaS.
- Landing page is static only.
- CTA text is exactly `Request a Reliability Audit`.
- CTA destination is exactly `#request-audit`.
- CTA form/email flow is deferred and out of scope.
- Reports and CSV are sanitized and privately delivered through S3 presigned URLs.
- Sanitized metadata retention is 90 days.
- Post-retention CSV email delivery is automated via SMTP environment variables.
- Raw bodies, headers, and traces are not stored by default.
- Bearer token is the first supported auth mechanism.

### Technical Assumptions Requiring Confirmation

- Exact static landing page path in the repository.
- Exact S3 presigned URL expiration duration for initial reports and retention CSV link fallback.
- Default endpoint request timeout.
- Whether sanitized metadata should be deleted, archived, or retained after successful post-retention CSV email.
- Whether SMTP username/password are always required in the target deployment or conditional based on provider.

## 16. Risks / Open Questions

### Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Production testing causes operational concern | Require waiver and internal approval references before execution. |
| Endpoint scope creep | Enforce max 10 unique `METHOD + PATH` endpoints. |
| Sensitive data leaks into artifacts | Sanitized-only models, redaction checks, no raw persistence. |
| Raw data accidentally persists through logs/cache | Logging discipline and artifact inspection tests. |
| S3 URLs are public or over-permissive | Private bucket, no public-read ACL, presigned URLs only. |
| Retention email fails silently | Delivery status ledger, sanitized failure logs, failure notification/remediation recipient. |
| SMTP secrets leak in errors | Redact env-derived secrets and prohibit full environment dumps. |
| Latency labels are disputed | Label pass/fail only with client-provided threshold. |
| Optional burst testing mistaken for default | Separate approval gate and workflow. |

### Open Questions

- Where exactly should written waivers and internal approval checklist references be stored?
- What expiration duration should be used for S3 presigned URLs?
- What static site path/framework should host the landing page?
- What endpoint request timeout default should be used?
- After post-retention CSV email succeeds, should retained sanitized metadata be deleted, archived, or kept elsewhere?

## 17. Implementation Notes

- Extend existing CLI/core/reporting/storage boundaries; do not add a customer-facing backend.
- Keep all audit commands operator-facing.
- Treat approval gates as fail-closed.
- Never serialize bearer token values into config snapshots, report data, CSV, logs, or emails.
- Build report/CSV/email payloads exclusively from sanitized metadata.
- Use private S3 object keys and presigned URLs; public S3 website/report delivery is prohibited.
- Implement retention automation so expired records are processed without manual email composition, but failures remain visible and retryable by an operator.
- Ensure static landing page CTA text and href are exact: `Request a Reliability Audit` -> `#request-audit`.
- Preserve product-spec traceability during implementation and QA.
