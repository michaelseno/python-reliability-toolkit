# Technical Design

## 1. Feature Overview

**Title:** 48-Hour API Reliability Audit MVP Technical Design  
**Status:** HITL-corrected implementation blueprint for existing branch `feature/api_reliability_audit_mvp`  
**Source Inputs:**

- `docs/product/api_reliability_audit_mvp_spec.md`
- `docs/bugs/api_reliability_audit_burst_stability_scope_correction_bug_report.md`
- `docs/uiux/api_reliability_audit_report_redesign_design_spec.md`
- `reliabilitykit/core/scan_packs.py`
- `reliabilitykit/core/scenario_registry.py`

The MVP remains a manual/operator-assisted API reliability audit, not a SaaS product. It audits up to 10 unique `METHOD + PATH` endpoints across the configured 48-hour check window, executes the approved standard scan pack for each endpoint, captures sanitized reliability evidence, and generates a modern static offline-friendly HTML report plus sanitized CSV artifacts for private delivery.

HITL correction resolves the prior scope ambiguity: `core_reliability_scan` from `reliabilitykit/core/scan_packs.py` is the standard MVP scan pack and includes `burst_stability`. `burst_stability` is allowed only as the bounded standard scan-pack check described in this document. It must not expand into load testing, chaos testing, destructive testing, broader fault injection, or other resilience testing without separate written approval.

## 2. Product Requirements Summary

- Audit up to 10 unique `METHOD + PATH` endpoints.
- Default schedule is 48 hours, 5 checks/day, approximately 10 check cycles; configurable 1-24 checks/day, with agreement reference required above 5/day.
- Bearer token auth is the first supported auth method; bearer token values must never appear in reports, CSV exports, logs, errors, emails, or persisted customer artifacts.
- Production execution requires written client waiver and internal approval references.
- Default persisted data is sanitized metadata only.
- Raw responses, bodies, headers, logs, trace logs, stack traces, tokens, and secret references are excluded by default.
- Runtime must resolve and apply scan-pack tests from `reliabilitykit/core/scan_packs.py` for each endpoint.
- The standard scan pack is `core_reliability_scan`, currently containing:
  1. `baseline_health`
  2. `repeated_stability`
  3. `burst_stability`
  4. `invalid_payload_handling`
  5. `missing_fields_validation`
  6. `auth_failure_handling`
  7. `timeout_sensitivity`
  8. `response_consistency`
- Reports must show a per-endpoint scan-pack matrix and test-level details: status, severity, rationale, sanitized evidence, remediation guidance, and not-run/not-applicable rationale where relevant.
- `burst_stability` is the only approved standard resilience-style check and must remain bounded.
- All other fault-injection, chaos, destructive, broader resilience, and load tests remain excluded unless separately approved.
- Reports must be modern static HTML, offline/static-friendly, accessible, and privacy-safe.
- CSV exports must contain sanitized metadata only.
- Report delivery uses private S3 presigned URLs; public permanent report URLs are prohibited.
- Sanitized metadata is retained for 90 days and then exported/emailed through automated SMTP configured by environment variables.

## 3. Requirement-to-Architecture Mapping

| Requirement / Acceptance Criterion | Technical Responsibility |
| --- | --- |
| Endpoint cap and uniqueness | Core validator normalizes endpoint identity as uppercase `METHOD + PATH` and fails closed above 10 unique enabled endpoints. |
| 48-hour schedule and frequency gates | Audit config validates duration/frequency and requires agreement reference above default 5 checks/day. |
| Bearer token safety | Auth boundary uses runtime secret references only; serializers, report builders, CSV exporters, logs, and exceptions must redact/exclude tokens and secret locations. |
| Production authorization | Pre-run validation requires production waiver and internal approval references before any request execution. |
| Sanitized metadata only | Execution converts raw request/response observations into approved summaries and discards raw bodies/headers/logs/traces by default. |
| Scan-pack execution | Runtime resolves `core_reliability_scan` from `scan_packs.py` and executes or explicitly records every scenario for every endpoint. |
| Per-endpoint scan matrix and test details | Result model captures `EndpointScanResult`; report view model groups rows by endpoint and scenario. |
| `burst_stability` included but bounded | Scenario runner enforces fixed low request/concurrency/time bounds and records guardrail metadata; no scaling knobs may convert it into load testing. |
| Exclude other resilience/load/fault/chaos/destructive tests | Scan-pack allowlist accepts only scenario IDs from approved `core_reliability_scan`; optional add-ons require separate approval and must not run by default. |
| Latency thresholds | Endpoint rollups label latency pass/fail only when `expected_latency_ms` exists; otherwise `observed_only`. |
| Static report/CSV | Reporting consumes sanitized result contracts only and emits static HTML plus sanitized CSV artifacts. |
| Privacy-safe report | Report generation applies privacy gates, escaping, redaction scanning, and excludes raw diagnostic material by default. |
| Private delivery and retention | Storage uses private S3 presigned URLs; retention automation sends sanitized CSV after 90 days through SMTP. |

## 4. Technical Scope

### Current Technical Scope

- Operator-assisted audit configuration, validation, runtime execution, sanitized result capture, report generation, private artifact delivery, and retention automation.
- Runtime scan-pack execution for every enabled endpoint using `reliabilitykit/core/scan_packs.py`.
- Standard MVP scan pack: `core_reliability_scan`.
- Capture of endpoint-cycle results, scenario-level scan results, endpoint rollups, overall verdict/score, findings, remediation, sanitized evidence, and report/CSV outputs.
- Bounded `burst_stability` as the only standard resilience-style check.
- Modern static HTML report/dashboard with embedded CSS only and no external network dependencies.
- Sanitized endpoint-cycle CSV and sanitized scan-results CSV.

