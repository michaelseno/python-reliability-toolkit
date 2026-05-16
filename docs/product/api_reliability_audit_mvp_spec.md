# Product Specification: 48-Hour API Reliability Audit MVP

**Status:** Authorized for full MVP implementation  
**Artifact Owner:** Product Owner  
**Repository:** `python_reliability_toolkit`  
**Scope Type:** Manual/operator-assisted MVP, not SaaS  
**Last Updated:** 2026-05-13

## 1. Executive Summary

The 48-Hour API Reliability Audit MVP is a manual/operator-assisted service offering built around the Python Reliability Toolkit. The service evaluates up to 10 API endpoints over a 48-hour period using scheduled endpoint checks, the standard runtime scan pack, sanitized reporting, and private report delivery.

Implementation of the full MVP described in this specification is authorized for branch `feature/api_reliability_audit_mvp`. The authorized implementation must preserve the manual/operator-assisted MVP scope and must not introduce SaaS onboarding, backend lead capture, payment, login, or self-service audit configuration.

The MVP is designed to validate market demand for a packaged reliability audit before investing in SaaS workflows, automated onboarding, payment processing, customer accounts, or managed monitoring.

The customer receives an HTML report/dashboard and sanitized CSV export through private S3 presigned URLs. The generated report is the product's primary selling artifact and must be substantially informative, impact-oriented, and actionable. The MVP prioritizes safety, authorization, minimal data retention, and clear handling of production APIs.

## 2. Problem Statement

Small engineering teams and API owners often lack an easy, low-commitment way to understand whether their APIs are reliable, responsive, and consistently available over a short evaluation window. Existing monitoring products may require ongoing setup, account configuration, or subscription commitments.

This MVP solves the problem by offering a bounded, 48-hour reliability audit that produces actionable evidence without requiring a SaaS onboarding flow or long-term monitoring commitment.

## 3. Goals and Non-Goals

### Goals

- Provide a clearly packaged 48-hour reliability audit for up to 10 API endpoints.
- Support manual/operator-assisted setup and execution.
- Capture availability, status code, latency, scan-pack scenario outcomes, and sanitized metadata across approximately 10 check cycles.
- Deliver a private, polished, impact-oriented HTML report/dashboard and sanitized CSV export that explain what was tested, what failed or passed, why it matters, and what remediation is recommended.
- Execute the standard audit scan pack from `reliabilitykit/core/scan_packs.py` for each audited endpoint during runtime.
- Include bounded `burst_stability` as the only approved resilience-style scenario in the standard audit scan pack, runtime, and report.
- Enforce written authorization before testing production APIs.
- Avoid storing raw API response bodies, headers, or trace logs by default.
- Validate whether customers will pay for a structured API reliability audit.
- Publish a Phase 1 static product landing page explaining the service.

### Non-Goals

- Build a SaaS product.
- Build automated customer signup, login, payment, or self-service audit configuration.
- Build form submission workflows on the landing page.
- Build landing-page email submission, backend lead capture, or automated sales intake flows.
- Provide continuous managed monitoring as part of the MVP.
- Provide schema validation in the MVP.
- Add resilience, fault-injection, chaos, destructive, or load-testing workflows beyond the explicitly approved bounded `burst_stability` standard-scan scenario.
- Treat `burst_stability` as load testing or as permission to expand the standard audit into broader resilience testing.
- Store raw response bodies, headers, or trace logs by default.

## 4. Target Users / Personas

### Primary Persona: Startup Technical Founder

- Owns or oversees a small production API.
- Needs evidence of API reliability before a launch, demo, fundraising event, or customer rollout.
- Wants a fast, low-friction review without adopting a full monitoring platform.

### Secondary Persona: Engineering Lead at a Small Team

- Responsible for API uptime and performance.
- Wants an external reliability snapshot to validate internal assumptions.
- Needs reportable findings that can be shared with stakeholders.

### Secondary Persona: Consultant or Agency Delivering APIs

- Wants to validate API reliability before handoff to a client.
- Needs a simple third-party audit artifact to support delivery quality.

## 5. MVP Scope

### In Scope

