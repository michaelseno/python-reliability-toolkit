# Technical Design

## 1. Feature Overview

**Title:** 48-Hour API Reliability Audit MVP Architecture Plan  
**Status:** Planning artifact only; approved for study/planning, not implementation  
**Source Product Spec:** `docs/product/api_reliability_audit_mvp_spec.md`  
**Repository:** `python_reliability_toolkit`  
**Scope Type:** Manual/operator-assisted MVP, not SaaS

This document defines the proposed technical architecture for a packaged 48-hour API Reliability Audit service built around the existing ReliabilityKit repository. It is intentionally limited to architecture planning. Source code should not be implemented from this document until downstream implementation work is explicitly authorized.

The MVP audits up to 10 unique `METHOD + PATH` endpoints over approximately 10 scheduled check cycles across 48 hours, produces an HTML report/dashboard and sanitized CSV export, and delivers artifacts through private S3 presigned URLs. The MVP requires strong privacy controls, written production-testing authorization where applicable, and no default persistence of raw API response bodies, raw headers, or trace logs.

## 2. Product Requirements Summary

- Standard audit supports up to 10 endpoints, where endpoint identity is unique `METHOD + PATH`.
- Default audit duration is 48 hours with 5 checks per day, approximately 10 check cycles total.
- MVP authentication support is bearer token first.
- Bearer tokens are sensitive and must never appear in reports or CSV exports.
- Production API testing requires written client waiver/agreement and an internal approval checklist before execution.
- Audit results capture sanitized metadata only by default: endpoint identifier, method, path, timestamp, status code, availability result, latency, check cycle identifier, and sanitized error/category metadata.
- Raw response bodies, raw headers, and trace logs are transient and are not stored by default.
- Raw data storage requires explicit written client demand and written approval and remains outside the default workflow.
- Client-provided latency thresholds may enable latency pass/fail labeling.
- If thresholds are absent, reports show observed latency only and must not label latency pass/fail.
- Reports consist of an HTML report/dashboard and sanitized CSV export.
- Report delivery uses private S3 presigned URLs only, not public permanent URLs.
- Sanitized metadata is retained for 90 days, then converted/exported to CSV and emailed to the client.
- Resilience/burst testing is optional, outside the main workflow, and requires separate written approval.
- Phase 1 includes a static informational landing page with no backend, login, payment, or form submission.
- Landing page CTA text must be exactly `Request a Reliability Audit`; destination is a placeholder pending confirmation.

## 3. Requirement-to-Architecture Mapping

| Product Requirement | Technical Responsibility |
| --- | --- |
| Up to 10 unique `METHOD + PATH` endpoints | Audit configuration validator enforces uniqueness and maximum endpoint count before execution. |
| 48-hour duration, 5 checks/day | Operator workflow schedules approximately 10 check cycles using existing CLI/run orchestration plus manual scheduling or external scheduler. |
| Bearer token first | Audit configuration supports bearer-token auth as sensitive runtime-only credential input. |
| Token exclusion from reports/CSV | Report and CSV contracts explicitly exclude all credential fields; redaction validation gates are required. |
| Production waiver and internal approval | Pre-run approval gate blocks execution when production flag is true and either approval artifact is missing. |
| Sanitized metadata collection | Result model stores only approved metadata fields. |
| No raw data persistence by default | Execution boundary discards response bodies/headers after deriving status, latency, and sanitized categories. |
| HTML report/dashboard + CSV | Reporting component emits static HTML and sanitized CSV artifacts. |
| Private S3 presigned delivery | Delivery component uploads artifacts to private S3 keys and generates time-limited presigned URLs. |
| 90-day retention and email export | Retention process tracks sanitized metadata expiration and performs post-retention CSV email delivery. |
| Optional resilience/burst testing | Separate approval gate and separate execution path; excluded from standard workflow. |
| Static landing page | Static frontend asset or static site page with informational sections only. |

## 4. Technical Scope

### Current Technical Scope

- Architecture for operator-assisted audit intake, validation, execution, reporting, delivery, and retention.
- Conceptual contracts for audit configuration, endpoint definitions, bearer auth, privacy policy, audit results, CSV export, and landing page content.
- CLI/operator workflow direction aligned to the current ReliabilityKit CLI-first architecture.
- Private S3/presigned URL report delivery model.
- Privacy and redaction boundaries preventing raw data persistence by default.
- Approval gates for production testing and optional resilience/burst testing.
- Static informational landing page approach.
- Technical testing and validation strategy.

