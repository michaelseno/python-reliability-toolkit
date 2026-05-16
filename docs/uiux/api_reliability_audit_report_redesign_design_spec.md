# Design Specification

## 1. Feature Overview

**Feature:** API Reliability Audit static HTML report/dashboard redesign  
**Status:** HITL correction design artifact; implementation-ready; no source-code implementation in this artifact  
**Branch context:** Continue on existing `feature/api_reliability_audit_mvp`; do not create a new branch, push, or open a PR.  
**Primary files inspected:**

- `reliabilitykit/reporting/audit.py`
- `reliabilitykit/core/audit.py`
- `reliabilitykit/core/scan_packs.py`
- `reliabilitykit/core/scenario_registry.py`
- `examples/api_reliability_audit/audit.local.yml`
- `examples/api_reliability_audit/README.md`
- `docs/product/api_reliability_audit_mvp_spec.md`
- `docs/architecture/api_reliability_audit_mvp_architecture.md`
- `docs/uiux/api_reliability_audit_mvp_design_spec.md`
- `docs/qa/api_reliability_audit_mvp_test_plan.md`

This specification redesigns the generated audit report as the product's primary customer-facing artifact. The output remains a **static, offline-friendly, privacy-safe HTML report** with a sanitized CSV export. It should look and read like a polished SaaS-grade reliability dashboard, while preserving the MVP boundary: local/operator-assisted execution, no customer accounts, no SaaS app shell, no live backend calls, and no public report URLs.

The redesign must add substantive scan-pack reporting. `reliabilitykit/core/scan_packs.py` currently defines `core_reliability_scan`, which resolves to the following scenario tests through `scenario_registry.py`:

1. Baseline Health — high severity if failed
2. Repeated Stability — high severity if failed
3. Burst Stability — high severity if failed
4. Invalid Payload Handling — medium severity if failed
5. Missing Fields Validation — medium severity if failed
6. Auth Failure Handling — high severity if failed
7. Timeout Sensitivity — high severity if failed
8. Response Consistency — medium severity if failed

Each audited endpoint should show per-scan-pack test results, including result status, severity, rationale, sanitized evidence, and remediation guidance.

**HITL scope correction:** `burst_stability` is confirmed in scope for the standard report/runtime as the only approved bounded resilience-style check in `core_reliability_scan`. It must be presented as **Burst Stability — bounded stability check**, not as load testing, chaos testing, destructive testing, fault injection, or a broader resilience package. Other fault-injection, chaos, destructive, broader resilience, stress, soak, capacity, throughput, or load tests remain excluded unless separately approved.

## 2. User Goal

The report reviewer wants to quickly answer:

- Is this API reliable enough for the audited scope?
- Which endpoints need attention first?
- Which specific reliability tests passed, failed, were warning-level, or were not run?
- What evidence supports each finding without exposing raw responses, tokens, headers, stack traces, or secrets?
- What remediation actions should the team take next?
- What was tested, when, under which privacy constraints, and what data can be exported?

## 3. UX Rationale

The current report technically renders but is low-impact because it emphasizes raw labels and rows rather than an audit narrative. The redesigned report should use an executive-first structure: verdict, key metrics, prioritized findings, endpoint scorecards, scan-pack evidence, trends, methodology, exports, and privacy notes.

Design approach:

- Use SaaS-style dashboard hierarchy for readability and perceived value.
- Convert raw endpoint rows into decision-ready summaries and drilldowns.
- Make scan-pack test results the core content model.
- Keep all evidence sanitized and bounded to approved metadata.
- Keep the artifact static: no network requests, no client-side persistence, no backend-dependent interactions.
- Fix current rendering issues: oversized cards, awkward wrapping, timestamp overflow, weak hierarchy, table readability, and poor responsive behavior.

## 4. User Flow