- Standard audit package covering up to 10 endpoints.
- Endpoint definition as a unique `METHOD + PATH` combination.
- Manual/operator-assisted collection of endpoint inventory, auth details, expected latency thresholds, and test authorization.
- Bearer token authentication support as the first supported auth method.
- Scheduled checks at a default frequency of 5 checks per day for 48 hours, resulting in approximately 10 check cycles total.
- Measurement of status code, availability result, latency, timestamp, endpoint identifier, method, path, and sanitized error/category metadata where applicable.
- Client-provided expected latency thresholds.
- Observed-latency-only reporting when thresholds are not provided.
- Runtime execution of the configured standard audit scan pack from `reliabilitykit/core/scan_packs.py` for each endpoint.
- Per-endpoint scan-pack result capture for each resolved scenario, including status, severity, rationale/purpose, sanitized evidence, affected cycles or timestamps where available, and remediation guidance.
- Bounded `burst_stability` execution as part of the standard audit scan pack and report, without requiring separate optional resilience approval.
- HTML report/dashboard generation as the main customer-facing artifact, including executive verdict, impact-oriented findings, endpoint scorecards, scan-pack matrix, test-level details, methodology, privacy notes, and export access.
- Sanitized CSV export from the HTML report/dashboard, including approved scan-pack result metadata when available.
- Private S3 presigned URL delivery for report artifacts.
- Sanitized metadata retention for 90 days.
- Automated conversion/export of retained metadata to CSV after 90 days and email delivery to the client using SMTP configuration supplied through environment variables.
- Transient processing of raw API response bodies, headers, and trace logs without default persistence.
- Written approval workflow for any raw data storage exception.
- Written waiver/agreement for production API testing.
- Internal approval checklist before production testing.
- Optional resilience, fault-injection, chaos, destructive, broader burst, or load testing only when separately approved in writing and outside the standard audit scope. This exclusion does not apply to the bounded standard `burst_stability` scan-pack scenario.
- Phase 1 static product landing page.

## 6. Explicit Out of Scope

- Self-service onboarding.
- Customer accounts or login.
- Payment processing.
- Backend services for the landing page.
- Contact form submission or lead capture form handling.
- Landing-page email capture or CTA email/form submission flows.
- Automated contract signing.
- Automated production authorization verification.
- Auth methods other than bearer token unless manually handled outside MVP scope.
- Schema validation.
- Load testing as part of the default audit.
- Any resilience/burst testing beyond the bounded standard `burst_stability` scan-pack scenario without separate written approval.
- Fault injection, chaos testing, destructive testing, soak testing, stress testing, spike testing, capacity testing, or other load/performance testing unless separately approved outside the standard audit.
- Expanding `burst_stability` into high-concurrency, high-volume, long-duration, capacity-discovery, saturation, or production load testing.
- Persistent raw response body, header, or trace log storage by default.
- Public report URLs.
- Additional endpoint pricing in the first MVP unless later explicitly approved.

## 7. User Journeys

### Journey 1: Standard Audit Request

1. Prospective client reviews the static landing page.
2. Client selects the CTA labeled “Request a Reliability Audit.”
3. CTA navigates to the placeholder destination `#request-audit`.
4. Operator manually coordinates audit intake outside the website; landing-page form submission, email submission, and backend lead capture are deferred and not part of this implementation.
5. Client provides endpoint list, auth details, expected latency thresholds if available, and written authorization.
6. Operator validates endpoint count and authorization.
7. Operator executes the 48-hour audit.
8. Operator delivers the HTML report/dashboard and sanitized CSV through private S3 presigned URLs.

### Journey 2: Production API Audit

1. Client requests testing against production APIs.
2. Client provides written waiver/agreement authorizing production testing.
3. Operator completes internal production approval checklist.
4. Operator proceeds only if both written authorization and internal approval are complete.
5. Operator executes the audit within agreed boundaries.

### Journey 3: Audit Without Latency Thresholds

1. Client does not provide expected latency thresholds.
2. Operator executes the audit.
3. Report includes observed latency metrics.
4. Report does not label latency as pass or fail.

### Journey 4: Standard Scan-Pack Audit Including Bounded Burst Stability

