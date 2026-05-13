from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from reliabilitykit.core.audit import (
    AuditConfig,
    AuditEndpoint,
    AuditResult,
    EndpointAuditResult,
    PrivacyPolicy,
    RetentionRecord,
    execute_check_cycle,
    load_audit_config,
    make_retention_record,
)
from reliabilitykit.core.scan_packs import resolve_scan_pack
from reliabilitykit.reporting.audit import CSV_COLUMNS, SCAN_RESULTS_CSV_COLUMNS, write_audit_csv, write_audit_html_report, write_scan_results_csv
from reliabilitykit.storage.local import LocalStorageBackend
from reliabilitykit.storage.retention import SmtpDeliveryConfig, process_retention_record
from reliabilitykit.storage.s3 import S3StorageBackend, build_audit_artifact_key


SENTINEL_TOKEN = "qa_bearer_token_must_not_leak_12345"
SENTINEL_BODY = "qa_raw_body_must_not_persist_12345"
SENTINEL_HEADER = "qa_raw_header_must_not_persist_12345"
SENTINEL_TRACE = "qa_trace_log_must_not_persist_12345"
SENTINEL_RAW_LOG = "qa_raw_log_must_not_persist_12345"
SENTINEL_STACK_TRACE = "qa_stack_trace_must_not_persist_12345"
SENTINEL_SMTP_PASSWORD = "qa_smtp_password_must_not_leak_12345"


def endpoint(idx: int, method: str = "GET", path: str | None = None, threshold: int | None = 200) -> AuditEndpoint:
    return AuditEndpoint(
        endpoint_id=f"ep-{idx}",
        method=method,
        path=path or f"/endpoint-{idx}",
        base_url="https://api.example.test",
        expected_latency_ms=threshold,
    )


def config(**overrides: object) -> AuditConfig:
    data = {
        "audit_id": "audit-001",
        "client_name": "Acme",
        "client_email": "client@example.test",
        "environment": "staging",
        "endpoints": [endpoint(1)],
    }
    data.update(overrides)
    return AuditConfig.model_validate(data)


def result_for_report() -> AuditResult:
    now = datetime(2026, 5, 5, tzinfo=UTC)
    return AuditResult(
        audit_id="audit-001",
        check_cycle_id="cycle-1",
        started_at=now,
        ended_at=now,
        retention_expires_at=now + timedelta(days=90),
        endpoint_results=[
            EndpointAuditResult(
                audit_id="audit-001",
                check_cycle_id="cycle-1",
                endpoint_id="ep-1",
                method="GET",
                path="/health",
                timestamp=now,
                status_code=200,
                available=True,
                latency_ms=150,
                expected_latency_ms=200,
                error_summary=f"safe {SENTINEL_TOKEN} {SENTINEL_BODY} {SENTINEL_HEADER} {SENTINEL_TRACE} {SENTINEL_RAW_LOG} {SENTINEL_STACK_TRACE}",
            ),
            EndpointAuditResult(
                audit_id="audit-001",
                check_cycle_id="cycle-1",
                endpoint_id="ep-2",
                method="GET",
                path="/observed",
                timestamp=now,
                status_code=200,
                available=True,
                latency_ms=250,
                expected_latency_ms=None,
            ),
        ],
    )


def test_ac1_endpoint_cap_and_unique_method_path() -> None:
    assert len(config(endpoints=[endpoint(i) for i in range(10)]).endpoints) == 10
    assert len(config(endpoints=[endpoint(1, "GET", "/users"), endpoint(2, "POST", "/users")]).endpoints) == 2
    with pytest.raises(Exception, match="no more than 10"):
        config(endpoints=[endpoint(i) for i in range(11)])
    with pytest.raises(Exception, match="duplicate endpoint"):
        config(endpoints=[endpoint(1, "get", "/health"), endpoint(2, "GET", "/health")])


def test_ac2_ac3_production_authorization_gates() -> None:
    with pytest.raises(Exception, match="waiver"):
        config(environment="production")
    with pytest.raises(Exception, match="internal approval"):
        config(environment="production", production_waiver_reference="waiver-123")
    approved = config(
        environment="production",
        production_waiver_reference="waiver-123",
        internal_approval_reference="approval-456",
    )
    assert approved.environment == "production"


def test_ac7_raw_data_exception_requires_written_demand_and_approval() -> None:
    with pytest.raises(Exception, match="explicit client request and written approval"):
        PrivacyPolicy(store_raw_bodies=True)
    policy = PrivacyPolicy(
        store_raw_bodies=True,
        raw_data_exception_reference="approval-1",
        raw_data_written_demand_reference="demand-1",
    )
    assert policy.store_raw_bodies is True


