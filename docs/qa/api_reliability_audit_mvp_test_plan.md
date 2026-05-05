# Test Plan

## 1. Feature Overview

**Title:** 48-Hour API Reliability Audit MVP QA Test Plan  
**Status:** Implementation-ready QA planning artifact; not executed; not QA sign-off  
**Feature/Service:** Manual/operator-assisted 48-Hour API Reliability Audit MVP for Python Reliability Toolkit  
**Source Product Spec:** `docs/product/api_reliability_audit_mvp_spec.md`  
**Source Architecture Plan:** `docs/architecture/api_reliability_audit_mvp_architecture.md`  
**Source UI/UX Spec:** `docs/uiux/api_reliability_audit_mvp_design_spec.md`  

This QA plan defines implementation-ready validation coverage for a manual/operator-assisted MVP that audits up to 10 unique `METHOD + PATH` API endpoints over 48 hours, using approximately 10 check cycles, bearer-token-first authentication, sanitized metadata reporting, private S3 presigned delivery, 90-day sanitized metadata retention, automated post-retention CSV email delivery via SMTP environment variables, and a Phase 1 static informational landing page.

This artifact is formal planning only. It does not implement tests, execute validation, approve release readiness, create a pull request, or push changes.

## 2. Acceptance Criteria Mapping

| Product AC | Requirement Summary | Planned QA Coverage |
| --- | --- | --- |
| AC-1 | Standard audit accepts no more than 10 unique `METHOD + PATH` endpoints; same path with different methods count separately. | Audit config validation tests for 0, 1, 10, 11 endpoints; duplicate entries; same path with different methods; different paths with same method. |
| AC-2 | Production testing requires written client waiver/agreement. | Negative gate tests proving production execution is blocked without waiver; positive tests with waiver plus internal approval. |
| AC-3 | Internal production approval is required before production testing may proceed. | Gate tests for waiver-only blocked state; waiver plus completed internal checklist allowed within approved scope. |
| AC-4 | Bearer tokens are sensitive and excluded from HTML report and CSV. | Auth handling and artifact redaction tests using sentinel token values searched across reports, CSV, logs, and generated artifacts. |
| AC-5 | HTML report and CSV are delivered through private S3 presigned URLs. | S3 delivery tests validating private objects, presigned URL generation, non-public access, URL expiry behavior, separate links for HTML and CSV, and no public/permanent artifact URLs. |
| AC-6 | Raw bodies, raw responses, raw headers, raw logs, trace logs, and stack traces are transient and not displayed or stored by default. | Privacy regression tests using sentinel body/header/trace/raw-log/raw-response/stack-trace content and file/artifact/log inspection after default runs. |
| AC-7 | Raw diagnostic artifact collection, inclusion/display, or persistence requires explicit written demand and approval and must be documented as outside default workflow. | Negative raw-artifact gate tests; positive exception-path documentation checks when both written demand and approval references exist. |
| AC-8 | CSV contains sanitized metadata only and excludes secrets/raw data. | CSV schema/content tests for allowed columns only, sanitized error fields, no tokens, no raw headers, no bodies, no traces, no secret references. |
| AC-9 | Sanitized metadata retained 90 days; after 90 days exported to CSV and emailed to client through automated SMTP environment-variable workflow; missing/invalid SMTP configuration must surface failure without secrets. | Retention policy tests using controllable time fixtures; export-after-90-days workflow tests; SMTP env var validation; attachment vs private presigned-link delivery tests; retryable `failed`/`retry_pending` state tests; sanitized failure surfacing and email dispatch evidence checks. |
| AC-10 | Resilience/burst testing is optional, outside main workflow, and requires separate written approval. | Gate tests proving standard workflow excludes burst behavior; negative approval tests; approved add-on path boundary checks. |
| AC-11 | Latency pass/fail labels only when thresholds are provided; absent thresholds show observed latency only. | Report and CSV tests for threshold-present, threshold-absent, and mixed threshold endpoint sets. |
| AC-12 | Default run frequency is 5 checks/day for 48 hours, approximately 10 check cycles; configurable frequency must be 1-24/day, require agreement above 5/day, and reconcile expected cycles. | Schedule/config tests for default duration/frequency/cycles, min/max bounds, above-default agreement gate, expected-cycle reconciliation, missed-cycle reporting, and bounded workload. |
| AC-13 | Static landing page includes required sections, exact CTA text, CTA href `#request-audit`, matching placeholder section, and no backend/payment/login/form/email submission or lead capture. | Static UI content, exact CTA link/anchor, accessibility, responsive, network/no-submission, and no-disallowed-functionality tests. |