1. Operator configures the standard audit scan pack for the approved endpoint list.
2. Runtime applies each resolved scan-pack scenario to each endpoint during the audit window.
3. The bounded `burst_stability` scenario runs as part of the standard scan pack using architect-approved safety bounds.
4. The report presents each endpoint's scan-pack outcomes, including `burst_stability`, with sanitized evidence and remediation guidance.
5. The report and CSV exclude raw logs, raw responses, raw bodies, raw headers, trace logs, stack traces, tokens, and secrets by default.

### Journey 5: Optional Broader Resilience or Load Testing Request

1. Client requests resilience, burst, fault-injection, chaos, destructive, stress, spike, soak, capacity, or load testing beyond bounded standard `burst_stability`.
2. Operator explains that this is not part of the standard audit workflow.
3. Client provides separate written approval.
4. Operator performs optional testing only within the separately approved boundaries and outside the standard audit scope.

## 8. Functional Requirements

### FR-1 Endpoint Scope

- The standard audit must support up to 10 endpoints.
- An endpoint must be counted as one unique `METHOD + PATH` combination.
- Different methods on the same path must count as separate endpoints.
- The same method on different paths must count as separate endpoints.

### FR-2 Audit Duration and Frequency

- The default audit duration must be 48 hours.
- The default run frequency must be 5 checks per day.
- The expected total number of check cycles must be approximately 10 over the 48-hour period.
- `checks_per_day` must be configurable within MVP bounds of minimum 1 and maximum 24.
- Values above the default 5 checks per day require an operator/client agreement reference before execution.
- `expected_check_cycles` must be reconciled with the configured `checks_per_day` over the 48-hour duration.

### FR-3 Authentication

- The MVP must support bearer token authentication first.
- Bearer tokens must be handled as sensitive credentials.
- Bearer tokens must not appear in customer-facing reports or CSV exports.

### FR-4 Production Testing Authorization

- Production API testing must require written client waiver/agreement.
- Production API testing must require completion of an internal approval checklist before any test execution.
- Testing must not proceed if either written client authorization or internal approval is missing.

### FR-5 Data Collection

- The audit must collect sanitized metadata needed to report reliability results.
- Sanitized metadata may include endpoint identifier, method, path, timestamp, status code, availability result, latency, check cycle identifier, scan-pack identifier, scenario identifier, scenario name, scenario category, scenario status, severity, sanitized evidence summary, affected cycles or timestamps, recommendation/remediation guidance, and sanitized error/category information.
- Raw API response bodies, raw responses, raw headers, raw logs, trace logs, and stack traces must be transient and must not be displayed or stored by default.

### FR-5A Standard Scan-Pack Runtime Execution

- The standard audit runtime must apply the configured standard audit scan pack from `reliabilitykit/core/scan_packs.py` to each audited endpoint.
- The reportable standard scan pack must include the scenarios resolved from `core_reliability_scan`: Baseline Health, Repeated Stability, Burst Stability, Invalid Payload Handling, Missing Fields Validation, Auth Failure Handling, Timeout Sensitivity, and Response Consistency, unless the scan-pack source changes through a separately approved product decision.
- Each endpoint must have a result for every resolved standard scan-pack scenario, or an explicit `Not run`, `Not applicable`, or `Incomplete` status with sanitized rationale.
- Runtime scan-pack execution must capture sanitized result metadata sufficient for report generation and QA validation.
- Scan-pack execution must preserve the configured 48-hour audit window, endpoint cap, authorization rules, privacy rules, and raw-data exclusions.

### FR-5B Bounded Standard `burst_stability` Scenario

- `burst_stability` must be included in the standard audit scan pack/runtime/report as the only approved resilience-style standard scenario.
- Standard `burst_stability` must not require the optional broader resilience/burst approval gate.
- Standard `burst_stability` must remain bounded by architect-approved runtime limits for concurrency, total requests per endpoint, duration, retry behavior, timeout behavior, and endpoint sequencing before implementation.
- Standard `burst_stability` must not be used to discover capacity limits, saturate systems, perform stress/spike/soak testing, or simulate destructive/fault-injection behavior.
- If architect-approved bounds are absent from implementation handoff, implementation must not invent bounds and must escalate for clarification before runtime changes.

