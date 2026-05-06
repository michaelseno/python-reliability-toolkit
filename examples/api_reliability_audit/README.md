# API Reliability Audit local workflow

This example is a copy-editable operator config for the API Reliability Audit MVP. It targets real configurable HTTP endpoints, not a mock server. The checked-in defaults use `https://httpbin.org` only so you can validate the local workflow before replacing the endpoints with approved client staging or production URLs.

## 1. Copy and edit the audit config

```bash
cp examples/api_reliability_audit/audit.local.yml /tmp/audit.local.yml
```

Edit `/tmp/audit.local.yml` before a real audit:

- Set `audit_id` to a stable operator identifier. The examples below assume `local-api-reliability-audit`.
- Replace each endpoint `base_url`, `path`, `method`, and optional `expected_latency_ms` with approved real endpoints.
- Keep no more than 10 enabled unique `METHOD + PATH` entries.
- For bearer auth, keep `auth.token_secret_reference: RELIABILITYKIT_AUDIT_BEARER_TOKEN` or change it to the env var/secret reference you will use at runtime. Do not put token values in YAML.
- If the target is production, set `environment: production` and provide `production_waiver_reference` and `internal_approval_reference` before execution.
- `checks_per_day` defaults to `5`, supports `1` through `24`, and must reconcile with `expected_check_cycles` over 48 hours. Values above `5` require `check_frequency_agreement_reference`.
- Leave raw diagnostic gates disabled by default. Any raw log/response/header/body/trace/stack-trace collection, inclusion, or persistence requires both `raw_data_written_demand_reference` and `raw_data_exception_reference`.

For a bearer-protected endpoint, set the token at runtime:

```bash
export RELIABILITYKIT_AUDIT_BEARER_TOKEN="replace-with-runtime-token"
```

For the default public `httpbin.org` dry run, you may leave the variable unset.

## 2. Run one local audit check cycle

```bash
rk audit run --config examples/api_reliability_audit/audit.local.yml
```

If you copied the config to `/tmp/audit.local.yml`, use that edited path instead. `--config` is required; the CLI does not assume a default audit config. This command validates the config, runs exactly one check cycle, snapshots sanitized audit metadata needed for later report generation, and prints the `audit_id` plus result JSON path.

The produced sanitized result JSON path is written under:

```text
.reliabilitykit/audits/<audit_id>/results/<cycle_id>.json
```

For the checked-in example audit id, the path will look like:

```text
.reliabilitykit/audits/local-api-reliability-audit/results/<cycle_id>.json
```

## 3. Generate the HTML report from the latest result

```bash
rk audit generate-report --id local-api-reliability-audit
```

The command finds the latest result JSON under:

```text
.reliabilitykit/audits/<audit_id>/results/<cycle_id>.json
```

It uses the persisted audit metadata snapshot when available and writes report artifacts under `.reliabilitykit/audits/reports/<audit_id>/`.

The generated report artifacts are:

```text
.reliabilitykit/audits/reports/local-api-reliability-audit/audit_report.html
.reliabilitykit/audits/reports/local-api-reliability-audit/audit_sanitized.csv
```

In general, report output is written to:

```text
.reliabilitykit/audits/reports/<audit_id>/audit_report.html
.reliabilitykit/audits/reports/<audit_id>/audit_sanitized.csv
```

Open the report on macOS:

```bash
open .reliabilitykit/audits/reports/local-api-reliability-audit/audit_report.html
```

No convenience/sample-report command is required or provided; the intended local workflow is `rk audit run --config ...`, then `rk audit generate-report --id ...`.