1. Reviewer opens the private static HTML report from local disk or a private presigned URL.
2. Reviewer sees one H1, an audit identity strip, and a prominent reliability verdict.
3. Reviewer scans executive metrics: endpoint count, scan-pack pass rate, availability, latency status, completed cycles, and high-severity failures.
4. Reviewer reads prioritized action items with severity, affected endpoint, and recommended next step.
5. Reviewer reviews endpoint health scorecards and selects/scrolls to endpoints with warnings or failures.
6. Reviewer inspects each endpoint's scan-pack test matrix and test-level details.
7. Reviewer reviews latency/availability summaries and cycle coverage. When reviewing `Burst Stability`, reviewer sees only bounded stability evidence and approved execution bounds; no load-capacity or throughput claims are implied.
8. Reviewer downloads the sanitized CSV if needed.
9. Reviewer confirms methodology, scope, privacy exclusions, retention, and delivery notes.

## 5. Information Hierarchy

1. **Reliability verdict:** overall outcome, confidence/coverage, high-severity blockers.
2. **Executive summary metrics:** concise KPI cards with meaningful labels and compact values.
3. **Key findings and prioritized actions:** issue/action list sorted by severity and impact.
4. **Endpoint health scorecards:** one summary card per endpoint with endpoint-level score and top risks.
5. **Scan-pack matrix:** per endpoint, one row per scan-pack scenario test.
6. **Test-level details:** rationale, evidence, remediation, status, severity, timestamps/cycles.
7. **Latency and availability summaries:** trends/rollups across cycles; observed-only behavior when thresholds are absent.
8. **Methodology and audit scope:** what was tested, scan pack used, time window, cycle coverage.
9. **Export and delivery:** sanitized CSV affordance and file metadata.
10. **Privacy and retention notes:** exclusions, raw diagnostic gates, 90-day retention.

## 6. Layout Structure

### Page Shell

- Static HTML document with embedded CSS only.
- No external fonts, scripts, images, analytics, iframes, or remote assets.
- Body background: light neutral SaaS-style surface preferred for printability, with optional dark hero band. Avoid the current all-dark low-contrast report shell.
- Main container max width: `1200px`; desktop padding `32px`; tablet `24px`; mobile `16px`.
- Use semantic landmarks: `header`, `main`, `section`, `footer`.
- Exactly one `h1`.

### Header / Audit Identity Strip

- Contains report title, audit ID, client display name, environment, generated timestamp, audit window, and privacy-safe badge: `Sanitized metadata only`.
- Long IDs/timestamps must use wrapping-safe styles: `overflow-wrap: anywhere; word-break: normal; font-size` no larger than body text.
- Do not place long retention timestamps in large metric cards.

### Executive Verdict Section

- Two-column desktop layout:
  - Left: reliability verdict panel.
  - Right: compact metric grid.
- Verdict must include text and icon/shape, not color alone.
- Recommended verdict labels:
  - `Ready with minor observations`
  - `Needs attention`
  - `High-risk reliability concerns`
  - `Incomplete audit data`
- Include one sentence explaining why the verdict was assigned.

### KPI Cards

Use compact cards with labels, values, and helper text. Cards must not be oversized.

Required cards:

- Endpoints audited: `n / max 10`
- Scan-pack tests: `passed / total`, plus failures and not-run count
- Availability: percentage or `Not enough data`
- Latency: threshold pass rate or `Observed only`
- Completed cycles: `completed / expected`
- High-severity failures: count

### Key Findings and Prioritized Action Items

- Display as a ranked list/table of findings.
- Sort order: critical/high failed tests, high-risk endpoint availability failures, threshold latency failures, medium failures, warnings, incomplete/not-run tests.
- Each finding includes severity, affected endpoint(s), related scan test, sanitized evidence summary, and recommended remediation.
- Empty state: `No failed scan-pack tests or endpoint reliability blockers were detected in the audited data.`

### Endpoint Health Scorecards

- Responsive card grid: desktop 2 columns, tablet 1-2 columns depending width, mobile 1 column.
- Each card includes:
  - Endpoint identity: method badge + path
  - Endpoint health score or verdict
  - Availability summary
  - Latency summary
  - Scan-pack pass/fail/not-run counts
  - Top issue if present
  - Link/anchor to endpoint detail section

### Endpoint Detail Sections

