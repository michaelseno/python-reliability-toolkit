# GitHub Issue

## 1. Feature Name

48-Hour API Reliability Audit MVP implementation (`api_reliability_audit_mvp`)

## 2. Problem Summary

Small engineering teams need a bounded, low-friction way to evaluate API reliability before launches, demos, fundraising events, rollouts, or handoffs without adopting a SaaS monitoring platform. This implementation anchors the full manual/operator-assisted MVP for a 48-hour API reliability audit covering up to 10 unique `METHOD + PATH` endpoints, approximately 10 check cycles, sanitized reporting, private report delivery, and 90-day sanitized metadata retention.

This is a planning/implementation anchor issue only. It must preserve the MVP boundary: no SaaS onboarding, no customer accounts/login, no payment flow, no backend landing-page lead capture, no self-service audit configuration, no landing-page form submission, and no landing-page email submission flow.

## 3. Linked Planning Documents

- Product Spec: `docs/product/api_reliability_audit_mvp_spec.md`
- Technical Design: `docs/architecture/api_reliability_audit_mvp_architecture.md`
- UI/UX Spec: `docs/uiux/api_reliability_audit_mvp_design_spec.md`
- QA Test Plan: `docs/qa/api_reliability_audit_mvp_test_plan.md`

## 4. Scope Summary

Implement the full MVP scope described in the planning artifacts:

- Manual/operator-assisted 48-hour reliability audit workflow.
- Standard audit cap of up to 10 unique `METHOD + PATH` API endpoints.
- Default schedule of 5 checks per day for 48 hours, approximately 10 total check cycles.
- Bearer-token-first authentication support with secret-safe handling.
- Production testing gates requiring written client waiver/agreement and internal approval before execution.
- Sanitized metadata collection for status code, availability, latency, endpoint identity, check cycle, timestamps, and sanitized error/category information.
- No raw response body, raw header, or trace-log persistence by default.
- Written approval workflow for any raw-data storage exception.
- Static HTML report/dashboard generation.
- Sanitized CSV export using the approved metadata-only contract.
- Private S3 presigned URL delivery for HTML and CSV artifacts; public report URLs are prohibited.
- 90-day sanitized metadata retention.
- Automated post-retention CSV export and client email delivery using SMTP settings supplied through environment variables.
- Operator-visible, retryable SMTP failure handling without exposing secrets.
- Optional resilience/burst testing only when separately approved in writing and outside the main audit workflow.
- Phase 1 static informational landing page with required sections and exact CTA behavior.
- Landing-page CTA text must be exactly `Request a Reliability Audit`.
- Landing-page CTA destination must be exactly `#request-audit`.
- The `#request-audit` section is a static placeholder only.
- Deferred CTA form/email behavior: no form submission, no email submission, no `mailto:` CTA, no backend lead capture, no CRM/newsletter/calendar/chat intake, no payment, no login, and no account creation in MVP.

## 5. Implementation Notes

- Continue implementation on branch `feature/api_reliability_audit_mvp`.
- Preserve the manual/operator-assisted service model; do not introduce SaaS behavior.
- Extend existing repository boundaries for CLI/core/reporting/storage/static frontend rather than adding customer-facing backend APIs.
- Treat approval gates as fail-closed.
- Do not serialize bearer token values into configs, reports, CSVs, logs, filenames, S3 keys, emails, or customer-facing artifacts.
- Generate reports, CSVs, retention exports, and emails exclusively from sanitized metadata.
- Use private S3 objects and time-limited presigned URLs for report and CSV delivery.
- Implement retention automation so sanitized metadata reaches 90 days, is exported to CSV, and is emailed to the client through SMTP environment variables.
- Required SMTP environment-variable contract is defined in the architecture artifact and includes host, port, sender, TLS/SSL flags, and retention failure notification recipient; SMTP secrets must be redacted from all outputs and failures.
- Keep retention email failures visible, sanitized, retryable, and operator-actionable; failures must not silently succeed.
- Landing page must include the required static sections: hero, problem/value proposition, what’s included, privacy/safety guarantees, pricing, how it works, FAQ, and CTA/static placeholder request section.
- Landing page must include exactly one visible `id="request-audit"` anchor target and must not replace the placeholder with form/email/backend behavior during MVP.

## 6. QA Section

QA execution must validate AC-1 through AC-13 from the Product Spec and QA Test Plan:

