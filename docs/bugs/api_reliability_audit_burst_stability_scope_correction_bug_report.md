# Bug Report

## 1. Summary

HITL validation confirmed a scope correction for the API Reliability Audit MVP: `burst_stability` must be included in the standard audit scan pack, runtime, and generated report because it is the only approved resilience-style check in scope. Other fault-injection, chaos, destructive, load, or broader resilience tests remain excluded unless separately approved. `burst_stability` must be bounded and must not become load testing.

## 2. Investigation Context

- Source of report: HITL validation/correction feedback.
- Branch context: active branch `feature/api_reliability_audit_mvp`; do **not** create a new branch, push, or create a PR.
- Related feature/workflow: 48-Hour API Reliability Audit MVP scan-pack execution, sanitized result capture, CSV/export, and customer-facing static HTML report redesign.
- Related design artifact: `docs/uiux/api_reliability_audit_report_redesign_design_spec.md`.
- Relevant user decision: `burst_stability` is part of the standard audit because it is the only resilience-style check involved; all other fault injections, chaos, destructive, or resilience tests remain excluded unless separately approved; `burst_stability` remains bounded and must not become load testing.

## 3. Observed Symptoms

- HITL reviewer rejected the generated audit report as low-impact and insufficient for the product's main selling point.
- UI/UX redesign identified scan-pack results as the core content needed for a higher-impact report and flagged an unresolved conflict around `burst_stability`:
  - `docs/uiux/api_reliability_audit_report_redesign_design_spec.md:23-34` lists `Burst Stability` inside `core_reliability_scan` and requires per-scan-pack results in the report.
  - `docs/uiux/api_reliability_audit_report_redesign_design_spec.md:416` says `burst_stability` needed clarification because prior product/architecture language treated resilience/burst testing as optional.
  - `docs/uiux/api_reliability_audit_report_redesign_design_spec.md:536` records the same issue as an open question/blocker.
- Product/architecture language still contains broader optional-resilience exclusions that can conflict with the now-confirmed exception:
  - `docs/product/api_reliability_audit_mvp_spec.md:46` says default audit workflow should not include resilience or burst testing.
  - `docs/product/api_reliability_audit_mvp_spec.md:104-105` excludes default load testing and unapproved resilience/burst testing.
  - `docs/architecture/api_reliability_audit_mvp_architecture.md:27` says resilience/burst testing is optional and outside the standard workflow.
- Expected behavior after HITL correction:
  - Standard audit includes the bounded `burst_stability` scenario from `core_reliability_scan`.
  - Runtime and data model capture sanitized `burst_stability` execution/result data like other scan-pack scenarios.
  - Report and CSV/export surface sanitized `burst_stability` status/evidence/remediation where scan-pack export coverage is approved.
  - No other resilience, chaos, destructive, fault-injection, or load-testing behavior is introduced without separate approval.

## 4. Evidence Collected

- `reliabilitykit/core/scan_packs.py:19-34`: `core_reliability_scan` includes `burst_stability` alongside baseline, repeated stability, validation, auth, timeout, and response-consistency scenarios.
- `reliabilitykit/core/scenario_registry.py:35-42`: `burst_stability` is defined as `Burst Stability`, category `burst_stability`, severity `high`, marker `scenario_burst_stability`, and tag `burst`.
- `reliabilitykit/core/audit.py:234-245`: `AuditResult` currently captures endpoint-cycle results only; no scan-pack/scenario result collection is present in the inspected model.
- `reliabilitykit/core/audit.py:339-385`: `execute_check_cycle()` performs one normal endpoint request per enabled endpoint and returns endpoint metadata; it does not execute or capture per-scenario scan-pack outcomes.
- `reliabilitykit/reporting/audit.py:12-26`: current CSV columns contain endpoint-cycle metadata only, with no scan-pack/scenario columns.
- `reliabilitykit/reporting/audit.py:104-124`: current report renders endpoint rows only, not a scan-pack matrix or `burst_stability` result.
- `docs/uiux/api_reliability_audit_report_redesign_design_spec.md:433-493`: UI/UX already requires backend/data-model additions for scan-pack execution, sanitized scan results, and CSV/export schema decision.
- `docs/uiux/api_reliability_audit_report_redesign_design_spec.md:513-539`: QA criteria require every endpoint to show every scenario from `core_reliability_scan` or explicit not-run/not-applicable rationale, while also listing the prior `burst_stability` scope conflict as an open question.

## 5. Execution Path / Failure Trace

1. Productized report redesign expects `core_reliability_scan` to be the substantive audit content model.
2. `core_reliability_scan` already includes `burst_stability` in `reliabilitykit/core/scan_packs.py`.
3. Prior product and architecture language broadly excluded default resilience/burst testing, causing ambiguity over whether `burst_stability` should run or be shown as gated/not-run.
4. HITL decision now resolves the ambiguity: `burst_stability` is the sole bounded resilience-style scenario allowed in the standard audit.
5. Current audit runtime/result/report path still only captures endpoint-level checks, so implementation must add scan-pack execution/result capture and ensure `burst_stability` is included without opening the door to load testing or other unapproved resilience tests.

## 6. Failure Classification

- Primary classification: Requirements Ambiguity.
- Contributing classification: Contract Mismatch, because product/architecture non-goals and UI/UX scan-pack/report requirements conflicted until the HITL decision clarified the exception.
- Severity: Blocker.
- Severity justification: This was raised during HITL validation/correction, blocks report redesign implementation sign-off, and directly affects the product's main customer-facing artifact and core scan-pack contract.

## 7. Root Cause Analysis

### Confirmed Root Cause

