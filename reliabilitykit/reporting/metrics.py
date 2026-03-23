from __future__ import annotations

from collections import Counter, defaultdict
import re
from statistics import mean, median, pstdev

from reliabilitykit.core.models import RunRecord


def _round(value: float) -> float:
    return round(value, 2)


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


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


def _extract_failure_fingerprint(error_message: str | None) -> str | None:
    if not error_message:
        return None
    match = re.search(r"^Fingerprint:\s*([0-9a-f]{6,40})\s*$", error_message, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower()


def _build_failure_clusters(runs: list[RunRecord]) -> list[dict]:
    cluster_map: dict[str, dict] = {}
    for run in runs:
        for test in run.tests:
            if test.status != "failed":
                continue
            fingerprint = _extract_failure_fingerprint(test.error_message)
            if not fingerprint:
                continue

            row = cluster_map.setdefault(
                fingerprint,
                {
                    "fingerprint": fingerprint,
                    "occurrences": 0,
                    "failure_types": Counter(),
                    "tests": Counter(),
                    "runs": set(),
                },
            )
            row["occurrences"] += 1
            row["failure_types"][test.failure_type] += 1
            row["tests"][test.nodeid] += 1
            row["runs"].add(run.run_id)

    output: list[dict] = []
    for row in cluster_map.values():
        top_failure_type = row["failure_types"].most_common(1)[0][0] if row["failure_types"] else "unknown"
        output.append(
            {
                "fingerprint": row["fingerprint"],
                "occurrences": row["occurrences"],
                "failure_type": top_failure_type,
                "tests_affected": len(row["tests"]),
                "runs_affected": len(row["runs"]),
                "top_tests": [
                    {"nodeid": nodeid, "count": count}
                    for nodeid, count in row["tests"].most_common(3)
                ],
            }
        )

    output.sort(key=lambda item: (-item["occurrences"], -item["runs_affected"], item["fingerprint"]))
    return output[:10]


def _compute_test_reliability(runs: list[RunRecord]) -> list[dict]:
    by_test: dict[str, list[tuple[RunRecord, object]]] = defaultdict(list)
    for run in runs:
        for test in run.tests:
            by_test[test.nodeid].append((run, test))

    rows: list[dict] = []
    for nodeid, entries in by_test.items():
        ordered = sorted(entries, key=lambda pair: pair[0].started_at)
        non_skipped = [test for _, test in ordered if test.status in {"passed", "failed"}]
        if not non_skipped:
            continue

        executions = len(non_skipped)
        passes = sum(1 for test in non_skipped if test.status == "passed")
        fails = executions - passes
        pass_rate = passes / executions
        fail_rate = fails / executions

        statuses = [test.status for test in non_skipped]
        transitions = sum(
            1
            for idx in range(1, len(statuses))
            if statuses[idx] != statuses[idx - 1]
        )
        flake_rate = transitions / (len(statuses) - 1) if len(statuses) > 1 else 0.0

        chaos_executions = 0
        chaos_failures = 0
        baseline_executions = 0
        baseline_failures = 0
        for run, test in ordered:
            if test.status not in {"passed", "failed"}:
                continue
            if run.chaos_profile:
                chaos_executions += 1
                if test.status == "failed":
                    chaos_failures += 1
            else:
                baseline_executions += 1
                if test.status == "failed":
                    baseline_failures += 1

        chaos_fail_rate = chaos_failures / chaos_executions if chaos_executions else 0.0
        baseline_fail_rate = baseline_failures / baseline_executions if baseline_executions else 0.0
        chaos_sensitivity = _clamp(chaos_fail_rate - baseline_fail_rate, 0.0, 1.0)

        durations = [test.duration_ms for test in non_skipped]
        duration_avg = mean(durations) if durations else 0.0
        duration_cv = (pstdev(durations) / duration_avg) if len(durations) > 1 and duration_avg > 0 else 0.0
        duration_stability = 1.0 - _clamp(duration_cv, 0.0, 1.0)

        failure_types = sorted({test.failure_type for test in non_skipped if test.status == "failed"})
        failure_diversity = len(failure_types)

        reliability_score = _round(
            (
                (pass_rate * 0.70)
                + ((1 - flake_rate) * 0.15)
                + ((1 - chaos_sensitivity) * 0.10)
                + (duration_stability * 0.05)
            )
            * 100
        )

        rows.append(
            {
                "nodeid": nodeid,
                "executions": executions,
                "passes": passes,
                "fails": fails,
                "pass_rate": _round(pass_rate * 100),
                "fail_rate": _round(fail_rate * 100),
                "flake_rate": _round(flake_rate * 100),
                "chaos_fail_rate": _round(chaos_fail_rate * 100),
                "baseline_fail_rate": _round(baseline_fail_rate * 100),
                "chaos_sensitivity": _round(chaos_sensitivity * 100),
                "duration_cv": _round(duration_cv),
                "failure_diversity": failure_diversity,
                "failure_types": failure_types,
                "reliability_score": _clamp(reliability_score, 0.0, 100.0),
            }
        )

    rows.sort(key=lambda row: (row["reliability_score"], -row["executions"], row["nodeid"]))
    return rows


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
            "run_reliability_avg": 0.0,
            "p50_duration_ms": 0,
            "p95_duration_ms": 0,
            "median_duration_ms": 0,
            "failure_distribution": {},
            "top_failing_tests": [],
            "top_reliability_risks": [],
            "failure_clusters": [],
            "test_reliability": [],
            "chaos_summary": {
                "chaos": {"runs": 0, "passed": 0, "failed": 0, "pass_rate": 0.0},
                "baseline": {"runs": 0, "passed": 0, "failed": 0, "pass_rate": 0.0},
            },
            "series": [],
        }

    ordered_runs = sorted(runs, key=lambda run: run.started_at)
    run_count = len(runs)
    pass_count = sum(1 for run in ordered_runs if run.status == "passed")
    pass_rate = _round((pass_count / run_count) * 100)

    durations = [run.duration_ms for run in ordered_runs]
    p50_duration_ms = _percentile(durations, 0.50)
    p95_duration_ms = _percentile(durations, 0.95)
    median_duration_ms = int(median(durations))

    failure_distribution = Counter(
        test.failure_type
        for run in ordered_runs
        for test in run.tests
        if test.status == "failed"
    )

    failing_tests = Counter(
        test.nodeid
        for run in ordered_runs
        for test in run.tests
        if test.status == "failed"
    )
    top_failing_tests = failing_tests.most_common(10)

    test_reliability = _compute_test_reliability(ordered_runs)
    top_reliability_risks = test_reliability[:10]
    failure_clusters = _build_failure_clusters(ordered_runs)
    test_reliability_lookup = {
        row["nodeid"]: row["reliability_score"] for row in test_reliability
    }

    chaos_runs = [run for run in ordered_runs if run.chaos_profile]
    baseline_runs = [run for run in ordered_runs if not run.chaos_profile]

    def summarize(group: list[RunRecord]) -> dict:
        total = len(group)
        passed = sum(1 for run in group if run.status == "passed")
        failed = total - passed
        group_pass_rate = _round((passed / total) * 100) if total else 0.0
        return {"runs": total, "passed": passed, "failed": failed, "pass_rate": group_pass_rate}

    series = []
    failure_severity = {
        "assertion_failure": 0.35,
        "timeout_navigation": 0.7,
        "timeout_selector": 0.65,
        "network_error": 0.8,
        "http_5xx": 0.9,
        "browser_crash": 1.0,
        "environment_error": 0.95,
        "unknown": 0.6,
    }

    for run in ordered_runs:
        total = len(run.tests)
        run_pass_rate = _round((run.totals["passed"] / total) * 100) if total else 0.0

        executed_tests = [test for test in run.tests if test.status in {"passed", "failed"}]
        avg_test_reliability = (
            mean(test_reliability_lookup.get(test.nodeid, 100.0) for test in executed_tests)
            if executed_tests
            else 100.0
        )
        failed_tests = [test for test in executed_tests if test.status == "failed"]
        avg_failure_severity = (
            mean(failure_severity.get(test.failure_type, 0.6) for test in failed_tests)
            if failed_tests
            else 0.0
        )
        severity_component = (1 - avg_failure_severity) * 100
        chaos_penalty = 8.0 if run.chaos_profile and failed_tests else 0.0
        run_reliability_score = _round(
            _clamp(
                (run_pass_rate * 0.65)
                + (avg_test_reliability * 0.25)
                + (severity_component * 0.10)
                - chaos_penalty,
                0.0,
                100.0,
            )
        )

        date_path = run.started_at.strftime("%Y/%m/%d")
        series.append(
            {
                "run_id": run.run_id,
                "started_at": run.started_at.isoformat(),
                "status": run.status,
                "duration_ms": run.duration_ms,
                "failed": run.totals["failed"],
                "pass_rate": run_pass_rate,
                "run_reliability_score": run_reliability_score,
                "chaos_profile": run.chaos_profile or "none",
                "chaos_intent": run.chaos_intent or "none",
                "report_path": f"runs/{date_path}/{run.run_id}/report.html",
                "run_json_path": f"runs/{date_path}/{run.run_id}/run.json",
            }
        )

    run_reliability_avg = _round(mean(row["run_reliability_score"] for row in series)) if series else 0.0

    return {
        "run_count": run_count,
        "pass_rate": pass_rate,
        "run_reliability_avg": run_reliability_avg,
        "p50_duration_ms": p50_duration_ms,
        "p95_duration_ms": p95_duration_ms,
        "median_duration_ms": median_duration_ms,
        "failure_distribution": dict(sorted(failure_distribution.items())),
        "top_failing_tests": top_failing_tests,
        "top_reliability_risks": top_reliability_risks,
        "failure_clusters": failure_clusters,
        "test_reliability": test_reliability,
        "chaos_summary": {
            "chaos": summarize(chaos_runs),
            "baseline": summarize(baseline_runs),
        },
        "series": series,
    }