@pytest.mark.parametrize(
    "flag",
    [
        "collect_raw_logs",
        "include_raw_logs",
        "persist_raw_logs",
        "collect_raw_responses",
        "include_raw_responses",
        "persist_raw_responses",
        "collect_stack_traces",
        "include_stack_traces",
        "persist_stack_traces",
    ],
)
def test_hitl_raw_logs_responses_and_stack_traces_fail_closed_without_request_and_approval(flag: str) -> None:
    with pytest.raises(Exception, match="explicit client request and written approval"):
        PrivacyPolicy(**{flag: True})

    approved = PrivacyPolicy(
        **{
            flag: True,
            "raw_data_exception_reference": "raw-approval-1",
            "raw_data_written_demand_reference": "client-request-1",
        }
    )
    assert getattr(approved, flag) is True


def test_ac10_resilience_burst_gate() -> None:
    with pytest.raises(Exception, match="resilience/burst"):
        config(resilience_burst_requested=True)
    approved = config(resilience_burst_requested=True, resilience_burst_approval_reference="burst-approval")
    assert approved.resilience_burst_requested is True


def test_ac11_ac12_default_schedule_and_latency_threshold_behavior() -> None:
    cfg = config(endpoints=[endpoint(1, threshold=200), endpoint(2, path="/observed", threshold=None)])
    assert cfg.schedule_duration_hours == 48
    assert cfg.checks_per_day == 5
    assert cfg.expected_check_cycles == 10
    row_pass = EndpointAuditResult(
        audit_id="a", check_cycle_id="c", endpoint_id="e", method="GET", path="/x", timestamp=datetime.now(UTC), available=True, latency_ms=200, expected_latency_ms=200
    )
    row_observed = EndpointAuditResult(
        audit_id="a", check_cycle_id="c", endpoint_id="e", method="GET", path="/x", timestamp=datetime.now(UTC), available=True, latency_ms=201, expected_latency_ms=None
    )
    assert row_pass.latency_status == "pass"
    assert row_observed.latency_status == "observed_only"


def test_hitl_checks_per_day_is_configurable_with_bounds_agreement_and_reconciled_cycles() -> None:
    min_cfg = config(checks_per_day=1, expected_check_cycles=2)
    assert min_cfg.checks_per_day == 1
    assert min_cfg.expected_check_cycles == 2

    max_cfg = config(checks_per_day=24, expected_check_cycles=48, check_frequency_agreement_reference="freq-agreement-24")
    assert max_cfg.checks_per_day == 24
    assert max_cfg.expected_check_cycles == 48

    with pytest.raises(Exception, match="between 1 and 24"):
        config(checks_per_day=0, expected_check_cycles=0)
    with pytest.raises(Exception, match="between 1 and 24"):
        config(checks_per_day=25, expected_check_cycles=50, check_frequency_agreement_reference="freq-agreement-25")
    with pytest.raises(Exception, match="agreement reference"):
        config(checks_per_day=6, expected_check_cycles=12)
    with pytest.raises(Exception, match="expected_check_cycles must be 12"):
        config(checks_per_day=6, expected_check_cycles=10, check_frequency_agreement_reference="freq-agreement-6")


def test_ac4_ac6_ac8_reports_and_csv_are_sanitized(tmp_path: Path) -> None:
    cfg = config()
    result = result_for_report()
    csv_path = write_audit_csv(result, tmp_path / "audit.csv")
    html_path = write_audit_html_report(cfg, result, tmp_path / "report.html", csv_href="audit.csv")

    with csv_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows and list(rows[0].keys()) == CSV_COLUMNS
    assert rows[0]["latency_status"] == "pass"
    assert rows[1]["latency_status"] == "observed_only"
    combined = csv_path.read_text(encoding="utf-8") + html_path.read_text(encoding="utf-8")
    for forbidden in [SENTINEL_TOKEN, SENTINEL_BODY, SENTINEL_HEADER, SENTINEL_TRACE, SENTINEL_RAW_LOG, SENTINEL_STACK_TRACE, "Authorization"]:
        assert forbidden not in combined


