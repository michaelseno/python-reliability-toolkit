# Bug Report

## 1. Summary

HITL validation identified three missed/correction requirements for the API Reliability Audit MVP: `checks_per_day` must remain defaulted to 5 but be configurable within recommended MVP bounds, raw diagnostic artifacts must be excluded by default from both display and persistence unless explicitly approved, and the static landing page must live at project-root `frontend/index.html` instead of `docs/frontend/api_reliability_audit_mvp_landing_page.html`.

## 2. Investigation Context

- Source of report: HITL validation pause.
- Branch context: active branch `feature/api_reliability_audit_mvp`; no new branch should be created.
- Related feature/workflow: 48-Hour API Reliability Audit MVP, including backend audit configuration/privacy gates, generated reports/artifact persistence, and Phase 1 static landing page.
- User action: static page review and requirements correction request.
- Relevant acceptance criteria affected: AC-6, AC-7, AC-8, AC-12, AC-13; also product requirements FR-2, FR-5, FR-6, FR-8, FR-10, FR-11, FR-13.

## 3. Observed Symptoms

### Symptom A — `checks_per_day` is not configurable

- Observed behavior: `AuditConfig.checks_per_day` defaults to 5, but validation rejects any value other than 5.
- Exact evidence: `reliabilitykit/core/audit.py:257-260` enforces default duration and then raises `AuditValidationError("standard audit checks_per_day must be 5")` when `config.checks_per_day != DEFAULT_CHECKS_PER_DAY`.
- Expected behavior from HITL correction: default remains 5 checks/day over 48 hours (~10 cycles), but `checks_per_day` is configurable with recommended MVP limits `min=1`, `max=24`; increases above default require operator/client agreement.

### Symptom B — raw diagnostic artifact policy needs stronger display and persistence coverage

- Observed behavior: current `PrivacyPolicy` gates raw body/header/trace storage flags, and generated MVP audit report/CSV tests assert sentinels are absent. However, the confirmed correction broadens/clarifies the requirement to reports and persisted artifacts/storage: raw logs, raw responses, and stack traces are not included or persisted by default, and may be collected/included/persisted only with explicit client request plus written approval/reference.
- Exact evidence: `reliabilitykit/core/audit.py:120-132` has `store_raw_bodies`, `store_raw_headers`, `store_trace_logs`, and requires `raw_data_exception_reference` plus `raw_data_written_demand_reference` only when those flags are true.
- Exact evidence: product spec currently states raw response bodies, raw headers, and trace logs are transient/not stored by default (`docs/product/api_reliability_audit_mvp_spec.md:172-182`, `231-241`) and reports avoid bearer tokens/raw response bodies/raw headers/trace logs (`191-196`).
- Expected behavior from HITL correction: default report contains audit results only; raw logs, raw responses, and stack traces must not be displayed or persisted by default. Any collection, inclusion, or persistence requires explicit client request and written approval/reference.

### Symptom C — static landing page is in the wrong location

- Observed behavior: landing page was implemented at `docs/frontend/api_reliability_audit_mvp_landing_page.html`.
- Exact evidence: frontend implementation report lists that path as the implemented location (`docs/frontend/api_reliability_audit_mvp_implementation_report.md:5`, `11-14`) and states the location was an assumption (`25-29`).
- Exact evidence: static page tests hard-code `docs/frontend/api_reliability_audit_mvp_landing_page.html` as `LANDING_PAGE` (`tests/unit/test_static_landing_page.py:5-10`).
- Exact evidence: repository root currently has no `frontend/` directory (`git status` shows `?? docs/frontend/`; root directory listing has no `frontend/`).
- Expected behavior from HITL correction: move static page to project-root `frontend/index.html`; keep `docs/frontend/` only for implementation docs.

## 4. Evidence Collected