### Out of Scope

- Source code implementation.
- SaaS onboarding, customer accounts, login, payment, backend landing page services, and form submissions.
- Automated contract signing or automated production authorization verification.
- Schema validation.
- Non-bearer-token auth standardization.
- Load testing as part of the default audit.
- Public report URLs.
- Additional endpoint pricing in the MVP.

### Future Technical Considerations

- Automated intake/configuration UI.
- Managed monitoring subscription workflows.
- Expanded authentication methods.
- Schema validation if customer demand emerges.
- Automated retention jobs and email dispatch if manual operation proves error-prone.
- Private CloudFront distribution or signed cookies for report delivery if S3 presigned URLs become limiting.

## 5. Architecture Overview

The MVP should remain local-first and operator-assisted, matching the existing repository posture. The architecture is a bounded workflow rather than a SaaS service:

1. **Static offer discovery:** visitor reads the static landing page and clicks the placeholder CTA.
2. **Manual intake:** operator collects endpoint list, bearer token details, latency thresholds if available, client contact, environment classification, written authorization, and optional resilience/burst request status outside the website.
3. **Configuration preparation:** operator creates/loads an `AuditConfig` that defines endpoint scope, auth reference, schedule parameters, privacy policy, and approval evidence references.
4. **Pre-run gates:** validator enforces endpoint cap, unique endpoint identity, production approval requirements, and resilience/burst exclusion unless separately approved.
5. **Scheduled execution:** operator or scheduler runs checks 5 times per day for 48 hours. Each check cycle records sanitized metadata only.
6. **Report generation:** static HTML report/dashboard and sanitized CSV export are generated from sanitized metadata.
7. **Private delivery:** report artifacts are uploaded to a private S3 bucket and delivered through time-limited presigned URLs.
8. **Retention:** sanitized metadata is retained for 90 days. At expiration, retained metadata is converted/exported to CSV and emailed to the client according to the selected operational process.

## 6. System Components

### Existing Repository Fit / Relevant Components

- `reliabilitykit/cli/`: existing Typer CLI entrypoint and command structure; natural place for future operator-facing audit commands if implementation is later approved.
- `reliabilitykit/core/`: existing configuration, contracts, runner, scan pack, and models areas; natural place for future audit-domain contracts and validation logic.
- `reliabilitykit/reporting/`: existing HTML dashboard/run/trend report generation; natural place for future audit report/dashboard generation and CSV export logic.
- `reliabilitykit/storage/`: existing local and S3 storage modules; natural place for future private artifact upload and presigned URL generation behavior.
- `.reliabilitykit/`: existing local output directory; suitable for transient/sanitized working outputs, with strict avoidance of raw body/header/trace persistence.
- `../s3-architecture-plan.md`: existing S3 planning is CI/dashboard oriented and originally mentions public-read as a prior phase. This audit MVP must diverge by requiring private S3 objects and presigned delivery from the beginning.

### Proposed Component Boundaries

#### Audit Intake and Configuration Boundary

- Owns structured audit configuration and pre-run validation.
- Does not collect data through the landing page.
- Does not persist bearer token values in reports or exports.

#### Audit Execution Boundary

- Performs endpoint checks.
- Measures status code, availability, latency, timestamp, and sanitized error/category metadata.
- Treats raw response bodies, raw headers, and traces as transient runtime data.
- Must not persist raw bodies, raw headers, or traces in default mode.

#### Reporting Boundary

- Generates customer-facing HTML dashboard and sanitized CSV.
- Reads sanitized metadata only.
- Excludes tokens, raw response bodies, raw headers, and trace logs.
- Handles threshold-aware latency labeling only when thresholds are present.

#### Delivery Boundary

- Uploads HTML and CSV report artifacts to private S3 object keys.
- Generates presigned URLs for client delivery.
- Does not create public unauthenticated permanent report URLs.

#### Retention Boundary

- Retains sanitized metadata for 90 days.
- Exports retained metadata to CSV after 90 days.
- Supports email delivery of post-retention CSV.
- Raw-data exceptions are separate and require documented written approval.

#### Static Landing Page Boundary

- Hosts informational content only.
- Contains no login, payment, backend API, or form submission.
- Uses exact CTA text `Request a Reliability Audit` with placeholder destination.

