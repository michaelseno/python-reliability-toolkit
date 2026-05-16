# Implementation Plan

## 1. Feature Overview
Implement the backend/core/reporting/storage/retention portion of the manual/operator-assisted 48-Hour API Reliability Audit MVP.

## 2. Technical Scope
Add audit domain models and fail-closed validation, sanitized check execution metadata, HTML/CSV reporting, private S3 presigned artifact delivery helpers, 90-day retention ledger processing, SMTP environment-variable parsing and delivery, and operator CLI commands. Preserve the existing CLI-first toolkit and do not add customer-facing APIs or landing-page backend behavior.

HITL correction scope updates schedule validation so `checks_per_day` remains defaulted to 5 but is configurable from 1 through 24, requires an operator/client agreement reference when increased above 5, and reconciles `expected_check_cycles` with the configured frequency. It also strengthens the raw diagnostic artifact gate so raw logs, raw responses, and stack traces are excluded from display and persistence by default and require explicit client request plus written approval/reference for any collection, inclusion, or persistence exception.

HITL usability correction scope adds a schema-valid, copy-editable local audit YAML and explicit validate → check-cycle → report documentation using produced result JSON paths. The current HITL correction streamlines the local workflow to `rk audit run --config ...` followed by `rk audit generate-report --id ...`. No convenience/sample-report command will be added.

HITL packaging correction scope fixes installed CLI importability for editable installs where Python does not process the editable `.pth` file, while preserving both `reliabilitykit` and short `rk` installed commands.

Current HITL report-template/backend correction scope implements runtime scan-pack execution from `reliabilitykit/core/scan_packs.py`, captures one sanitized scan result per standard scenario per endpoint, includes bounded `burst_stability` as the only approved resilience-style standard check, emits scan-results CSV metadata, and redesigns the static HTML report as a substantive SaaS-style offline dashboard.

## 3. Source Inputs
- `docs/architecture/api_reliability_audit_mvp_architecture.md`
- `docs/product/api_reliability_audit_mvp_spec.md`
- `docs/qa/api_reliability_audit_mvp_test_plan.md`
- `docs/bugs/api_reliability_audit_mvp_hitl_corrections_bug_report.md`
- `docs/bugs/api_reliability_audit_sample_report_usability_gap_bug_report.md`
- `docs/bugs/api_reliability_audit_rk_entrypoint_import_bug_report.md`
- `docs/bugs/api_reliability_audit_burst_stability_scope_correction_bug_report.md`
- `docs/uiux/api_reliability_audit_report_redesign_design_spec.md`
- `docs/release/api_reliability_audit_mvp_implementation_issue.md`
- Existing `reliabilitykit` CLI/core/reporting/storage/test conventions.

## 4. API Contracts Affected
No public or customer-facing backend API contracts are in MVP scope.

Operator-facing CLI commands will be available under `reliabilitykit audit` and the short `rk audit` console entry point for validating configs, running one check cycle, generating reports, delivering via private S3 presigned URLs, creating retention records, and processing expired retention records.

Installed command wrappers must load `reliabilitykit.cli.main:app` without relying on the repository current working directory. The wrapper may use editable-install metadata only as a fallback when the normal package import path is unavailable.

The local documented audit workflow uses streamlined commands:
- `rk audit run --config <audit.yml>` — `--config` is required, validates config, runs one check cycle, writes `.reliabilitykit/audits/<audit_id>/results/<cycle_id>.json`, snapshots audit metadata, and prints `audit_id` plus result path.
- `rk audit generate-report --id <audit_id>` — discovers the latest result JSON under `.reliabilitykit/audits/<audit_id>/results/`, uses the persisted snapshot when available, and writes `.reliabilitykit/audits/reports/<audit_id>/audit_report.html` and `audit_sanitized.csv`.
- Report generation now also writes `.reliabilitykit/audits/reports/<audit_id>/audit_scan_results_sanitized.csv` and links both sanitized CSV artifacts from the static HTML report.

## 5. Data Models / Storage Affected
- New audit models: `AuditConfig`, `AuditEndpoint`, `BearerAuthConfig`, `PrivacyPolicy`, `RetentionPolicy`, `EndpointAuditResult`, `AuditResult`, and `RetentionRecord`.
- Scan-pack/runtime models added to sanitized result metadata: `ScenarioRuntimeDefinition`, `ScanPackExecutionPlan`, and `EndpointScanResult`.
- `AuditConfig.scan_pack_id` defaults to `core_reliability_scan` and validates fail-closed for the MVP standard pack.
- `AuditResult` stores scan-pack metadata, execution plan, sanitized `scan_results`, and report rollup fields.
- `AuditConfig.checks_per_day` validation changes to min `1`, max `24`; `AuditConfig.check_frequency_agreement_reference` is required only when `checks_per_day > 5`.
- `AuditConfig.expected_check_cycles` must equal `schedule_duration_hours * checks_per_day / 24` for the standard 48-hour audit.
- `PrivacyPolicy` adds explicit raw diagnostic artifact flags for raw logs, raw responses, and stack traces; all default false and all require both explicit request and written approval/reference when enabled.
- Local sanitized workspace under `.reliabilitykit/audits/` and `.reliabilitykit/retention/` only.
- CSV contract exactly: `audit_id`, `check_cycle_id`, `endpoint_id`, `method`, `path`, `timestamp`, `status_code`, `available`, `latency_ms`, `expected_latency_ms`, `latency_status`, `error_category`, `error_summary`.
- Scan-results CSV contract: `audit_id`, `check_cycle_id`, `endpoint_id`, `method`, `path`, `scan_pack_id`, `scenario_id`, `scenario_name`, `category`, `severity_if_failed`, `status`, `rationale`, `evidence_summary`, `remediation`, `observed_at`, `affected_cycle_ids`, `sample_count`, `not_run_reason`, `not_applicable_reason`, `raw_data_included`.
- Private S3 object upload/presign helper; no public ACL or permanent URL behavior.
- Local check-cycle output path remains `.reliabilitykit/audits/<audit_id>/results/<cycle_id>.json`.
- Local audit config snapshots are written to `.reliabilitykit/audits/<audit_id>/audit_config_snapshot.json` to support later report generation without re-passing the config path.
- Local report output paths remain `.reliabilitykit/audits/reports/<audit_id>/audit_report.html` and `.reliabilitykit/audits/reports/<audit_id>/audit_sanitized.csv`.
- Local scan-results CSV output path is `.reliabilitykit/audits/reports/<audit_id>/audit_scan_results_sanitized.csv`.

