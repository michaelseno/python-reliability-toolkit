from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from typer.testing import CliRunner

from reliabilitykit.core.audit import AuditConfig, AuditEndpoint, AuditResult, EndpointAuditResult
from reliabilitykit.cli.main import app
from reliabilitykit.storage.local import LocalStorageBackend


runner = CliRunner()


def _config_with_chaos(path: Path) -> None:
    path.write_text(
        """
project:
  name: reliability-toolkit
chaos:
  profiles:
    latency_light:
      mode: latency
      intent_class: resilience
      probability: 0.3
      seed: 21
      latency_ms:
        min: 200
        max: 500
      targets:
        - host: api.example.com
          url_pattern: /products
          methods: [GET]
          resource_types: [xhr, fetch]
    checkout_fault:
      mode: mixed
      intent_class: fault
      probability: 0.4
      seed: 7
      status_codes: [500, 503]
      targets:
        - host: api.example.com
          url_pattern: /users
          methods: [GET, POST]
          resource_types: [xhr, fetch]
""".strip(),
        encoding="utf-8",
    )


def _audit_config(path: Path, audit_id: str = "audit-cli") -> None:
    path.write_text(
        f"""
audit_id: {audit_id}
client_name: CLI Client
client_email: cli@example.test
environment: staging
endpoints:
  - endpoint_id: health
    method: GET
    path: /health
    base_url: https://api.example.test
    expected_latency_ms: 250
""".strip(),
        encoding="utf-8",
    )


def _audit_result(audit_id: str, cycle_id: str, available: bool = True) -> AuditResult:
    now = datetime(2026, 5, 6, tzinfo=UTC)
    return AuditResult(
        audit_id=audit_id,
        check_cycle_id=cycle_id,
        started_at=now,
        ended_at=now,
        retention_expires_at=now + timedelta(days=90),
        endpoint_results=[
            EndpointAuditResult(
                audit_id=audit_id,
                check_cycle_id=cycle_id,
                endpoint_id="health",
                method="GET",
                path="/health",
                timestamp=now,
                status_code=200 if available else 500,
                available=available,
                latency_ms=100,
                expected_latency_ms=250,
            )
        ],
    )


def test_chaos_list_shows_profiles(tmp_path: Path) -> None:
    config_path = tmp_path / "reliabilitykit.yaml"
    _config_with_chaos(config_path)

    result = runner.invoke(app, ["chaos", "list", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "latency_light" in result.output
    assert "checkout_fault" in result.output
    assert "fault_injection=resilience" in result.output
    assert "mode=latency" in result.output


def test_run_rejects_unknown_chaos_profile(tmp_path: Path) -> None:
    config_path = tmp_path / "reliabilitykit.yaml"
    _config_with_chaos(config_path)

    result = runner.invoke(
        app,
        ["run", "--config", str(config_path), "--chaos", "missing_profile", "--", "tests/unit/test_classifier.py"],
    )

    assert result.exit_code != 0
    assert "Unknown chaos profile 'missing_profile'" in result.output
    assert "latency_light" in result.output


def test_chaos_show_outputs_profile_details(tmp_path: Path) -> None:
    config_path = tmp_path / "reliabilitykit.yaml"
    _config_with_chaos(config_path)

    result = runner.invoke(app, ["chaos", "show", "latency_light", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "latency_light fault_injection=resilience mode=latency" in result.output
    assert "targets:" in result.output
    assert "pattern=/products" in result.output


def test_chaos_show_rejects_unknown_profile(tmp_path: Path) -> None:
    config_path = tmp_path / "reliabilitykit.yaml"
    _config_with_chaos(config_path)

    result = runner.invoke(app, ["chaos", "show", "unknown_profile", "--config", str(config_path)])

    assert result.exit_code != 0
    assert "Unknown chaos profile 'unknown_profile'" in result.output
    assert "checkout_fault" in result.output


def test_audit_run_requires_config() -> None:
    result = runner.invoke(app, ["audit", "run"])

    assert result.exit_code != 0
    assert "Missing option" in result.output
    assert "--config" in result.output


def test_audit_run_writes_result_and_snapshot(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class Response:
        status = 200

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self, _: int = -1) -> bytes:
            return b""

    monkeypatch.setattr("reliabilitykit.core.audit.urlopen", lambda *args, **kwargs: Response())
    config_path = tmp_path / "audit.yml"
    storage_root = tmp_path / ".reliabilitykit"
    _audit_config(config_path)

    result = runner.invoke(app, ["audit", "run", "--config", str(config_path), "--storage-root", str(storage_root)])

    assert result.exit_code == 0
    assert "audit_id: audit-cli" in result.output
    assert "result_json:" in result.output
    result_files = list((storage_root / "audits" / "audit-cli" / "results").glob("*.json"))
    assert len(result_files) == 1
    assert (storage_root / "audits" / "audit-cli" / "audit_config_snapshot.json").exists()


def test_audit_generate_report_uses_latest_result_and_output_paths(tmp_path: Path) -> None:
    storage_root = tmp_path / ".reliabilitykit"
    storage = LocalStorageBackend(storage_root)
    audit_id = "audit-cli"
    storage.write_audit_config_snapshot(
        AuditConfig(
            audit_id=audit_id,
            client_name="Snapshot Client",
            client_email="snapshot@example.test",
            environment="staging",
            endpoints=[AuditEndpoint(endpoint_id="health", method="GET", path="/health", base_url="https://api.example.test")],
        )
    )
    old_path = storage.write_audit_result(_audit_result(audit_id, "cycle-old", available=False))
    new_path = storage.write_audit_result(_audit_result(audit_id, "cycle-new", available=True))
    old_time = datetime(2026, 5, 6, 1, tzinfo=UTC).timestamp()
    new_time = datetime(2026, 5, 6, 2, tzinfo=UTC).timestamp()
    os.utime(old_path, (old_time, old_time))
    os.utime(new_path, (new_time, new_time))

    result = runner.invoke(app, ["audit", "generate-report", "--id", audit_id, "--storage-root", str(storage_root)])

    assert result.exit_code == 0
    html_path = storage_root / "audits" / "reports" / audit_id / "audit_report.html"
    csv_path = storage_root / "audits" / "reports" / audit_id / "audit_sanitized.csv"
    assert f"html_report: {html_path}" in result.output
    assert f"sanitized_csv: {csv_path}" in result.output
    assert "cycle-new" in csv_path.read_text(encoding="utf-8")
    assert "cycle-old" not in csv_path.read_text(encoding="utf-8")
    assert "Snapshot Client" in html_path.read_text(encoding="utf-8")


def test_audit_help_does_not_expose_sample_report_command() -> None:
    result = runner.invoke(app, ["audit", "--help"])

    assert result.exit_code == 0
    assert "sample-report" not in result.output
    assert "generate-report" in result.output