## 7. Data Models

These are conceptual contracts for future implementation. Field names are planning-level and may be refined during implementation design review.

## AuditConfig

### Purpose

Defines one client audit, including endpoints, schedule, authorization posture, privacy policy, reporting, delivery, and retention metadata.

### Primary Key

- `audit_id`: unique operator-generated identifier.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Unique audit identifier. |
| `client_name` | string | Client display name for operator and report context. |
| `client_email` | string | Email address for delivery/retention communications. |
| `environment` | enum | `production`, `staging`, `development`, or `other`. |
| `production_waiver_reference` | string/null | Reference to written waiver/agreement if production testing is requested. |
| `internal_approval_reference` | string/null | Reference to completed internal approval checklist if production testing is requested. |
| `endpoints` | list[`AuditEndpoint`] | Up to 10 unique endpoint definitions. |
| `auth` | `BearerAuthConfig`/null | Bearer-token auth configuration or reference. |
| `schedule_duration_hours` | integer | Default `48`. |
| `checks_per_day` | integer | Default `5`. |
| `expected_check_cycles` | integer | Approximately `10`. |
| `privacy_policy` | `PrivacyPolicy` | Data handling and retention policy for the audit. |
| `resilience_burst_requested` | boolean | Whether optional resilience/burst testing was requested. |
| `resilience_burst_approval_reference` | string/null | Required only for optional resilience/burst execution. |
| `report_artifact_prefix` | string | Private S3 prefix for generated artifacts. |
| `created_at` | datetime | Configuration creation timestamp. |

### Ownership Model

Scoped to the client audit. Operators may access configuration under internal operating procedures. Customer-facing outputs must exclude secrets and raw data.

### Lifecycle

Created during manual intake, validated before execution, used during audit execution/reporting, and retained according to internal policy. Sanitized metadata follows 90-day retention; secret handling should minimize or avoid persistence.

## AuditEndpoint

### Purpose

Defines one audited API endpoint and optional latency threshold.

### Primary Key

- Composite identity: `method + path` within an audit.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `endpoint_id` | string | Stable identifier for report rows. |
| `method` | enum/string | HTTP method. Different methods on same path count separately. |
| `path` | string | Endpoint path. Different paths count separately. |
| `base_url` | string | Target host/base URL for the audit. |
| `expected_latency_ms` | integer/null | Client-provided latency threshold. Null means observed latency only. |
| `enabled` | boolean | Whether the endpoint is included in the audit. |
| `notes` | string/null | Operator-only context; must not include secrets. |

### Ownership Model

Scoped to one `AuditConfig`.

### Lifecycle

Created during intake. Endpoint count and uniqueness are validated before execution. Changes after execution starts should require explicit operator notation.

## BearerAuthConfig

### Purpose

Defines how bearer token authentication is provided to runtime checks.

### Primary Key

- Associated with `audit_id` or an operator-managed secret reference.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `auth_type` | enum | Must be `bearer_token` for MVP standard support. |
| `token_secret_reference` | string | Reference to secret location or runtime input; not the token value in reports/CSV. |
| `header_name` | string | Default `Authorization`. |
| `token_prefix` | string | Default `Bearer`. |

### Ownership Model

Sensitive operator-held credential scoped to the audit. It must not be customer-facing output data.

### Lifecycle

Provided during manual intake, used only during execution, rotated/revoked per client agreement, and excluded from all reporting artifacts.

## PrivacyPolicy

### Purpose

Captures audit-specific privacy, raw-data, and retention choices.

### Primary Key

- Associated with `audit_id`.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `store_raw_bodies` | boolean | Default `false`; true only with written exception. |
| `store_raw_headers` | boolean | Default `false`; true only with written exception. |
| `store_trace_logs` | boolean | Default `false`; true only with written exception. |
| `raw_data_exception_reference` | string/null | Written demand/approval reference if any raw storage is enabled. |
| `sanitized_metadata_retention_days` | integer | Must be `90` for MVP. |
| `post_retention_export_required` | boolean | Must be `true` for MVP. |
| `post_retention_email` | string | Client email address for final CSV. |

### Ownership Model

Scoped per audit. Determines what data may be retained and exported.

### Lifecycle

Created before execution. Raw data fields remain false by default. Any exception must be documented before collection.

## AuditResult

### Purpose

Represents the sanitized aggregate result set for one audit.

### Primary Key

