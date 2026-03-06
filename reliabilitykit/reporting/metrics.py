from __future__ import annotations

from collections import Counter
from statistics import median

from reliabilitykit.core.models import RunRecord


def _round(value: float) -> float:
    return round(value, 2)


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * percentile
    low = int(rank)
    high = min(low + 1, len(sorted_values) - 1)
    fraction = rank - low
    return int(sorted_values[low] + (sorted_values[high] - sorted_values[low]) * fraction)


def build_run_metrics(run: RunRecord) -> dict:
    totals = run.totals
    total_tests = len(run.tests)
    pass_rate = _round((totals["passed"] / total_tests) * 100) if total_tests else 0.0
    avg_duration_ms = int(sum(t.duration_ms for t in run.tests) / total_tests) if total_tests else 0

    failure_distribution = Counter(
        test.failure_type for test in run.tests if test.status == "failed"
    )

    top_slowest = sorted(run.tests, key=lambda t: t.duration_ms, reverse=True)[:5]
    failed_tests = [test for test in run.tests if test.status == "failed"]

    total_artifacts = sum(len(test.artifacts) for test in run.tests)
    tests_with_artifacts = sum(1 for test in run.tests if test.artifacts)
    chaos_events = sum(len(test.chaos_events) for test in run.tests)

    return {
        "total_tests": total_tests,
        "pass_rate": pass_rate,
        "avg_duration_ms": avg_duration_ms,
        "failure_distribution": dict(sorted(failure_distribution.items())),
        "top_slowest": top_slowest,
        "failed_tests": failed_tests,
        "total_artifacts": total_artifacts,
        "tests_with_artifacts": tests_with_artifacts,
        "chaos_events": chaos_events,
        "totals": totals,
    }


def build_trend_metrics(runs: list[RunRecord]) -> dict:
    if not runs:
        return {
            "run_count": 0,
            "pass_rate": 0.0,
            "p50_duration_ms": 0,
            "p95_duration_ms": 0,
            "median_duration_ms": 0,
            "failure_distribution": {},
            "top_failing_tests": [],
            "chaos_summary": {
                "chaos": {"runs": 0, "passed": 0, "failed": 0, "pass_rate": 0.0},
                "baseline": {"runs": 0, "passed": 0, "failed": 0, "pass_rate": 0.0},
            },
            "series": [],
        }

    run_count = len(runs)
    pass_count = sum(1 for run in runs if run.status == "passed")
    pass_rate = _round((pass_count / run_count) * 100)

    durations = [run.duration_ms for run in runs]
    p50_duration_ms = _percentile(durations, 0.50)
    p95_duration_ms = _percentile(durations, 0.95)
    median_duration_ms = int(median(durations))

    failure_distribution = Counter(
        test.failure_type
        for run in runs
        for test in run.tests
        if test.status == "failed"
    )

    failing_tests = Counter(
        test.nodeid
        for run in runs
        for test in run.tests
        if test.status == "failed"
    )
    top_failing_tests = failing_tests.most_common(10)

    chaos_runs = [run for run in runs if run.chaos_profile]
    baseline_runs = [run for run in runs if not run.chaos_profile]

    def summarize(group: list[RunRecord]) -> dict:
        total = len(group)
        passed = sum(1 for run in group if run.status == "passed")
        failed = total - passed
        group_pass_rate = _round((passed / total) * 100) if total else 0.0
        return {"runs": total, "passed": passed, "failed": failed, "pass_rate": group_pass_rate}

    series = []
    for run in runs:
        total = len(run.tests)
        run_pass_rate = _round((run.totals["passed"] / total) * 100) if total else 0.0
        series.append(
            {
                "run_id": run.run_id,
                "started_at": run.started_at.isoformat(),
                "status": run.status,
                "duration_ms": run.duration_ms,
                "failed": run.totals["failed"],
                "pass_rate": run_pass_rate,
                "chaos_profile": run.chaos_profile or "none",
            }
        )

    return {
        "run_count": run_count,
        "pass_rate": pass_rate,
        "p50_duration_ms": p50_duration_ms,
        "p95_duration_ms": p95_duration_ms,
        "median_duration_ms": median_duration_ms,
        "failure_distribution": dict(sorted(failure_distribution.items())),
        "top_failing_tests": top_failing_tests,
        "chaos_summary": {
            "chaos": summarize(chaos_runs),
            "baseline": summarize(baseline_runs),
        },
        "series": series,
    }