## 3. Test Scenarios

### 3.1 Test Strategy by Layer

#### Product Requirements Validation

- Verify implementation behavior remains traceable to AC-1 through AC-13.
- Review operator workflow artifacts for manual-MVP boundaries and absence of SaaS assumptions.
- Validate explicit out-of-scope items are not accidentally introduced: self-service onboarding, accounts/login, payment, schema validation, default load testing, public report URLs, and landing-page form handling.

#### Audit Config Validation

- Positive: exactly 10 unique endpoints are accepted.
- Negative: 11 unique endpoints are rejected before execution.
- Edge: same path with `GET` and `POST` counts as two endpoints.
- Edge: duplicate `METHOD + PATH` entries are rejected or de-duplicated before execution with operator-visible evidence.
- Negative: invalid/missing method, path, base URL, schedule duration, or retention configuration blocks execution.

#### Bearer Auth Handling

- Positive: bearer token can be supplied as runtime secret or secret reference and used for authorized checks.
- Security: token value never appears in customer-facing HTML, CSV, logs, exception text, screenshots, filenames, S3 object keys, or exported metadata.
- Negative: missing/invalid token produces sanitized auth failure metadata without exposing token or raw response data.

#### No Raw Data Persistence / Privacy Regression

- Use mock API responses containing unique sentinel strings in body, headers, raw responses, raw logs, trace-like error output, and stack traces.
- Confirm default outputs persist only sanitized metadata.
- Inspect generated artifacts, local output directories, S3 artifacts, report HTML, CSV, and logs for absence of sentinel raw data.
- Validate raw diagnostic artifact collection, inclusion/display, and persistence flags default to false and fail closed without explicit client request plus written approval/reference.

#### Sanitized Result Model

- Verify allowed fields only: audit ID, check cycle ID, endpoint ID, method, path, timestamp, status code, availability, latency, expected latency where provided, latency status, sanitized error category, and sanitized error summary.
- Validate unavailable fields render as explicit `Not available`, `Not measured`, `Observed only`, or equivalent non-ambiguous text.
- Validate no raw payloads, headers, trace logs, tokens, or secret references are included.

#### Sanitized CSV Export

- Verify CSV headers match the approved sanitized metadata contract.
- Verify row count aligns with endpoint count multiplied by completed check cycles, accounting for missed cycles if applicable.
- Verify absent thresholds do not create pass/fail latency labels.
- Verify CSV export is linked/labeled as sanitized metadata.

#### HTML Report / Dashboard Validation

- Verify report includes audit metadata, scope summary, expected/completed cycles, endpoint results, latency interpretation, sanitized error categories, CSV export link, privacy/exclusion notes, retention notes, and delivery guidance.
- Validate no secrets/raw data are rendered.
- Validate threshold-aware latency display: pass/fail only when threshold exists; observed-only otherwise.
- Validate empty or partial audit data does not produce misleading availability or latency summaries.

#### S3 Private / Presigned Delivery Validation

- Verify artifacts are uploaded to private S3 object keys.
- Verify public unauthenticated permanent access is blocked.
- Verify presigned URLs allow time-limited client access to HTML and CSV artifacts.
- Verify expired URL behavior is documented and regeneration path is available to operator.
- Verify object key naming avoids tokens, client secrets, raw paths containing sensitive values, or raw payload-derived values.

#### Retention / Export-After-90-Days Validation

