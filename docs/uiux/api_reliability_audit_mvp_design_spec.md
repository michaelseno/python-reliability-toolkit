# Design Specification

## 1. Feature Overview

**Title:** 48-Hour API Reliability Audit MVP UI/UX Plan  
**Status:** Planning artifact only; approved for study/planning, not implementation  
**Source Product Spec:** `docs/product/api_reliability_audit_mvp_spec.md`  
**Source Architecture Plan:** `docs/architecture/api_reliability_audit_mvp_architecture.md`  
**Scope Type:** Manual/operator-assisted MVP, not SaaS  
**Frontend Scope:** Static informational landing page and static HTML report/dashboard expectations only

The 48-Hour API Reliability Audit MVP is a bounded, operator-assisted service for evaluating up to 10 unique `METHOD + PATH` API endpoints over 48 hours. The customer-facing experience consists of:

1. a Phase 1 static product landing page; and
2. a private static HTML report/dashboard with a sanitized CSV export delivered through S3 presigned URLs.

No heavy frontend application, SaaS onboarding flow, login, payment flow, customer account area, backend form handling, or self-service audit configuration is needed for the MVP.

### Executive Summary

The UX must communicate a clear, safe, low-commitment reliability audit offer while avoiding the expectation of a SaaS product. The landing page should explain the service, constraints, privacy posture, pricing, process, and CTA. The report/dashboard should present audit outcomes using sanitized metadata only, with clear distinctions between availability results, status-code behavior, observed latency, and threshold-based latency pass/fail labels when thresholds exist.

The operator experience is not a full UI in MVP scope, but planning must define intake, authorization, production waiver, raw-data exception, and optional resilience/burst opt-in UX requirements so manual templates/checklists can be implemented consistently outside a productized frontend.

## 2. User Goal

### Buyer / Client

The buyer wants to understand whether the audit is relevant, safe, affordable, and easy to request without committing to a monitoring platform.

### Operator

The operator wants a complete, unambiguous intake and approval path before running checks, especially for production APIs, bearer tokens, endpoint limits, latency thresholds, raw-data exceptions, and optional resilience/burst testing.

### Report Reviewer

The report reviewer wants to quickly understand reliability outcomes, endpoint-level findings, latency observations, CSV export contents, and data-handling guarantees without exposure to secrets or raw API data.

## 3. UX Rationale

- Keep discovery simple: one static landing page supports offer validation without backend investment.
- Keep the service trust-forward: authorization, safety, privacy, and private delivery should appear before or near purchase intent content.
- Keep execution operator-assisted: manual coordination is intentional and must not be disguised as self-service.
- Keep reports evidence-oriented: summary first, endpoint details second, raw data never shown by default.
- Keep latency interpretation precise: pass/fail labels are allowed only when client-provided thresholds exist; otherwise latency is presented as observed-only.
- Keep optional add-ons clearly separated: resilience/burst testing must never appear as part of the standard audit.

## 4. User Flow

### Buyer / Client Journey

1. Visitor lands on the static product page.
2. Visitor reads the hero, value proposition, included items, safety guarantees, pricing, process, and FAQ.
3. Visitor selects the CTA with exact text: **Request a Reliability Audit**.
4. CTA navigates to a placeholder destination until the final destination is confirmed.
5. Operator coordinates intake outside the website.
6. Client provides endpoint list, environment classification, bearer-token details if needed, expected latency thresholds if available, and written authorization.
7. Client receives private S3 presigned URLs for HTML report/dashboard and sanitized CSV export after audit completion.

### Operator Journey

1. Operator receives audit request through the placeholder CTA destination or manual channel.
2. Operator collects client contact, endpoint inventory, auth approach, environment, thresholds, and requested options.
3. Operator confirms no more than 10 unique `METHOD + PATH` endpoints.
4. If production testing is requested, operator obtains written production waiver/agreement.
5. Operator completes internal production approval checklist before testing production APIs.
6. If resilience/burst testing is requested, operator obtains separate written approval and keeps it outside the standard workflow.
7. Operator confirms raw bodies, headers, and trace logs will not be stored by default unless an explicit written raw-data exception exists.
8. Operator runs the audit, generates static report and CSV, uploads artifacts privately, and delivers presigned URLs.

### Report Reviewer Journey