- `audit_id` plus `result_id` or generated run group identifier.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Parent audit identifier. |
| `started_at` | datetime | First check timestamp. |
| `completed_at` | datetime/null | Completion timestamp. |
| `check_cycles_expected` | integer | Approximately 10. |
| `check_cycles_completed` | integer | Number of cycles completed. |
| `endpoint_results` | list[`EndpointAuditResult`] | Sanitized per-endpoint check results. |
| `report_html_s3_key` | string/null | Private S3 object key for HTML report. |
| `csv_s3_key` | string/null | Private S3 object key for sanitized CSV. |
| `retention_expires_at` | datetime | 90 days after retention start. |

### Ownership Model

Scoped to client audit and retained as sanitized metadata.

### Lifecycle

Created during execution, finalized after report generation, retained for 90 days, then exported to CSV and emailed.

## EndpointAuditResult

### Purpose

Represents one sanitized endpoint observation for one check cycle.

### Primary Key

- Composite: `audit_id + check_cycle_id + endpoint_id + timestamp`.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Parent audit identifier. |
| `check_cycle_id` | string/integer | Identifier for scheduled check cycle. |
| `endpoint_id` | string | Endpoint identifier. |
| `method` | string | HTTP method. |
| `path` | string | Endpoint path. |
| `timestamp` | datetime | Observation timestamp. |
| `status_code` | integer/null | HTTP status code if available. |
| `available` | boolean | Availability result derived from response/error outcome. |
| `latency_ms` | integer/float/null | Observed latency. |
| `expected_latency_ms` | integer/null | Client threshold if provided. |
| `latency_status` | enum/null | `pass`/`fail` only when threshold exists; null/`observed_only` when absent. |
| `error_category` | string/null | Sanitized error category only. |
| `error_summary` | string/null | Sanitized non-sensitive summary. |

### Ownership Model

Scoped to client audit. Customer-facing exportable if sanitized.

### Lifecycle

Created per endpoint check, included in report/CSV, retained for 90 days.

## CSV Export Contract

### Purpose

Defines customer-facing sanitized metadata export.

### Fields / Columns

| Column | Description |
| --- | --- |
| `audit_id` | Audit identifier. |
| `check_cycle_id` | Check cycle identifier. |
| `endpoint_id` | Endpoint identifier. |
| `method` | HTTP method. |
| `path` | Endpoint path. |
| `timestamp` | Observation timestamp. |
| `status_code` | HTTP status code if available. |
| `available` | Availability boolean/result. |
| `latency_ms` | Observed latency. |
| `expected_latency_ms` | Threshold if provided. |
| `latency_status` | `pass`/`fail` only when threshold exists; otherwise blank or `observed_only`. |
| `error_category` | Sanitized category. |
| `error_summary` | Sanitized summary. |

### Explicitly Excluded

- Bearer tokens.
- Raw API response bodies.
- Raw headers.
- Trace logs.
- Unredacted request/response payloads.
- Secret references that could reveal credential location.

## Landing Page Content Model

### Purpose

Defines the static informational content required for Phase 1 offer validation.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `hero_headline` | string | Describes the 48-hour API Reliability Audit. |
| `value_proposition` | string | Explains short reliability audit value. |
| `whats_included_items` | list[string] | Duration, endpoint cap, check frequency, report, CSV. |
| `privacy_safety_items` | list[string] | Authorization, private delivery, sanitized metadata, no raw persistence by default. |
| `pricing_items` | list[string] | Standard $750, optional validation pricing if used, optional add-on pricing where applicable. |
| `how_it_works_steps` | list[string] | Request, intake, approval, 48-hour checks, report delivery. |
| `faq_items` | list[object] | Endpoint limits, production testing, auth, retention, latency thresholds, optional resilience/burst. |
| `cta_text` | string | Must be exactly `Request a Reliability Audit`. |
| `cta_href` | string | Placeholder destination pending confirmation. |

### Lifecycle

Static content published during Phase 1 and updated only through repository/static site changes. No user data is collected.

## 8. API Contracts

No public or customer-facing backend API contracts are in current MVP scope.

The MVP is manual/operator-assisted and CLI/local workflow based. The static landing page must not submit forms and must not call backend services. Report delivery uses AWS S3 presigned URL mechanisms rather than repository-hosted application APIs.

### External Integration Contract: Private S3 Presigned Report Delivery