- Verify sanitized metadata retention is configured for 90 days.
- Use controlled dates/time travel in planned automated tests to validate post-retention CSV generation.
- Verify post-retention CSV contains sanitized metadata only.
- Verify automated post-retention email delivery uses SMTP configuration supplied only through environment variables.
- Validate required SMTP env vars: `RELIABILITYKIT_SMTP_HOST`, `RELIABILITYKIT_SMTP_PORT`, `RELIABILITYKIT_SMTP_FROM_EMAIL`, `RELIABILITYKIT_SMTP_USE_TLS`, `RELIABILITYKIT_SMTP_USE_SSL`, and `RELIABILITYKIT_RETENTION_FAILURE_NOTIFY_EMAIL`.
- Validate conditional/optional SMTP env vars: `RELIABILITYKIT_SMTP_USERNAME`, `RELIABILITYKIT_SMTP_PASSWORD`, `RELIABILITYKIT_SMTP_FROM_NAME`, `RELIABILITYKIT_SMTP_TIMEOUT_SECONDS`, and `RELIABILITYKIT_RETENTION_MAX_ATTACHMENT_MB`.
- Negative: missing required SMTP env vars, non-numeric port/timeout/size values, conflicting TLS+SSL settings, SMTP auth failure, connection timeout, recipient rejection, attachment rejection, and S3 presign failure in link mode must not silently succeed.
- Verify SMTP password, username where sensitive, bearer token, raw API data, environment dumps, and stack traces containing secrets are redacted from logs, failure notifications, customer-facing artifacts, CSV, and reports.
- Verify failed delivery records remain operator-actionable and retryable using `delivery_status` of `failed` or `retry_pending`, incremented `attempt_count`, sanitized `last_error_category`, and `last_attempt_at`.
- Verify re-running already `sent` retention records does not resend unless explicit operator override is provided.
- Verify attachment mode is used for generated CSV at or below `RELIABILITYKIT_RETENTION_MAX_ATTACHMENT_MB` or implementation default.
- Verify private S3 presigned-link mode is used when CSV exceeds the configured threshold or attachment constraints require link delivery; linked CSV object must be private, time-limited, sanitized, and non-public.
- Verify failure notification to `RELIABILITYKIT_RETENTION_FAILURE_NOTIFY_EMAIL` contains sanitized diagnostic information and remediation guidance only.
- Validate behavior for missed or overdue retention tasks, including due-date detection and operator-visible remediation state.

#### Production Waiver / Internal Approval Gates

- Negative: production flag with no waiver blocks execution.
- Negative: waiver present but internal checklist missing blocks execution.
- Positive: waiver and internal approval complete allows execution only within approved endpoint scope.
- Validate approval evidence references are captured before execution and are not customer-facing secrets.

#### Optional Resilience / Burst Approval Gates

- Verify standard audit never performs resilience/burst checks by default.
- Negative: requested burst testing without separate written approval is blocked.
- Positive: separately approved burst test remains outside main workflow and within documented boundaries.
- Validate report does not imply burst testing occurred unless approved and executed separately.

#### Latency Threshold Behavior

- Threshold provided: report and CSV may label pass/fail against threshold.
- Threshold absent: report and CSV show observed latency only, with no pass/fail label.
- Mixed thresholds: per-endpoint behavior is correct and does not apply global pass/fail where endpoint threshold is absent.
- Boundary: latency exactly equal to threshold uses the implementation-defined expected rule, which must be documented before execution.

#### Static Landing Page Validation

- Verify required sections: hero headline, problem/value proposition, what’s included, privacy/safety guarantees, pricing, how it works, FAQ, and CTA.
- Verify exact CTA text: `Request a Reliability Audit`.
- Verify every landing-page CTA is a real same-page link with exact href `#request-audit`.
- Verify exactly one visible matching placeholder section exists with `id="request-audit"`, a programmatically identifiable heading, and static explanatory copy that manual intake is coordinated outside the website.
- Verify CTA activation navigates to `#request-audit` only and does not submit a form, open `mailto:`, start payment, create account, log in, call backend APIs, capture email, trigger scheduler/chat widgets, or store lead data.
- Verify page communicates manual/operator-assisted MVP and not SaaS.
- Verify no forms, input fields for lead capture, submit buttons, backend calls, login elements, payment widgets, email capture, CRM/newsletter/calendar/chat widgets, or form submission behavior are present.

#### Accessibility / Responsive Validation

- Validate semantic landmarks, one H1, hierarchical headings, accessible links, keyboard navigation, visible focus states, color contrast, text status labels, and table semantics.
- Validate responsive layouts on mobile, tablet, and desktop widths.
- Validate CTA target size and table readability on small screens.
- Validate FAQ accessibility if implemented as an accordion; static FAQ is preferred.

### 3.2 Positive Test Scenarios

| ID | Scenario | Expected Result |
| --- | --- | --- |
| P-001 | Configure standard audit with 10 unique endpoints, staging environment, bearer token, and thresholds. | Config is valid; execution may be scheduled for 48 hours / 5 checks per day. |
| P-002 | Generate report from sanitized successful and failed endpoint observations. | HTML and CSV contain approved sanitized metadata and exclude secrets/raw data. |
| P-003 | Deliver final HTML and CSV through private S3 presigned URLs. | Client can access artifacts through presigned URLs; direct public access is blocked. |
| P-004 | Production audit with waiver and internal approval complete. | Execution allowed only for approved endpoint scope. |
| P-005 | Thresholds provided for all endpoints. | Latency labels are present and calculated against thresholds. |
| P-006 | Landing page with all required sections, exact CTA text, exact href `#request-audit`, and matching placeholder section. | Static page meets content and same-page placeholder navigation requirements without backend behavior. |
| P-007 | Retention expires at 90 days with valid SMTP env vars and CSV below attachment threshold. | Sanitized post-retention CSV is emailed as an attachment; delivery status becomes `sent`. |
| P-008 | Retention expires at 90 days with valid SMTP env vars and CSV above attachment threshold. | Sanitized CSV is uploaded to private S3 and client email contains a time-limited presigned link; delivery status becomes `sent`. |

