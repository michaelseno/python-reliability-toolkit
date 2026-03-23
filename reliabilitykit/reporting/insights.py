from __future__ import annotations

from collections import Counter
import re

from reliabilitykit.core.models import RunRecord


def _risk_level(score: float) -> str:
    if score >= 85:
        return "Low"
    if score >= 65:
        return "Moderate"
    return "High"


def _top_failure_type(run: RunRecord) -> str | None:
    failures = [test.failure_type for test in run.tests if test.status == "failed"]
    if not failures:
        return None
    return Counter(failures).most_common(1)[0][0]


def _extract_scenario_id(nodeid: str, test_name: str) -> str:
    if test_name.startswith("test_"):
        return test_name.removeprefix("test_")
    if "::" in nodeid:
        candidate = nodeid.split("::")[-1]
    else:
        candidate = nodeid
    candidate = candidate.split("[")[0]
    return re.sub(r"^test_", "", candidate)


def _scenario_title(scenario_id: str) -> str:
    return scenario_id.replace("_", " ").title()


def _normalize_failure_type(raw_type: str, chaos_profile: str | None = None) -> str:
    mapping = {
        "timeout_navigation": "timeout_failure",
        "timeout_selector": "timeout_failure",
        "network_error": "intermittent_failure",
        "http_5xx": "validation_failure",
        "assertion_failure": "assertion_failure",
        "browser_crash": "unknown_failure",
        "environment_error": "unknown_failure",
        "unknown": "unknown_failure",
    }
    normalized = mapping.get(raw_type, "unknown_failure")
    if chaos_profile and normalized != "unknown_failure":
        return "chaos_triggered_failure"
    return normalized


def _scenario_insight(status: str, duration_ms: int, failure_type: str) -> str:
    if status == "passed":
        return f"Stable, avg {duration_ms} ms"
    if failure_type == "chaos_triggered_failure":
        return "Unstable under chaos conditions"
    if failure_type == "timeout_failure":
        return "Timeout sensitivity detected"
    if failure_type == "validation_failure":
        return "Validation behavior is inconsistent"
    return f"Failure observed ({failure_type})"


def build_run_insights(run: RunRecord, metrics: dict) -> dict:
    total = metrics.get("total_tests", 0)
    failed = metrics.get("totals", {}).get("failed", 0)
    pass_rate = metrics.get("pass_rate", 0.0)
    chaos_events = metrics.get("chaos_events", 0)

    score = max(0.0, min(100.0, pass_rate - min(25.0, failed * 3.0) - min(15.0, chaos_events * 0.5)))
    top_failure = _top_failure_type(run)

    findings: list[str] = []
    recommendations: list[str] = []
    scenario_breakdown: list[dict] = []

    normalized_failures = Counter(
        _normalize_failure_type(test.failure_type, run.chaos_profile)
        for test in run.tests
        if test.status == "failed"
    )

    for test in run.tests:
        scenario_id = _extract_scenario_id(test.nodeid, test.name)
        normalized_type = _normalize_failure_type(test.failure_type, run.chaos_profile if test.status == "failed" else None)
        scenario_breakdown.append(
            {
                "scenario_id": scenario_id,
                "scenario_name": _scenario_title(scenario_id),
                "status": test.status,
                "status_icon": "✅" if test.status == "passed" else "❌",
                "duration_ms": test.duration_ms,
                "failure_type": normalized_type,
                "insight": _scenario_insight(test.status, test.duration_ms, normalized_type),
            }
        )

    if failed == 0:
        findings.append("All executed scenarios passed in this run.")
    else:
        findings.append(f"{failed}/{total} scenarios failed.")

    if run.chaos_profile:
        findings.append(f"Chaos profile '{run.chaos_profile}' was active with seed {run.chaos_seed or 'default'}.")
        if chaos_events:
            findings.append(f"Observed {chaos_events} chaos events impacting request flow.")
    else:
        findings.append("Run executed under baseline conditions without chaos injection.")

    if top_failure:
        findings.append(f"Most frequent failure classification: {_normalize_failure_type(top_failure, run.chaos_profile)}.")

    scenario_status = {row["scenario_id"]: row["status"] for row in scenario_breakdown}
    if scenario_status.get("burst_stability") == "failed":
        findings.append("System becomes unstable under burst traffic.")
    if scenario_status.get("repeated_stability") == "failed":
        findings.append("Response stability degrades under repeated requests.")
    if scenario_status.get("invalid_payload_handling") == "failed" or scenario_status.get("missing_fields_validation") == "failed":
        findings.append("Payload validation handling is inconsistent.")
    if run.chaos_profile and failed > 0:
        findings.append(f"Reliability drops under chaos profile '{run.chaos_profile}'.")

    if failed > 0:
        recommendations.append("Prioritize highest-frequency failure category and retest with same seed for reproducibility.")
        recommendations.append("Review failed scenario diagnostics first (trace, event log, raw failure output).")
    else:
        recommendations.append("Maintain this baseline and schedule a paired chaos run for resilience comparison.")

    if run.chaos_profile:
        recommendations.append("Compare this run against nearest baseline run to quantify chaos impact.")
    else:
        recommendations.append("Run one chaos-enabled scan pack lane to validate resilience under fault conditions.")

    if metrics.get("avg_duration_ms", 0) > 1500:
        recommendations.append("Investigate elevated latency and optimize high-duration scenarios.")

    if normalized_failures.get("validation_failure", 0) > 0:
        recommendations.append("Add stronger input validation guards for malformed payloads.")
    if scenario_status.get("burst_stability") == "failed":
        recommendations.append("Implement rate limiting and defensive burst handling.")
    if normalized_failures.get("timeout_failure", 0) > 0:
        recommendations.append("Tune timeout thresholds and add retry with backoff for transient failures.")

    return {
        "reliability_score": int(round(score)),
        "risk_level": _risk_level(score),
        "findings": findings[:5],
        "recommendations": recommendations[:5],
        "scenario_breakdown": scenario_breakdown,
        "failure_classification_summary": [
            {"failure_type": failure_type, "count": count}
            for failure_type, count in sorted(normalized_failures.items(), key=lambda item: (-item[1], item[0]))
        ],
        "context": {
            "scan_pack": run.scan_pack or "n/a",
            "surface": run.surface,
            "chaos_profile": run.chaos_profile or "none",
            "fault_injection": run.chaos_intent or "none",
            "run_type": "chaos" if run.chaos_profile else "baseline",
            "timestamp": run.started_at.isoformat(),
        },
    }
