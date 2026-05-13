from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import typer

from reliabilitykit.core.audit import AuditConfig, AuditEndpoint, AuditResult, execute_check_cycle, load_audit_config, load_audit_result, make_retention_record, validate_audit_config
from reliabilitykit.reporting.audit import write_audit_csv, write_audit_html_report, write_scan_results_csv
from reliabilitykit.storage.local import LocalStorageBackend
from reliabilitykit.storage.retention import process_retention_record
from reliabilitykit.storage.s3 import S3StorageBackend, build_audit_artifact_key


audit_app = typer.Typer(help="Operator-assisted API Reliability Audit MVP commands.")


def _new_cycle_id() -> str:
    return datetime.now(UTC).strftime("cycle-%Y%m%dT%H%M%S%fZ")


def _fallback_config_from_result(result: AuditResult) -> AuditConfig:
    endpoints_by_id: dict[str, AuditEndpoint] = {}
    for row in result.endpoint_results:
        endpoints_by_id.setdefault(
            row.endpoint_id,
            AuditEndpoint(
                endpoint_id=row.endpoint_id,
                method=row.method,
                path=row.path,
                base_url="https://example.invalid",
                expected_latency_ms=row.expected_latency_ms,
            ),
        )
    checks_per_day = max(1, min(24, result.expected_check_cycles // 2))
    if checks_per_day * 2 != result.expected_check_cycles:
        checks_per_day = 5
    return AuditConfig(
        audit_id=result.audit_id,
        client_name=result.audit_id,
        client_email="operator@example.invalid",
        environment="other",
        endpoints=list(endpoints_by_id.values()) or [AuditEndpoint(endpoint_id="unknown", method="GET", path="/", base_url="https://example.invalid")],
        checks_per_day=checks_per_day,
        expected_check_cycles=result.expected_check_cycles,
        check_frequency_agreement_reference="metadata-unavailable" if checks_per_day > 5 else None,
    )


@audit_app.command("validate")
def validate_config(config: str = typer.Option(..., help="Path to audit YAML config")) -> None:
    audit_config = load_audit_config(config)
    validate_audit_config(audit_config)
    typer.echo(
        f"Audit config valid: {audit_config.audit_id} endpoints={len([e for e in audit_config.endpoints if e.enabled])} "
        f"schedule={audit_config.schedule_duration_hours}h/{audit_config.checks_per_day} checks per day/{audit_config.expected_check_cycles} cycles"
    )


@audit_app.command("run")
def run_audit(
    config: str = typer.Option(..., help="Path to audit YAML config"),
    storage_root: str = typer.Option(".reliabilitykit", help="Local sanitized workspace root"),
) -> None:
    audit_config = load_audit_config(config)
    validate_audit_config(audit_config)
    result = execute_check_cycle(audit_config, _new_cycle_id())
    storage = LocalStorageBackend(Path(storage_root))
    storage.write_audit_config_snapshot(audit_config)
    output = storage.write_audit_result(result)
    typer.echo(f"audit_id: {audit_config.audit_id}")
    typer.echo(f"result_json: {output}")


@audit_app.command("check-cycle")
def check_cycle(
    config: str = typer.Option(..., help="Path to audit YAML config"),
    cycle_id: str = typer.Option(..., help="Operator cycle identifier"),
    storage_root: str = typer.Option(".reliabilitykit", help="Local sanitized workspace root"),
) -> None:
    audit_config = load_audit_config(config)
    result = execute_check_cycle(audit_config, cycle_id)
    storage = LocalStorageBackend(Path(storage_root))
    storage.write_audit_config_snapshot(audit_config)
    output = storage.write_audit_result(result)
    typer.echo(f"Sanitized audit check cycle written: {output}")


@audit_app.command("report")
def report(
    config: str = typer.Option(..., help="Path to audit YAML config"),
    result_json: str = typer.Option(..., help="Path to sanitized audit result JSON"),
    output_dir: str = typer.Option(".reliabilitykit/audits/reports", help="Output directory for report artifacts"),
) -> None:
    audit_config = load_audit_config(config)
    result = load_audit_result(result_json)
    out = Path(output_dir) / audit_config.audit_id
    csv_path = write_audit_csv(result, out / "audit_sanitized.csv")
    scan_csv_path = write_scan_results_csv(result, out / "audit_scan_results_sanitized.csv")
    html_path = write_audit_html_report(audit_config, result, out / "audit_report.html", csv_href=csv_path.name, scan_csv_href=scan_csv_path.name)
    typer.echo(f"HTML report generated: {html_path}")
    typer.echo(f"Sanitized CSV generated: {csv_path}")
    typer.echo(f"Sanitized scan-results CSV generated: {scan_csv_path}")


@audit_app.command("generate-report")
def generate_report(
    audit_id: str = typer.Option(..., "--id", help="Audit identifier to report"),
    storage_root: str = typer.Option(".reliabilitykit", help="Local sanitized workspace root"),
) -> None:
    storage = LocalStorageBackend(Path(storage_root))
    result_path = storage.latest_audit_result_path(audit_id)
    if result_path is None:
        raise typer.BadParameter(f"No audit result JSON found under {Path(storage_root) / 'audits' / audit_id / 'results'}")
    result = storage.read_audit_result(result_path)
    audit_config = storage.read_audit_config_snapshot(audit_id) or _fallback_config_from_result(result)
    out = Path(storage_root) / "audits" / "reports" / audit_id
    csv_path = write_audit_csv(result, out / "audit_sanitized.csv")
    scan_csv_path = write_scan_results_csv(result, out / "audit_scan_results_sanitized.csv")
    html_path = write_audit_html_report(audit_config, result, out / "audit_report.html", csv_href=csv_path.name, scan_csv_href=scan_csv_path.name)
    typer.echo(f"audit_id: {audit_id}")
    typer.echo(f"result_json: {result_path}")
    typer.echo(f"html_report: {html_path}")
    typer.echo(f"sanitized_csv: {csv_path}")
    typer.echo(f"sanitized_scan_results_csv: {scan_csv_path}")


@audit_app.command("deliver")
def deliver(
    config: str = typer.Option(..., help="Path to audit YAML config"),
    html_path: str = typer.Option(..., help="Local HTML report path"),
    csv_path: str = typer.Option(..., help="Local sanitized CSV path"),
    bucket: str = typer.Option(..., help="Private S3 bucket"),
    expires_seconds: int = typer.Option(604800, help="Presigned URL expiration in seconds"),
) -> None:
    audit_config = load_audit_config(config)
    s3 = S3StorageBackend(bucket)
    html_key = build_audit_artifact_key(audit_config.report_artifact_prefix, audit_config.audit_id, Path(html_path).name)
    csv_key = build_audit_artifact_key(audit_config.report_artifact_prefix, audit_config.audit_id, Path(csv_path).name)
    html_url = s3.upload_and_presign(html_path, html_key, "text/html", expires_seconds)
    csv_url = s3.upload_and_presign(csv_path, csv_key, "text/csv", expires_seconds)
    typer.echo(json.dumps({"html_presigned_url": html_url, "csv_presigned_url": csv_url}, indent=2))


@audit_app.command("retention-create")
def retention_create(
    config: str = typer.Option(..., help="Path to audit YAML config"),
    result_json: str = typer.Option(..., help="Sanitized metadata location"),
    storage_root: str = typer.Option(".reliabilitykit", help="Local sanitized workspace root"),
) -> None:
    audit_config = load_audit_config(config)
    record = make_retention_record(audit_config, result_json)
    output = LocalStorageBackend(Path(storage_root)).write_retention_record(record)
    typer.echo(f"Retention record written: {output}")


@audit_app.command("retention-process")
def retention_process(
    storage_root: str = typer.Option(".reliabilitykit", help="Local sanitized workspace root"),
    output_dir: str = typer.Option(".reliabilitykit/retention/exports", help="Retention CSV export directory"),
    override_sent: bool = typer.Option(False, help="Allow explicit resend for already sent records"),
) -> None:
    storage = LocalStorageBackend(Path(storage_root))
    processed = 0
    for record_path in storage.list_retention_records():
        record = storage.read_retention_record(record_path)
        updated = process_retention_record(record, output_dir, override_sent=override_sent)
        storage.write_retention_record(updated)
        processed += 1
        typer.echo(f"{updated.audit_id}: status={updated.delivery_status} attempts={updated.attempt_count} error={updated.last_error_category or '-'}")
    typer.echo(f"Retention records processed: {processed}")