One section per endpoint. Each section includes:

1. Endpoint summary header.
2. Scan-pack test matrix.
3. Test-level detail cards/rows.
4. Latency and availability summary for that endpoint.

Endpoint anchors should be deterministic and sanitized, e.g. `#endpoint-httpbin-status-200` derived from `endpoint_id`.

### Scan-Pack Test Matrix

For each endpoint, render all resolved scenarios from the configured scan pack.

Columns:

- Test
- Category
- Status
- Severity if failed
- Evidence
- Recommendation
- Last observed / cycles

Statuses:

- `Pass`
- `Fail`
- `Warning`
- `Not run`
- `Not applicable`
- `Incomplete`

Rows must include text labels and visible badges. Do not rely on color only.

`Burst Stability` row requirements:

- Render as a standard row in the matrix for every audited endpoint because it is part of `core_reliability_scan`.
- Test label: `Burst Stability`.
- Category label: `Bounded stability check` or `Stability` rather than `Load`, `Stress`, `Capacity`, `Chaos`, or generic `Resilience package`.
- Evidence copy must use bounded language, for example: `Bounded burst check completed within approved limits; sanitized status and timing metadata only.`
- Recommendation copy must stay narrow, for example: `Review short-interval request handling and timeout/error behavior for this endpoint.` Do not recommend capacity planning, throughput benchmarking, autoscaling validation, stress testing, or load-test tooling unless a separate approved scope exists.
- If execution data is missing after scan-pack support is expected, show `Incomplete — bounded stability result was not captured` rather than `Not run — separate approval required`.
- If architecture/backend reports that approved bounds were not available at runtime, show `Not run — approved bounded check configuration missing` and do not infer a pass/fail result.
- Do not display charts, counters, or labels that imply load volume, capacity, requests-per-second benchmarking, soak duration, max concurrency discovery, or traffic simulation.

### Test-Level Detail Cards

Each scan-pack test should have an expandable-looking but static detail block. If no JavaScript is used, all details are visible. If native `<details>`/`<summary>` is used, it remains offline-safe and keyboard accessible.

Each test detail includes:

- Scenario name and ID
- Scan pack name and ID
- Status and severity
- Purpose/rationale from scenario definition
- What was evaluated in plain language
- Sanitized evidence only
- Affected cycles or timestamps
- Remediation guidance
- Privacy note when evidence is intentionally limited

For `burst_stability`, the detail block must include a scope note: `This is a bounded stability check included in the standard audit scan pack. It is not a load, stress, chaos, destructive, or broader resilience test.` If sanitized runtime bounds are supplied by backend/architecture, display them as configuration metadata using neutral labels such as `Approved bounded check limits`; do not promote them as performance targets or capacity measurements.

### Latency and Availability Summary

- Include endpoint and overall summaries.
- For thresholds:
  - If `expected_latency_ms` exists, show threshold pass/fail and max/median/p95 where available.
  - If absent, show `Observed only — no client threshold provided` and do not use pass/fail language.
- For trend-like presentation in static HTML:
  - Use compact cycle tables and simple CSS bars/sparklines if data exists.
  - No canvas or external chart libraries.

### Export / CSV Section

- Primary link/button: `Download sanitized CSV metadata`.
- Helper text: `Contains approved sanitized metadata only; excludes tokens, raw responses, headers, bodies, trace logs, and stack traces.`
- If no CSV link is available, show explicit unavailable state and operator guidance.

### Methodology, Scope, Privacy, and Delivery Notes

- Methodology and scope should state:
  - Audit window
  - Expected and completed cycles
  - Endpoint count
  - Scan pack used
  - Scenario count
  - Environment
  - Auth handling summary without secret references
- Scope must explicitly state that `Burst Stability` is included as one bounded standard scan-pack stability check and that all other load, stress, soak, capacity, chaos, destructive, fault-injection, or broader resilience tests are excluded unless separately approved.
- Privacy notes should preserve MVP rules:
  - Raw logs, raw responses, raw response bodies, raw headers, trace logs, stack traces, bearer tokens, and secret references are excluded by default.
  - Raw diagnostic data may be displayed/persisted only with explicit client request and written approval/reference.
  - Sanitized metadata retention is 90 days.
  - Private delivery uses private S3 presigned URLs; public permanent URLs are prohibited.