### 3.3 Negative Test Scenarios

| ID | Scenario | Expected Result |
| --- | --- | --- |
| N-001 | Configure 11 unique endpoints. | Validation blocks standard audit execution. |
| N-002 | Production environment without written waiver. | Execution is blocked. |
| N-003 | Production waiver present but internal checklist incomplete. | Execution is blocked. |
| N-004 | Raw data storage requested without written demand and approval. | Raw storage remains disabled; execution requiring raw storage is blocked. |
| N-005 | Resilience/burst requested without separate approval. | Burst testing is blocked and excluded from standard workflow. |
| N-006 | Bearer token included in mock failure message. | Token is redacted/excluded from all outputs. |
| N-007 | Landing page contains form, login, payment, or backend submission. | Defect; page violates MVP scope. |
| N-008 | Report URL is public permanent URL. | Defect; delivery violates private presigned requirement. |
| N-009 | Required SMTP env var is missing or invalid during post-retention send. | Delivery does not silently succeed; sanitized failure is surfaced and status is `failed` or `retry_pending`. |
| N-010 | SMTP secret/password appears in logs, notification, CSV, report, or retained metadata after failure. | Defect; SMTP secrets must be redacted everywhere. |
| N-011 | Landing page CTA uses `mailto:`, backend route, form action, payment URL, login URL, or any href other than `#request-audit`. | Defect; CTA must navigate to `#request-audit` only. |

### 3.4 Edge-Case Test Scenarios

| ID | Scenario | Expected Result |
| --- | --- | --- |
| E-001 | Duplicate `GET /health` appears twice in intake. | Duplicate is rejected or resolved before execution; count remains unique by `METHOD + PATH`. |
| E-002 | `GET /users` and `POST /users` are included. | Counted as two unique endpoints. |
| E-003 | Some endpoints have thresholds and others do not. | Pass/fail only appears for thresholded endpoints; others show observed-only. |
| E-004 | Audit completes fewer than expected cycles due to operator miss. | Report shows expected vs completed cycles and avoids misleading complete-audit claims. |
| E-005 | Mock API returns large body and sensitive-like headers. | Body/header data remains transient and absent from stored outputs. |
| E-006 | No endpoint observations are recorded. | Report displays clear empty state; CSV behavior is explicit and non-misleading. |
| E-007 | Presigned URL expires before client access. | Public access remains blocked; process supports regeneration guidance. |
| E-008 | Post-retention CSV size equals attachment threshold exactly. | Boundary rule is documented and applied consistently; delivery mode remains sanitized and private. |
| E-009 | Retention job is re-run after status `sent`. | No duplicate email is sent unless explicit operator override is supplied. |
| E-010 | Retention job is re-run after status `failed` or `retry_pending`. | Retry attempt is allowed; attempt count increments; failure/success state is updated without leaking secrets. |
| E-011 | Page is loaded directly with `#request-audit` hash. | Browser lands on the static placeholder section; no dynamic submission behavior occurs. |

### 3.5 Security and Privacy Test Scenarios

| ID | Scenario | Expected Result |
| --- | --- | --- |
| S-001 | Sentinel bearer token value appears in runtime configuration. | Sentinel token is absent from all customer-facing and persisted artifacts. |
| S-002 | Raw response body includes PII-like sentinel data. | PII-like sentinel data is absent from reports, CSV, logs, and retained metadata. |
| S-003 | Raw headers include `Authorization`, cookies, and custom secrets. | Header values are not persisted by default and not exported. |
| S-004 | S3 object ACL/policy permits public read. | Defect; objects must remain private with presigned access only. |
| S-005 | CSV includes unapproved columns or secret references. | Defect; CSV must contain sanitized metadata only. |
| S-006 | Raw-data exception enabled without approval reference. | Execution blocked or raw flags rejected fail-closed. |
| S-007 | SMTP password/user/app-password sentinel is configured through env vars. | Sentinel is absent from logs, failures, notifications, reports, CSV, retained metadata, and artifacts. |
| S-008 | Retention email uses private S3 link mode. | Link points to a private time-limited presigned URL; no public S3 website URL or public-read object is used. |

