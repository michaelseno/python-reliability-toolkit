from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from reliabilitykit.core.models import RunEnvironment, RunRecord, TestRecord as RKTestRecord
from reliabilitykit.reporting.html_dashboard import write_dashboard_report
from reliabilitykit.reporting.html_run import write_run_report
from reliabilitykit.reporting.html_trend import write_trend_report
from reliabilitykit.reporting.json_writer import write_json


def _golden_path(name: str) -> Path:
    return Path(__file__).parents[1] / "golden" / name


def _normalize_html(content: str) -> str:
    lines = []
    for raw in content.strip().splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        lines.append(line)
    return "\n".join(lines)


def _sample_run() -> RunRecord:
    started = datetime(2026, 3, 3, 12, 0, 0, tzinfo=UTC)
    ended = datetime(2026, 3, 3, 12, 0, 12, tzinfo=UTC)
    return RunRecord(
        run_id="20260303T120000Z-golden01",
        project="reliability-toolkit",
        started_at=started,
        ended_at=ended,
        duration_ms=12000,
        status="failed",
        chaos_profile="checkout_fault",
        chaos_seed=7,
        environment=RunEnvironment(
            os="Darwin 24.3.0",
            python_version="3.13.2",
            pytest_version="9.0.2",
            host="dev-machine",
        ),
        tests=[
            RKTestRecord(
                nodeid="tests/e2e/test_file.py::test_ok",
                name="test_ok",
                status="passed",
                started_at=started,
                ended_at=started,
                duration_ms=200,
            ),
            RKTestRecord(
                nodeid="tests/e2e/test_file.py::test_fail",
                name="test_fail",
                status="failed",
                started_at=started,
                ended_at=ended,
                duration_ms=500,
                error_message="AssertionError: expected value",
                failure_type="assertion_failure",
                classification_confidence=0.9,
            ),
        ],
    )


def test_json_output_matches_golden(tmp_path: Path) -> None:
    run = _sample_run()
    out = tmp_path / "run.json"
    write_json(run, out)

    actual = json.loads(out.read_text(encoding="utf-8"))
    expected = json.loads(_golden_path("run_record.json").read_text(encoding="utf-8"))
    assert actual == expected


def test_run_html_matches_golden(tmp_path: Path) -> None:
    run = _sample_run()
    out = tmp_path / "report.html"
    write_run_report(run, out)

    actual = _normalize_html(out.read_text(encoding="utf-8"))
    expected = _normalize_html(_golden_path("run_report.html").read_text(encoding="utf-8"))
    assert actual == expected


def test_trend_html_matches_golden(tmp_path: Path) -> None:
    run = _sample_run()
    out = tmp_path / "trend.html"
    write_trend_report([run], out)

    actual = _normalize_html(out.read_text(encoding="utf-8"))
    expected = _normalize_html(_golden_path("trend_report.html").read_text(encoding="utf-8"))
    assert actual == expected


def test_dashboard_html_matches_golden(tmp_path: Path) -> None:
    run = _sample_run()
    out = tmp_path / "dashboard.html"
    write_dashboard_report([run], out)

    actual = _normalize_html(out.read_text(encoding="utf-8"))
    expected = _normalize_html(_golden_path("dashboard_report.html").read_text(encoding="utf-8"))
    assert actual == expected