### FR-6 Raw Data Exception Handling

- Raw data storage may occur only if explicitly demanded by the client and approved in writing.
- Any raw diagnostic artifact collection, report inclusion/display, or persistence exception must be explicitly requested by the client and documented with written approval/reference before collection.
- Raw data exception handling is not part of the default workflow.

### FR-7 Latency Thresholds

- The client may provide expected latency thresholds.
- If thresholds are provided, the report may evaluate latency against those thresholds.
- If thresholds are absent, the report must show observed latency only.
- If thresholds are absent, the report must not label latency as pass or fail.

### FR-8 Report Generation

- The audit must produce an HTML report/dashboard.
- The HTML report/dashboard must include or link to a sanitized CSV export.
- The HTML report/dashboard must be the primary customer-facing value artifact and must provide an executive verdict, concise KPI summary, prioritized findings, endpoint health scorecards, scan-pack matrix, test-level details, latency/availability summaries, methodology/scope notes, privacy notes, and export access.
- For each endpoint, the report must show every resolved standard scan-pack scenario with status, severity when relevant, rationale/purpose, sanitized evidence, affected cycles or timestamps where available, and remediation guidance.
- The report must explain impact in customer-facing language, including which failures or warnings matter most and what next action is recommended.
- If a scenario was not run, not applicable, or incomplete, the report must state that status and provide sanitized rationale instead of leaving the result blank.
- The report must avoid exposing bearer tokens, raw logs, raw responses, raw response bodies, raw headers, trace logs, and stack traces.

### FR-9 Report Delivery

- Reports must be delivered using private S3 presigned URLs.
- Report URLs must not be public unauthenticated permanent links.
- The delivery workflow must allow the client to access the HTML report/dashboard and sanitized CSV export.

### FR-10 CSV Export

- CSV exports must contain sanitized metadata only.
- CSV exports must include approved sanitized endpoint-cycle metadata and approved sanitized scan-pack result metadata needed to reconcile the HTML report.
- CSV exports must not contain bearer tokens, secrets, raw logs, raw responses, raw response bodies, raw headers, trace logs, or stack traces.

### FR-11 Retention and Post-Retention Export

- Sanitized metadata must be retained for 90 days.
- After 90 days, retained metadata must be converted/exported to CSV.
- The post-retention CSV must be emailed to the client.
- Post-retention CSV email delivery must be automated through SMTP settings provided by environment variables.
- The retained metadata must not include raw logs, raw responses, stack traces, raw response bodies, raw headers, or trace logs unless an explicit client request and written raw data approval/reference exists.

### FR-12 Optional Broader Resilience, Fault, or Load Testing

- Resilience, broader burst, fault-injection, chaos, destructive, stress, spike, soak, capacity, or load testing beyond bounded standard `burst_stability` must be optional only.
- These broader tests must not be part of the standard audit workflow.
- These broader tests must require separate written approval before execution.
- The existence of standard `burst_stability` must not be interpreted as approval to add additional resilience, burst, fault, chaos, destructive, or load tests to the standard scan pack.

### FR-13 Static Landing Page

- A Phase 1 static landing page must describe the audit service.
- The landing page must be informational only.
- The landing page must not include backend functionality, payment, login, or form submission in the MVP.
- The CTA text must be exactly: “Request a Reliability Audit.”
- The CTA destination must be the placeholder anchor `#request-audit`.
- The CTA must not submit a form, open an email submission flow, call a backend API, initiate payment, or create/login to an account.

## 9. Privacy, Safety, Authorization Requirements

- Production API testing requires written waiver/agreement from the client.
- Production API testing requires internal approval checklist completion.
- Operators must confirm endpoint scope before executing tests.
- Operators must confirm that standard bounded `burst_stability` remains within approved bounds.
- Operators must confirm whether any broader resilience, burst, fault-injection, chaos, destructive, or load testing beyond standard `burst_stability` is requested and separately approved.
- Bearer tokens must be treated as confidential secrets.
- Customer-facing reports and CSV exports must contain sanitized metadata only.
- Raw response bodies, headers, and trace logs must be transient and not stored by default.
- Raw logs, raw responses, raw response bodies, raw headers, trace logs, and stack traces must not be displayed or persisted by default.
- Any raw diagnostic artifact collection, report inclusion/display, or persistence requires explicit written client demand and written approval/reference.
- Reports must be delivered only through private S3 presigned URLs.