1. Reviewer opens the private S3 presigned URL for the HTML report/dashboard.
2. Reviewer scans the audit summary for scope, time window, check cycles completed, and headline availability/latency outcomes.
3. Reviewer reviews endpoint-level tables and any sanitized error categories.
4. Reviewer downloads the sanitized CSV export if needed.
5. Reviewer sees privacy/retention notes, including 90-day sanitized metadata retention and post-retention CSV email.

## 5. Information Hierarchy

### Landing Page Priority

1. Offer clarity: “48-hour API Reliability Audit”.
2. Outcome/value: reliability evidence without SaaS onboarding.
3. Scope: up to 10 endpoints, 5 checks/day, approximately 10 cycles.
4. Safety/privacy: authorization, no raw persistence by default, private delivery, sanitized CSV.
5. Pricing: $750 standard; optional validation and add-on pricing where used.
6. Process: request, intake, approval, 48-hour checks, report delivery.
7. FAQ: constraints and edge cases.
8. CTA: exact text **Request a Reliability Audit**.

### Report/Dashboard Priority

1. Audit identity and completion status.
2. Scope and methodology summary.
3. Overall availability and check-cycle completion.
4. Endpoint-level findings.
5. Latency threshold status or observed-only latency.
6. Sanitized error categories.
7. CSV export access.
8. Privacy, exclusions, retention, and delivery notes.

## 6. Layout Structure

### Static Landing Page

- **Header:** simple brand/service name, same-page anchor navigation, primary CTA.
- **Hero:** headline, concise supporting copy, primary CTA, safety note.
- **Problem / Value Proposition:** short narrative explaining why a bounded audit is useful.
- **What’s Included:** card or checklist layout covering duration, endpoint cap, check frequency, report, CSV, private delivery.
- **Privacy / Safety Guarantees:** high-visibility section with authorization and data handling promises.
- **Pricing:** pricing cards or stacked rows for standard MVP price and optional validation/add-on/future monitoring references.
- **How It Works:** numbered steps.
- **FAQ:** accessible accordion or static question list. Static list is preferred for MVP simplicity.
- **Final CTA:** repeated CTA with exact text.

### HTML Report / Dashboard

- **Report Header:** audit name, client display name if approved, audit ID, generated timestamp, report window.
- **Summary Panel:** endpoints audited, check cycles expected/completed, overall availability, threshold coverage.
- **Methodology / Safety Panel:** confirms sanitized metadata-only reporting and no default raw-data persistence.
- **Endpoint Results Table:** method, path, availability, status-code summary, latency metrics, threshold status, sanitized error category.
- **Timeline / Cycle Table:** check cycle, timestamp, endpoint count checked, failures, noteworthy sanitized categories.
- **CSV Export Area:** direct link/button to sanitized CSV export artifact.
- **Retention / Delivery Notes:** S3 presigned delivery, URL expiry caveat, 90-day metadata retention, post-retention CSV email.

### Operator Intake / Authorization UX Requirements

This is not a customer-facing product UI for MVP. It may be represented as manual checklists, intake documents, or internal templates. Any future implementation must preserve the following sections:

- Client identity and contact.
- Endpoint inventory table with unique `METHOD + PATH` counting.
- Environment classification.
- Bearer token handling instructions.
- Latency threshold capture per endpoint or global note that thresholds are absent.
- Production waiver status.
- Internal production approval checklist status.
- Raw-data exception status.
- Optional resilience/burst testing status and separate approval reference.

## 7. Components

### Landing Page Components

- Header/navigation
- Hero section
- CTA link/button
- Feature/value cards
- Safety guarantee checklist
- Pricing card/rows
- How-it-works stepper
- FAQ list
- Footer with privacy/scope reminder

### Report/Dashboard Components

- Report header
- Summary metric cards
- Methodology notice
- Endpoint results table
- Cycle summary table
- Latency status badge
- Availability status badge
- CSV download link/button
- Privacy/retention notice
- Error/empty-state notices for incomplete or unavailable data

### Manual/Operator UX Artifacts

- Intake checklist
- Production waiver checklist
- Internal approval checklist
- Optional resilience/burst opt-in confirmation
- Raw-data exception confirmation

## 8. Interaction Behavior

### Landing Page CTA

- **Trigger:** click or keyboard activation on CTA.
- **System response:** navigate to configured placeholder destination.
- **UI feedback:** browser navigation occurs; no form submission or loading spinner is required.
- **Success behavior:** visitor reaches placeholder destination.
- **Failure behavior:** if placeholder URL is unavailable, browser displays normal link failure; no custom backend error state is required.

