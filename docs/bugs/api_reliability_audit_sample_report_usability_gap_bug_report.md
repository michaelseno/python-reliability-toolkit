# Bug Report

## 1. Summary

During HITL validation/correction on `feature/api_reliability_audit_mvp`, the local API Reliability Audit workflow remains too verbose and is missing the confirmed short executable and simplified audit commands. The clarified requirement is to support `rk audit run --config examples/api_reliability_audit/audit.local.yml` for a full local check cycle and `rk audit generate-report --id <audit_id>` for report generation from the latest persisted result.

## 2. Investigation Context

- Source of report: HITL validation/correction feedback.
- Branch context: active branch `feature/api_reliability_audit_mvp`; do **not** create a new branch.
- Related feature/workflow: API Reliability Audit MVP local terminal workflow and HTML report generation.
- Relevant user action/commands required by clarification:
  - `rk audit run --config examples/api_reliability_audit/audit.local.yml`
  - `rk audit generate-report --id <audit_id>`
- Acceptance criteria impact:
  - Local terminal commands must be streamlined.
  - `--config` is required for `audit run`; no default config should be assumed.
  - Report generation should use persisted/snapshot audit metadata if available and should not require the user to manually pass config/result JSON paths.
  - Do not add a convenience `sample-report` command.

## 3. Observed Symptoms

- Failing workflow: HITL/local user workflow for running an audit and generating the HTML report with simple commands.
- Existing CLI shape requires longer commands and manual artifact wiring:
  - `reliabilitykit audit validate --config ...`
  - `reliabilitykit audit check-cycle --config ... --cycle-id ...`
  - `reliabilitykit audit report --config ... --result-json ... --output-dir ...`
- Current package script exposes only `reliabilitykit`, not the required short executable `rk`.
- Existing audit subcommands are `validate`, `check-cycle`, `report`, `deliver`, `retention-create`, and `retention-process`; required `run` and `generate-report` commands are absent.
- Expected behavior:
  - Users can invoke the CLI as `rk ...`.
  - `rk audit run --config examples/api_reliability_audit/audit.local.yml` validates config, runs one check cycle, persists a sanitized result JSON under `.reliabilitykit/audits/<audit_id>/results/<cycle_id>.json`, and prints `audit_id` plus result path.
  - `rk audit generate-report --id <audit_id>` finds the latest result JSON under `.reliabilitykit/audits/<audit_id>/results/`, uses persisted/snapshot audit metadata when available, and writes `audit_report.html` and `audit_sanitized.csv` under `.reliabilitykit/audits/reports/<audit_id>/`.

## 4. Evidence Collected

- `pyproject.toml:22-23` defines only one console script: `reliabilitykit = "reliabilitykit.cli.main:app"`; no `rk` entry point is currently declared.
- `reliabilitykit/cli/main.py:21-29` registers the top-level CLI commands and adds the audit app at `audit`, but this does not create a short executable alias by itself.
- `reliabilitykit/cli/commands/audit.py:18-25` implements `audit validate` with required `--config`.
- `reliabilitykit/cli/commands/audit.py:28-38` implements `audit check-cycle` with required `--config` and required `--cycle-id`; it writes a result through `LocalStorageBackend.write_audit_result()` and prints only the output path.
- `reliabilitykit/cli/commands/audit.py:41-53` implements `audit report`, requiring both `--config` and `--result-json`; it does not discover the latest result by audit id.
- `reliabilitykit/storage/local.py:73-84` writes audit results to `.reliabilitykit/audits/<audit_id>/results/<cycle_id>.json` when the default root is used.
- `reliabilitykit/storage/local.py:73-78` currently also creates `.reliabilitykit/audits/<audit_id>/reports`, while the clarified required report output is `.reliabilitykit/audits/reports/<audit_id>/`.
- Existing related report previously documented a local usability gap around placeholder report commands and absence of a direct, copy-pasteable local workflow.

## 5. Execution Path / Failure Trace

1. HITL reviewer attempts to follow a concise local workflow using the now-confirmed `rk` command shape.
2. Installed package metadata only exposes `reliabilitykit`, so `rk ...` is not available unless separately added outside the package.
3. Even when using `reliabilitykit`, the audit CLI does not provide `audit run`; the user must manually call separate validate/check-cycle commands and supply a cycle id.
4. The check-cycle command persists the result JSON under the required results directory, but it does not provide the required combined workflow or explicit `audit_id` output.
5. Report generation then requires the user to manually locate and pass both config and result JSON to `audit report`; there is no `audit generate-report --id <audit_id>` command that discovers the latest result and uses persisted/snapshot metadata.
6. The local audit/report workflow therefore does not meet the clarified usability acceptance criteria.

## 6. Failure Classification

- Primary classification: Application Bug.
- Contributing classification: Documentation Gap / Requirements Clarification from HITL.
- Severity: High.
- Severity justification: This is a HITL correction blocker for the delivered API Reliability Audit MVP local workflow. The underlying check/report primitives exist, but the accepted user-facing workflow and executable contract are missing.

## 7. Root Cause Analysis

### Most Likely Root Cause