def test_ac6_check_cycle_does_not_persist_response_body_headers_or_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        status = 200

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self, _: int = -1) -> bytes:
            return SENTINEL_BODY.encode()

    monkeypatch.setattr("reliabilitykit.core.audit.urlopen", lambda *args, **kwargs: Response())
    audit_result = execute_check_cycle(config(), "cycle-1")
    serialized = audit_result.model_dump_json()
    assert len(audit_result.scan_results) == len(resolve_scan_pack("core_reliability_scan").scenario_ids)
    assert {row.scenario_id for row in audit_result.scan_results} == set(resolve_scan_pack("core_reliability_scan").scenario_ids)
    burst = next(row for row in audit_result.scan_results if row.scenario_id == "burst_stability")
    assert burst.status == "pass"
    assert burst.sample_count == 5
    assert "max_concurrency=3" in (burst.evidence_summary or "")
    assert SENTINEL_BODY not in serialized
    assert SENTINEL_HEADER not in serialized
    assert SENTINEL_TRACE not in serialized


def test_hitl_scan_pack_results_csv_and_report_render_scan_matrix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        status = 200

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self, _: int = -1) -> bytes:
            return SENTINEL_BODY.encode()

    monkeypatch.setattr("reliabilitykit.core.audit.urlopen", lambda *args, **kwargs: Response())
    cfg = config(endpoints=[endpoint(1, method="GET", path="/health")])
    audit_result = execute_check_cycle(cfg, "cycle-1")
    scan_csv = write_scan_results_csv(audit_result, tmp_path / "audit_scan_results_sanitized.csv")
    html_report = write_audit_html_report(cfg, audit_result, tmp_path / "audit_report.html", csv_href="audit_sanitized.csv", scan_csv_href=scan_csv.name)

    with scan_csv.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows and list(rows[0].keys()) == SCAN_RESULTS_CSV_COLUMNS
    assert len(rows) == 8
    assert any(row["scenario_id"] == "burst_stability" and row["category"] == "Bounded stability check" for row in rows)
    content = html_report.read_text(encoding="utf-8")
    assert "Executive verdict" in content
    assert "Per-endpoint scan-pack matrix" in content
    assert "Burst Stability" in content
    assert "not a load, stress, chaos, destructive, or broader resilience test" in content
    assert "max 5 total requests" in content
    for forbidden in [SENTINEL_TOKEN, SENTINEL_BODY, "Authorization", "throughput benchmarking", "autoscaling validation"]:
        assert forbidden not in content + scan_csv.read_text(encoding="utf-8")


def test_hitl_standard_scan_pack_excludes_unapproved_load_chaos_fault_scenarios() -> None:
    scenario_ids = set(resolve_scan_pack("core_reliability_scan").scenario_ids)
    assert "burst_stability" in scenario_ids
    explicitly_unapproved = {"load_test", "stress_test", "soak_test", "capacity_test", "chaos_injection", "fault_injection", "destructive_test"}
    assert scenario_ids.isdisjoint(explicitly_unapproved)


def test_ac5_private_s3_presigned_delivery_uses_private_acl(tmp_path: Path) -> None:
    class Client:
        def __init__(self) -> None:
            self.extra_args = None
            self.params = None

        def upload_file(self, filename: str, bucket: str, key: str, ExtraArgs: dict[str, str]) -> None:  # noqa: N803 boto-style arg
            self.extra_args = ExtraArgs

        def generate_presigned_url(self, operation: str, Params: dict[str, str], ExpiresIn: int) -> str:  # noqa: N803 boto-style arg
            self.params = Params
            return f"https://signed.example/{Params['Key']}?X-Amz-Signature=test"

    artifact = tmp_path / "report.html"
    artifact.write_text("sanitized", encoding="utf-8")
    client = Client()
    s3 = S3StorageBackend("private-bucket", client=client)
    key = build_audit_artifact_key("audit-prefix", "audit-001", "report.html")
    url = s3.upload_and_presign(artifact, key, "text/html", 60)
    assert client.extra_args == {"ACL": "private", "ContentType": "text/html"}
    assert "X-Amz-Signature" in url
    assert SENTINEL_TOKEN not in key
    with pytest.raises(ValueError):
        s3.upload_private_file(artifact, "https://public.example/report.html")


