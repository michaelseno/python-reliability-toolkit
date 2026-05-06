# Bug Report

## 1. Summary

During HITL correction validation on `feature/api_reliability_audit_mvp`, the installed `rk` console executable is present after `uv pip install -e .` but fails before CLI dispatch with `ModuleNotFoundError: No module named 'reliabilitykit'`. The module invocation path works, so the blocker is isolated to package/import discoverability for the installed console-script workflow.

## 2. Investigation Context

- Source of report: HITL QA validation.
- Branch context: active branch `feature/api_reliability_audit_mvp`; no new branch should be created.
- Related feature/workflow: 48-Hour API Reliability Audit MVP simplified local CLI workflow.
- Required user-facing commands:
  - `rk audit run --config examples/api_reliability_audit/audit.local.yml`
  - `rk audit generate-report --id local-api-reliability-audit`
- QA report inspected: `docs/qa/api_reliability_audit_mvp_test_report.md`.

## 3. Observed Symptoms

- Failing workflow: installed `rk` executable after editable install.
- Install evidence: QA report lines 138-142 show `uv pip install -e .` completed successfully and installed `reliabilitykit==0.1.0`.
- Exact failure for `.venv/bin/rk --help`:

```text
Traceback (most recent call last):
  File "/Users/mjseno/Documents/Development/2026_fortfolio_projects/python_reliability_toolkit/.venv/bin/rk", line 4, in <module>
    from reliabilitykit.cli.main import app
ModuleNotFoundError: No module named 'reliabilitykit'
```

- Exact same import failure occurs for:
  - `.venv/bin/rk audit run --config examples/api_reliability_audit/audit.local.yml`
  - `.venv/bin/rk audit run`
  - `.venv/bin/rk audit --help`
- Expected behavior:
  - `rk --help` and `rk audit --help` should dispatch to Typer help.
  - `rk audit run --config ...` should validate config, run one check cycle, persist the result, and print `audit_id`/`result_json`.
  - `rk audit run` without `--config` should reach Typer validation and report `Missing option '--config'`.
- Diagnostic pass evidence: QA report lines 98-129 show `.venv/bin/python -m reliabilitykit.cli.main ...` works for `audit run`, missing-config validation, and `audit generate-report`.

## 4. Evidence Collected

- `docs/qa/api_reliability_audit_mvp_test_report.md:15`: QA marked the feature **Not approved** because the required installed `rk` executable fails.
- `docs/qa/api_reliability_audit_mvp_test_report.md:43-47`, `60-64`, `77-80`: traceback fails at generated script line 4 while importing `reliabilitykit.cli.main`.
- `docs/qa/api_reliability_audit_mvp_test_report.md:146-152`: focused and full pytest suites passed (`35 passed`, `121 passed`), so current tests do not cover installed console-script importability.
- `.venv/bin/rk:1-10`: generated script uses the venv interpreter and imports `from reliabilitykit.cli.main import app` at top level.
- `pyproject.toml:22-24`: console scripts are declared as:
  - `reliabilitykit = "reliabilitykit.cli.main:app"`
  - `rk = "reliabilitykit.cli.main:app"`
- `pyproject.toml:26-30`: setuptools package discovery is configured with `package-dir = {"" = "."}` and `include = ["reliabilitykit*"]`.
- `reliabilitykit/cli/main.py:5-11`: CLI module imports application subcommands from the `reliabilitykit` package; module-level invocation succeeds under QA, confirming the CLI implementation itself can run when the package is importable.
- `docs/backend/api_reliability_audit_mvp_implementation_report.md:98` records an earlier local console-script import failure with the same `ModuleNotFoundError`; line 104 later reports a pass for `uv pip install -e . && ./.venv/bin/rk --help`, indicating this may be environment/path-sensitive and not covered by automated validation.

## 5. Execution Path / Failure Trace

1. QA installs the project in editable mode with `uv pip install -e .`.
2. The install creates `.venv/bin/rk` from the `[project.scripts]` entry point in `pyproject.toml`.
3. When `.venv/bin/rk` is executed, Python runs the generated script from `.venv/bin`.
4. Before Typer can dispatch any command, the generated script executes `from reliabilitykit.cli.main import app`.
5. The interpreter cannot resolve the top-level `reliabilitykit` package in the console-script context and raises `ModuleNotFoundError`.
6. Because failure occurs before `reliabilitykit.cli.main.app` is loaded, all `rk audit ...` commands fail identically and never reach audit command logic.

## 6. Failure Classification

- Primary classification: Application Bug.
- Subtype: packaging / console-entrypoint importability defect.
- Severity: Blocker.
- Severity justification: This is the exact HITL-required local workflow and documented command path. QA cannot approve the simplified CLI correction while `rk` fails before dispatch, even though module-level fallback commands work.
- Reproducibility: Always reproducible in the QA report for the installed `rk` path; module path separately passes.

## 7. Root Cause Analysis

### Most Likely Root Cause

The installed console script is being generated correctly, but the editable install does not reliably make the repository's `reliabilitykit` package importable in the console-script execution context. The immediate failure is not in `audit run` or `generate-report`; it is package discovery/import setup for the installed entry point.