## 10. Static Landing Page Requirements

The static landing page must include the following sections:

1. **Hero headline** describing the 48-hour API Reliability Audit.
2. **Problem/value proposition** explaining why teams need a short reliability audit.
3. **What’s included** listing audit duration, endpoint cap, check frequency, report, and sanitized CSV.
4. **Privacy/safety guarantees** covering authorization, private delivery, sanitized metadata, and no raw data persistence by default.
5. **Pricing** showing the standard MVP price and optional validation pricing if used.
6. **How it works** explaining request, intake, approval, 48-hour checks, and report delivery.
7. **FAQ** addressing endpoint limits, production testing, auth, data retention, latency thresholds, standard bounded `burst_stability`, and exclusion of broader unapproved resilience/fault/load testing.
8. **CTA** using the exact text “Request a Reliability Audit.”

Landing page constraints:

- Must be static and informational only.
- Must not require a backend.
- Must not include login.
- Must not include payment processing.
- Must not submit forms.
- Must not include email capture or backend lead capture.
- CTA destination must be the placeholder anchor `#request-audit`.

## 11. Pricing/Package Assumptions

- Standard public MVP price: **$750** for one 48-hour API Reliability Audit covering up to 10 endpoints.
- Optional early validation price: **$500** for limited first audits.
- Optional broader resilience/burst add-on during validation, outside the standard audit and requiring separate approval: **+$300**.
- Later optional broader resilience/burst add-on price, outside the standard audit and requiring separate approval: **+$500**.
- Standard bounded `burst_stability` is included in the standard audit scan pack and is not priced as an optional add-on.
- Future managed monitoring add-on: starting at **$399/month**.
- Additional endpoint pricing is deferred; possible future price is **+$35 per endpoint** after the process is proven.
- Additional endpoint pricing should not be included in the first MVP unless explicitly approved later.

## 12. Acceptance Criteria

### AC-1 Endpoint Cap and Definition

Given a client submits endpoints for a standard audit  
When the operator reviews the endpoint list  
Then the audit must accept no more than 10 unique `METHOD + PATH` combinations.

Given two entries share the same path but use different HTTP methods  
When endpoint count is calculated  
Then each unique `METHOD + PATH` combination must count as a separate endpoint.

### AC-2 Production Waiver/Authorization

Given a client requests testing against a production API  
When written waiver/agreement has not been provided  
Then production testing must not proceed.

Given a client requests testing against a production API  
When written waiver/agreement has been provided  
Then the operator may proceed only after internal production approval is also complete.

### AC-3 Internal Production Approval

Given written client authorization exists for production testing  
When the internal approval checklist is incomplete  
Then production testing must not proceed.

Given written client authorization exists and the internal approval checklist is complete  
When the endpoint scope is confirmed  
Then production testing may proceed within the approved scope.

### AC-4 Bearer Token Handling

Given a client provides a bearer token for API authentication  
When the audit is configured and executed  
Then the bearer token must be treated as sensitive and must not appear in the HTML report or CSV export.

### AC-5 Private S3 Presigned Delivery

Given an audit report has been generated  
When the report is delivered to the client  
Then the HTML report/dashboard and sanitized CSV export must be delivered through private S3 presigned URLs.

### AC-5A Standard Scan-Pack Execution Per Endpoint

Given a standard audit is executed for an approved endpoint list  
When runtime checks are performed  
Then each endpoint must be evaluated against every scenario resolved from the configured standard audit scan pack.

Given the configured standard audit scan pack resolves scenarios from `core_reliability_scan`  
When the audit runtime records results  
Then results must include Baseline Health, Repeated Stability, Burst Stability, Invalid Payload Handling, Missing Fields Validation, Auth Failure Handling, Timeout Sensitivity, and Response Consistency for each endpoint, or an explicit `Not run`, `Not applicable`, or `Incomplete` status with sanitized rationale.