#### Purpose

Privately deliver HTML report/dashboard and sanitized CSV artifacts to the client.

#### Authentication / Authorization

- Operator or automation must have AWS permissions to upload objects to the private report bucket and generate presigned URLs.
- Client access is limited to the generated presigned URL validity window.

#### Inputs

- Local generated artifact paths for HTML and CSV.
- Destination private S3 bucket and object keys.
- Presigned URL expiration duration, pending confirmation.

#### Outputs

- Time-limited presigned URL for HTML report/dashboard.
- Time-limited presigned URL for sanitized CSV export.

#### Error Conditions

- Upload failure.
- Missing artifact.
- Missing AWS credentials or insufficient IAM permissions.
- Presigned URL generation failure.
- Expired URL requiring regeneration.

#### Side Effects

- Writes report artifacts to private S3.
- Produces presigned URLs for manual client delivery.

#### Idempotency / Duplicate Handling

- Re-uploading the same finalized artifacts to the same object keys should overwrite only if operator intentionally regenerates the final report.
- Prefer immutable audit artifact keys with audit ID and generated timestamp to avoid accidental replacement.

## 9. Frontend Impact

### Components Affected

- New Phase 1 static product landing page.
- Future/static HTML audit report/dashboard generated from sanitized metadata.

### API Integration

- Landing page: none.
- Report/dashboard: no backend API required for MVP; CSV may be a static linked/downloadable artifact.

### UI States

#### Landing Page

- Static informational state only.
- No loading, authenticated, payment, or form-submission states.
- CTA destination placeholder behavior must be explicit.

#### HTML Report/Dashboard

- Completed audit summary.
- Endpoint-level availability/status/latency tables.
- Observed-latency-only presentation when thresholds are absent.
- Threshold-based latency labels only when expected latency thresholds were provided.
- Link to sanitized CSV export.
- No display of bearer tokens, raw bodies, headers, or trace logs.

## 10. Backend Logic

### Responsibilities

- Validate audit configuration before execution.
- Enforce endpoint cap and uniqueness.
- Enforce production authorization gates.
- Enforce optional resilience/burst approval gates.
- Execute scheduled endpoint checks through operator-run/local tooling.
- Derive sanitized metadata from each check.
- Generate static HTML and sanitized CSV artifacts.
- Upload artifacts to private S3 and generate presigned URLs.
- Support 90-day sanitized metadata retention and post-retention CSV email workflow.

### Validation Flow

1. Load audit configuration.
2. Normalize endpoint identity as `METHOD + PATH`.
3. Reject more than 10 unique endpoint identities.
4. Reject duplicate endpoint definitions unless intentionally de-duplicated before execution.
5. If `environment = production`, require both `production_waiver_reference` and `internal_approval_reference`.
6. If resilience/burst execution is requested, require separate `resilience_burst_approval_reference`; otherwise ensure it is not executed.
7. Confirm bearer token handling uses sensitive runtime input/secret reference.
8. Confirm privacy policy defaults do not store raw bodies, raw headers, or traces.
9. If any raw storage flag is true, require `raw_data_exception_reference` before collection.

### Business Rules

- Testing must not proceed when production approvals are incomplete.
- Standard audit must not exceed 10 unique `METHOD + PATH` endpoints.
- Default check frequency is 5/day for 48 hours.
- Latency pass/fail labels require a client threshold.
- CSV exports contain sanitized metadata only.
- Reports are delivered through private S3 presigned URLs only.
- Raw data exception handling is outside default workflow.

### Persistence Flow

- During execution, write only sanitized metadata and generated artifacts.
- Raw response bodies, raw headers, and trace logs are discarded after deriving allowed fields.
- Store finalized HTML and CSV artifacts in private S3.
- Retain sanitized metadata for 90 days.
- At retention expiry, export sanitized metadata to CSV and email to client.
- After export/email, deletion/archive behavior requires confirmation because the product spec says retained metadata is converted/exported after 90 days but does not explicitly state whether source metadata is deleted immediately afterward.

### Error Handling

- Configuration validation errors block execution and return operator-actionable messages.
- Endpoint check failures become sanitized `EndpointAuditResult` rows with status/availability/error category when possible.
- Network timeouts should be classified without persisting raw trace logs.
- Report generation failures block delivery until corrected.
- S3 upload or presigned URL failures require retry/regeneration by operator.
- Expired presigned URLs should be regenerated from private S3 artifacts if still within retention/availability policy.