## 7. Components

- Report header / identity strip
- Privacy-safe badge
- Reliability verdict panel
- KPI metric cards
- Severity badges
- Status badges
- Key findings list
- Prioritized action item row
- Endpoint health scorecard
- Endpoint detail section
- Scan-pack test matrix
- Test detail block or native disclosure
- Latency summary card
- Availability summary card
- Cycle coverage table
- CSV download link/button
- Methodology/scope panel
- Privacy and delivery notes panel
- Empty/incomplete data alert
- Print-friendly footer

## 8. Interaction Behavior

### Static Navigation / Anchor Links

- **Trigger:** Click or keyboard activation on internal links.
- **System response:** Browser scrolls to the endpoint/detail section.
- **UI feedback:** Target section heading is visible; focused links use visible focus ring.
- **Failure:** Broken anchors are implementation defects.

### Native Details Disclosure, if Used

- **Trigger:** Click or keyboard activation on `<summary>`.
- **System response:** Browser expands/collapses details.
- **UI feedback:** Expanded/collapsed state is conveyed by native semantics and visible indicator.
- **Failure:** If CSS hides summary text or removes keyboard access, this is an implementation defect.

### CSV Download

- **Trigger:** Click or keyboard activation on CSV link/button.
- **System response:** Browser opens or downloads sanitized CSV.
- **UI feedback:** Link text identifies sanitized metadata.
- **Success:** CSV artifact is accessible through private/local path or presigned URL.
- **Failure:** Expired/missing link helper text says: `If this private link has expired, request a regenerated report link from the operator.`

### No Dynamic SaaS Behavior

- No login, filters that require scripts, backend calls, live refresh, customer account navigation, payment, or forms.
- Any optional client-side enhancement must preserve full content availability when JavaScript is disabled. Prefer no JavaScript for MVP report generation.

## 9. Component States

### Status Badge

- **Default:** Text label plus semantic color/icon/shape.
- **Hover:** Not required unless badge is inside an interactive link; if linked, underline or subtle background change.
- **Focus:** If linked, visible focus ring.
- **Active:** If linked, pressed state through background/border change.
- **Disabled:** Not applicable; use `Not run` or `Not applicable` as data states instead.
- **Loading:** Not applicable for static report.
- **Success:** `Pass` badge with text.
- **Error:** `Fail` badge with text.
- **Empty:** `No result recorded` or `Not run`; never blank.

### Severity Badge

- **Default:** `High`, `Medium`, `Low`, or `Info` text.
- **Hover/Focus/Active:** Only if interactive; otherwise none.
- **Disabled/Loading:** Not applicable.
- **Error:** High severity should be visually prominent and text-labeled.
- **Empty:** `Severity not assigned` only when data contract is missing; treat as QA defect for known scan-pack scenarios.

### KPI Card

- **Default:** Label, compact value, helper text.
- **Hover/Active:** Not interactive by default; no hover effect required.
- **Focus:** Not focusable unless it contains a link.
- **Disabled/Loading:** Not applicable.
- **Success/Error/Empty:** Values display status text: `No data`, `Observed only`, `Incomplete`, or `Not enough data` as appropriate.

### Endpoint Scorecard

- **Default:** Endpoint identity, verdict, compact metrics, anchor link.
- **Hover:** If entire card is linked, show border/background change; otherwise only link hover.
- **Focus:** Link focus ring visible.
- **Active:** Linked card/link shows pressed state.
- **Disabled/Loading:** Not applicable.
- **Success:** Endpoint verdict text indicates healthy/pass.
- **Error:** Endpoint verdict text indicates failure/attention needed.
- **Empty:** Show `No endpoint result data captured` and avoid computed percentages.

### Scan-Pack Matrix