### Out of Scope

- Public/customer backend APIs, SaaS onboarding, accounts, login, payment, forms, lead capture, or self-service audit configuration.
- Schema validation as a generic product capability.
- Non-bearer auth standardization, except manual operator handling outside MVP.
- Load testing, stress testing, soak testing, capacity testing, chaos testing, destructive testing, generalized fault injection, or broader resilience suites.
- Any additional resilience/burst scenario beyond the bounded standard `burst_stability` check unless separately approved.
- Public S3 objects or permanent unauthenticated URLs.
- Raw diagnostic artifact collection, display, persistence, or export by default.

### Future Technical Considerations

- Additional scan packs after product approval and explicit safety classification.
- Expanded auth methods and schema-aware validation.
- Managed job queue or service runner if local/operator scheduling becomes insufficient.
- Private CloudFront signed URLs/cookies if S3 presigned URLs become operationally limiting.

## 5. Architecture Overview

The MVP workflow remains local/operator-first:

1. **Manual intake:** operator collects endpoint list, auth reference, environment, latency thresholds, approval references, and privacy posture.
2. **Audit configuration:** operator creates `AuditConfig` including `scan_pack_id = core_reliability_scan` unless a future approved pack is explicitly configured.
3. **Pre-run validation:** core validation fails closed for endpoint cap, duplicates, production approvals, raw-data exception gates, frequency gates, and scan-pack allowlist violations.
4. **Scan-pack resolution:** runtime calls `resolve_scan_pack(config.scan_pack_id)` and materializes scenario definitions from `scenario_registry.py`.
5. **Scheduled cycle execution:** for each check cycle and each enabled endpoint, runtime executes all standard scan-pack scenarios or records a `not_run`, `not_applicable`, or `incomplete` result with rationale.
6. **Sanitized capture:** scenario runners produce `EndpointScanResult` rows and endpoint-cycle observations using sanitized evidence only.
7. **Aggregation:** report builder computes endpoint rollups, scan-pack pass rates, scores/verdicts, findings, and remediation lists.
8. **Report/export generation:** reporting emits a static HTML dashboard plus sanitized CSV artifacts.
9. **Private delivery:** storage uploads artifacts to private S3 keys and creates time-limited presigned URLs.
10. **Retention:** sanitized metadata is retained for 90 days, then exported and emailed through SMTP automation.

## 6. System Components

### `reliabilitykit/cli/`

- Provides operator commands for validation, execution, report generation, private delivery, and retention processing.
- Must not expose public/customer HTTP APIs.
- Surfaces validation failures and execution summaries without secrets.

### `reliabilitykit/core/scan_packs.py`

- Source of approved scan-pack definitions.
- `core_reliability_scan` is the standard MVP scan pack and must include `burst_stability` unless product scope changes.
- Runtime must not hard-code a divergent scenario list in reporting or runners.

### `reliabilitykit/core/scenario_registry.py`

- Source of scenario metadata: scenario ID, display name, category, description/rationale, severity, marker, and tags.
- Scenario metadata should be extended or mapped to approved remediation guidance without exposing raw data.

### `reliabilitykit/core/`

- Owns audit contracts, validation, scenario execution orchestration, bounded `burst_stability` guardrails, sanitized evidence generation, result normalization, rollup/verdict calculations, and privacy gates.
- Must keep bearer token values and secret references out of serializable/customer-facing models.

### `reliabilitykit/reporting/`

- Generates static HTML and sanitized CSV artifacts exclusively from sanitized view models.
- Renders executive verdict, KPI cards, findings, endpoint scorecards, scan-pack matrix, test-level details, latency/availability summaries, methodology, export section, and privacy notes.
- Must not fetch external assets, make network calls, use analytics, or depend on JavaScript for core content.

### `reliabilitykit/storage/`

- Owns sanitized local workspace, private S3 artifact upload, and presigned URL generation.
- Must prevent public-read ACLs/public static website delivery.

### Retention Automation Boundary

- CLI command plus scheduler/cron or repository-local automation entrypoint.
- Processes expired retention records, regenerates sanitized CSV from retained sanitized metadata, sends SMTP email, and records sanitized delivery state.

## 7. Data Models

## AuditConfig

### Purpose

Defines one client audit.

### Primary Key

- `audit_id`

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Unique audit identifier. |
| `client_name` | string | Client display name. |
| `client_email` | string | Delivery and retention email recipient. |
| `environment` | enum | `production`, `staging`, `development`, or `other`. |
| `production_waiver_reference` | string/null | Required for production. Reference only. |
| `internal_approval_reference` | string/null | Required for production. Reference only. |
| `endpoints` | list[`AuditEndpoint`] | Up to 10 unique enabled endpoint definitions. |
| `auth` | `BearerAuthConfig`/null | Bearer auth reference. |
| `scan_pack_id` | string | Default and MVP value: `core_reliability_scan`. |
| `schedule_duration_hours` | integer | Default `48`. |
| `checks_per_day` | integer | Default `5`, allowed `1..24`. |
| `expected_check_cycles` | integer | Derived from duration/frequency; default approximately `10`. |
| `check_frequency_agreement_reference` | string/null | Required when `checks_per_day > 5`. |
| `privacy_policy` | `PrivacyPolicy` | Raw-data and retention posture. |
| `optional_resilience_requested` | boolean | False for standard bounded `burst_stability`; true only for separately approved add-ons. |
| `optional_resilience_approval_reference` | string/null | Required only for out-of-scope optional add-ons, not for standard bounded `burst_stability`. |
| `report_artifact_prefix` | string | Private S3 artifact prefix. |
| `retention` | `RetentionPolicy` | 90-day metadata retention and post-retention delivery settings. |
| `created_at` | datetime | Creation timestamp. |