Given scan-pack scenario execution produces evidence  
When scenario results are persisted for reporting  
Then only sanitized scenario metadata may be retained, and raw logs, raw responses, raw bodies, raw headers, trace logs, stack traces, bearer tokens, and secrets must be excluded by default.

### AC-5B Impact-Oriented Report Substance

Given a standard audit completes with scan-pack results  
When the HTML report/dashboard is generated  
Then the report must include an executive verdict, KPI summary, prioritized findings, endpoint health scorecards, scan-pack matrix, test-level details, latency/availability summaries, methodology/scope notes, privacy notes, and export access.

Given an endpoint has scan-pack results  
When a reviewer views that endpoint in the report  
Then every resolved scan-pack scenario must display status, severity when relevant, rationale/purpose, sanitized evidence, affected cycles or timestamps where available, and remediation guidance.

Given a scan-pack scenario has failed, warned, not run, is not applicable, or is incomplete  
When the report renders the scenario  
Then the report must state the scenario status and sanitized rationale without leaving the result blank.

Given the report includes findings  
When findings are displayed  
Then they must be prioritized by severity and impact using customer-facing language that explains why the issue matters and what next action is recommended.

### AC-5C Bounded Standard `burst_stability`

Given a standard audit is executed  
When the standard scan pack is applied  
Then bounded `burst_stability` must be included for each endpoint without requiring separate optional resilience approval.

Given bounded `burst_stability` is executed  
When runtime limits are evaluated  
Then execution must remain within architect-approved limits for concurrency, total requests per endpoint, duration, retry behavior, timeout behavior, and endpoint sequencing.

Given architect-approved runtime bounds for `burst_stability` are missing  
When implementation or execution is attempted  
Then implementation must escalate for clarification and must not invent bounds or expand the test into load testing.

Given standard `burst_stability` is included in the audit  
When the scan pack is reviewed  
Then no additional resilience, fault-injection, chaos, destructive, stress, spike, soak, capacity, or load-testing scenarios may be added to the standard audit without separate approval.

### AC-6 No Raw Data Persistence by Default

Given an audit check receives API response bodies, headers, or trace data during execution  
When the default audit workflow is used  
Then raw response bodies, raw headers, and trace logs must remain transient and must not be stored.

### AC-7 Raw Data Storage Exception

Given a client requests raw data storage  
When explicit written demand and written approval are not both present  
Then raw data must not be stored.

Given explicit written demand and written approval are both present  
When raw data storage is performed  
Then the exception must be documented as outside the default workflow.

### AC-8 Sanitized CSV Only

Given the HTML report/dashboard includes CSV export functionality  
When the CSV is generated  
Then the CSV must contain sanitized metadata only and must exclude bearer tokens, secrets, raw logs, raw responses, raw response bodies, raw headers, trace logs, and stack traces.

Given scan-pack result metadata is included in the HTML report  
When the CSV is generated  
Then the CSV must include approved sanitized scan-pack result fields sufficient to reconcile endpoint scenario statuses with the HTML report.

### AC-9 90-Day Metadata Retention and Email Export

Given sanitized metadata has been collected for an audit  
When the audit completes  
Then sanitized metadata must be retained for 90 days.

Given sanitized metadata reaches the 90-day retention point  
When retention expires  
Then the metadata must be converted/exported to CSV and emailed to the client through the automated SMTP-based delivery workflow configured by environment variables.

Given the SMTP environment variable configuration is missing or invalid  
When the post-retention CSV email workflow attempts delivery  
Then email delivery must not silently succeed and the failure must be surfaced for operator remediation without exposing secrets in customer-facing artifacts.

### AC-10 Optional Broader Resilience, Fault, or Load Testing Approval

Given a client has purchased or requested the standard audit  
When no separate written approval exists for broader resilience, fault-injection, chaos, destructive, stress, spike, soak, capacity, or load testing  
Then those broader tests must not be performed.

Given separate written approval exists for broader resilience, fault-injection, chaos, destructive, stress, spike, soak, capacity, or load testing  
When the operator performs the test  
Then the test must remain outside the main audit workflow and within the separately approved scope.