## 6. Files Expected to Change
- `reliabilitykit/core/audit.py`
- `reliabilitykit/core/scenario_registry.py`
- `reliabilitykit/reporting/audit.py`
- `reliabilitykit/storage/local.py`
- `reliabilitykit/storage/s3.py`
- `reliabilitykit/storage/retention.py`
- `reliabilitykit/cli/commands/audit.py`
- `reliabilitykit/cli/main.py`
- `pyproject.toml`
- `scripts/reliabilitykit`
- `scripts/rk`
- Unit tests under `tests/unit/`
- Backend implementation documentation under `docs/backend/`
- `examples/api_reliability_audit/audit.local.yml`
- `examples/api_reliability_audit/README.md`

## 7. Security / Authorization Considerations
Production audits fail closed without waiver and internal approval references. Optional resilience/burst add-ons outside the standard bounded `burst_stability` check remain outside the standard workflow and are blocked without a separate approval reference. Bearer token values are read from runtime env vars only and are not serialized to models, reports, CSV, logs, S3 keys, emails, or errors. Raw bodies, raw headers, and trace logs are not stored by default; raw storage flags require a documented exception reference.

The HITL-approved exception is standard bounded `burst_stability` from `core_reliability_scan`; it does not require the optional resilience approval gate, but it is hard-bounded to max concurrency 3, max total requests 5 per endpoint per cycle, max duration 10 seconds, no ramp-up, no sustained/soak duration, no throughput/capacity goal, no cross-endpoint simultaneous burst by default, and no extra retries. Other resilience/load/fault/chaos/destructive scenarios remain excluded unless separately approved.

Frequency increases above the default are blocked unless an operator/client agreement reference is captured. Raw logs, raw responses, and stack traces are not included in generated reports, CSV exports, local sanitized workspace files, retention exports, email payloads, or S3 artifacts by default.

The example config stores only a bearer-token environment variable/reference, not a token value. Production/staging approval and raw diagnostic gates are documented as operator-editable references and default to safe non-production/no-raw behavior.

## 8. Dependencies / Constraints
No new required dependency will be added. S3 support will use optional `boto3` when available or an injected test/client object. SMTP uses Python standard-library `smtplib`/`email` and environment variables defined by the architecture.

The installed CLI fallback must use only standard-library packaging/runtime metadata access and must not hardcode repository paths or secrets.

## 9. Assumptions
- Initial and retention fallback presigned URL expiration defaults to 7 days where not specified; operators may override per command/helper.
- Latency equal to threshold is treated as `pass` because the observed latency is not greater than the client threshold.
- Endpoint identity normalizes HTTP method to uppercase and uses the provided path string as the path identity.
- Source sanitized metadata is retained after successful retention email because deletion/archive is explicitly open in the design.
- The operator/client agreement reference for `checks_per_day > 5` is represented as `check_frequency_agreement_reference`; this is a reference string only and is not rendered in customer-facing artifacts.
- For the 48-hour standard audit, expected check cycles are derived exactly as `(48 * checks_per_day) / 24`, yielding `2 * checks_per_day`.
- Existing raw body/header/trace exception references are reused as the explicit request and written approval gate for raw logs, raw responses, and stack traces to avoid adding a separate approval workflow.
- The copy-editable local example uses `https://httpbin.org` as a real public HTTP dry-run target so users can try the workflow locally, while documentation requires replacing endpoints with approved client staging or production targets for actual audits.
- `audit run` generates a UTC timestamp-based cycle id because the confirmed requirement does not specify a caller-provided cycle id for the streamlined command.
- `audit generate-report` uses the newest result file by filesystem modification time, with filename as a tie-breaker.
- If an audit metadata snapshot is unavailable, `audit generate-report` falls back to minimal result-derived metadata so historical sanitized results can still render; new `audit run` and `check-cycle` executions write the snapshot.
- Python 3.13 on macOS may skip `.pth` files that carry the `UF_HIDDEN` flag; the installed script wrapper can safely recover editable source location from `direct_url.json` because `uv pip install -e .` writes that local editable metadata.
- Validation-oriented scenarios without an approved endpoint-specific schema/payload contract are recorded as `not_applicable` rather than sending synthetic or potentially destructive payloads.

## 10. Validation Plan
- `./.venv/bin/python -m pytest tests/unit/test_api_reliability_audit_mvp.py tests/unit/test_cli_commands.py`
- `./.venv/bin/python -m pytest tests/unit/test_api_reliability_audit_mvp.py tests/unit/test_cli_commands.py tests/unit/test_packaging_entrypoints.py`
- Broader unit suite if feasible: `python -m pytest tests/unit`
- `./.venv/bin/rk audit run --config examples/api_reliability_audit/audit.local.yml`
- `uv pip install -e .`
- From outside the repository CWD: `./.venv/bin/rk --help` and `./.venv/bin/reliabilitykit --help`