### Ownership Model

Scoped to one client audit; operator-owned. Customer-facing outputs exclude secrets and raw data.

### Lifecycle

Created during manual intake, validated before execution, used for runtime/report/delivery/retention, retained according to policy.

## AuditEndpoint

### Purpose

Defines one endpoint and optional latency threshold.

### Primary Key

- `audit_id + endpoint_id`; uniqueness also enforced by uppercase `METHOD + PATH` within audit.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `endpoint_id` | string | Stable sanitized identifier used in reports/anchors/CSV. |
| `method` | string | HTTP method normalized uppercase. |
| `path` | string | Endpoint path. |
| `base_url` | string | Target base URL; report may show environment/domain only if privacy-approved. |
| `expected_latency_ms` | integer/null | Optional latency threshold. Null means observed-only. |
| `enabled` | boolean | Included when true. |
| `notes` | string/null | Operator-only; must not include secrets. |

### Ownership Model

Scoped to one `AuditConfig`.

### Lifecycle

Created before execution; changes after execution starts require re-validation and operator notation.

## BearerAuthConfig

### Purpose

Defines how bearer auth is supplied at runtime without exposing token values.

### Primary Key

- Associated with `audit_id` or operator-managed secret source.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `auth_type` | enum | `bearer_token`. |
| `token_secret_reference` | string | Runtime env var or secret-store reference; never included in customer-facing artifacts. |
| `header_name` | string | Default `Authorization`; not rendered with value. |
| `token_prefix` | string | Default `Bearer`. |

### Ownership Model

Sensitive operator-held credential metadata.

### Lifecycle

Used only to inject runtime auth; token values are never serialized.

## PrivacyPolicy

### Purpose

Captures privacy and raw-data exception posture.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `store_raw_bodies` | boolean | Default `false`; true only with written exception. |
| `store_raw_headers` | boolean | Default `false`; true only with written exception. |
| `store_trace_logs` | boolean | Default `false`; true only with written exception. |
| `collect_raw_logs` / `include_raw_logs` / `persist_raw_logs` | boolean | Default `false`; true only with explicit client demand and approval. |
| `collect_raw_responses` / `include_raw_responses` / `persist_raw_responses` | boolean | Default `false`; true only with explicit client demand and approval. |
| `collect_stack_traces` / `include_stack_traces` / `persist_stack_traces` | boolean | Default `false`; true only with explicit client demand and approval. |
| `raw_data_exception_reference` | string/null | Required if any raw storage/inclusion flag is true. |
| `raw_data_written_demand_reference` | string/null | Required if raw diagnostic collection/display/persistence is requested. |
| `sanitized_metadata_retention_days` | integer | Must be `90`. |

### Ownership Model

Scoped per audit.

### Lifecycle

Validated pre-run; raw-data flags fail closed without approval references.

## ScanPackExecutionPlan

### Purpose

Runtime plan derived from `scan_packs.py` and `scenario_registry.py`; prevents drift between configured scan pack, runtime, report, and CSV.

### Primary Key

- `audit_id + scan_pack_id + generated_at`

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Parent audit. |
| `scan_pack_id` | string | `core_reliability_scan` for MVP. |
| `scan_pack_name` | string | Display name from scan pack. |
| `scan_pack_description` | string | Description from scan pack. |
| `scenario_count` | integer | Count of resolved scenario IDs. |
| `scenarios` | list[`ScenarioRuntimeDefinition`] | Ordered scenario definitions. |
| `generated_at` | datetime | Plan creation time. |

### Ownership Model

Scoped to one audit run.

### Lifecycle

Generated after config validation; stored/snapshotted with sanitized result metadata for report reproducibility.

## ScenarioRuntimeDefinition

### Purpose

Serializable safe scenario metadata used by runtime and reporting.

### Primary Key

- `scan_pack_id + scenario_id`

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `scenario_id` | string | Registry scenario ID. |
| `scenario_name` | string | Human label. |
| `category` | string | Scenario category. |
| `rationale` | string | Safe description/purpose from registry or approved copy. |
| `severity_if_failed` | enum | `high`, `medium`, `low`, `info`. |
| `remediation` | string | Approved generic remediation guidance. |
| `execution_type` | enum | `single`, `sequential_repeated`, `bounded_burst`, `negative_validation`, `auth_negative`, `timeout`, `consistency`. |
| `is_standard_mvp` | boolean | True for all scenarios in `core_reliability_scan`. |

### Ownership Model

Public-safe metadata. Must not include endpoint-specific raw data or secrets.

### Lifecycle

Resolved at runtime; used for every endpoint's expected scenario rows.

## CheckCycleResult

### Purpose

Captures one scheduled cycle's endpoint-level sanitized observations.

### Primary Key

