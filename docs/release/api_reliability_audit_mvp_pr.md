# Pull Request

## 1. Feature Name

api_reliability_audit_mvp

## 2. Summary

Implements the API Reliability Audit MVP and incorporates HITL correction loops for the scan-pack-driven audit runtime, generated static reports, local CLI workflow, landing page, retention email support, and privacy/sanitization requirements. The release keeps the MVP bounded to an operator-assisted audit service without SaaS onboarding, accounts, payment, lead capture, or public report delivery.

## 3. Related Documents

- Product Spec: docs/product/api_reliability_audit_mvp_spec.md
- Technical Design: docs/architecture/api_reliability_audit_mvp_architecture.md
- UI/UX Spec: docs/uiux/api_reliability_audit_mvp_design_spec.md
- Report Redesign UI/UX Spec: docs/uiux/api_reliability_audit_report_redesign_design_spec.md
- QA Plan: docs/qa/api_reliability_audit_mvp_test_plan.md
- QA Report: docs/qa/api_reliability_audit_mvp_test_report.md
- Implementation Issue Artifact: docs/release/api_reliability_audit_mvp_issue.md
- Bug Reports: docs/bugs/api_reliability_audit_burst_stability_scope_correction_bug_report.md; docs/bugs/api_reliability_audit_sample_report_usability_gap_bug_report.md; docs/bugs/legacy_ui_smoke_hand_tools_timeout_bug_report.md

## 4. Changes Included

- Added scan-pack-driven audit execution and report generation for the operator-assisted API Reliability Audit MVP.
- Added local `rk audit run` and `rk audit generate-report` workflow for sanitized audit collection and static report generation.
- Added modern SaaS-style static HTML audit report UI while preserving sanitized metadata-only reporting.
- Bounded `burst_stability` as an optional, separately approved workflow outside the standard audit path.
- Added static informational landing page at `frontend/index.html` with the required `Request a Reliability Audit` CTA and static `#request-audit` placeholder.
- Added SMTP-backed retention email support for sanitized post-retention CSV delivery and visible, retryable failure handling.
- Preserved privacy/sanitization constraints: no bearer tokens, SMTP secrets, raw response bodies, raw headers, trace logs, public report URLs, or disallowed SaaS/lead-capture behavior in MVP artifacts.
- Updated product, architecture, QA, UI/UX, bug, and release artifacts to reflect MVP implementation and HITL corrections.

## 5. QA Status

- Approved: YES
- QA evidence: `[QA SIGN-OFF APPROVED]` in docs/qa/api_reliability_audit_mvp_test_report.md
- HITL: HITL validation successful

## 6. Test Coverage

- Acceptance coverage for AC-1 through AC-13, including endpoint caps, production authorization gates, bearer-token exclusion, private delivery, raw-data exception handling, sanitized CSV/report output, retention email behavior, burst testing separation, latency threshold behavior, audit scheduling, and landing-page CTA/static-placeholder behavior.
- Local workflow validation for `rk audit run`, `rk audit generate-report`, generated sample report usability, and bounded HITL correction scenarios.
- Privacy/security validation for sanitized-only artifacts and redaction of secrets from reports, CSVs, logs, filenames, emails, and failure messages.

## 7. Risks / Notes

- Production audits remain fail-closed on written client authorization and internal approval.
- Optional burst/resilience testing requires separate written approval and is not part of the standard audit workflow.
- SMTP retention delivery depends on correctly supplied environment variables; failures are surfaced in sanitized, retryable, operator-actionable form.
- Runtime outputs, local report outputs, caches, ignored files, and `.runtime_context` files are intentionally excluded from release.

## 8. Linked Issue

- Closes #5