Given a standard audit includes bounded `burst_stability`  
When optional broader-test approval is absent  
Then bounded `burst_stability` may still run as part of the standard scan pack, but no other broader resilience, fault, chaos, destructive, or load tests may run.

### AC-11 Latency Threshold Behavior

Given a client provides expected latency thresholds  
When the report is generated  
Then latency results may be labeled against those thresholds.

Given a client does not provide expected latency thresholds  
When the report is generated  
Then the report must show observed latency only and must not label latency as pass or fail.

### AC-12 Audit Frequency

Given a standard 48-hour audit is configured  
When the default run frequency is used  
Then checks must run 5 times per day for approximately 10 total check cycles.

Given a standard 48-hour audit is configured  
When `checks_per_day` is set below 1 or above 24  
Then validation must block execution.

Given a standard 48-hour audit is configured  
When `checks_per_day` is greater than the default 5 without an operator/client agreement reference  
Then validation must block execution.

Given a standard 48-hour audit is configured  
When `checks_per_day` is configured within bounds  
Then `expected_check_cycles` must match the configured frequency over 48 hours.

### AC-13 Static Landing Page Content and CTA

Given the Phase 1 landing page is created  
When a visitor views the page  
Then the page must include hero headline, problem/value proposition, what’s included, privacy/safety guarantees, pricing, how it works, FAQ, and CTA sections.

Given the Phase 1 landing page CTA is displayed  
When a visitor reads the CTA  
Then the CTA text must be exactly “Request a Reliability Audit.”

Given the Phase 1 landing page CTA is displayed  
When a visitor activates the CTA  
Then the CTA must navigate to `#request-audit` only.

Given the Phase 1 landing page is implemented for MVP  
When the page is reviewed  
Then it must not include backend functionality, payment processing, login, form submission, email submission, or lead capture.

## 13. Metrics / Success Criteria

- At least one paid or validation-priced audit can be completed manually without SaaS onboarding.
- Operator can complete intake, authorization validation, audit execution, report generation, and delivery for up to 10 endpoints.
- Standard audit runtime applies the configured scan pack to each endpoint and captures sanitized scenario-level results.
- The generated HTML report provides enough impact-oriented substance for a customer to understand overall verdict, endpoint priorities, failed/warning/not-run scenarios, sanitized evidence, and recommended remediation.
- Bounded `burst_stability` is included as standard scan-pack evidence without introducing load testing or broader unapproved resilience testing.
- Report artifacts are delivered privately through S3 presigned URLs.
- Customer-facing CSV contains sanitized metadata only.
- No raw response bodies, headers, or trace logs are stored during default audits.
- Landing page clearly communicates the offer, price, workflow, and safety posture.
- Customer feedback indicates whether the audit package is understandable and worth purchasing.

## 14. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Production testing could cause customer concern or operational risk. | Require written waiver/agreement and internal approval checklist before production testing. |
| Raw or sensitive data could leak into reports. | Restrict reports and CSV exports to sanitized metadata only; exclude tokens, raw bodies, headers, and trace logs. |
| Customers may expect SaaS functionality. | Clearly state that MVP is manual/operator-assisted and landing page is informational only. |
| Latency interpretation may be disputed without thresholds. | Require client-provided thresholds for pass/fail labeling; otherwise report observed latency only. |
| `burst_stability` could be misinterpreted as load testing or as approval for broader resilience testing. | Define `burst_stability` as the only bounded standard resilience-style scenario; require architect-approved runtime bounds; explicitly exclude other resilience/fault/chaos/destructive/load testing without separate approval. |
| Report remains too thin to support the product's main value proposition. | Require per-endpoint scan-pack details, impact-oriented findings, sanitized evidence, and remediation guidance in the HTML report. |
| Endpoint scope creep may reduce service feasibility. | Enforce up to 10 unique `METHOD + PATH` endpoints for the standard audit. |
| Retention workflow may be operationally forgotten. | Architecture and QA artifacts must define and validate 90-day export/email procedure. |

## 15. Open Questions / Deferred Decisions

### Open Questions