- `audit_id + check_cycle_id + endpoint_id + timestamp`

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Parent audit. |
| `check_cycle_id` | string | Cycle identifier. |
| `endpoint_id` | string | Endpoint identifier. |
| `method` | string | HTTP method. |
| `path` | string | Endpoint path. |
| `timestamp` | datetime | Observation time. |
| `status_code` | integer/null | HTTP status if available. |
| `available` | boolean/null | Availability result where measured. |
| `latency_ms` | integer/float/null | Observed latency. |
| `expected_latency_ms` | integer/null | Configured threshold. |
| `latency_status` | enum | `pass`, `fail`, `observed_only`, or `not_measured`. |
| `error_category` | string/null | Sanitized category. |
| `error_summary` | string/null | Sanitized summary; no raw body/header/trace. |

### Ownership Model

Scoped to client audit and exportable only as sanitized metadata.

### Lifecycle

Created during execution, retained for 90 days, used in report/CSV/rollups.

## EndpointScanResult

### Purpose

Captures one scenario result for one endpoint. This is the core contract for the redesigned report's scan-pack matrix and test-level details.

### Primary Key

- `audit_id + endpoint_id + scan_pack_id + scenario_id + check_cycle_id/null`

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Parent audit. |
| `check_cycle_id` | string/null | Cycle ID when scenario ran per cycle; null allowed for aggregate-only scenario result. |
| `endpoint_id` | string | Endpoint identifier. |
| `method` | string | HTTP method. |
| `path` | string | Endpoint path. |
| `scan_pack_id` | string | `core_reliability_scan`. |
| `scan_pack_name` | string | Display name. |
| `scenario_id` | string | Scenario ID. |
| `scenario_name` | string | Human label. |
| `category` | string | Scenario category. |
| `severity_if_failed` | enum | `high`, `medium`, `low`, `info`. |
| `status` | enum | `pass`, `fail`, `warning`, `not_run`, `not_applicable`, `incomplete`. |
| `rationale` | string | Safe scenario purpose. |
| `expected_behavior` | string/null | Safe expected behavior summary. |
| `observed_behavior` | string/null | Sanitized observed behavior summary only. |
| `evidence_summary` | string/null | Sanitized evidence. No raw bodies, headers, tokens, logs, traces, stack traces, or secret references. |
| `remediation` | string/null | Approved safe remediation guidance. |
| `not_run_reason` | string/null | Required when status is `not_run` or `incomplete` due to skipped execution. |
| `not_applicable_reason` | string/null | Required when status is `not_applicable`. |
| `observed_at` | datetime/null | Last observation time. |
| `affected_cycle_ids` | list[string] | Cycle IDs contributing to result. |
| `sample_count` | integer | Number of sanitized observations used. |
| `raw_data_included` | boolean | Default `false`; true only under approved exception. |
| `raw_data_exception_reference` | string/null | Approval reference if raw data exception exists; should not expose secret locations. |

### Ownership Model

Scoped to one audit and endpoint. Customer/export safe only after privacy validation.

### Lifecycle

Created during each cycle or aggregation step. Persisted as sanitized metadata, rendered in report, exported to scan-results CSV, retained for 90 days.

## BurstStabilityExecutionGuardrails

### Purpose

Defines the hard bounds that keep `burst_stability` a standard reliability check rather than load testing.

### Primary Key

- `audit_id + endpoint_id + check_cycle_id + scenario_id=burst_stability`

### Fields / Constants

| Field | Value / Type | Description |
| --- | --- | --- |
| `max_concurrent_requests` | `3` | Maximum in-flight requests for the burst scenario per endpoint. |
| `max_total_requests` | `5` | Maximum requests issued by the burst scenario per endpoint per cycle. |
| `max_burst_duration_seconds` | `10` | Hard wall-clock cap for the scenario per endpoint. |
| `endpoint_execution_order` | enum | Default `sequential_across_endpoints`; do not burst multiple endpoints simultaneously by default. |
| `retry_policy` | enum | `no_extra_retries`; do not retry failed burst requests unless retry is part of the generic client timeout behavior and recorded. |
| `ramp_up` | enum | `none`; fixed small bounded group only. |
| `sustained_duration` | integer | `0`; no soak/sustained load period. |
| `allowed_methods` | policy | Use the configured safe endpoint method only; do not invent destructive payloads. |
| `stop_on_safety_signal` | boolean | True; stop scenario if safety/authorization/timeout guardrail is hit. |

### Ownership Model

Internal runtime safety metadata; report may summarize as `bounded check: max 5 requests, max concurrency 3, no sustained load`.

### Lifecycle

Applied every time `burst_stability` runs. Any implementation change increasing these bounds requires product/architecture approval.

### Difference From Load Testing

`burst_stability` verifies whether a single endpoint tolerates a very small, short-lived, fixed concurrent request group without obvious instability. It does **not** measure capacity, throughput, saturation, scaling limits, sustained concurrency, maximum RPS, soak behavior, stress limits, or degradation curves. It has no ramp-up, no duration-based target rate, no cross-endpoint concurrency, no autoscaling objective, and no operator-tunable workload expansion in the standard MVP.

## EndpointAuditSummary

### Purpose

Endpoint-level rollup for scorecards and detail headers.

### Primary Key

- `audit_id + endpoint_id`

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `endpoint_id` | string | Endpoint identifier. |
| `method` | string | HTTP method. |
| `path` | string | Endpoint path. |
| `availability_percent` | float/null | Computed from endpoint-cycle results. |
| `latency_summary_ms` | object/null | `{min, median, p95, max}` when measurable. |
| `expected_latency_ms` | integer/null | Threshold when configured. |
| `latency_status` | enum | `pass`, `fail`, `observed_only`, `not_measured`. |
| `scan_total_count` | integer | Expected scenario count from resolved scan pack. |
| `scan_pass_count` | integer | Number of pass results. |
| `scan_fail_count` | integer | Number of fail results. |
| `scan_warning_count` | integer | Number of warning results. |
| `scan_not_run_count` | integer | Number of not-run/incomplete results. |
| `scan_not_applicable_count` | integer | Number of not-applicable results. |
| `high_severity_failure_count` | integer | Failed high-severity scenarios. |
| `score` | integer/null | 0-100 deterministic endpoint score; null if insufficient data. |
| `verdict` | enum | `healthy`, `needs_attention`, `high_risk`, `incomplete`. |
| `top_issue` | string/null | Safe summary for scorecard. |