## 11. File Structure

Planning-only proposed future organization if implementation is authorized:

```text
docs/architecture/api_reliability_audit_mvp_architecture.md   # this planning artifact
docs/product/api_reliability_audit_mvp_spec.md                # source product spec
reliabilitykit/cli/                                           # future audit operator commands
reliabilitykit/core/                                          # future audit config/contracts/validation
reliabilitykit/reporting/                                     # future audit HTML/CSV report generation
reliabilitykit/storage/                                       # future private S3 upload/presigned delivery
.reliabilitykit/                                              # local sanitized run/report workspace
<static-site-path>/                                           # future landing page location, pending repo convention
```

No source files are created or modified as part of this architecture planning artifact.

## 12. Security

### Authentication

- MVP supports bearer token authentication first.
- Bearer tokens must be treated as confidential secrets.
- Prefer runtime environment variables, local secret store, or operator-managed secret reference over plaintext config persistence.

### Authorization

- Production tests require written client waiver/agreement and internal approval checklist completion.
- Resilience/burst testing requires separate written approval.
- S3 report bucket must remain private; client access is through presigned URLs only.

### Input Validation

- Validate endpoint count and unique `METHOD + PATH` identity.
- Validate URLs and HTTP methods before execution.
- Validate absence/presence of latency thresholds to control labeling.
- Validate privacy policy raw-storage flags and exception references.

### Misuse Risks

- Accidentally running against production without approval.
- Leaking bearer tokens through logs, reports, CSV, screenshots, or exception traces.
- Persisting raw response bodies/headers/traces in default runs.
- Treating optional resilience/burst tests as standard checks.
- Delivering reports via public or overly long-lived URLs.

### Required Controls

- Pre-run safety checklist.
- Redaction checks for reports and CSV exports.
- Logging discipline: logs must avoid raw headers, authorization values, bodies, and trace content.
- Private S3 bucket policy with least-privilege IAM.
- Written evidence references captured before production or raw-data exceptions.

## 13. Reliability

### Retries

- Endpoint checks should avoid aggressive retries that alter the intended measurement profile.
- If retry behavior is later implemented, it must be documented in reports to avoid misleading availability metrics.
- S3 upload and presigned URL generation may be retried by operator/automation on transient AWS failures.

### Timeouts

- Endpoint check timeout defaults require implementation-time confirmation.
- Timeout events should be recorded as sanitized availability failures with latency/error category where applicable.

### Failure Modes

- Missed scheduled cycle: record/check-cycle gap should be visible to operator and, if material, in the report summary.
- Partial endpoint failure: record per-endpoint sanitized result without aborting the whole audit cycle unless safety requires stopping.
- Credential failure: classify as auth failure without exposing token.
- Report generation failure: block S3 delivery until artifacts are regenerated.
- Expired S3 URL: regenerate if artifact is still authorized and available.
- Retention process missed: operational queue/checklist must surface audits approaching or exceeding 90 days.

### Logging / Monitoring

- Operator logs should include audit ID, cycle ID, endpoint ID, status category, and high-level errors only.
- Logs must not include bearer tokens, raw headers, raw response bodies, or trace logs.
- Manual MVP should maintain an operational checklist or audit ledger for cycle completion, delivery, and retention status.

### Performance Considerations

- Standard workload is bounded: up to 10 endpoints x approximately 10 cycles.
- Default checks should be sequential or modestly parallel to avoid unintended load.
- Resilience/burst testing is excluded from standard performance assumptions.

## 14. Dependencies

- Existing ReliabilityKit CLI-first execution model.
- Existing local output/reporting conventions under `.reliabilitykit/`.
- Existing reporting modules as potential future foundation for static HTML output.
- Existing storage modules, including S3 scaffold, with required audit-specific private/presigned constraints.
- AWS S3 private bucket and IAM permissions for artifact delivery.
- Email mechanism for post-retention CSV delivery, pending confirmation.
- Operator-maintained written authorization/checklist storage, pending confirmation.
- Static hosting approach for landing page, pending confirmation.

## 15. Assumptions

### Confirmed Assumptions from Product Spec

- MVP is manual/operator-assisted, not SaaS.
- Reports are static artifacts delivered through private S3 presigned URLs.
- Sanitized metadata retention is 90 days.
- Raw bodies, headers, and traces are not stored by default.
- Bearer token is the first supported auth mechanism.
- Schema validation is deferred.
- Static landing page is informational only.