- **Default:** All configured scan-pack tests visible per endpoint.
- **Hover:** Row background change allowed for readability.
- **Focus:** Interactive links/disclosures within rows have visible focus.
- **Active:** Native control active state if using `<details>`.
- **Disabled/Loading:** Not applicable.
- **Success/Error:** Pass/fail rows use text labels and badges.
- **Empty:** If scan-pack data is absent, show explicit alert: `Scan-pack execution data was not captured for this endpoint.` This should fail QA once backend support is expected.
- **Burst Stability scope state:** `Burst Stability` is not a gated optional row. It appears with the same status vocabulary as other standard scenarios. If missing, use `Incomplete` or the explicit bounded-configuration `Not run` reason defined above; do not say separate resilience approval is required for this standard check.

### CSV Link/Button

- **Default:** Visible primary link/button with clear label.
- **Hover:** Underline or background change while preserving contrast.
- **Focus:** 2px or greater visible outline with at least 3:1 contrast.
- **Active:** Pressed state.
- **Disabled:** If no CSV available, render non-interactive explanatory text instead of a disabled fake button.
- **Loading:** Not applicable.
- **Success:** Browser opens/downloads CSV.
- **Error:** Static helper text for expired/missing link.

## 10. Responsive Design Rules

### Desktop ≥ 1024px

- Max content width `1200px`.
- Executive section: verdict panel + KPI grid.
- KPI grid: 3 columns or auto-fit compact cards.
- Endpoint scorecards: 2 columns.
- Tables use full width; sticky headers optional for print-unfriendly contexts, not required.

### Tablet 768px–1023px

- Executive section stacks if KPI cards become cramped.
- KPI grid: 2 columns.
- Endpoint cards: 1–2 columns based on available width.
- Scan matrix remains a table inside a horizontally scrollable container.

### Mobile < 768px

- Single-column layout.
- Metric cards stack.
- Long IDs and timestamps wrap safely.
- Tables are wrapped in `.table-scroll` with `overflow-x: auto`, visible scroll affordance, and no clipped content.
- Consider cardified matrix rows only if all headers remain programmatically associated; otherwise preserve table + horizontal scroll.
- Minimum touch target size: 44px height for links/buttons where feasible.

### Print / PDF Friendly

- Use `@media print` to switch to white background, dark text, remove heavy shadows, expand `<details>` content where feasible, avoid orphaned headings, and show link URLs for CSV/private links if appropriate.
- Avoid all-dark backgrounds for printable body content.

## 11. Visual Design Tokens

Implementation may adjust exact values, but should follow these constraints:

- **Surface:** `#f8fafc` page, `#ffffff` cards, `#e2e8f0` borders.
- **Text:** `#0f172a` primary, `#475569` secondary, `#64748b` metadata.
- **Brand/accent:** `#2563eb` or equivalent accessible blue.
- **Success:** green family with text contrast; include `Pass` text.
- **Warning:** amber/orange family with text contrast; include `Warning` text.
- **Error/high risk:** red family with text contrast; include `Fail` / severity text.
- **Info/observed-only:** blue/slate family with text label.
- **Spacing:** 4px base scale; common gaps 8, 12, 16, 24, 32px.
- **Radius:** 12–20px for cards; avoid overly large cards.
- **Typography:** system UI stack; H1 28–36px desktop, 24–28px mobile; body 14–16px; table text minimum 13px.
- **Badges:** compact pill or rounded rectangle with border and text; do not use color-only dots.

## 12. Accessibility Requirements

- Exactly one `h1`; all sections use hierarchical headings without skipping levels.
- Use semantic tables for matrices and cycle data with `<caption>` or nearby heading, `<thead>`, `<tbody>`, and scoped headers.
- Status and severity must be text-labeled; color cannot be the only indicator.
- Links/buttons must have visible focus indicators.
- Internal anchor links must have descriptive text, e.g. `View scan results for GET /status/200`.
- If `<details>` is used, keep native keyboard and screen reader behavior; do not replace with inaccessible custom accordions.
- Contrast must meet WCAG AA: 4.5:1 for normal text, 3:1 for large text and focus indicators.
- Long strings must wrap without causing horizontal page overflow.
- Decorative icons must be `aria-hidden="true"`; meaningful icons require accessible text.
- Alerts for incomplete or missing data should use clear text. `role="status"` or `role="note"` may be used for non-dynamic report notices; no live region is needed because content is static.