### Ownership Model

Computed from sanitized results.

### Lifecycle

Generated during report view-model assembly; may be persisted as derived sanitized metadata for retention/report reproducibility.

## Finding

### Purpose

Prioritized action item for executive summary.

### Primary Key

- `audit_id + finding_id`

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `finding_id` | string | Deterministic sanitized ID. |
| `severity` | enum | `high`, `medium`, `low`, `info`. |
| `status` | enum | `open`, `observed`, `incomplete`. |
| `endpoint_id` | string/null | Affected endpoint, null for audit-wide issue. |
| `method` | string/null | HTTP method. |
| `path` | string/null | Endpoint path. |
| `scenario_id` | string/null | Related scenario. |
| `title` | string | Safe concise finding title. |
| `evidence_summary` | string | Sanitized evidence. |
| `remediation` | string | Recommended next step. |
| `sort_rank` | integer | Precomputed priority order. |

### Ownership Model

Computed from sanitized results only.

### Lifecycle

Generated during report view-model assembly and exported only if fields pass privacy gates.

## AuditResult

### Purpose

Top-level result bundle for report/export/delivery/retention.

### Primary Key

- `audit_id + result_id`

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Parent audit. |
| `result_id` | string | Generated result ID. |
| `scan_pack_id` | string | `core_reliability_scan`. |
| `scan_pack_name` | string | Display name. |
| `scan_pack_description` | string | Description. |
| `scan_pack_scenario_count` | integer | Scenario count. |
| `check_cycle_results` | list[`CheckCycleResult`] | Sanitized endpoint-cycle observations. |
| `scan_results` | list[`EndpointScanResult`] | Sanitized scenario results. |
| `endpoint_summaries` | list[`EndpointAuditSummary`] | Computed endpoint rollups. |
| `findings` | list[`Finding`] | Prioritized sanitized findings. |
| `overall_score` | integer/null | 0-100 deterministic audit score; null if insufficient data. |
| `overall_verdict` | enum | `ready_with_minor_observations`, `needs_attention`, `high_risk_reliability_concerns`, `incomplete_audit_data`. |
| `verdict_rationale` | string | Human-readable sanitized explanation. |
| `generated_at` | datetime | Report generation time. |
| `report_html_s3_key` | string/null | Private S3 key. |
| `endpoint_cycle_csv_s3_key` | string/null | Private S3 key. |
| `scan_results_csv_s3_key` | string/null | Private S3 key. |
| `retention_expires_at` | datetime | 90-day expiry. |

### Ownership Model

Scoped to client audit; exportable only through private channels.

### Lifecycle

Created after execution/aggregation, delivered privately, retained for 90 days, then used for post-retention CSV export.

## Verdict and Score Contract

### Purpose

Defines deterministic rollup behavior.

### Rules

- If no endpoint results or required scan-pack data is missing for all endpoints: `overall_score = null`, `overall_verdict = incomplete_audit_data`.
- Start each endpoint score at `100` when at least one required scan result exists.
- Subtract `25` for each failed high-severity scenario, `15` for each failed medium-severity scenario, `5` for each warning, and `10` for each required `not_run`/`incomplete` scenario without acceptable rationale.
- Floor endpoint score at `0`.
- Endpoint verdict:
  - `high_risk` if any high-severity scenario fails or score `< 70`.
  - `needs_attention` if any medium failure/warning/not-run required scenario exists or score `< 90`.
  - `healthy` if score `>= 90` with no failed required scenarios.
  - `incomplete` if insufficient scan data prevents scoring.
- Overall score is the rounded mean of scorable endpoint scores; null if none are scorable.
- Overall verdict:
  - `high_risk_reliability_concerns` if any endpoint is `high_risk` or any high-severity finding is open.
  - `needs_attention` if any endpoint is `needs_attention` or required data is partially incomplete.
  - `ready_with_minor_observations` if all scorable endpoints are healthy and no high/medium failures exist.
  - `incomplete_audit_data` if no scorable endpoint data exists or expected scan-pack rows are absent.

## CSV Export Contracts

### Endpoint-Cycle CSV

Columns:

`audit_id`, `check_cycle_id`, `endpoint_id`, `method`, `path`, `timestamp`, `status_code`, `available`, `latency_ms`, `expected_latency_ms`, `latency_status`, `error_category`, `error_summary`

### Scan-Results CSV

Columns:

`audit_id`, `check_cycle_id`, `endpoint_id`, `method`, `path`, `scan_pack_id`, `scenario_id`, `scenario_name`, `category`, `severity_if_failed`, `status`, `rationale`, `evidence_summary`, `remediation`, `observed_at`, `affected_cycle_ids`, `sample_count`, `not_run_reason`, `not_applicable_reason`, `raw_data_included`

### Explicitly Excluded From All CSVs

Bearer tokens, authorization header values, raw request bodies, raw response bodies, raw headers, raw responses, raw logs, trace logs, stack traces, unredacted payloads, SMTP credentials, and secret references that reveal credential locations.

