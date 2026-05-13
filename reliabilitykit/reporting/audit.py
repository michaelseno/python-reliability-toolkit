from __future__ import annotations

import csv
import html
from pathlib import Path

from jinja2 import Template

from statistics import median

from reliabilitykit.core.audit import AuditConfig, AuditResult, EndpointAuditResult, EndpointScanResult, sanitize_text


CSV_COLUMNS = [
    "audit_id",
    "check_cycle_id",
    "endpoint_id",
    "method",
    "path",
    "timestamp",
    "status_code",
    "available",
    "latency_ms",
    "expected_latency_ms",
    "latency_status",
    "error_category",
    "error_summary",
]

SCAN_RESULTS_CSV_COLUMNS = [
    "audit_id",
    "check_cycle_id",
    "endpoint_id",
    "method",
    "path",
    "scan_pack_id",
    "scenario_id",
    "scenario_name",
    "category",
    "severity_if_failed",
    "status",
    "rationale",
    "evidence_summary",
    "remediation",
    "observed_at",
    "affected_cycle_ids",
    "sample_count",
    "not_run_reason",
    "not_applicable_reason",
    "raw_data_included",
]


def sanitized_row(result: EndpointAuditResult) -> dict[str, str | int | float | bool | None]:
    return {
        "audit_id": result.audit_id,
        "check_cycle_id": result.check_cycle_id,
        "endpoint_id": result.endpoint_id,
        "method": result.method,
        "path": result.path,
        "timestamp": result.timestamp.isoformat(),
        "status_code": result.status_code,
        "available": result.available,
        "latency_ms": result.latency_ms,
        "expected_latency_ms": result.expected_latency_ms,
        "latency_status": result.latency_status,
        "error_category": sanitize_text(result.error_category, max_length=64),
        "error_summary": sanitize_text(result.error_summary, max_length=180),
    }


