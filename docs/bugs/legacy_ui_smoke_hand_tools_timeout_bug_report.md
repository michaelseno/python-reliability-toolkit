# Bug Report

## 1. Summary

Full-suite HITL sign-off failed on one legacy UI smoke test: `tests/e2e/tests/test_smoke_routes.py::test_page_smoke_loads[/category/hand-tools]`. The immediate failure is a Playwright navigation timeout while loading the external public site `https://practicesoftwaretesting.com/category/hand-tools`.

Current evidence supports an external dependency / network timing failure, not an API Reliability Audit MVP product regression.

## 2. Investigation Context

- Source of report: HITL QA validation.
- Branch context: existing branch `feature/api_reliability_audit_mvp`; no branch/PR/push requested.
- Related feature/workflow: API Reliability Audit MVP scan-pack report implementation sign-off.
- Failing workflow: full pytest regression suite after focused MVP validation.
- Failing test: `tests/e2e/tests/test_smoke_routes.py::test_page_smoke_loads[/category/hand-tools]`.
- QA result context: focused MVP validation passed 13/13; focused automated tests and unit tests passed; full regression suite had `124 passed, 1 failed`.

## 3. Observed Symptoms

- Failing test / command: QA ran full pytest suite; report records full suite result as `124 passed, 1 failed in 284.22s`.
- Exact error from QA report: `playwright._impl._errors.TimeoutError: Page.goto: Timeout 30000ms exceeded.`
- Observed behavior: Playwright timed out navigating to `https://practicesoftwaretesting.com/category/hand-tools`, waiting for `domcontentloaded`.
- Expected behavior: the legacy UI smoke route should load successfully and expose the expected notification element.
- Relevant QA evidence: `docs/qa/api_reliability_audit_mvp_test_report.md` records the failure in the failed tests table and classifies it as `Environment Issue / possible Flaky Test`.

## 4. Evidence Collected

Files inspected:

- `docs/qa/api_reliability_audit_mvp_test_report.md`
  - Lines 10-14: release-focused manual/artifact checks passed, focused automated tests passed, full unit suite passed, full pytest regression suite failed with one test.
  - Lines 107-117: failing test, timeout message, URL, and QA classification.
- `tests/e2e/tests/test_smoke_routes.py`
  - Test is marked `legacy_ui` and `smoke`.
  - It parametrizes over `SMOKE_ROUTES` and calls `open_and_assert_route(home_page, path)`.
- `tests/e2e/data/route_data.py`
  - `SMOKE_ROUTES` includes `/category/hand-tools`.
- `tests/e2e/flows/navigation_flows.py`
  - `open_and_assert_route()` calls `home_page.goto(path)` and then asserts notification visibility.
- `tests/e2e/pages/base_page.py`
  - `BasePage` hard-codes `base_url="https://practicesoftwaretesting.com"`.
  - `goto()` calls `page.goto(f"{self.base_url}{path}", wait_until="domcontentloaded")` without a test-local mock/server dependency.
- `tests/e2e/conftest.py`
  - Playwright launches Chromium and creates a real browser context.
  - It aborts some Cloudflare/challenge/analytics routes, indicating these legacy UI tests interact with a public site that may present external-service behavior.
- `pyproject.toml`
  - Defines `legacy_ui` marker as `deprecated but supported UI end-to-end scenarios` and `smoke` as fast route/UI smoke checks.

Configuration findings:

- No evidence found that this route is served by the application under test.
- The route target is an external public website, not an API Reliability Audit MVP module, CLI command, report generator, or local fixture.
- The failed route is in a legacy UI smoke suite, separate from the API Reliability Audit MVP focused/unit coverage.

## 5. Execution Path / Failure Trace

1. Full regression suite executes `test_page_smoke_loads` with parameter `path="/category/hand-tools"`.
2. The test constructs `HomePage(page)`.
3. `open_and_assert_route(home_page, path)` calls `home_page.goto(path)`.
4. `BasePage.goto()` constructs `https://practicesoftwaretesting.com/category/hand-tools` and calls Playwright `page.goto(..., wait_until="domcontentloaded")`.
5. Playwright waits up to its default navigation timeout of 30000 ms.
6. The external page does not reach `domcontentloaded` within that timeout in the QA run, so Playwright raises `TimeoutError` before the notification visibility assertion runs.

## 6. Failure Classification

- Primary classification: **Environment / Configuration Issue**.
- Contributing classification: **Flaky Test / Timing Issue**.
- Severity: **Medium** for release process / CI confidence because QA sign-off rules block approval while an executed full suite is red.
- Direct MVP impact: **Low** because focused API Reliability Audit MVP validation passed and the failing code path is a legacy external UI smoke route, not the scan-pack runtime/report implementation.

Severity justification:

- The full suite is red, preventing QA sign-off in this pass.
- The failure is isolated to an external public website navigation timeout and does not exercise the API audit runtime, report generation, CSV generation, scan-pack registry, or MVP CLI commands.

## 7. Root Cause Analysis