- AC-1: Endpoint cap and unique `METHOD + PATH` endpoint definition.
- AC-2: Production waiver/authorization requirement.
- AC-3: Internal production approval requirement.
- AC-4: Bearer token handling and exclusion from reports/CSV.
- AC-5: Private S3 presigned delivery for HTML report/dashboard and sanitized CSV.
- AC-6: No raw response body, raw header, or trace-log persistence by default.
- AC-7: Raw data storage exception requires explicit written demand and written approval.
- AC-8: Sanitized CSV only; no bearer tokens, raw bodies, raw headers, trace logs, or secret references.
- AC-9: 90-day sanitized metadata retention and automated post-retention CSV email delivery through SMTP environment variables, including visible sanitized failure handling when SMTP config is missing or invalid.
- AC-10: Optional resilience/burst testing approval gate and separation from the standard audit workflow.
- AC-11: Latency threshold behavior; observed-only reporting when thresholds are absent and pass/fail labels only when thresholds are provided.
- AC-12: Audit frequency of 5 checks per day for 48 hours, approximately 10 total check cycles.
- AC-13: Static landing page content and CTA requirements, including exact CTA text, exact `#request-audit` destination, matching placeholder section, and no backend/payment/login/form/email submission or lead capture.

Release readiness requires executed QA evidence, passing validation for AC-1 through AC-13, no unresolved blocker/high-severity privacy or security defects, and explicit release QA sign-off before any PR/release action.

## 7. Risks / Open Questions

Risks:

- Production testing could proceed without sufficient authorization if gates are not fail-closed.
- Bearer tokens, SMTP credentials, raw response bodies, headers, trace logs, or sensitive metadata could leak into reports, CSVs, logs, emails, S3 keys, or failure messages.
- S3 report artifacts could be accidentally exposed through public or permanent URLs.
- Landing page could drift into SaaS, lead capture, payment, login, or email/form submission behavior outside MVP scope.
- Retention/export-after-90-days workflow could fail silently or expose SMTP diagnostics/secrets.
- Resilience/burst testing could be mistaken for standard audit behavior.
- Latency pass/fail labels could be misleading when thresholds are absent.

Open questions to resolve during implementation planning/execution:

- What format and storage location should be used for written waivers/agreements and internal approval checklists?
- What expiration duration should be used for initial S3 presigned report URLs and retention CSV presigned-link fallback?
- What concrete sender address and remediation recipient values should be configured for `RELIABILITYKIT_SMTP_FROM_EMAIL` and `RELIABILITYKIT_RETENTION_FAILURE_NOTIFY_EMAIL`?
- After the 90-day CSV export/email succeeds, should source sanitized metadata be deleted, archived, or retained elsewhere?
- What static site path/framework should host the Phase 1 landing page in this repository?
- What default endpoint request timeout should be used for audit checks?
- How should endpoint identity normalize query strings, trailing slashes, case sensitivity, and URL templates?
- For latency exactly equal to threshold, should the expected label be pass or fail?
- What evidence format is required for raw-data storage exceptions and optional resilience/burst approvals?
- What S3 presigned URL regeneration SLA or manual process should be communicated to clients?

## 8. Definition of Done

- Implementation remains on the approved feature branch and preserves the manual/operator-assisted MVP boundary.
- All linked planning artifacts remain referenced and traceable.
- Full MVP scope is implemented without SaaS onboarding, backend lead capture, payment, login, customer accounts, self-service configuration, landing-page form submission, or landing-page email submission.
- Static landing page includes required sections, exact CTA text `Request a Reliability Audit`, exact destination `#request-audit`, exactly one matching placeholder section, and no deferred/disallowed CTA behavior.
- Audit validation enforces endpoint cap, production waiver, internal approval, optional resilience/burst approval, raw-data exception rules, latency threshold behavior, schedule defaults, and sanitized-only outputs.
- HTML report/dashboard and sanitized CSV export are generated from sanitized metadata only.
- Report and CSV delivery uses private S3 presigned URLs only.
- Sanitized metadata retention is 90 days with automated post-retention CSV email through SMTP environment variables.
- SMTP failures are surfaced without secrets and remain retryable/operator-actionable.
- AC-1 through AC-13 are implemented and validated.
- QA evidence demonstrates all critical tests passed with no unresolved blocker/high-severity privacy or security defects.
- Release QA sign-off and HITL validation must be completed before any push/PR/release action.