def test_hitl_example_audit_config_validates_and_documented_paths_match(tmp_path: Path) -> None:
    example_config = Path(__file__).parents[2] / "examples" / "api_reliability_audit" / "audit.local.yml"
    cfg = load_audit_config(example_config)
    assert cfg.audit_id == "local-api-reliability-audit"
    assert cfg.auth is not None
    assert cfg.auth.token_secret_reference == "RELIABILITYKIT_AUDIT_BEARER_TOKEN"
    assert cfg.checks_per_day == 5
    assert cfg.expected_check_cycles == 10
    assert all(endpoint.base_url.startswith("https://") for endpoint in cfg.endpoints)

    now = datetime(2026, 5, 5, tzinfo=UTC)
    result = AuditResult(
        audit_id=cfg.audit_id,
        check_cycle_id="local-001",
        started_at=now,
        ended_at=now,
        retention_expires_at=now + timedelta(days=90),
        endpoint_results=[
            EndpointAuditResult(
                audit_id=cfg.audit_id,
                check_cycle_id="local-001",
                endpoint_id=cfg.endpoints[0].endpoint_id,
                method=cfg.endpoints[0].method,
                path=cfg.endpoints[0].path,
                timestamp=now,
                status_code=200,
                available=True,
                latency_ms=100,
                expected_latency_ms=cfg.endpoints[0].expected_latency_ms,
            )
        ],
    )

    storage_root = tmp_path / ".reliabilitykit"
    result_path = LocalStorageBackend(storage_root).write_audit_result(result)
    assert result_path == storage_root / "audits" / cfg.audit_id / "results" / "local-001.json"

    report_root = storage_root / "audits" / "reports"
    report_dir = report_root / cfg.audit_id
    csv_path = write_audit_csv(result, report_dir / "audit_sanitized.csv")
    html_path = write_audit_html_report(cfg, result, report_dir / "audit_report.html", csv_href=csv_path.name)
    assert html_path == storage_root / "audits" / "reports" / cfg.audit_id / "audit_report.html"
    assert csv_path == storage_root / "audits" / "reports" / cfg.audit_id / "audit_sanitized.csv"


def smtp_env(**overrides: str) -> dict[str, str]:
    env = {
        "RELIABILITYKIT_SMTP_HOST": "smtp.example.test",
        "RELIABILITYKIT_SMTP_PORT": "587",
        "RELIABILITYKIT_SMTP_FROM_EMAIL": "reports@example.test",
        "RELIABILITYKIT_SMTP_USE_TLS": "true",
        "RELIABILITYKIT_SMTP_USE_SSL": "false",
        "RELIABILITYKIT_RETENTION_FAILURE_NOTIFY_EMAIL": "ops@example.test",
        "RELIABILITYKIT_SMTP_PASSWORD": SENTINEL_SMTP_PASSWORD,
        "RELIABILITYKIT_RETENTION_MAX_ATTACHMENT_MB": "10",
    }
    env.update(overrides)
    return env


def test_ac9_smtp_env_validation_redacts_secret() -> None:
    cfg = SmtpDeliveryConfig.from_env(smtp_env())
    assert cfg.host == "smtp.example.test"
    with pytest.raises(Exception) as excinfo:
        SmtpDeliveryConfig.from_env(smtp_env(RELIABILITYKIT_SMTP_USE_SSL="true"))
    assert SENTINEL_SMTP_PASSWORD not in str(excinfo.value)
    with pytest.raises(Exception, match="Missing SMTP"):
        SmtpDeliveryConfig.from_env({})


def test_ac9_retention_email_attachment_success_and_idempotency(tmp_path: Path) -> None:
    result_path = tmp_path / "result.json"
    result_path.write_text(result_for_report().model_dump_json(), encoding="utf-8")
    record = RetentionRecord(
        audit_id="audit-001",
        client_email="client@example.test",
        metadata_location=str(result_path),
        retention_started_at=datetime.now(UTC) - timedelta(days=91),
        retention_expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    sent_messages = []

    class SMTP:
        def __init__(self, cfg: SmtpDeliveryConfig) -> None:
            self.cfg = cfg

        def __enter__(self) -> "SMTP":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def starttls(self) -> None:
            return None

        def send_message(self, message: object) -> None:
            sent_messages.append(message)

    updated = process_retention_record(record, tmp_path / "exports", env=smtp_env(), smtp_factory=SMTP)
    assert updated.delivery_status == "sent"
    assert updated.delivery_mode == "attachment"
    assert updated.attempt_count == 1
    assert len(sent_messages) == 1
    assert SENTINEL_SMTP_PASSWORD not in str(sent_messages[0])

    rerun = process_retention_record(updated, tmp_path / "exports", env=smtp_env(), smtp_factory=SMTP)
    assert rerun.attempt_count == 1
    assert len(sent_messages) == 1


def test_ac9_retention_missing_smtp_fails_retryable_without_secret(tmp_path: Path) -> None:
    result_path = tmp_path / "result.json"
    result_path.write_text(result_for_report().model_dump_json(), encoding="utf-8")
    record = make_retention_record(config(), str(result_path), datetime.now(UTC) - timedelta(days=91))
    updated = process_retention_record(record, tmp_path / "exports", env={})
    assert updated.delivery_status == "retry_pending"
    assert updated.last_error_category == "smtp_config_missing"
    assert updated.attempt_count == 1
    assert SENTINEL_SMTP_PASSWORD not in updated.model_dump_json()