### Landing Page Navigation

- **Trigger:** click or keyboard activation on same-page anchor link.
- **System response:** move viewport to target section.
- **UI feedback:** focus should move or remain understandable; target section should have a programmatically identifiable heading.
- **Success behavior:** selected content is visible.
- **Failure behavior:** broken anchors must be treated as implementation defects.

### Report CSV Export

- **Trigger:** click or keyboard activation on CSV export link/button.
- **System response:** browser downloads or opens the sanitized CSV artifact from the private presigned URL.
- **UI feedback:** link label must identify the file as sanitized CSV metadata.
- **Success behavior:** reviewer obtains CSV with approved sanitized columns only.
- **Failure behavior:** expired or invalid presigned URL should be explained in report delivery email/process; report UI may include static helper text: “If this link has expired, request a regenerated private link.”

### Report Table Review

- **Trigger:** scroll, keyboard table navigation, or screen reader table navigation.
- **System response:** no dynamic behavior required.
- **UI feedback:** table headers remain clear; status badges include text, not color alone.
- **Success behavior:** reviewer can compare endpoint outcomes without raw data exposure.
- **Failure behavior:** if a metric is unavailable, show `Not available` or `Not measured`, not blank ambiguous cells.

### Intake / Authorization UX

- **Trigger:** operator reviews manual checklist before audit execution.
- **System response:** execution must be blocked outside UI if required approvals are incomplete.
- **UI feedback:** manual checklist must mark blocked conditions explicitly.
- **Success behavior:** operator proceeds only with endpoint cap, authorization, privacy, and option gates satisfied.
- **Failure behavior:** missing production waiver, internal approval, raw-data exception approval, or burst approval blocks the relevant testing path.

## 9. Component States

### CTA Link/Button

- **Default:** visible with exact text **Request a Reliability Audit**.
- **Hover:** underline or visual emphasis change while maintaining contrast.
- **Focus:** visible focus indicator with at least 3:1 contrast against adjacent colors.
- **Active:** pressed/activated state visible during click/keyboard activation.
- **Disabled:** not applicable for static link; do not render disabled CTA unless destination is intentionally unavailable, in which case use explanatory text instead of a fake button.
- **Loading:** not applicable; no backend submission.
- **Success:** navigation to placeholder destination.
- **Error:** browser/link failure only; no app-level error.
- **Empty:** not applicable.

### Navigation Links

- **Default:** readable text links.
- **Hover:** underline or color shift with sufficient contrast.
- **Focus:** visible focus ring/outline.
- **Active:** current/activated link styling if implemented.
- **Disabled/Loading/Success/Error/Empty:** not applicable for static anchors, except broken anchors are defects.

### FAQ Items

- **Default:** if static list, all questions and answers visible. If accordion is later used, questions are collapsed buttons by default.
- **Hover:** only applicable for accordion triggers; visible affordance change.
- **Focus:** accordion trigger receives visible focus.
- **Active:** accordion trigger indicates expanded/collapsed state.
- **Disabled/Loading/Success/Error/Empty:** not applicable.

### Report Summary Metric Cards

- **Default:** display metric label, value, and context.
- **Hover:** not required unless cards are interactive; avoid implying clickability.
- **Focus/Active:** not applicable unless interactive.
- **Disabled/Loading:** not applicable for generated static completed report.
- **Success:** completed metrics visible.
- **Error:** show `Not available` with reason when metric cannot be calculated from sanitized metadata.
- **Empty:** show `No data recorded` only when no observations exist.

### Availability Status Badge

- **Default:** text label such as `Available`, `Unavailable`, or `Partial`.
- **Hover:** not required.
- **Focus/Active:** not applicable unless badge has tooltip; avoid tooltip-only information.
- **Disabled/Loading:** not applicable.
- **Success:** `Available` state may use green plus text.
- **Error:** `Unavailable` state may use red plus text.
- **Empty:** `Not measured` when no observation exists.

### Latency Status Badge

- **Default:** show `Pass`, `Fail`, or `Observed only`.
- **Hover/Focus/Active:** not applicable unless interactive; avoid tooltip-only explanations.
- **Disabled/Loading:** not applicable.
- **Success:** `Pass` only when `expected_latency_ms` exists and observed latency is within threshold.
- **Error:** `Fail` only when `expected_latency_ms` exists and observed latency exceeds threshold.
- **Empty:** `Observed only` or `No threshold provided`; never label pass/fail without threshold.

