from __future__ import annotations

from collections import Counter

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


def build_run_insights(run: RunRecord, metrics: dict) -> dict:
    total = metrics.get("total_tests", 0)
    failed = metrics.get("totals", {}).get("failed", 0)
    pass_rate = metrics.get("pass_rate", 0.0)
    chaos_events = metrics.get("chaos_events", 0)

    score = max(0.0, min(100.0, pass_rate - min(25.0, failed * 3.0) - min(15.0, chaos_events * 0.5)))
    top_failure = _top_failure_type(run)

    findings: list[str] = []
    recommendations: list[str] = []

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
        findings.append(f"Most frequent failure classification: {top_failure}.")

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

    return {
        "reliability_score": round(score, 2),
        "risk_level": _risk_level(score),
        "findings": findings[:5],
        "recommendations": recommendations[:5],
    }