### 3.6 Implementation-Ready Automated Test Design

| Test ID | Maps To | Purpose | Input / Setup | Expected Output | Validation Logic |
| --- | --- | --- | --- | --- | --- |
| API-AUDIT-001 | AC-1 | Validate endpoint cap and `METHOD + PATH` uniqueness. | Audit configs with 0, 1, 10, 11, duplicate, and same-path/different-method endpoints. | Valid configs pass; 11 unique endpoints and unresolved duplicates fail closed. | Assert validation result, blocked-state message, and normalized endpoint identities. |
| API-AUDIT-002 | AC-2, AC-3 | Validate production authorization gates. | Production configs with no waiver, waiver only, and waiver plus internal approval. | Missing either gate blocks execution; both references allow approved scope only. | Assert execution command/validator refuses blocked configs and exposes actionable non-secret error. |
| API-AUDIT-003 | AC-4, AC-6, AC-8 | Validate redaction and no raw persistence. | Mock API returns sentinel bearer token, raw body, raw headers, and trace-like failure text. | HTML, CSV, logs, retained metadata, local workspace, and S3 keys contain sanitized metadata only. | Scan artifacts/logs/records for sentinels and assert CSV columns match approved contract. |
| API-AUDIT-004 | AC-5 | Validate private initial artifact delivery. | Generated HTML and CSV artifacts with configured private S3 bucket/prefix. | Separate time-limited presigned URLs are produced; public/permanent unauthenticated access is blocked. | Assert object ACL/policy is private, URL type is presigned, public URL access fails, and expiry behavior is documented. |
| API-AUDIT-005 | AC-9 | Validate automated retention SMTP configuration. | Expired retention record with complete/invalid/missing SMTP env var combinations. | Valid config attempts send; invalid config fails visibly with sanitized remediation state. | Assert env parsing, failure categories, redacted logs/notifications, `attempt_count`, `last_attempt_at`, and `failed`/`retry_pending` state. |
| API-AUDIT-006 | AC-9 | Validate post-retention attachment vs private-link behavior. | Expired retention records with CSV sizes below, equal to, and above attachment threshold. | Below/equal threshold follows documented attachment rule; above threshold uses private S3 presigned link. | Inspect email payload mode, S3 privacy in link mode, CSV sanitization, and final `sent` status after SMTP success. |
| API-AUDIT-007 | AC-9 | Validate retry and idempotency state. | Retention records in `pending`, `failed`, `retry_pending`, and `sent` states. | Failed states are retryable; already `sent` is not resent without explicit override. | Assert status transitions, attempt increments, no duplicate sends, and sanitized error history. |
| API-AUDIT-008 | AC-10 | Validate optional resilience/burst gate. | Standard audit, burst requested without approval, and burst requested with separate approval. | Standard workflow excludes burst; unapproved burst blocks; approved burst remains outside main workflow. | Assert workflow flags, approval reference requirement, and report scope language. |
| API-AUDIT-009 | AC-11, AC-12 | Validate schedule and latency interpretation. | 48-hour/default 5-per-day config, 1-per-day, 24-per-day with agreement, invalid 0/25, above-default without agreement, mismatched expected cycles, and threshold-present/absent/mixed endpoint results. | Default remains approximately 10 expected cycles; configurable frequencies reconcile expected cycles; invalid/out-of-agreement configs fail closed; pass/fail only for thresholded endpoints; observed-only where absent. | Assert schedule metadata, expected/completed cycles, bounds errors, agreement-reference gate, expected-cycle reconciliation, HTML labels, and CSV `latency_status`. |
| UI-AUDIT-001 | AC-13 | Validate static landing-page required content and CTA. | Rendered landing page at desktop/tablet/mobile widths. | Required sections present; CTA text exactly `Request a Reliability Audit`; href exactly `#request-audit`; one matching placeholder section exists. | DOM assertions for sections, exact text/href, single `id="request-audit"`, heading, responsive layout, keyboard focus, and accessible link semantics. |
| UI-AUDIT-002 | AC-13 | Validate absence of disallowed landing-page behavior. | Rendered landing page with network interception and DOM inspection. | No forms, email capture, `mailto:` CTA, backend calls, login, payment, scheduler/chat, or lead capture. | Assert no form/input/submit lead-capture elements, no forbidden href/action targets, and no network requests on CTA activation. |