### Endpoint Results Table

- **Default:** all endpoint rows displayed with method, path, status, availability, latency, and sanitized error category.
- **Hover:** row highlight optional on pointer devices; must not be sole way to read data.
- **Focus:** if table contains links, each link receives visible focus. Static cells do not need focus.
- **Active:** link activation only where applicable.
- **Disabled/Loading:** not applicable for static completed report.
- **Success:** rows render with sanitized metadata.
- **Error:** unavailable fields use explicit text such as `Not available`.
- **Empty:** show a prominent empty-state message: `No endpoint observations were recorded for this audit.`

### CSV Export Link/Button

- **Default:** labeled `Download sanitized CSV` or equivalent.
- **Hover:** visible link/button emphasis.
- **Focus:** visible focus indicator.
- **Active:** pressed state.
- **Disabled:** if CSV is unavailable, render non-interactive text explaining why; do not provide a dead link.
- **Loading:** not applicable unless future dynamic generation is added.
- **Success:** CSV downloads/opens.
- **Error:** expired/private URL failure handled through delivery process; static helper text instructs reviewer to request regeneration.
- **Empty:** if no CSV generated, show `Sanitized CSV export unavailable` with reason.

### Manual Approval Checklist Items

- **Default:** unchecked / pending.
- **Hover:** not applicable for document-based checklist; if implemented in UI, row highlight optional.
- **Focus:** visible focus for checkboxes/links if interactive.
- **Active:** selected checklist item updates state.
- **Disabled:** approval-dependent actions disabled or blocked until required items complete.
- **Loading:** not applicable.
- **Success:** checked / approved with reference captured.
- **Error:** blocked state with missing requirement named explicitly.
- **Empty:** no approval reference captured; treat as incomplete.

## 10. Responsive Design Rules

### Desktop

- Landing page uses a centered max-width content layout with multi-column cards where space allows.
- Report summary cards may use a 3–4 column grid.
- Endpoint tables may use full-width layout with horizontal overflow only if necessary.

### Tablet

- Reduce multi-column sections to two columns.
- Keep pricing and safety sections highly readable with generous spacing.
- Report metric cards wrap to two columns.
- Tables may allow horizontal scrolling with visible table captions.

### Mobile

- Stack all landing page sections vertically.
- Header navigation may collapse to a simple stacked list or be reduced to key anchors and CTA; no complex menu is required.
- CTA must remain easy to activate with a minimum 44px target height.
- Pricing cards stack vertically.
- Report summary cards stack vertically.
- Endpoint and cycle tables may use horizontal scrolling or card-style rows; headers/labels must remain associated with values.
- Avoid fixed-position elements that obscure report content on small screens.

## 11. Visual Design Tokens

Final brand tokens are not defined in upstream artifacts. Use existing repository/site conventions if available during implementation. Minimum token guidance:

- **Typography:** system sans-serif stack; clear hierarchy with one H1 per page/report.
- **Spacing:** use consistent spacing scale such as 4px base increments; maintain at least 24px between major sections on mobile and 48px on desktop.
- **Status colors:** green for available/pass, red for unavailable/fail, amber/neutral for partial/observed-only; always pair color with text.
- **Contrast:** all text and meaningful UI elements must meet WCAG 2.2 AA contrast ratios.
- **Tables:** use clear borders or row separators; avoid dense spreadsheet styling for the summary report.

## 12. Accessibility Requirements

- Use semantic HTML landmarks: `header`, `main`, `section`, `footer`, and `nav` where applicable.
- Use one descriptive H1 per page/report and hierarchical headings thereafter.
- CTA must be a real link (`a`) when it navigates, not a button unless it performs an in-page action.
- All links and interactive elements must be keyboard accessible using Tab, Shift+Tab, Enter, and Space where appropriate.
- Provide visible focus indicators for all interactive elements.
- Do not communicate status by color alone; badges must include text labels.
- Tables must include captions or nearby headings, column headers, and accessible cell associations.
- CSV export link must have accessible text that indicates it exports sanitized metadata.
- Error, empty, and unavailable states must be expressed in plain language.
- Presigned URL expiry messaging should be understandable without relying on visual-only cues.
- FAQ accordions, if used later, must expose `aria-expanded` and maintain keyboard support. Static FAQ content is preferred for MVP simplicity.