### Technical Assumptions Requiring Confirmation

- The operator may use an external scheduler, calendar, cron, or manual process to trigger the 5 checks/day during the MVP.
- Sanitized metadata may be stored locally first under `.reliabilitykit/` before private S3 delivery, provided raw data is not persisted.
- Post-retention email may initially be operator-sent manually unless automation is explicitly approved.
- Private S3 object keys should include audit ID and generation timestamp for traceability.
- Presigned URL expiration should be short-lived, but exact duration is not specified.
- Deletion behavior after 90-day CSV export/email is not specified and requires confirmation.
- Landing page static site location in the repository is not yet defined.

## 16. Risks / Open Questions

### Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Production testing causes operational concern | Require written client waiver and internal approval checklist before execution. |
| Endpoint scope creep | Enforce maximum 10 unique `METHOD + PATH` endpoints during config validation. |
| Sensitive data leaks into artifacts | Use sanitized metadata-only contracts and redaction validation before delivery. |
| Raw data accidentally persists through logs/cache | Explicit no-raw persistence boundary; logging discipline; artifact inspection tests. |
| S3 URLs are exposed or over-permissive | Use private bucket and presigned URLs only; avoid public-read configuration. |
| Retention workflow is forgotten | Maintain operator retention ledger/checklist; consider future automated reminders/jobs. |
| Latency pass/fail labels are disputed | Only label pass/fail when client thresholds are provided; otherwise observed-only. |
| Optional burst testing mistaken for default audit | Separate workflow and written approval gate. |

### Open Questions

- What exact placeholder destination should the landing page CTA use?
- What format and storage location should be used for written waivers/agreements and internal approval checklists?
- Who owns the 90-day CSV email: operator, automated job, or another process?
- What expiration duration should be used for S3 presigned report URLs?
- What email address or delivery mechanism should be used for post-retention CSV delivery?
- After the 90-day CSV export/email, should source sanitized metadata be deleted, archived, or retained elsewhere?
- What static site path/framework should host the Phase 1 landing page in this repository?
- What default endpoint request timeout should be used for audit checks?

## 17. Implementation Notes

- This document is an architecture planning artifact only. Do not implement source code until implementation is separately approved.
- Favor extending current CLI-first ReliabilityKit patterns rather than introducing SaaS services.
- Keep the MVP operator-assisted: configuration validation and check execution may be command-driven but should not imply customer self-service.
- Treat all customer credentials as secrets from intake through execution.
- Build reports and CSV from sanitized metadata only; never from raw response body/header/trace fields.
- Avoid public S3 website/report delivery patterns for this MVP. Private S3 plus presigned URLs is mandatory.
- Make production and resilience/burst approval gates fail-closed.
- Ensure observed-only latency presentation is visibly distinct from threshold-based latency pass/fail.
- Keep static landing page implementation independent from audit execution and storage systems.
- Preserve product-spec traceability during downstream implementation planning and QA artifact creation.

## Phased Technical Roadmap

### Phase 1: Planning and Static Offer Validation

- Maintain product, architecture, QA, and UI/UX planning artifacts.
- Define static landing page content and repository location.
- Prepare informational landing page with required sections and exact CTA text.

### Phase 2: Manual Audit MVP Execution

- Add or operate a manual audit configuration workflow.
- Validate endpoint cap, auth handling, production approvals, and privacy policy before execution.
- Execute approximately 10 check cycles across 48 hours.
- Generate static HTML report/dashboard and sanitized CSV.
- Upload private artifacts to S3 and deliver presigned URLs.

### Phase 3: Process Hardening

- Standardize operator checklists and evidence references.
- Improve redaction validation and report consistency.
- Add retention ledger/reminders for 90-day CSV email workflow.
- Evaluate customer feedback and operational effort.

### Phase 4: Future Productization

- Consider automated onboarding, payment, login, expanded auth, schema validation, and managed monitoring only after MVP validation.

## Deferred Items

- SaaS onboarding, accounts, login, payment, and self-service configuration.
- Contact form submission or lead capture backend.
- Automated contract signing or production authorization verification.
- Schema validation.
- Non-bearer authentication standardization.
- Default load/resilience/burst testing.
- Additional endpoint pricing.
- Managed monitoring subscription workflows.