## 13. Edge Cases

- **No endpoint results:** Show `Incomplete audit data` verdict and do not compute misleading percentages.
- **Partial cycle completion:** Show completed vs expected cycles and lower confidence wording.
- **Scan-pack data missing:** Show explicit scan-pack missing-data alert; QA should fail once scan-pack execution is required.
- **Scenario not applicable:** Show `Not applicable` with rationale; do not hide the row.
- **Latency threshold absent:** Show observed latency only; no pass/fail latency labels.
- **Latency not measured:** Show `Not measured`; do not display `0 ms` unless actual value is zero.
- **CSV link absent:** Show static guidance instead of a broken/empty link.
- **Long audit IDs, endpoint paths, timestamps, retention dates:** Wrap safely; never overflow cards.
- **Raw data exception approved:** Only display raw diagnostic excerpts if explicit client request and written approval/reference exist. Even then, clearly label the exception and keep secrets redacted. Default report excludes raw data.
- **Bounded Burst Stability included:** `burst_stability` is confirmed as a standard bounded stability check. If it does not execute, report the concrete data/configuration reason (`Incomplete`, `Not run — approved bounded check configuration missing`, or `Not applicable` with rationale). Do not label it as optional, gated by separate approval, or part of a load/resilience package.
- **Out-of-scope test references:** If imported data contains unapproved load, stress, soak, capacity, chaos, destructive, fault-injection, or broader resilience results, do not render them as part of the standard report. Show only approved scan-pack scenarios unless product/architecture provides separate written approval and UI scope is updated.

## 14. Developer Handoff Notes

### UX Diagnosis of Current Report

Evidence from `reliabilitykit/reporting/audit.py` shows the current report is a minimal dark page with summary cards, a CSV section, an endpoint table, and privacy notes. It lacks:

- A meaningful reliability verdict.
- Prioritized findings or action guidance.
- Endpoint-level rollups beyond individual rows.
- Scan-pack test content, despite `scan_packs.py` defining a productized `core_reliability_scan`.
- Strong information hierarchy.
- Robust responsive table handling.
- Safe wrapping for long audit IDs/timestamps, especially retention expiration.
- Substantive customer-facing evidence and remediation detail.

### Required Backend / Data-Model Changes

The current core model captures endpoint check results only. To support the redesigned report, backend/core must add scan-pack execution and sanitized result capture.

Required data contract additions:

```text
AuditResult
  scan_pack_id: string
  scan_pack_name: string
  scan_pack_description: string
  scan_pack_scenario_count: integer
  endpoint_summaries: list[EndpointAuditSummary]        # may be computed for report generation
  scan_results: list[EndpointScanPackResult]

EndpointScanPackResult
  audit_id: string
  check_cycle_id: string | null                         # null allowed for aggregate result
  endpoint_id: string
  method: string
  path: string
  scan_pack_id: string
  scenario_id: string
  scenario_name: string
  category: string
  severity_if_failed: high | medium | low | info
  status: pass | fail | warning | not_run | not_applicable | incomplete
  rationale: string                                     # from scenario definition / sanitized
  evidence_summary: string | null                       # sanitized only
  remediation: string | null                            # safe guidance
  observed_at: datetime | null
  affected_cycle_ids: list[string]
  expected_behavior: string | null
  observed_behavior: string | null                      # sanitized metadata, not raw body/header/log
  raw_data_included: boolean = false
  raw_data_exception_reference: string | null            # only if approved; avoid exposing secret references
  bounded_check_scope_note: string | null                # required for burst_stability; sanitized, non-load wording

EndpointAuditSummary
  endpoint_id: string
  method: string
  path: string
  availability_percent: float | null
  latency_summary_ms: { min, median, p95, max } | null
  expected_latency_ms: integer | null
  latency_status: pass | fail | observed_only | not_measured
  scan_pass_count: integer
  scan_fail_count: integer
  scan_warning_count: integer
  scan_not_run_count: integer
  high_severity_failure_count: integer
  verdict: healthy | needs_attention | high_risk | incomplete
```