The approved MVP scope had conflicting language: `core_reliability_scan` and the report redesign require `burst_stability` scan-pack visibility, while product/architecture non-goals broadly exclude resilience/burst testing from the standard workflow. HITL has now confirmed a narrow exception: include bounded `burst_stability` as the only standard resilience-style check; continue excluding all other fault-injection, chaos, destructive, load, or broader resilience tests unless separately approved.

### Immediate failure point

- Specification/design handoff ambiguity around whether `burst_stability` is standard or separately gated.
- Runtime/report implementation gap: inspected `AuditResult`, `execute_check_cycle()`, report template, and CSV export do not yet capture/render per-scenario scan-pack results.

### Supporting evidence

- `scan_packs.py` includes `burst_stability` in the standard `core_reliability_scan`.
- UI/UX report redesign explicitly flagged the conflict at lines 416 and 536.
- Product/architecture docs contain broader optional-resilience exclusions that need a carved-out exception for bounded `burst_stability`.

### Plausible contributing factors

- The scenario description in `scenario_registry.py:39` says "Concurrent burst traffic remains resilient," which could be misread as load testing unless implementation defines strict bounds.
- CSV/export schema for scan-pack results is still undecided in the UI/UX handoff (`docs/uiux/api_reliability_audit_report_redesign_design_spec.md:486-489`, `539`).

## 8. Confidence Level

High.

The scope decision is directly supplied by HITL feedback, and the affected code/docs are directly evidenced. Exact runtime bounds for `burst_stability` still require PO/architecture approval before implementation.

## 9. Recommended Fix

- Likely owners/routes:
  - PO: update product scope/non-goals to document the narrow `burst_stability` exception and preserve exclusion of all other unapproved resilience/fault/chaos/destructive/load tests.
  - Architect: update architecture scan-pack execution/data model and define bounded `burst_stability` runtime constraints.
  - UI/UX: update `docs/uiux/api_reliability_audit_report_redesign_design_spec.md` to close the open question and reflect the confirmed standard-scan behavior.
  - dev-backend: implement scan-pack execution/result capture and ensure `burst_stability` remains bounded.
  - report-template implementation owner: render `burst_stability` in scan-pack matrix/test detail sections using sanitized evidence only.
  - QA: add acceptance/regression coverage for the confirmed exception and exclusion boundaries.
- Likely files/modules:
  - Product scope/non-goals: `docs/product/api_reliability_audit_mvp_spec.md`.
  - Architecture scan-pack execution/data model: `docs/architecture/api_reliability_audit_mvp_architecture.md` and backend model/runtime design.
  - Scan-pack definition: `reliabilitykit/core/scan_packs.py` should continue including `burst_stability` in `core_reliability_scan`; add comments/metadata only if useful to prevent future removal or over-expansion.
  - Scenario metadata: `reliabilitykit/core/scenario_registry.py` may need bounded-language clarification/remediation guidance.
  - Audit runtime/result capture: `reliabilitykit/core/audit.py` and related runner/orchestration modules need sanitized per-scenario result models and execution path.
  - Report generation/template: `reliabilitykit/reporting/audit.py` or replacement template must render scan-pack matrix/test details including `burst_stability`.
  - CSV/export if applicable: add sanitized scan-pack result export or approved expanded CSV schema; do not include raw logs/responses/headers/bodies/traces/stack traces/secrets.
  - QA coverage: `docs/qa/api_reliability_audit_mvp_test_plan.md`, QA report, and targeted unit/integration/report-template tests.
- Expected correction:
  - Treat `burst_stability` as standard, bounded scan-pack reliability evidence.
  - Do not require the optional `resilience_burst_approval_reference` for standard bounded `burst_stability`.
  - Continue requiring separate written approval for any other resilience/burst add-on, fault injection, chaos, destructive testing, or load testing.
  - Define bounds so `burst_stability` cannot scale into load testing (for example, limited request count/concurrency/duration and safe sequential/modest parallel behavior approved by architect/PO).

## 10. Suggested Validation Steps

- Product/architecture review confirms docs carve out only bounded `burst_stability` from broader optional-resilience exclusions.
- Unit/contract tests verify `core_reliability_scan` contains `burst_stability` and excludes unapproved chaos/fault/destructive/load scenarios.
- Runtime tests verify standard audit executes/captures bounded `burst_stability` without requiring optional resilience approval and without exceeding approved bounds.
- Negative tests verify other resilience/burst/fault/chaos/destructive/load tests remain rejected or not run without separate written approval.
- Report-template tests verify every endpoint renders `Burst Stability` in the scan-pack matrix/test details with status, severity, sanitized evidence, and remediation.
- CSV/export tests verify `burst_stability` sanitized metadata is exported if scan-pack export is approved, and raw logs/responses/headers/bodies/traces/stack traces/secrets remain absent.
- HITL re-review confirms the redesigned report uses scan-pack results as substantive customer-facing evidence and no longer treats `burst_stability` as an unresolved blocker.

## 11. Open Questions / Missing Evidence

- Exact operational bounds for `burst_stability` are not yet specified: maximum concurrent requests, total requests per endpoint, duration, retry behavior, timeout, and whether execution is sequential across endpoints.
- Final CSV/export schema for scan-pack results still needs product/QA approval.
- Whether the UI/UX design artifact should be updated directly or superseded by an implementation addendum is a routing decision for UI/UX/PO.

## 12. Final Investigator Decision

Ready for developer fix.

The HITL decision resolves the prior scope ambiguity. Implementation should proceed on the existing branch after PO/architecture/UI/UX update the handoff contract, with backend/report-template/QA changes scoped to bounded standard `burst_stability` and continued exclusion of all other unapproved resilience/load/fault/chaos/destructive testing.