## 13. Edge Cases

- More than 10 unique endpoints requested: intake UX must state the standard audit cap and block standard execution until scope is reduced or future pricing is approved.
- Duplicate endpoint entries: operator UX must clarify that endpoint identity is unique `METHOD + PATH`; duplicates must be resolved before execution.
- Same path with different methods: report and intake must show these as separate endpoints.
- Production API without written waiver: blocked.
- Production API with waiver but no internal approval checklist: blocked.
- Bearer token supplied: never displayed in landing page, report, CSV, screenshots, or export fields.
- Thresholds absent: report displays observed latency only and no pass/fail latency labels.
- Some endpoints have thresholds and others do not: show pass/fail only for rows with thresholds; show `Observed only` for rows without thresholds.
- Missed check cycle: report should show expected versus completed cycles and indicate incomplete measurement if material.
- Presigned URL expired: delivery copy should instruct client to request a regenerated private link.
- CSV unavailable: report must not show a dead download link.
- Raw-data storage requested: must be treated as an exception requiring explicit written demand and approval before collection.
- Resilience/burst requested: must be separated from the standard workflow and require separate written approval.
- Empty audit results: report must show no observations recorded and avoid misleading summary percentages.

## 14. Developer Handoff Notes

- This is a planning artifact only. Do not implement frontend, backend, PR, release, or deployment work from this document without separate authorization.
- No heavy frontend/SaaS is needed now.
- The landing page must be static and informational only: no backend, no login, no payment, no form submission.
- CTA text must be exactly: **Request a Reliability Audit**.
- CTA destination remains a placeholder pending confirmation.
- Report/dashboard should be generated as a static HTML artifact from sanitized metadata only.
- CSV export must contain sanitized metadata only and exclude bearer tokens, raw bodies, raw headers, trace logs, unredacted payloads, and secret references.
- Reports and CSVs are delivered through private S3 presigned URLs only.
- Use threshold-aware latency labels only when thresholds are provided.
- Treat operator-facing intake and approval UX as manual documents/templates/checklists in MVP scope, not a product UI.

## 15. Intake / Authorization UX Requirements

Manual intake must collect and clearly confirm:

- Client name and delivery email.
- Endpoint list with method, path, base URL, and optional threshold.
- Endpoint count based on unique `METHOD + PATH`.
- Environment classification: production, staging, development, or other.
- Bearer token handling instructions and confirmation that token values are excluded from outputs.
- Written authorization reference for all testing.
- Production waiver/agreement reference if environment is production.
- Internal approval checklist reference if environment is production.
- Raw-data exception answer, defaulting to no raw persistence.
- Optional resilience/burst answer, defaulting to not included.
- 90-day sanitized metadata retention and post-retention CSV email acknowledgement.

## 16. Production Waiver UX

- Production testing must be presented as a special approval path, not the default.
- Waiver copy should explicitly state testing boundaries, endpoint scope, schedule, expected check frequency, and that resilience/burst is excluded unless separately approved.
- Operator checklist must contain two independent gates:
  1. written client production waiver/agreement; and
  2. completed internal production approval checklist.
- If either gate is missing, status is `Blocked — production testing not approved`.

## 17. Optional Resilience / Burst Opt-In UX

- Present as optional add-on only, outside the standard audit workflow.
- Copy must not imply load testing is included in the $750 standard audit.
- Require separate written approval and approved boundaries before execution.
- Pricing copy may state: validation add-on **+$300**; later add-on **+$500**.
- If not approved, report should not include resilience/burst results or imply they were performed.

## 18. Client-Facing Report / Dashboard Information Architecture

Recommended report sections:

1. Report title and audit metadata.
2. Scope summary: endpoints, method/path definition, check window, expected/completed cycles.
3. Executive result summary.
4. Endpoint result table.
5. Latency interpretation note.
6. Sanitized error/category summary.
7. CSV export section.
8. Privacy and exclusions section.
9. Retention and delivery section.
10. Contact/regeneration note for expired URLs.

## 19. Sanitized CSV Export UX

- Label the action `Download sanitized CSV`.
- Adjacent helper text: `Contains sanitized metadata only. Excludes bearer tokens, raw response bodies, raw headers, and trace logs.`
- CSV fields should align to the architecture contract: audit ID, check cycle ID, endpoint ID, method, path, timestamp, status code, availability, latency, expected latency if provided, latency status, sanitized error category, sanitized error summary.
- If the link is a presigned URL, include static expiry guidance in delivery communication or report text.