## 4. Edge Cases

- Endpoint cap boundary: 0, 1, 10, and 11 unique endpoints.
- Endpoint identity normalization: method case, trailing slashes, query strings, duplicate paths, and same path with different methods. Normalization rules require implementation confirmation.
- Threshold boundary: observed latency equal to threshold, missing thresholds, mixed thresholds, zero/negative threshold values.
- Partial execution: missed cycle, failed endpoint, timeout, auth failure, network error, and no observations.
- Privacy sentinels in body, headers, token, error message, trace-like exception, URL, and operator notes.
- Presigned URL expiry and regeneration.
- Retention due date exactly at 90 days, before 90 days, and overdue after 90 days.
- SMTP configuration boundaries: missing required env vars, invalid numeric env vars, conflicting TLS/SSL flags, authentication-required vs no-auth server behavior, timeout handling, and sanitized failure surfacing.
- Retention delivery state transitions: `pending` to `sent`, `pending` to `failed`/`retry_pending`, retry from failed states, and no duplicate send for already `sent` records without override.
- Retention delivery mode boundary: CSV under threshold, equal to threshold, above threshold, provider attachment rejection, and private presigned-link fallback.
- Landing page small-screen table/card behavior and keyboard-only CTA/navigation access.
- Landing page CTA/anchor boundaries: exact case-sensitive CTA text, exact href `#request-audit`, exactly one matching anchor target, direct hash load, and absence of forms/email/backend submission behavior.

## 5. Test Types Covered

- Requirements traceability review.
- Functional validation: config validation, auth handling, execution metadata, reporting, CSV, private delivery, automated SMTP retention delivery, landing page.
- Negative validation: blocked production, blocked raw storage, blocked burst testing, endpoint over-limit, public URL, invalid SMTP configuration, disallowed landing-page functionality.
- Edge-case validation: duplicate endpoints, mixed thresholds, missed cycles, empty results, expired URLs, retention delivery retries, attachment-size thresholds.
- Security/privacy validation: bearer/SMTP secret redaction, no raw persistence, sanitized export, private delivery.
- Integration validation: config-to-execution, execution-to-report, report-to-CSV, artifacts-to-S3, retention-to-SMTP-email, retention-to-private-S3-link fallback.
- Accessibility validation: WCAG 2.2 AA-oriented semantic, keyboard, contrast, focus, table, and status-text checks.
- Responsive validation: desktop, tablet, and mobile layouts.
- Non-functional validation: bounded workload, safe defaults, operator evidence, failure recovery, maintainability of retention process.

## 6. Coverage Justification

The planned coverage directly maps every product acceptance criterion to at least one validation area and includes positive, negative, edge-case, security/privacy, non-functional, and UI/accessibility scenarios. Highest-risk areas receive explicit regression coverage: production authorization, raw data persistence, bearer-token leakage, SMTP secret leakage, sanitized CSV contents, private S3 delivery, retention delivery state, latency labeling, optional burst approval gates, automated retention/export-after-90-days email behavior, attachment vs private presigned-link delivery, and static landing-page CTA constraints.

## 7. Non-Functional Validation

| Area | Planned Validation |
| --- | --- |
| Security | Verify bearer token and SMTP secret exclusion, private S3 delivery, fail-closed approval gates, no public report URLs, and least-exposure artifact naming. |
| Privacy | Verify raw bodies, headers, and trace logs are transient by default; CSV/report contain sanitized metadata only. |
| Reliability | Verify missed cycles and partial failures are represented accurately without aborting unrelated endpoint reporting. |
| Performance / Load Safety | Verify standard workload remains bounded to up to 10 endpoints and approximately 10 cycles; burst testing excluded unless approved. |
| Accessibility | Validate semantic HTML, keyboard operation, visible focus, contrast, text-based statuses, and accessible tables. |
| Responsiveness | Validate landing page and report usability at mobile, tablet, and desktop breakpoints. |
| Operability | Validate operator-facing evidence references, blocked-state messages, retention ledger/process, SMTP failure surfacing, retryable delivery state, and presigned URL regeneration flow. |
| Auditability | Validate traceability from intake approvals to execution scope, generated artifacts, delivery, SMTP attempts, retention/export status, and failure remediation status. |

## 8. Test Data and Mock API Strategy

Future implementation should use controlled mock APIs rather than real production APIs by default.

### Mock Endpoint Set