- `git status --short --branch`: confirmed active branch `feature/api_reliability_audit_mvp` and untracked `docs/frontend/` plus test/report artifacts.
- `reliabilitykit/core/audit.py:151-163`: `AuditConfig` includes `schedule_duration_hours`, `checks_per_day`, `expected_check_cycles`, and `privacy_policy`.
- `reliabilitykit/core/audit.py:257-262`: validation currently hard-requires duration 48, `checks_per_day == 5`, and `expected_check_cycles == 10`.
- `reliabilitykit/core/audit.py:120-132`: raw data flags fail closed unless written demand and approval references are set.
- `tests/unit/test_api_reliability_audit_mvp.py:131-135`: tests only assert default `checks_per_day == 5` and expected cycles `10`; no configurable bounds or approval-gate coverage for increased frequency was found in inspected test slice.
- `tests/unit/test_api_reliability_audit_mvp.py:146-180`: tests assert report/CSV/check-cycle serialization exclude sentinel raw body/header/trace values.
- `docs/product/api_reliability_audit_mvp_spec.md:154-159`: FR-2 currently documents only default duration/frequency/cycles, not configurable frequency bounds or approval requirement above default.
- `docs/product/api_reliability_audit_mvp_spec.md:172-182`, `191-196`, `203-214`, `231-241`: current privacy/report/CSV/retention requirements cover raw response bodies, raw headers, and trace logs, but HITL correction explicitly adds raw logs, raw responses, stack traces, report display, persisted artifacts/storage, and written approval/reference for exceptions.
- `docs/frontend/api_reliability_audit_mvp_implementation_report.md:25-29`: frontend path under `docs/frontend/` was implemented as an assumption because no static app path existed.
- `tests/unit/test_static_landing_page.py:5-10`: landing page test target points at `docs/frontend/api_reliability_audit_mvp_landing_page.html`.
- `docs/qa/api_reliability_audit_mvp_test_report.md:24-31`: QA previously marked AC-6 and AC-12/AC-13 as passing under the earlier interpretation, so QA coverage must be updated for the corrected requirements.

## 5. Execution Path / Failure Trace

1. Operator creates or validates an `AuditConfig` for a standard audit.
2. `AuditConfig` validation calls `validate_audit_config()` from `reliabilitykit/core/audit.py`.
3. Any non-default `checks_per_day` value reaches `if config.checks_per_day != DEFAULT_CHECKS_PER_DAY` and is rejected, preventing allowed configurable schedules.
4. Report generation/persistence currently use sanitized models in the MVP path, but the explicit exception policy needs to cover display and persisted artifacts/storage for raw logs, raw responses, and stack traces, not only raw bodies/headers/trace logs.
5. Static page validation and implementation point to `docs/frontend/api_reliability_audit_mvp_landing_page.html`, so the deployable frontend artifact is not at the requested project-root `frontend/index.html` path.

## 6. Failure Classification

- Primary classification: Requirements Ambiguity / Missed Requirement.
- Contributing classification: Application Bug for the backend configurability behavior because current validation rejects an explicitly required valid configuration range.
- Severity: Blocker.
- Severity justification: HITL validation is paused, the correction scope changes acceptance criteria before release, and AC-12/AC-13 cannot pass under the confirmed corrected requirements until implementation/tests/docs are updated.

## 7. Root Cause Analysis

### Most Likely Root Cause

The implemented MVP followed an earlier/static interpretation of the requirements: check frequency was treated as fixed at 5/day, raw-data privacy was validated for the original body/header/trace scope, and the landing page location was chosen by implementer assumption because no frontend root existed.

### Immediate failure points

- Backend: `reliabilitykit/core/audit.py:259-260` rejects any `checks_per_day` value other than 5.
- Frontend/tests: `docs/frontend/api_reliability_audit_mvp_landing_page.html` and `tests/unit/test_static_landing_page.py:5-10` use the wrong static page location.
- QA/docs: QA report marks the prior AC-12/AC-13 scope as passing; acceptance criteria/test plan need correction to the HITL-confirmed scope.

### Supporting evidence

- The frontend implementation report explicitly labels `docs/frontend/` as an assumption (`docs/frontend/api_reliability_audit_mvp_implementation_report.md:25-29`).
- Product FR-2 states default frequency but does not document configurability/bounds/approval above default (`docs/product/api_reliability_audit_mvp_spec.md:154-159`).
- Current backend validation enforces fixed frequency, not bounded configurability (`reliabilitykit/core/audit.py:257-260`).