## 20. Privacy / Safety Messaging

Required messaging themes:

- Production APIs require written waiver/agreement and internal approval before testing.
- Standard audit covers up to 10 unique `METHOD + PATH` endpoints.
- Bearer tokens are handled as sensitive credentials and excluded from reports/CSV.
- Reports and CSV exports contain sanitized metadata only.
- Raw response bodies, headers, and trace logs are transient and not stored by default.
- Raw-data storage requires explicit written demand and approval.
- Reports are delivered through private S3 presigned URLs, not public permanent links.
- Sanitized metadata is retained for 90 days, then exported to CSV and emailed to the client.

## 21. Static Landing Page Information Architecture

Required sections in order:

1. Hero headline.
2. Problem/value proposition.
3. What’s included.
4. Privacy/safety guarantees.
5. Pricing.
6. How it works.
7. FAQ.
8. CTA.

## 22. Landing Page Copy Direction and CTA Behavior

### Copy Direction

- Hero headline should emphasize a 48-hour audit, not ongoing monitoring.
- Value proposition should target small teams needing quick evidence before launch, demo, fundraising, rollout, or handoff.
- “What’s included” should name up to 10 endpoints, 5 checks/day, approximately 10 cycles, HTML report/dashboard, sanitized CSV, and private delivery.
- Privacy copy should be plain and prominent.
- Pricing should include:
  - Standard public MVP price: **$750**.
  - Optional early validation price: **$500** for limited first audits if desired.
  - Optional resilience/burst add-on: **+$300** during validation, later **+$500**.
  - Future managed monitoring: starting at **$399/month**.
- Future monitoring must be framed as future/optional, not current MVP functionality.

### CTA Behavior

- CTA text must be exactly **Request a Reliability Audit**.
- CTA is a static link to a placeholder destination pending confirmation.
- CTA must not submit a form.
- CTA must not initiate payment.
- CTA must not create an account or login session.

## 23. Acceptance Criteria

- Landing page includes hero headline, problem/value proposition, what’s included, privacy/safety guarantees, pricing, how it works, FAQ, and CTA.
- Landing page CTA text is exactly **Request a Reliability Audit**.
- Landing page has no backend, payment, login, or form submission behavior.
- Landing page clearly states the MVP is manual/operator-assisted and not SaaS.
- Intake UX requires no more than 10 unique `METHOD + PATH` endpoints for the standard audit.
- Production testing UX requires written waiver/agreement and internal approval checklist before execution.
- Optional resilience/burst UX requires separate written approval and is outside the standard workflow.
- Report/dashboard shows observed-only latency when thresholds are absent and does not label latency pass/fail.
- Report/dashboard shows pass/fail latency labels only when thresholds are provided.
- CSV export is labeled as sanitized and excludes secrets/raw data.
- Report/dashboard and CSV delivery assumptions use private S3 presigned URLs only.
- Accessibility requirements for keyboard navigation, semantic structure, focus indicators, contrast, text status labels, and table semantics are met.

## 24. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Visitors expect a SaaS product | State that the MVP is a manual/operator-assisted audit; avoid login, account, dashboard signup, and payment UI. |
| Production testing appears too casual | Surface waiver/internal approval language prominently in privacy and FAQ sections. |
| Resilience/burst testing is mistaken for standard load testing | Present as optional add-on only with separate written approval and separate pricing. |
| Sensitive data exposure in report/CSV | Use sanitized metadata-only labels; include explicit exclusions in CSV/report copy. |
| Latency results are misinterpreted | Use `Observed only` when thresholds are absent; pass/fail only with thresholds. |
| Expired presigned URLs confuse reviewers | Include helper text explaining how to request regenerated private links. |
| Dense report tables are difficult on mobile | Use horizontal scroll with captions or responsive card rows preserving labels. |

## 25. Open Questions

- What exact placeholder destination should the landing page CTA use?
- What format and storage location should be used for written waivers/agreements and internal approval checklists?
- Who owns the 90-day CSV email: operator, automated job, or another process?
- What expiration duration should be used for S3 presigned report URLs?
- What email address or delivery mechanism should be used for post-retention CSV delivery?
- After the 90-day CSV export/email, should source sanitized metadata be deleted, archived, or retained elsewhere?
- What static site path/framework should host the Phase 1 landing page in this repository?