CSV/export should either:

1. keep the existing endpoint-cycle CSV and add a second sanitized scan-results CSV, or
2. add scan-result columns to an expanded CSV contract only if QA/product approves the schema change.

Do not include raw bodies, raw headers, raw responses, stack traces, bearer tokens, secret references, or raw logs in any new field by default.

For `burst_stability`, backend/report view-model should provide sanitized bounded-check metadata only when approved by architecture/product, such as whether the bounded check configuration was present and a neutral scope note. The UI must not derive or display load-test metrics, throughput targets, capacity findings, or max-concurrency claims from this scenario.

Backend must also define deterministic verdict/score calculations, including handling for partial data and not-run tests.

### Required Frontend / Report Template Changes

Update `reliabilitykit/reporting/audit.py` or move the template to a maintainable template file. The redesigned static report must render:

- Header/identity strip with safe wrapping.
- Executive verdict.
- KPI metric cards with compact values.
- Prioritized findings/action items.
- Endpoint scorecards.
- Per-endpoint scan-pack test matrix.
- Test-level details with severity, rationale, sanitized evidence, and remediation.
- Latency/availability summaries.
- Methodology/scope.
- CSV/export affordance.
- Privacy, retention, and delivery notes.

Implementation should precompute report view-model fields rather than embedding complex logic in Jinja. Use HTML escaping for all dynamic fields.

### QA Acceptance Criteria

- Report has exactly one `h1`, semantic sections, and no broken heading hierarchy.
- Report renders without horizontal page overflow at 320px, 768px, and desktop widths.
- Long audit IDs, endpoint paths, retention timestamps, and generated timestamps wrap without overflowing cards.
- KPI cards are compact and do not dominate the viewport with label-only content.
- Executive verdict is present and text-labeled.
- Key findings/action items are present or a clear empty state is shown.
- Every endpoint shows a health scorecard.
- Every endpoint shows every scenario from `core_reliability_scan` or an explicit `Not run` / `Not applicable` row with rationale.
- Every endpoint shows `Burst Stability` as a standard `core_reliability_scan` row with category/copy that describes a bounded stability check, not load testing or a resilience package.
- Each scan-pack test row includes test name, category, status, severity, evidence summary, and recommendation.
- Test details never include bearer tokens, raw headers, raw bodies, raw responses, raw logs, trace logs, stack traces, or secret references by default.
- Latency labels obey threshold rules: threshold absent means `Observed only`, never pass/fail.
- CSV link is labeled as sanitized metadata; missing CSV state is explicit.
- Tables remain readable with horizontal scroll on small screens.
- Status and severity are not color-only.
- Focus states are visible for all links/disclosures.
- Print preview is readable on a light background and does not hide core report content.
- Static HTML contains no external network dependencies, analytics scripts, login/payment/forms, or SaaS account UI.
- Report copy contains no unsupported load/stress/soak/capacity/chaos/destructive/fault-injection claims for `Burst Stability`.

### Risks / Open Questions / Blockers

- `scan_packs.py` defines scenarios but the inspected audit execution model does not yet capture per-scenario runtime results. Backend implementation is required before the report can show substantive scan-pack data.
- `burst_stability` scope ambiguity is closed by HITL: include it as the only bounded resilience-style check in the standard scan pack/report. Remaining implementation risk is that architecture/backend still need to define and enforce exact operational bounds so the scenario cannot expand into load testing.
- Remediation guidance is not currently defined in `scenario_registry.py`; backend/product should add standardized safe remediation text per scenario or report generation must map scenario IDs to approved guidance.
- Verdict scoring rules are not currently defined. Product/backend should approve deterministic rules before QA sign-off.
- Current CSV contract covers endpoint-cycle metadata only. Scan-pack export coverage needs a schema decision.