- `GET /health` returns 200 with low latency.
- `GET /status` returns intermittent 500 to validate availability failure reporting.
- `POST /orders` returns 201 and validates method/path uniqueness.
- `GET /slow` returns delayed response for latency threshold tests.
- `GET /timeout` simulates timeout and sanitized error category.
- `GET /auth-required` requires bearer token and returns sanitized auth failure on invalid token.
- `GET /raw-sentinel` returns body/header/trace sentinel values to validate no raw persistence.

### Sentinel Values

- Bearer token sentinel: `qa_bearer_token_must_not_leak_12345`.
- SMTP password sentinel: `qa_smtp_password_must_not_leak_12345`.
- SMTP username sentinel: `qa_smtp_username_must_not_leak_12345`.
- Raw body sentinel: `qa_raw_body_must_not_persist_12345`.
- Raw header sentinel: `qa_raw_header_must_not_persist_12345`.
- Trace sentinel: `qa_trace_log_must_not_persist_12345`.
- Raw log sentinel: `qa_raw_log_must_not_persist_12345`.
- Raw response sentinel: `qa_raw_response_must_not_persist_12345`.
- Stack trace sentinel: `qa_stack_trace_must_not_persist_12345`.

### Data Sets

- Valid 10-endpoint configuration.
- Invalid 11-endpoint configuration.
- Duplicate endpoint configuration.
- Production config with no waiver, waiver-only, and waiver-plus-internal-approval variants.
- Threshold-present, threshold-absent, and mixed-threshold configurations.
- Raw-data exception absent and documented raw-data exception variants.
- Optional resilience/burst absent, requested-without-approval, and approved variants.
- SMTP env var variants: complete valid config; missing required values; invalid port/timeout/size; TLS+SSL conflict; auth failure; recipient rejection; timeout.
- Retention record variants: `pending`, `sent`, `failed`, and `retry_pending`, with `attempt_count`, `last_attempt_at`, and sanitized `last_error_category` expectations.
- Post-retention CSV size variants: below threshold, equal to threshold, above threshold, and provider attachment rejection to exercise attachment vs private presigned-link behavior.
- Landing-page DOM variants for automated UI checks: valid static page; missing anchor; duplicate anchor; wrong CTA href; form/email/backend/payment/login elements present.

## 9. Manual QA Checklist

Future manual QA execution should confirm:

- [ ] Product scope remains manual/operator-assisted, not SaaS.
- [ ] Standard audit caps at 10 unique `METHOD + PATH` endpoints.
- [ ] Production testing is blocked without written client waiver/agreement.
- [ ] Production testing is blocked without internal approval checklist completion.
- [ ] Bearer tokens are handled as sensitive credentials and excluded from outputs.
- [ ] Raw bodies, raw responses, headers, raw logs, trace logs, and stack traces are not displayed or stored by default.
- [ ] Raw diagnostic artifact collection, inclusion/display, or persistence exception requires written demand and approval before collection.
- [ ] Sanitized result model contains approved metadata fields only.
- [ ] CSV export contains sanitized metadata only.
- [ ] HTML report/dashboard includes scope, methodology, results, CSV, privacy, delivery, and retention notes.
- [ ] Reports and CSV exports are delivered through private S3 presigned URLs only.
- [ ] Sanitized metadata retention is set to 90 days.
- [ ] Post-retention CSV export/email process is automated, has due-date tracking, delivery evidence, and operator-visible remediation state.
- [ ] SMTP env var validation covers required, optional, conditional, invalid, and conflicting values.
- [ ] SMTP credentials and failure diagnostics are redacted from logs, notifications, customer artifacts, CSV, and reports.
- [ ] Retention email delivery supports retryable `failed`/`retry_pending` state and prevents duplicate sends after `sent` unless explicitly overridden.
- [ ] Post-retention CSV delivery is validated for both attachment mode and private S3 presigned-link mode.
- [ ] Resilience/burst testing is excluded from standard workflow unless separately approved in writing.
- [ ] Latency pass/fail labels appear only when thresholds are provided.
- [ ] Landing page includes all required sections.
- [ ] CTA text is exactly `Request a Reliability Audit`.
- [ ] CTA href is exactly `#request-audit` and exactly one matching visible `id="request-audit"` placeholder section exists.
- [ ] CTA uses placeholder navigation only and does not submit forms, open email/`mailto:`, start payment, create login, call backend APIs, trigger scheduling/chat widgets, or capture/store leads.
- [ ] Landing page and report meet keyboard, focus, contrast, semantic heading, status text, and table accessibility expectations.
- [ ] Mobile, tablet, and desktop layouts remain usable.