The delivered CLI exposes lower-level audit primitives but not the clarified product-level local workflow contract. The package lacks the required `rk` executable alias, and the audit command group lacks the required `run` and `generate-report` commands that encapsulate validation, result persistence, latest-result discovery, and report output conventions.

### Immediate failure point

- Missing CLI entry point: `pyproject.toml` does not define `rk`.
- Missing commands: `reliabilitykit/cli/commands/audit.py` does not define `run` or `generate-report`.

### Underlying root cause

- Earlier implementation centered on explicit operator primitives (`validate`, `check-cycle`, `report`) and placeholder/manual wiring. HITL clarification now requires a simplified local audit workflow with stable short command names and automatic artifact lookup.

### Supporting evidence

- Console script evidence: only `reliabilitykit` is registered (`pyproject.toml:22-23`).
- Command evidence: audit command file contains `validate`, `check-cycle`, and `report`, but not required `run`/`generate-report` commands (`reliabilitykit/cli/commands/audit.py:18-53`).
- Storage evidence: result persistence path already aligns with `.reliabilitykit/audits/<audit_id>/results/<cycle_id>.json` (`reliabilitykit/storage/local.py:80-84`), so the correction can build on existing storage behavior.

### Plausible contributing factors

- Existing report generation requires `--config` and `--result-json`, which is correct for a low-level primitive but mismatches the clarified simplified command contract.
- Persisted/snapshot audit metadata support may be incomplete or absent; `LocalStorageBackend` currently shows result and retention record methods but no obvious audit metadata snapshot write/read method in the inspected file.

## 8. Confidence Level

High.

The mismatch is directly visible in package entry points and audit CLI command definitions. Full runtime confirmation was not performed because this task requested investigation/reporting only and did not authorize executing application commands or tests.

## 9. Recommended Fix

- Likely owner: backend/full-stack CLI developer, with documentation support.
- Likely files/modules:
  - `pyproject.toml` for adding the `rk` console script alias.
  - `reliabilitykit/cli/commands/audit.py` for adding `audit run` and `audit generate-report`.
  - `reliabilitykit/storage/local.py` and/or audit core/reporting modules if metadata snapshot persistence/discovery needs support.
  - Local workflow docs/README and `examples/api_reliability_audit/audit.local.yml` documentation references.
- Expected correction:
  - Add `rk = "reliabilitykit.cli.main:app"` as a short executable while preserving `reliabilitykit` unless product explicitly decides otherwise.
  - Add `rk audit run --config <path>` with `--config` required and no default config fallback.
  - `audit run` should validate config, run exactly one local check cycle, persist the result to `.reliabilitykit/audits/<audit_id>/results/<cycle_id>.json`, persist/snapshot audit metadata if needed for later report generation, and print both `audit_id` and result JSON path.
  - Add `rk audit generate-report --id <audit_id>` that locates the latest result JSON under `.reliabilitykit/audits/<audit_id>/results/`, uses persisted/snapshot audit metadata if available, and writes `audit_report.html` plus `audit_sanitized.csv` under `.reliabilitykit/audits/reports/<audit_id>/`.
  - Update local workflow documentation to use only the clarified commands for the happy path.
  - Do not add `sample-report`.
- Cautions/constraints:
  - Do not assume a default config for `audit run`; `--config` is explicitly required.
  - Avoid committing `.reliabilitykit` runtime artifacts or secrets.
  - Preserve existing lower-level commands unless there is a deliberate compatibility decision to remove/rename them.

## 10. Suggested Validation Steps

- Install the package locally in the supported development mode and confirm `rk --help` works.
- Run `rk audit run --config examples/api_reliability_audit/audit.local.yml` against a safe configured endpoint.
- Confirm stdout includes `audit_id` and a result path.
- Confirm result JSON exists at `.reliabilitykit/audits/<audit_id>/results/<cycle_id>.json`.
- Run `rk audit generate-report --id <audit_id>`.
- Confirm generated files exist at `.reliabilitykit/audits/reports/<audit_id>/audit_report.html` and `.reliabilitykit/audits/reports/<audit_id>/audit_sanitized.csv`.
- Confirm report generation uses the latest result when multiple cycle JSON files exist.
- Confirm `rk audit run` fails clearly when `--config` is omitted.
- Confirm no `sample-report` command appears in `rk audit --help`.
- Update/verify docs show the simplified local workflow and do not rely on placeholder-only commands.

## 11. Open Questions / Missing Evidence

- The exact cycle id generation rule for `audit run` is not specified. Developer should choose a deterministic safe convention such as timestamp/UUID unless product specifies otherwise.
- The persisted/snapshot audit metadata format and storage path are not specified. Developer should choose a minimal local metadata artifact that supports `generate-report --id` without requiring the original config path.
- Whether `generate-report` should fail if metadata is unavailable or fall back to result-only metadata is not fully specified; requirement says use persisted/snapshot audit metadata “if available.”

## 12. Final Investigator Decision

Ready for developer fix.

This is a HITL-confirmed usability/correction issue on the active branch. The existing implementation provides useful primitives, but it does not satisfy the clarified CLI contract for `rk audit run` and `rk audit generate-report`.