## RetentionRecord

### Purpose

Tracks 90-day retention state and post-retention CSV email automation.

### Primary Key

- `audit_id + retention_expires_at`

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `audit_id` | string | Parent audit. |
| `client_email` | string | Recipient. |
| `metadata_location` | string | Sanitized metadata location only. |
| `retention_started_at` | datetime | Usually audit completion time. |
| `retention_expires_at` | datetime | `retention_started_at + 90 days`. |
| `export_csv_path_or_key` | string/null | Sanitized post-retention CSV location. |
| `delivery_mode` | enum | `attachment` or `presigned_s3_link`. |
| `delivery_status` | enum | `pending`, `sent`, `failed`, `retry_pending`. |
| `last_attempt_at` | datetime/null | Last SMTP attempt. |
| `last_error_category` | string/null | Sanitized failure category. |
| `attempt_count` | integer | SMTP attempt count. |

### Ownership Model

Operator-owned operational metadata; no secrets or raw API data.

### Lifecycle

Created at audit completion; processed when retention expires; retryable on sanitized failure.

## 8. API Contracts

No public or customer-facing backend API contracts are in MVP scope. The landing page and static report must not call backend services.

### External Integration Contract: Private S3 Presigned Report Delivery

#### Purpose

Privately deliver static HTML report and sanitized CSV artifacts.

#### Authentication / Authorization

Operator/automation uses least-privilege AWS credentials. Client access is limited to presigned URL validity.

#### Inputs

- Local sanitized HTML report path.
- Local endpoint-cycle CSV path.
- Local scan-results CSV path.
- Private S3 bucket and audit-specific object keys.
- Presigned URL expiration duration.

#### Outputs

- Time-limited presigned URL for HTML report.
- Time-limited presigned URL for endpoint-cycle CSV.
- Time-limited presigned URL for scan-results CSV.

#### Error Conditions

Missing artifact, upload failure, invalid AWS credentials, insufficient IAM permission, public ACL attempt, presign failure, expired URL.

#### Side Effects

Writes private S3 objects and produces URLs.

#### Idempotency / Duplicate Handling

Prefer immutable keys containing `audit_id` and generation timestamp. Re-upload same key only for intentional operator regeneration.

### External Integration Contract: Post-Retention CSV SMTP Email

#### Purpose

Automatically email sanitized post-retention CSV artifacts after 90-day retention expires.

#### Authentication / Authorization

SMTP credentials come only from `RELIABILITYKIT_*` environment variables and must be redacted from all outputs.

#### Inputs

- Expired `RetentionRecord`.
- Retained sanitized endpoint-cycle and scan-result metadata.
- Client recipient email.
- SMTP config from environment variables.

#### Message Contract

- Recipient: `client_email`.
- Sender: `RELIABILITYKIT_SMTP_FROM_EMAIL` and optional display name.
- Subject/body: identify audit and sanitized export only; no secrets, raw data, or stack traces.
- Payload: sanitized CSV attachment(s) or private S3 presigned link(s) depending on size.

#### Success Status

Mark `RetentionRecord.delivery_status = sent` only after SMTP send succeeds.

#### Error Status / Failure Conditions

Missing SMTP config, authentication failure, connection timeout, recipient rejection, attachment-size rejection, S3 upload/presign failure, unexpected send error.

#### Idempotency / Duplicate Handling

Do not resend already `sent` records without explicit operator override. Failed/retry-pending records may retry with sanitized state.

## 9. Frontend Impact

### Components Affected

- Static product landing page.
- Generated static HTML audit report/dashboard.

### API Integration

- Landing page: none.
- Report: none. CSV links point to local files or private presigned URLs.

### UI States

#### HTML Report/Dashboard

- Completed audit summary with one `h1` and safe wrapping for long IDs/timestamps.
- Executive verdict: `Ready with minor observations`, `Needs attention`, `High-risk reliability concerns`, or `Incomplete audit data`.
- KPI cards: endpoints audited, scan-pack tests, availability, latency, completed cycles, high-severity failures.
- Key findings/action items, or explicit empty state.
- Endpoint scorecards.
- Per-endpoint scan-pack matrix showing every scenario from `core_reliability_scan`, including `Burst Stability`.
- Test-level details with status, severity, rationale, sanitized evidence, remediation, and privacy note.
- Latency/availability summaries with observed-only labeling when thresholds are absent.
- CSV/export section with links to sanitized metadata only.
- Methodology/scope/privacy notes including bounded `burst_stability` explanation.
- Missing data states: `Not run`, `Not applicable`, `Incomplete`, or explicit scan-pack missing-data alert; never blank.

## 10. Backend Logic

### Responsibilities

- Validate audit configuration and approval gates.
- Resolve `core_reliability_scan` from `scan_packs.py`.
- Execute or explicitly record every scenario for every endpoint.
- Enforce bounded `burst_stability` guardrails.
- Convert observations to sanitized result contracts.
- Compute endpoint summaries, findings, scores, verdicts, and CSV/report view models.
- Generate static HTML and CSV artifacts from sanitized data only.
- Upload artifacts privately and manage retention email automation.

### Validation Flow