### Immediate failure point

- `.venv/bin/rk:4`: `from reliabilitykit.cli.main import app` raises `ModuleNotFoundError`.

### Supporting evidence

- The generated script directly imports `reliabilitykit.cli.main` at line 4.
- QA reports all installed `rk` invocations fail at that same import line.
- `python -m reliabilitykit.cli.main ...` works from the repository, proving the CLI/audit code can execute when the package is on `sys.path`.
- `pyproject.toml` declares the scripts but relies on editable package discovery/import path setup for a flat-layout package.

### Plausible contributing factors

- Automated tests import the package from the repository working directory, so they can pass even when the installed console script cannot import outside that implicit working-directory path.
- The implementation report contains both a prior import failure and a later pass for the same general console-script workflow, which suggests the validation may be sensitive to install state, current working directory, stale editable metadata, or environment path setup.

## 8. Confidence Level

Medium-high.

The failure point and affected packaging files are directly evidenced. Full confirmation of the exact packaging metadata defect requires a developer reproduction that inspects the post-install `site-packages` editable metadata and verifies importability from outside the repository working directory.

## 9. Recommended Fix

- Likely owner: backend / Python packaging owner.
- Likely files/modules:
  - `pyproject.toml`
  - `reliabilitykit/cli/main.py` only if a wrapper function is needed for entry-point robustness
  - QA/unit packaging smoke coverage under tests or validation scripts
- Expected correction:
  1. Reproduce from a clean venv and from a directory outside the repository: install with `uv pip install -e <repo>`, then run `<repo>/.venv/bin/rk --help` and verify `<repo>/.venv/bin/python -c "import reliabilitykit"` without relying on repository CWD.
  2. Fix package discovery/editable install metadata so the `reliabilitykit` package is importable by installed console scripts. Inspect/adjust `pyproject.toml` setuptools configuration rather than changing audit command behavior.
  3. Preserve both console scripts: `reliabilitykit` and `rk`.
  4. If changing the entry-point target, keep behavior equivalent and ensure it still loads the Typer app; do not mask import failures with path hacks in the generated script.
- Cautions/constraints:
  - Do not treat this as an audit-command implementation issue; `audit run` and `generate-report` already work via module invocation in QA evidence.
  - Avoid relying on the current working directory as the import mechanism. The installed executable must work as an installed CLI.

## 10. Suggested Validation Steps

- Clean environment validation:
  - remove/recreate `.venv` or use a fresh temp venv;
  - `uv pip install -e .`;
  - from a temp directory outside the repo, run `.venv/bin/python -c "import reliabilitykit; import reliabilitykit.cli.main"`;
  - from a temp directory outside the repo, run `.venv/bin/rk --help` and `.venv/bin/rk audit --help`.
- Required HITL workflow validation:
  - `.venv/bin/rk audit run --config examples/api_reliability_audit/audit.local.yml --storage-root <tmp>` prints `audit_id` and `result_json` and writes the result.
  - `.venv/bin/rk audit generate-report --id local-api-reliability-audit --storage-root <tmp>` prints `html_report` and `sanitized_csv` and writes both artifacts.
  - `.venv/bin/rk audit run` reports Typer's missing `--config` error instead of a traceback.
- Regression coverage:
  - Add a smoke test or QA check that validates the installed console script after editable install, preferably from outside the repository CWD.
  - Re-run focused CLI/audit tests and the full pytest suite after the packaging fix.

## 11. Open Questions / Missing Evidence

- Exact post-install editable metadata from the QA run was not provided beyond the generated script traceback and install success output.
- It is not yet proven whether the defect is caused by stale venv metadata, current-working-directory assumptions in validation, or the specific setuptools flat-layout configuration. Developer reproduction from a clean venv should settle this.

## 12. Final Investigator Decision

Ready for developer fix.

The blocker is sufficiently isolated to Python packaging/importability for the installed `rk` entry point. Route to the backend/Python packaging developer for a scoped `pyproject.toml`/entry-point fix plus installed-CLI smoke validation.

## 13. Developer Correction Notes

- Reproduced the blocker from outside the repository CWD in the existing `.venv`.
- Confirmed that the generated editable-install shim failed before Typer dispatch because Python did not add the editable source path to `sys.path`.
- Root cause evidence: the existing macOS/Python 3.13 environment skipped `__editable__.reliabilitykit-0.1.0.pth` because the file carried the `UF_HIDDEN` file flag, leaving `reliabilitykit` undiscoverable for installed scripts outside the repository CWD.
- Correction: replaced generated console-entrypoint shims with packaged installed scripts for both `rk` and `reliabilitykit`. The scripts import `reliabilitykit.cli.main:app` directly and use local editable-install `direct_url.json` metadata as a fallback only when the normal import path is unavailable.
- Validation after correction: `uv pip install -e .`, then from outside the repository CWD both `.venv/bin/rk --help` and `.venv/bin/reliabilitykit --help` passed and listed the `audit` command group.