Root cause confidence label: **Most Likely Root Cause**

Immediate failure point:

- `BasePage.goto()` calls Playwright `page.goto()` for `https://practicesoftwaretesting.com/category/hand-tools`; navigation times out after 30000 ms before `domcontentloaded`.

Underlying root cause:

- The legacy UI smoke test depends on an external public website and is therefore exposed to network latency, public site slowness, CDN/bot-protection behavior, or transient availability issues. The failure is most consistent with an external dependency or environment/network timing issue.

Supporting evidence:

- `BasePage` default `base_url` is `https://practicesoftwaretesting.com`.
- The failed parameter `/category/hand-tools` is one of the static `SMOKE_ROUTES`.
- QA’s exact failure is a Playwright navigation timeout to that external URL, not an assertion against API Reliability Audit MVP output.
- QA report states focused MVP validation passed 13/13 and focused/unit tests passed.
- The failing test is marked `legacy_ui`, described in project config as deprecated but supported UI end-to-end scenarios.

Plausible contributing factors:

- External site/CDN behavior may vary by time, network, or bot-detection state.
- The test has no retry, no external health precheck, and no local fixture/mocked target.
- The test uses a fixed 30s Playwright navigation timeout and requires `domcontentloaded` from a third-party site.

No evidence currently supports:

- A product/application defect in the API Reliability Audit MVP implementation.
- A regression introduced by scan-pack report implementation.
- A test assertion mismatch after page load; the test failed before assertions ran.

## 8. Confidence Level

**High** that this is not an API Reliability Audit MVP application regression.

**Medium-High** that the primary cause is external dependency/network timing. The exact external condition cannot be confirmed without rerun artifacts, network logs, or successful/failed repeats, but the code path and error strongly support this classification.

## 9. Recommended Fix

Likely owner: **QA/test** unless project policy requires deterministic full-suite execution; then route to the test/platform owner.

Recommended QA handling for current HITL correction loop:

1. Rerun only the failed legacy UI smoke test once or twice to determine if it is transient:
   - `pytest tests/e2e/tests/test_smoke_routes.py::test_page_smoke_loads --maxfail=1 -q`
   - Or rerun the specific parametrized case if shell escaping supports it.
2. If rerun passes, classify as flaky external dependency and attach this report to QA sign-off notes.
3. If rerun repeatedly fails while other MVP checks remain green, do not route to API Reliability Audit MVP backend/frontend implementation as a product defect; route to QA/test owner for external-test policy.

Recommended longer-term test change if deterministic release gates are required:

- In `tests/e2e/pages/base_page.py` / E2E fixture setup, make the legacy UI base URL configurable via environment variable and point CI/HITL to a controlled target where possible.
- Or mark external legacy UI tests separately from release-blocking MVP tests and run them as allowed-to-flake/non-blocking external smoke checks.
- Or add an explicit external-site precheck/skip policy for `legacy_ui` tests when `practicesoftwaretesting.com` cannot load reliably.

Cautions:

- Do not change API Reliability Audit MVP application code for this failure based on current evidence.
- Avoid increasing timeouts as the only fix unless QA confirms the site is consistently slow but healthy; longer timeouts would not remove the external dependency risk.

## 10. Suggested Validation Steps

Targeted validation:

- Rerun the failed legacy UI smoke route/case and record pass/fail and timing.
- If it fails again, capture Playwright trace/screenshot/console/request-failed artifacts from the existing E2E artifact mechanism.
- Confirm whether other `SMOKE_ROUTES` continue to pass against `https://practicesoftwaretesting.com`.

Regression checks for MVP release decision:

- Keep the focused API Reliability Audit MVP checks as authoritative for the scan-pack/report implementation:
  - `rk audit run --config examples/api_reliability_audit/audit.local.yml`
  - `rk audit generate-report --id local-api-reliability-audit`
  - focused audit/static/packaging tests
  - unit suite
- Expected behavior: focused MVP validations remain green, generated HTML/CSV artifacts meet report requirements, and no scan-pack/runtime/report tests regress.

If a test-policy fix is implemented:

- Verify `legacy_ui` tests are either deterministic against a controlled target or clearly separated from release-blocking MVP gates.
- Verify external-site unavailable/timeout behavior is reported as skipped/non-blocking only under an approved marker or environment policy.

## 11. Open Questions / Missing Evidence

- Was the failed `/category/hand-tools` case rerun immediately, and did it pass or fail again?
- Were Playwright trace/screenshot/request-failed artifacts captured for this exact failure?
- Is the release policy intended to block API Reliability Audit MVP sign-off on legacy external UI smoke tests?
- Should `legacy_ui` tests remain in the full release-blocking suite, given their hard dependency on a public website?

## 12. Final Investigator Decision

**Likely test/environment issue, not application fix.**

Ready for QA/test handling. No API Reliability Audit MVP application-code change is recommended based on current evidence. Current release impact is a QA gate/blocker only because the executed full suite is red; direct product impact to the scan-pack report implementation is low.