- What is the required format and storage location for written waivers/agreements and internal approval checklists?
- What expiration duration should be used for S3 presigned report URLs?
- What exact SMTP environment variable names and required fields will implementation standardize for automated post-retention CSV email delivery?
- What sender email address and support/remediation recipient should be used for automated SMTP delivery failures?
- What exact architect-approved runtime bounds will be used for standard `burst_stability` concurrency, total requests per endpoint, duration, retry behavior, timeout behavior, and endpoint sequencing?
- What exact sanitized CSV columns will represent scan-pack scenario results while preserving privacy exclusions?

### Deferred Decisions

- Whether to add schema validation based on customer demand.
- Whether to include additional endpoint pricing after the process is proven.
- Whether to create SaaS onboarding, payment, login, or self-service configuration.
- Whether to add landing-page CTA form submission, email submission, or lead capture after MVP validation.
- Whether to formalize managed monitoring starting at $399/month.
- Whether to standardize non-bearer-token authentication methods.
- Whether to offer separately approved broader resilience, fault-injection, chaos, destructive, or load-testing services after MVP validation.

## 16. Phase Roadmap

### Phase 1: Planning and Static Offer Validation

- Create product specification.
- Create architecture plan.
- Create QA/test plan.
- Create UI/UX plan for static landing page and report/dashboard expectations.
- Publish or prepare static informational landing page.

### Phase 2: Manual Audit MVP Execution

- Run operator-assisted intake.
- Validate authorization and endpoint scope.
- Execute 48-hour checks.
- Execute the standard audit scan pack for each endpoint, including bounded `burst_stability`.
- Generate impact-oriented HTML report/dashboard and sanitized CSV with endpoint-level and scan-pack-level results.
- Deliver reports via private S3 presigned URLs.

### Phase 3: Process Hardening

- Improve operator checklist, report consistency, retention workflow, and customer communication templates.
- Evaluate early customer feedback and willingness to pay.
- Decide whether to add schema validation, additional endpoint pricing, or recurring monitoring.

### Phase 4: Future Productization

- Consider customer accounts, automated onboarding, payments, managed monitoring, and expanded auth support only after MVP validation.

## 17. Dependencies on Architecture, UI/UX, and QA Artifacts

### Architecture Dependencies

- Define safe credential handling for bearer tokens.
- Define audit execution workflow for 48-hour checks and approximately 10 cycles.
- Define sanitized metadata schema.
- Define sanitized scan-pack result schema for endpoint-level scenario results.
- Define standard scan-pack runtime execution flow for each endpoint.
- Define explicit safe runtime bounds for standard `burst_stability` so it cannot become load testing.
- Define report artifact generation and S3 presigned URL delivery approach.
- Define 90-day retention and post-retention CSV export/email workflow.
- Define SMTP environment variable contract and failure handling for automated post-retention CSV email delivery.
- Define controls preventing default raw body/header/trace persistence.

### UI/UX Dependencies

- Define static landing page layout and copy hierarchy.
- Define HTML report/dashboard structure.
- Define sanitized CSV export presentation and access flow.
- Define report presentation for executive verdict, prioritized findings, endpoint scorecards, scan-pack matrix, test-level details, sanitized evidence, and remediation guidance.
- Define visual treatment for observed latency versus threshold-based pass/fail results.

### QA Dependencies

- Validate endpoint cap and endpoint counting behavior.
- Validate production waiver and internal approval requirements.
- Validate bearer token exclusion from reports and CSV exports.
- Validate S3 presigned URL delivery expectations.
- Validate no raw response body/header/trace persistence by default.
- Validate sanitized CSV contents.
- Validate standard scan-pack execution/result coverage for every endpoint.
- Validate report includes per-endpoint scan-pack matrix and test-level details for every resolved scenario.
- Validate bounded `burst_stability` is included in standard audit results without requiring optional broader resilience approval.
- Validate no broader resilience, fault-injection, chaos, destructive, stress, spike, soak, capacity, or load-testing scenarios run without separate written approval.
- Validate 90-day retention and CSV email process.
- Validate optional broader resilience/fault/load testing approval gate.
- Validate latency threshold behavior.
- Validate static landing page required sections and CTA text.