def write_audit_csv(result: AuditResult, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for endpoint_result in result.endpoint_results:
            writer.writerow(sanitized_row(endpoint_result))
    return output


def sanitized_scan_row(result: EndpointScanResult) -> dict[str, str | int | bool | None]:
    return {
        "audit_id": result.audit_id,
        "check_cycle_id": result.check_cycle_id,
        "endpoint_id": result.endpoint_id,
        "method": result.method,
        "path": result.path,
        "scan_pack_id": result.scan_pack_id,
        "scenario_id": result.scenario_id,
        "scenario_name": result.scenario_name,
        "category": "Bounded stability check" if result.scenario_id == "burst_stability" else result.category,
        "severity_if_failed": result.severity_if_failed,
        "status": result.status,
        "rationale": sanitize_text(result.rationale, max_length=240),
        "evidence_summary": sanitize_text(result.evidence_summary, max_length=360),
        "remediation": sanitize_text(result.remediation, max_length=260),
        "observed_at": result.observed_at.isoformat() if result.observed_at else None,
        "affected_cycle_ids": ";".join(sanitize_text(cycle, max_length=80) or "" for cycle in result.affected_cycle_ids),
        "sample_count": result.sample_count,
        "not_run_reason": sanitize_text(result.not_run_reason, max_length=240),
        "not_applicable_reason": sanitize_text(result.not_applicable_reason, max_length=240),
        "raw_data_included": result.raw_data_included,
    }


def write_scan_results_csv(result: AuditResult, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCAN_RESULTS_CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for scan_result in result.scan_results:
            writer.writerow(sanitized_scan_row(scan_result))
    return output


def _status_label(status: str) -> str:
    return status.replace("_", " ").title()


def _endpoint_summary(config: AuditConfig, result: AuditResult, endpoint_id: str) -> dict[str, object]:
    endpoint = next((item for item in config.endpoints if item.endpoint_id == endpoint_id), None)
    endpoint_rows_raw = [row for row in result.endpoint_results if row.endpoint_id == endpoint_id]
    scan_rows = [row for row in result.scan_results if row.endpoint_id == endpoint_id]
    latencies = sorted(row.latency_ms for row in endpoint_rows_raw if row.latency_ms is not None)
    availability = round((sum(1 for row in endpoint_rows_raw if row.available) / len(endpoint_rows_raw)) * 100, 1) if endpoint_rows_raw else None
    failures = [row for row in scan_rows if row.status == "fail"]
    warnings = [row for row in scan_rows if row.status == "warning"]
    incomplete = [row for row in scan_rows if row.status in {"not_run", "incomplete"}]
    score = None
    verdict = "incomplete"
    if scan_rows:
        score = 100
        for row in failures:
            score -= 25 if row.severity_if_failed == "high" else 15 if row.severity_if_failed == "medium" else 5
        score -= 5 * len(warnings)
        score -= 10 * len(incomplete)
        score = max(0, score)
        verdict = "high_risk" if any(row.severity_if_failed == "high" for row in failures) or score < 70 else "needs_attention" if failures or warnings or incomplete or score < 90 else "healthy"
    return {
        "endpoint_id": endpoint_id,
        "anchor": "endpoint-" + "".join(ch if ch.isalnum() else "-" for ch in endpoint_id.lower()),
        "method": (endpoint.method if endpoint else endpoint_rows_raw[0].method if endpoint_rows_raw else "GET"),
        "path": (endpoint.path if endpoint else endpoint_rows_raw[0].path if endpoint_rows_raw else "/"),
        "availability": availability,
        "latency": {
            "min": latencies[0] if latencies else None,
            "median": round(median(latencies), 2) if latencies else None,
            "max": latencies[-1] if latencies else None,
        },
        "expected_latency_ms": endpoint.expected_latency_ms if endpoint else (endpoint_rows_raw[0].expected_latency_ms if endpoint_rows_raw else None),
        "scan_total": len(scan_rows),
        "pass": sum(1 for row in scan_rows if row.status == "pass"),
        "fail": len(failures),
        "warning": len(warnings),
        "not_run": len(incomplete),
        "not_applicable": sum(1 for row in scan_rows if row.status == "not_applicable"),
        "high_failures": sum(1 for row in failures if row.severity_if_failed == "high"),
        "score": score,
        "verdict": verdict.replace("_", " ").title(),
        "top_issue": failures[0].scenario_name if failures else warnings[0].scenario_name if warnings else incomplete[0].scenario_name if incomplete else None,
        "scan_rows": scan_rows,
        "endpoint_rows": [sanitized_row(row) for row in endpoint_rows_raw],
    }


def _build_report_view(config: AuditConfig, result: AuditResult, scan_csv_href: str | None = None) -> dict[str, object]:
    endpoint_ids = [endpoint.endpoint_id for endpoint in config.endpoints if endpoint.enabled] or sorted({row.endpoint_id for row in result.endpoint_results})
    summaries = [_endpoint_summary(config, result, endpoint_id) for endpoint_id in endpoint_ids]
    total_scan = len(result.scan_results)
    passed_scan = sum(1 for row in result.scan_results if row.status == "pass")
    failed_scan = sum(1 for row in result.scan_results if row.status == "fail")
    not_run_scan = sum(1 for row in result.scan_results if row.status in {"not_run", "incomplete"})
    high_failures = sum(1 for row in result.scan_results if row.status == "fail" and row.severity_if_failed == "high")
    availability_rows = result.endpoint_results
    availability = round((sum(1 for row in availability_rows if row.available) / len(availability_rows)) * 100, 1) if availability_rows else None
    latency_threshold_rows = [row for row in availability_rows if row.expected_latency_ms is not None and row.latency_ms is not None]
    latency_pass_rate = round((sum(1 for row in latency_threshold_rows if row.latency_status == "pass") / len(latency_threshold_rows)) * 100, 1) if latency_threshold_rows else None
    scorable = [summary["score"] for summary in summaries if summary["score"] is not None]
    overall_score = round(sum(scorable) / len(scorable)) if scorable else None
    if overall_score is None or total_scan == 0:
        verdict = "Incomplete audit data"
        rationale = "Required scan-pack rows were not available for scoring."
    elif high_failures or any(summary["verdict"] == "High Risk" for summary in summaries):
        verdict = "High-risk reliability concerns"
        rationale = "One or more high-severity scan-pack checks failed."
    elif failed_scan or not_run_scan:
        verdict = "Needs attention"
        rationale = "Some scan-pack checks failed, were incomplete, or require review."
    else:
        verdict = "Ready with minor observations"
        rationale = "Audited endpoints completed the standard scan pack without failed required checks."
    findings = []
    for row in result.scan_results:
        if row.status in {"fail", "warning", "not_run", "incomplete"}:
            findings.append({"severity": row.severity_if_failed if row.status == "fail" else "info", "endpoint": f"{row.method} {row.path}", "test": row.scenario_name, "status": _status_label(row.status), "evidence": row.evidence_summary or row.not_run_reason or "Sanitized metadata only", "remediation": row.remediation or "Review endpoint behavior."})
    severity_rank = {"high": 0, "medium": 1, "low": 2, "info": 3}
    findings.sort(key=lambda item: severity_rank.get(str(item["severity"]), 4))
    return {
        "endpoint_summaries": summaries,
        "findings": findings,
        "total_scan": total_scan,
        "passed_scan": passed_scan,
        "failed_scan": failed_scan,
        "not_run_scan": not_run_scan,
        "high_failures": high_failures,
        "availability": availability,
        "latency_pass_rate": latency_pass_rate,
        "overall_score": overall_score,
        "verdict": verdict,
        "rationale": rationale,
        "scan_csv_href": scan_csv_href,
    }


AUDIT_REPORT_TEMPLATE = Template(
    """
<!doctype html><html lang="en"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>API Reliability Audit Report - {{ audit_id }}</title>
<style>
:root{--ink:#172033;--muted:#5d6b82;--line:#dbe4ef;--soft:#f6f8fb;--brand:#155eef;--ok:#087443;--bad:#b42318;--warn:#b54708;--info:#475467}*{box-sizing:border-box}body{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:0;background:#eef3f8;color:var(--ink);line-height:1.45}header{background:linear-gradient(135deg,#0b1220,#173b7a);color:white;padding:32px 0}.wrap{max-width:1200px;margin:0 auto;padding:0 32px}.identity{display:flex;gap:12px;flex-wrap:wrap;margin-top:14px}.pill,.badge{display:inline-flex;align-items:center;border-radius:999px;padding:4px 10px;font-weight:700;font-size:.78rem;overflow-wrap:anywhere}.pill{background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.25)}.badge{background:#eef4ff;color:#1849a9}.badge.pass{background:#ecfdf3;color:var(--ok)}.badge.fail{background:#fef3f2;color:var(--bad)}.badge.warning{background:#fffaeb;color:var(--warn)}.badge.incomplete,.badge.not_run,.badge.not_applicable{background:#f2f4f7;color:var(--info)}main{padding:24px 0 40px}section{background:white;border:1px solid var(--line);border-radius:20px;padding:22px;margin:18px 0;box-shadow:0 10px 28px rgba(16,24,40,.06)}h1{font-size:clamp(1.8rem,4vw,3rem);margin:0}h2{margin:0 0 14px;font-size:1.35rem}h3{margin:0 0 8px}.note{color:var(--muted)}.hero{display:grid;grid-template-columns:1.2fr 1.8fr;gap:16px}.verdict{border-left:6px solid var(--brand);background:#f8fbff}.score{font-size:3rem;font-weight:900;letter-spacing:-.04em}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}.card{border:1px solid var(--line);border-radius:16px;padding:14px;background:var(--soft);min-width:0}.label{color:var(--muted);font-size:.75rem;text-transform:uppercase;letter-spacing:.05em}.value{font-size:1.45rem;font-weight:850;margin-top:4px;overflow-wrap:anywhere}.endpoint-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.method{background:#e0eaff;color:#1849a9;border-radius:8px;padding:3px 7px;font-weight:850;margin-right:6px}.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:14px}table{width:100%;border-collapse:collapse;min-width:760px}th,td{text-align:left;border-bottom:1px solid var(--line);padding:11px;vertical-align:top;overflow-wrap:anywhere}th{color:var(--muted);font-size:.76rem;text-transform:uppercase;background:#f8fafc}tr:last-child td{border-bottom:0}details{border:1px solid var(--line);border-radius:14px;padding:12px;margin:10px 0;background:#fcfdff}summary{cursor:pointer;font-weight:800}.actions{padding-left:20px}.privacy{background:#f8fafc;border-style:dashed}.footer{color:var(--muted);font-size:.9rem}@media(max-width:760px){.wrap{padding:0 16px}.hero{grid-template-columns:1fr}section{padding:16px}.value{font-size:1.2rem}}
</style></head><body><header><div class="wrap"><h1>48-Hour API Reliability Audit Report</h1><div class="identity"><span class="pill">Audit ID: {{ audit_id }}</span><span class="pill">Client: {{ client_name }}</span><span class="pill">Environment: {{ environment }}</span><span class="pill">Generated: {{ generated_at }}</span><span class="pill">Sanitized metadata only</span></div></div></header>
<main class="wrap">
<section class="hero"><div class="card verdict"><div class="label">Executive verdict</div><div class="score">{{ view.overall_score if view.overall_score is not none else '—' }}</div><h2>{{ view.verdict }}</h2><p>{{ view.rationale }}</p></div><div class="grid">
<div class="card"><div class="label">Endpoints audited</div><div class="value">{{ endpoint_count }} / 10</div><p class="note">Enabled unique METHOD + PATH endpoints.</p></div>
<div class="card"><div class="label">Scan-pack tests</div><div class="value">{{ view.passed_scan }} / {{ view.total_scan }}</div><p class="note">Failures: {{ view.failed_scan }} · Not-run/incomplete: {{ view.not_run_scan }}</p></div>
<div class="card"><div class="label">Availability</div><div class="value">{{ view.availability if view.availability is not none else 'Not enough data' }}{% if view.availability is not none %}%{% endif %}</div><p class="note">Sanitized endpoint-cycle observations.</p></div>
<div class="card"><div class="label">Latency</div><div class="value">{% if view.latency_pass_rate is none %}Observed only{% else %}{{ view.latency_pass_rate }}%{% endif %}</div><p class="note">Threshold pass rate when thresholds exist.</p></div>
<div class="card"><div class="label">Completed cycles</div><div class="value">{{ completed_cycles }} / {{ expected_cycles }}</div><p class="note">Latest local result bundle.</p></div>
<div class="card"><div class="label">High-severity failures</div><div class="value">{{ view.high_failures }}</div><p class="note">Prioritize these first.</p></div>
</div></section>
<section><h2>Prioritized findings and actions</h2>{% if view.findings %}<ol class="actions">{% for f in view.findings %}<li><strong>{{ f.severity|title }} · {{ f.test }} · {{ f.status }}</strong><br><span class="note">{{ f.endpoint }} — {{ f.evidence }}</span><br>Recommended action: {{ f.remediation }}</li>{% endfor %}</ol>{% else %}<p>No failed scan-pack tests or endpoint reliability blockers were detected in the audited data.</p>{% endif %}</section>
<section><h2>Endpoint health scorecards</h2><div class="endpoint-grid">{% for ep in view.endpoint_summaries %}<article class="card"><h3><span class="method">{{ ep.method }}</span>{{ ep.path }}</h3><div class="value">{{ ep.score if ep.score is not none else '—' }} <span class="note">{{ ep.verdict }}</span></div><p>Availability: {{ ep.availability if ep.availability is not none else 'Not enough data' }}{% if ep.availability is not none %}%{% endif %}<br>Latency: {% if ep.expected_latency_ms %}threshold {{ ep.expected_latency_ms }} ms{% else %}Observed only — no client threshold provided{% endif %}<br>Scan pack: {{ ep.pass }} pass · {{ ep.fail }} fail · {{ ep.warning }} warning · {{ ep.not_run }} not-run/incomplete · {{ ep.not_applicable }} N/A</p>{% if ep.top_issue %}<p><strong>Top issue:</strong> {{ ep.top_issue }}</p>{% endif %}<p><a href="#{{ ep.anchor }}">Review endpoint details</a></p></article>{% endfor %}</div></section>
{% for ep in view.endpoint_summaries %}<section id="{{ ep.anchor }}"><h2><span class="method">{{ ep.method }}</span>{{ ep.path }}</h2><p class="note">Endpoint score {{ ep.score if ep.score is not none else '—' }} · {{ ep.verdict }} · Availability {{ ep.availability if ep.availability is not none else 'not enough data' }}{% if ep.availability is not none %}%{% endif %}</p><h3>Per-endpoint scan-pack matrix</h3><div class="table-wrap"><table><thead><tr><th>Test</th><th>Category</th><th>Status</th><th>Severity if failed</th><th>Evidence</th><th>Recommendation</th><th>Last observed / cycles</th></tr></thead><tbody>{% for row in ep.scan_rows %}<tr><td>{{ row.scenario_name }}</td><td>{% if row.scenario_id == 'burst_stability' %}Bounded stability check{% else %}{{ row.category }}{% endif %}</td><td><span class="badge {{ row.status }}">{{ row.status.replace('_',' ')|title }}</span></td><td>{{ row.severity_if_failed|title }}</td><td>{{ row.evidence_summary or row.not_run_reason or row.not_applicable_reason or 'Sanitized metadata only' }}</td><td>{{ row.remediation }}</td><td>{{ row.observed_at.isoformat() if row.observed_at else 'Not observed' }}<br>{{ row.affected_cycle_ids|join(', ') }}</td></tr>{% endfor %}</tbody></table></div><h3>Test-level detail cards</h3>{% for row in ep.scan_rows %}<details open><summary>{{ row.scenario_name }} <span class="badge {{ row.status }}">{{ row.status.replace('_',' ')|title }}</span></summary><p><strong>Scenario ID:</strong> {{ row.scenario_id }} · <strong>Scan pack:</strong> {{ row.scan_pack_name }} ({{ row.scan_pack_id }}) · <strong>Severity:</strong> {{ row.severity_if_failed|title }}</p><p><strong>Purpose:</strong> {{ row.rationale }}</p><p><strong>What was evaluated:</strong> {{ row.expected_behavior or 'Scenario applicability and sanitized endpoint behavior were evaluated.' }}</p><p><strong>Sanitized evidence:</strong> {{ row.evidence_summary or row.not_run_reason or row.not_applicable_reason or 'No raw diagnostic data included.' }}</p><p><strong>Remediation guidance:</strong> {{ row.remediation }}</p>{% if row.scenario_id == 'burst_stability' %}<p class="note"><strong>Scope note:</strong> This is a bounded stability check included in the standard audit scan pack. It is not a load, stress, chaos, destructive, or broader resilience test. Approved bounded check limits: max 5 total requests per endpoint per cycle, max concurrency 3, max duration 10 seconds, no ramp-up, no sustained/soak duration, no throughput or capacity goal, no cross-endpoint simultaneous burst by default, and no extra retries.</p>{% endif %}<p class="note">Privacy note: evidence is intentionally limited to sanitized metadata; raw logs, responses, headers, bodies, traces, stack traces, bearer tokens, and secret references are excluded by default.</p></details>{% endfor %}<h3>Latency and availability summary</h3><div class="table-wrap"><table><thead><tr><th>Cycle</th><th>Status code</th><th>Available</th><th>Latency</th><th>Latency label</th><th>Error</th></tr></thead><tbody>{% for row in ep.endpoint_rows %}<tr><td>{{ row.check_cycle_id }}</td><td>{{ row.status_code if row.status_code is not none else 'Not available' }}</td><td>{{ 'Yes' if row.available else 'No' }}</td><td>{{ row.latency_ms if row.latency_ms is not none else 'Not measured' }}{% if row.latency_ms is not none %} ms{% endif %}</td><td>{{ 'Observed only — no client threshold provided' if row.latency_status == 'observed_only' else row.latency_status|title }}</td><td>{{ row.error_category or '-' }}{% if row.error_summary %}: {{ row.error_summary }}{% endif %}</td></tr>{% endfor %}</tbody></table></div></section>{% endfor %}
<section><h2>Sanitized CSV exports</h2>{% if csv_href %}<p><a class="badge" href="{{ csv_href }}">Download sanitized endpoint-cycle CSV metadata</a></p>{% endif %}{% if view.scan_csv_href %}<p><a class="badge" href="{{ view.scan_csv_href }}">Download sanitized scan-results CSV metadata</a></p>{% endif %}<p class="note">Contains approved sanitized metadata only; excludes tokens, raw responses, headers, bodies, trace logs, and stack traces.</p></section>
<section class="privacy"><h2>Methodology, scope, privacy, and delivery</h2><ul><li>Scan pack used: {{ scan_pack_name }} ({{ scan_pack_id }}) with {{ scan_pack_scenario_count }} standard scenario tests.</li><li>Audit window: 48 hours expected schedule; completed cycles shown from this local result bundle.</li><li>Burst Stability is included as one bounded standard scan-pack stability check. All other load, stress, soak, capacity, chaos, destructive, fault-injection, or broader resilience tests are excluded unless separately approved.</li><li>Bearer token values are runtime-only and not present in this report, CSV exports, logs, emails, or persisted customer artifacts.</li><li>Raw logs, raw responses, raw response bodies, raw headers, trace logs, stack traces, bearer tokens, and secret references are excluded by default.</li><li>Raw diagnostic data may be displayed or persisted only with explicit client request and written approval references.</li><li>Sanitized metadata retention is 90 days. Private delivery must use private S3 presigned URLs; public permanent URLs are prohibited.</li></ul></section>
<p class="footer">Generated as a static, offline-friendly HTML report with embedded CSS only and no external assets or scripts.</p></main></body></html>
"""
)


def write_audit_html_report(config: AuditConfig, result: AuditResult, output_path: str | Path, csv_href: str | None = None, scan_csv_href: str | None = None) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    completed_cycles = len({row.check_cycle_id for row in result.endpoint_results})
    view = _build_report_view(config, result, scan_csv_href=scan_csv_href)
    content = AUDIT_REPORT_TEMPLATE.render(
        audit_id=html.escape(result.audit_id),
        client_name=html.escape(config.client_name),
        environment=html.escape(config.environment),
        generated_at=result.generated_at.isoformat(),
        expected_cycles=result.expected_check_cycles,
        completed_cycles=completed_cycles,
        retention_expires_at=result.retention_expires_at.isoformat(),
        endpoint_count=len([endpoint for endpoint in config.endpoints if endpoint.enabled]),
        scan_pack_id=html.escape(result.scan_pack_id),
        scan_pack_name=html.escape(result.scan_pack_name),
        scan_pack_scenario_count=result.scan_pack_scenario_count,
        csv_href=csv_href,
        view=view,
    )
    output.write_text(content, encoding="utf-8")
    return output