## 10. Release Readiness Criteria for Future Implementation

Future implementation should not be considered release-ready unless all of the following are evidenced:

- All AC-1 through AC-13 critical validation tests pass.
- No unresolved blocker or high-severity privacy/security defects remain.
- Production and resilience/burst approval gates fail closed.
- Bearer token and raw-data sentinel scans pass across all generated artifacts and logs.
- CSV and HTML reports contain sanitized metadata only.
- S3 report delivery uses private objects and presigned URLs only.
- Retention/export-after-90-days workflow has automated SMTP delivery, environment-variable validation, sanitized failure surfacing, retryable state, evidence trail, and passing validation.
- Both post-retention delivery modes pass: direct sanitized CSV attachment and private S3 presigned-link fallback for oversized/attachment-constrained CSVs.
- Landing page is static and informational only, with required sections, exact CTA text, exact href `#request-audit`, matching placeholder section, and no form/email/backend submission behavior.
- Accessibility and responsive checks pass for landing page and report/dashboard.
- Manual operator checklist is complete and maps to production, raw-data, endpoint, threshold, retention, and burst approval requirements.
- Test evidence includes execution output, inspected artifacts, relevant logs, and any screenshots where UI validation applies.

## 11. Risks and Mitigations

| Risk | QA Mitigation |
| --- | --- |
| Production testing proceeds without adequate authorization. | Require negative gate tests for missing waiver and missing internal approval; inspect operator evidence references. |
| Secrets or raw API data leak into reports, CSV, logs, or S3 keys. | Use sentinel values and artifact-wide scans; require sanitized metadata contract tests. |
| Public S3 configuration accidentally exposes reports. | Validate bucket/object privacy, public access blocking, and presigned-only access. |
| Landing page implies SaaS, payment, login, or self-service onboarding. | Static page content and behavior tests; inspect for forms, backend calls, login/payment components. |
| Landing page CTA drifts into lead capture or email submission. | Enforce exact CTA text, exact href `#request-audit`, exactly one matching static anchor section, and negative DOM/network/form checks. |
| Latency pass/fail labels are misleading without thresholds. | Require threshold-absent and mixed-threshold report/CSV tests. |
| Optional resilience/burst testing is mistaken for standard audit behavior. | Gate and report-scope tests proving burst tests are separate and approval-bound. |
| 90-day retention/export workflow fails silently. | Require automated SMTP env validation, sanitized failure surfacing, failure notification, retryable delivery state, and evidence of due-date processing. |
| SMTP credentials leak during error handling. | Use SMTP sentinel secrets and scan logs, notifications, retained records, reports, and CSV outputs. |
| Oversized post-retention CSV cannot be emailed as attachment. | Validate size threshold behavior and private presigned-link fallback with private S3 object checks. |
| Endpoint scope creep exceeds MVP capacity. | Boundary tests for endpoint count and uniqueness. |
| Accessibility is deferred because page/report are static. | Include WCAG-oriented checks in release readiness criteria. |

## 12. Deferred QA Scope

- SaaS onboarding, customer accounts, login, payment, and self-service audit configuration.
- Contact form submission or lead capture backend.
- Automated contract signing or automated production authorization verification.
- Schema validation.
- Standardized auth methods beyond bearer token.
- Default load testing, stress testing, or resilience/burst testing as part of standard workflow.
- Additional endpoint pricing behavior.
- Managed monitoring subscription workflows.
- Full production API testing without explicit written waiver/agreement and internal approval.
- Non-SMTP post-retention delivery mechanisms outside the environment-variable SMTP workflow.

## 13. Open Questions

1. What format and storage location should be used for written waivers/agreements and internal approval checklists?
2. What expiration duration should be used for S3 presigned report URLs?
3. What concrete sender address and remediation recipient values should be configured for SMTP environments using `RELIABILITYKIT_SMTP_FROM_EMAIL` and `RELIABILITYKIT_RETENTION_FAILURE_NOTIFY_EMAIL`?
4. After the 90-day CSV export/email, should source sanitized metadata be deleted, archived, or retained elsewhere?
5. What static site path/framework should host the Phase 1 landing page in this repository?
6. What default endpoint request timeout should be used for audit checks?
7. How should endpoint identity normalize query strings, trailing slashes, case sensitivity, and URL templates?
8. For latency exactly equal to a threshold, should the expected label be pass or fail?
9. What evidence format is required for raw-data storage exceptions and optional resilience/burst approvals?
10. What S3 presigned URL regeneration SLA or manual process should be communicated to clients?
