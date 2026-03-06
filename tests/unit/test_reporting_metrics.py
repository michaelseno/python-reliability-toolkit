from __future__ import annotations

from datetime import UTC, datetime, timedelta

from reliabilitykit.core.models import RunEnvironment, RunRecord, TestRecord as RKTestRecord
from reliabilitykit.reporting.metrics import build_run_metrics, build_trend_metrics


def _run(run_id: str, status: str, duration_ms: int, chaos_profile: str | None = None) -> RunRecord:
    started = datetime(2026, 3, 3, 12, 0, 0, tzinfo=UTC)
    ended = started + timedelta(milliseconds=duration_ms)
    return RunRecord(
        run_id=run_id,
        project="reliability-toolkit",
        started_at=started,
        ended_at=ended,
        duration_ms=duration_ms,
        status=status,
        chaos_profile=chaos_profile,
        environment=RunEnvironment(os="Darwin", python_version="3.13.2"),
        tests=[
            RKTestRecord(
                nodeid="tests/e2e/test_file.py::test_a",
                name="test_a",
                status="passed",
                started_at=started,
                ended_at=started,
                duration_ms=100,
            ),
            RKTestRecord(
                nodeid="tests/e2e/test_file.py::test_b",
                name="test_b",
                status="failed" if status == "failed" else "passed",
                started_at=started,
                ended_at=ended,
                duration_ms=400,
                failure_type="assertion_failure" if status == "failed" else "unknown",
                error_message="AssertionError: expected value" if status == "failed" else None,
            ),
        ],
    )


def test_build_run_metrics_counts_and_distribution() -> None:
    run = _run("r1", "failed", 1200)
    metrics = build_run_metrics(run)
    assert metrics["total_tests"] == 2
    assert metrics["pass_rate"] == 50.0
    assert metrics["failure_distribution"] == {"assertion_failure": 1}
    assert metrics["top_slowest"][0].nodeid.endswith("test_b")


def test_build_trend_metrics_chaos_summary_and_percentiles() -> None:
    runs = [
        _run("r1", "passed", 1000),
        _run("r2", "failed", 2000, chaos_profile="checkout_fault"),
        _run("r3", "passed", 3000, chaos_profile="latency_light"),
    ]
    metrics = build_trend_metrics(runs)
    assert metrics["run_count"] == 3
    assert metrics["pass_rate"] == 66.67
    assert metrics["p50_duration_ms"] == 2000
    assert metrics["chaos_summary"]["chaos"]["runs"] == 2
    assert metrics["chaos_summary"]["baseline"]["runs"] == 1
    assert metrics["top_failing_tests"][0][0].endswith("test_b")