1. Load `AuditConfig`.
2. Normalize endpoint identity as uppercase `METHOD + PATH`.
3. Reject more than 10 unique enabled endpoints.
4. Reject duplicate endpoint identities unless de-duplicated before execution.
5. If production, require `production_waiver_reference` and `internal_approval_reference`.
6. Validate `scan_pack_id`; MVP default is `core_reliability_scan`.
7. Resolve scan pack and scenario definitions. Fail closed if unknown scenario IDs exist.
8. Ensure standard run does not include unapproved scenarios outside resolved `core_reliability_scan`.
9. Treat `burst_stability` as standard only under the hard bounds in `BurstStabilityExecutionGuardrails`; do not require optional resilience approval for this bounded scenario.
10. Require separate approval for any non-standard resilience/burst/load/fault/chaos/destructive scenario or any attempt to raise `burst_stability` bounds.
11. Validate bearer token reference without serializing token value.
12. Validate privacy policy; raw-data flags require written demand and approval references.
13. Validate S3 private delivery configuration and retention SMTP configuration before those phases.

### Business Rules

- Every enabled endpoint must produce one row per resolved scan-pack scenario in the final report model.
- If a scenario cannot run safely, write `not_run` or `not_applicable` with rationale; do not omit it.
- `burst_stability` must use max 5 total requests, max concurrency 3, max 10 seconds per endpoint per cycle, no ramp, no sustained duration, no cross-endpoint simultaneous burst, and no extra retries.
- Latency pass/fail labels require `expected_latency_ms`; otherwise report `observed_only`.
- Negative validation/auth scenarios must avoid destructive payloads and must not expose raw request/response content.
- CSV and HTML generation must use sanitized models only.

### Persistence Flow

- During execution, only sanitized endpoint-cycle and scan-result metadata may be written.
- Raw logs, raw responses, bodies, headers, traces, stack traces, bearer tokens, and SMTP credentials are discarded/redacted and excluded from local workspace, S3, HTML, CSV, logs, emails, and retention exports by default.
- Persist the resolved scan-pack snapshot so reports remain reproducible if registry text changes later.
- Store finalized artifacts in private S3.
- Retain sanitized metadata for 90 days, then generate sanitized post-retention CSV export(s) and deliver via SMTP.

### Error Handling

- Configuration validation errors block execution with operator-actionable, secret-free messages.
- Unknown scan-pack/scenario IDs block execution.
- Scenario runtime failures become sanitized `fail`, `warning`, or `incomplete` results depending on cause.
- Safety guardrail violations stop the affected scenario and record `incomplete` or `not_run` with rationale.
- Endpoint/network timeouts are categorized without storing traces.
- Report privacy-gate failures block artifact delivery.
- S3/SMTP failures are retryable and surfaced with sanitized diagnostics.

## 11. File Structure

Implementation should extend existing repository boundaries without introducing a SaaS service:

```text
docs/architecture/api_reliability_audit_mvp_architecture.md   # this HITL-corrected technical design
docs/bugs/api_reliability_audit_burst_stability_scope_correction_bug_report.md
docs/uiux/api_reliability_audit_report_redesign_design_spec.md
reliabilitykit/cli/                                           # operator commands
reliabilitykit/core/scan_packs.py                             # scan-pack source of truth
reliabilitykit/core/scenario_registry.py                      # scenario metadata source
reliabilitykit/core/                                          # audit contracts, execution, rollups, privacy gates
reliabilitykit/reporting/                                     # static HTML and sanitized CSV generation
reliabilitykit/storage/                                       # sanitized workspace, private S3, presigned URLs
.reliabilitykit/                                              # sanitized local workspace only
```

## 12. Security

### Authentication

- Bearer token auth is supported first.
- Token values must be supplied through runtime environment variables, local secret store, or operator-managed secret channel.
- SMTP credentials are loaded from environment variables only.

### Authorization

- Production execution requires client waiver and internal approval references.
- Standard bounded `burst_stability` does not require optional resilience approval.
- Any attempt to run broader resilience, load, fault-injection, chaos, destructive testing, or increased burst bounds requires separate written approval and is out of standard MVP scope.
- S3 artifacts must be private and delivered only with presigned URLs.

### Input Validation

- Validate endpoint cap, method/path uniqueness, URL/method shape, latency threshold types, approval references, scan-pack IDs, scenario IDs, burst guardrails, raw-data exception references, S3 configuration, and SMTP configuration.

### Misuse Risks

- Running against production without approval.
- Accidentally escalating `burst_stability` into load testing.
- Executing unapproved chaos/fault/destructive/load scenarios.
- Leaking tokens/secrets through report/CSV/log/error/email paths.
- Persisting raw response data in local/S3/retention artifacts.
- Publishing public S3 objects or permanent unauthenticated URLs.

### Required Controls

- Fail-closed validation gates.
- Scan-pack allowlist and scenario snapshot.
- Hard-coded standard `burst_stability` bounds unless a future approved config model supersedes them.
- Sanitized evidence builder and denylist checks for generated HTML/CSV/email/logs.
- HTML escaping for all dynamic report fields.
- Private S3 bucket policy and least-privilege IAM.

## 13. Reliability

### Retries

- Endpoint checks should avoid aggressive retries that distort measurements.
- `burst_stability` uses `no_extra_retries` in the standard scope.
- S3 and SMTP may retry transient failures with sanitized status tracking.
- Retention retries must not duplicate successful client emails without operator override.

### Timeouts

- Endpoint request timeout remains an implementation setting and must be recorded in methodology metadata.
- `burst_stability` has a hard scenario wall-clock cap of 10 seconds per endpoint per cycle.
- SMTP timeout should come from `RELIABILITYKIT_SMTP_TIMEOUT_SECONDS` or a safe default.

### Failure Modes