### Plausible contributing factors

- Existing tests mirror the earlier requirement wording and therefore passed without covering corrected scenarios: configurable `checks_per_day` bounds, approval/reference requirement for values above 5, and root `frontend/index.html` location.

## 8. Confidence Level

High.

The path/location issue and fixed-frequency validation are directly evidenced by source files and tests. The raw-artifact policy is mostly implemented for the original MVP objects, but the HITL correction expands/clarifies the contract; additional code inspection during implementation should confirm all generated report/dashboard and storage paths comply.

## 9. Recommended Fix

### Backend owner: dev-backend

- Update `AuditConfig` / `validate_audit_config()` in `reliabilitykit/core/audit.py` to allow `checks_per_day` values from 1 through 24.
- Keep default `checks_per_day = 5` and default 48-hour expected cycles around 10.
- Add an approval/reference field or reuse a clearly named existing agreement reference for `checks_per_day > 5`; reject increased frequency when the operator/client agreement reference is missing.
- Update `expected_check_cycles` handling so it remains consistent with configurable frequency over 48 hours or is validated against the configured frequency rather than hard-coded to 10 when frequency changes.
- Extend privacy policy naming/validation as needed so raw logs, raw responses, and stack traces are covered by the same explicit-request-plus-written-approval/reference gate for collection, display, inclusion, and persistence.

### Frontend owner: dev-frontend

- Move/copy the static page artifact to project-root `frontend/index.html`.
- Keep `docs/frontend/` for implementation plan/report documentation only; do not leave the deployable HTML page there unless explicitly retained as documentation.
- Update static landing page tests to target `frontend/index.html`.

### QA owner: QA/test

- Update QA test plan/report and unit tests for corrected AC scope:
  - default schedule remains 48h / 5 checks/day / ~10 cycles;
  - `checks_per_day=1` and `checks_per_day=24` are valid when expected-cycle handling/agreement rules are satisfied;
  - `checks_per_day=0` and `checks_per_day=25` are rejected;
  - `checks_per_day > 5` is rejected without operator/client agreement reference and accepted with it;
  - raw logs/raw responses/stack traces sentinels are absent from default reports and persisted artifacts/storage;
  - raw artifact inclusion/persistence is only accepted with explicit client request and written approval/reference;
  - static page exists at `frontend/index.html`, with `docs/frontend/` reserved for docs.

## 10. Suggested Validation Steps

- Run targeted unit tests for `AuditConfig` schedule validation covering default, min, max, below-min, above-max, and above-default approval scenarios.
- Run privacy/sentinel tests scanning generated HTML reports, CSV exports, local persisted audit results, retention records, and any storage/upload artifacts for raw log/raw response/stack-trace sentinel values.
- Run exception-path tests proving raw artifact collection/inclusion/persistence is fail-closed without explicit request plus written approval/reference.
- Run static page tests against `frontend/index.html` and verify no deployable HTML remains incorrectly under `docs/frontend/`.
- Re-run the focused MVP unit tests and the QA AC/privacy validation script after implementation.
- Manual HITL re-review should confirm page location and copy reflect configurable check frequency and default raw-artifact exclusion.

## 11. Open Questions / Missing Evidence

- Exact field name/source of truth for “operator/client agreement” for `checks_per_day > 5` is not yet specified.
- Whether `expected_check_cycles` should be operator-configurable, derived from `schedule_duration_hours * checks_per_day / 24`, or validated with tolerance needs product/backend confirmation.
- Whether approved raw-artifact exception storage requires a separate retention/deletion policy beyond sanitized metadata retention is not specified in the HITL note.

## 12. Final Investigator Decision

Ready for developer fix.

Root cause is clear for the fixed-frequency validation and wrong frontend location. The raw-artifact requirement is a confirmed contract clarification/missed requirement requiring implementation and QA coverage updates, with minor open questions about naming and retention semantics for approved exceptions.
