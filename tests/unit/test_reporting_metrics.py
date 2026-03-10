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
                error_message=(
                    "Headline: AssertionError: expected value\n"
                    "Phase: call\n"
                    "Location: tests/e2e/test_file.py:20\n"
                    "Fingerprint: abc123ef45"
                    if status == "failed"
                    else None
                ),
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
    assert metrics["run_reliability_avg"] > 0
    assert metrics["chaos_summary"]["chaos"]["runs"] == 2
    assert metrics["chaos_summary"]["baseline"]["runs"] == 1
    assert metrics["top_failing_tests"][0][0].endswith("test_b")
    assert metrics["series"][0]["run_reliability_score"] >= 0


def test_build_trend_metrics_test_reliability_flake_rate() -> None:
    runs = [
        _run("r1", "passed", 1000),
        _run("r2", "failed", 1000),
        _run("r3", "passed", 1000),
    ]
    metrics = build_trend_metrics(runs)
    reliability_row = next(row for row in metrics["test_reliability"] if row["nodeid"].endswith("test_b"))

    assert reliability_row["executions"] == 3
    assert reliability_row["pass_rate"] == 66.67
    assert reliability_row["flake_rate"] == 100.0
    assert reliability_row["reliability_score"] < 80.0


def test_build_trend_metrics_groups_failure_clusters() -> None:
    runs = [_run("r1", "failed", 1000), _run("r2", "failed", 1200), _run("r3", "passed", 900)]
    metrics = build_trend_metrics(runs)

    assert metrics["failure_clusters"]
    top_cluster = metrics["failure_clusters"][0]
    assert top_cluster["fingerprint"] == "abc123ef45"
    assert top_cluster["occurrences"] == 2
    assert top_cluster["runs_affected"] == 2