- Missed cycle: record gap and surface in report confidence/coverage.
- Partial endpoint failure: record sanitized result and continue other endpoints unless safety requires stopping.
- Scenario not safely runnable: record `not_run`/`not_applicable`/`incomplete` with rationale.
- Credential failure: classify as auth failure without token disclosure.
- Report generation privacy failure: block delivery.
- Expired S3 URL: regenerate if artifact remains authorized/available.
- SMTP failure: mark failed/retry-pending with sanitized diagnostics.

### Logging / Monitoring

- Logs may include audit ID, cycle ID, endpoint ID, scenario ID, status category, delivery mode, and sanitized error category.
- Logs must not include bearer tokens, authorization headers, raw bodies, raw headers, raw logs, traces, stack traces, SMTP passwords, full environment dumps, or CSV contents.
- Maintain an operational ledger for cycle completion, scenario coverage, report delivery, retention expiry, and retention email status.

### Performance Considerations

- Standard workload is bounded by max 10 endpoints, approximately 10 cycles, and 8 standard scan-pack scenarios.
- Endpoint execution should be sequential or modestly parallel; `burst_stability` must be sequential across endpoints by default.
- The bounded burst adds at most 5 requests per endpoint per cycle and must not be used to infer capacity.
- CSV sizes are expected to be small for MVP; retention email still needs attachment-size fallback to private S3 link.

## 14. Dependencies

- Existing `reliabilitykit` CLI-first execution model.
- `reliabilitykit/core/scan_packs.py` as scan-pack source of truth.
- `reliabilitykit/core/scenario_registry.py` for scenario metadata.
- Report redesign artifact for static HTML layout/content expectations.
- AWS S3 private bucket and IAM permissions for artifact upload/presign.
- SMTP provider credentials/configuration via `RELIABILITYKIT_SMTP_*` environment variables.
- Operator-maintained written authorization/checklist storage.

## 15. Assumptions

### Confirmed Assumptions from Product / HITL Correction

- MVP remains manual/operator-assisted, not SaaS.
- Runtime must apply scan-pack tests from `scan_packs.py` for each endpoint.
- `core_reliability_scan` is the standard MVP scan pack.
- `burst_stability` is included in the standard audit as the only bounded resilience-style check.
- Standard bounded `burst_stability` does not require optional resilience approval.
- All other resilience, fault-injection, chaos, destructive, and load tests remain excluded unless separately approved.
- Reports and CSV are sanitized and private/offline/static-friendly.
- Raw bodies, headers, traces, tokens, logs, stack traces, and secret references are excluded by default.
- Sanitized metadata retention is 90 days.

### Technical Assumptions Requiring Confirmation

- The exact endpoint request timeout default.
- Exact S3 presigned URL expiration duration.
- Whether post-retention export should produce one combined CSV or separate endpoint-cycle and scan-results CSVs. This design recommends separate CSVs to avoid breaking the existing endpoint-cycle contract.
- Whether sanitized metadata should be deleted, archived, or retained elsewhere after successful post-retention email.
- Final approved remediation copy per scenario if not added directly to `scenario_registry.py`.

## 16. Risks / Open Questions

### Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| `burst_stability` is misused as load testing | Hard guardrails: max 5 requests, max concurrency 3, max 10 seconds, no ramp/soak/capacity metrics, sequential across endpoints. |
| Scenario list drifts between runtime and report | Resolve scan pack from `scan_packs.py`; snapshot `ScanPackExecutionPlan`; report expected rows from snapshot. |
| Scan-pack data absent produces weak report | Treat missing scan-pack execution data as `incomplete_audit_data` and QA failure once backend support is expected. |
| Sensitive data leaks into evidence | Sanitized evidence model, denylist scans, HTML escaping, raw-data gates, no raw persistence. |
| Negative validation scenarios harm endpoints | Use safe minimal invalid/missing payload checks only for approved endpoint/method context; record `not_applicable` if unsafe. |
| Latency labels are misleading | Pass/fail only with configured thresholds; otherwise `observed_only`. |
| Public artifact exposure | Private S3 objects only; presigned URLs; no public-read ACL. |
| Retention email fails silently | Delivery ledger, retryable statuses, sanitized operator notification. |

### Open Questions

- Should remediation guidance live in `scenario_registry.py`, a separate report-copy map, or product-owned content file?
- What exact endpoint timeout default should QA expect?
- What S3 presigned URL expiration should be used for initial delivery and retention fallback links?
- After successful post-retention CSV email, should retained sanitized metadata be deleted or archived?
- Are any configured endpoints unsafe for validation/auth negative scenarios by method semantics, requiring `not_applicable` rather than execution?

## 17. Implementation Notes

- Do not add production source code as part of this architecture update.
- Implement scan-pack runtime by resolving `core_reliability_scan`; do not duplicate the scenario list in report code.
- Ensure every endpoint renders every scenario row, including `Burst Stability`, with status and rationale.
- Persist a sanitized scenario-plan snapshot for reproducibility.
- Build report view models before template rendering; avoid complex business logic inside HTML templates.
- Generate two CSV artifacts unless product/QA later approves one expanded combined CSV.
- Run privacy gates before writing or uploading HTML/CSV artifacts.
- Include bounded `burst_stability` methodology text in the report so customers understand it is not load testing.
- Preserve exact static-report constraints: embedded CSS only, no external fonts/scripts/images/analytics/iframes, no backend calls, no client-side persistence.
- Add QA coverage for scan-pack completeness, `burst_stability` inclusion, burst guardrail enforcement, unapproved scenario exclusion, privacy redaction, CSV columns, and static report accessibility/responsiveness.
