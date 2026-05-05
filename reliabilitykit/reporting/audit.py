from __future__ import annotations

import csv
import html
from pathlib import Path

from jinja2 import Template

from reliabilitykit.core.audit import AuditConfig, AuditResult, EndpointAuditResult, sanitize_text


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


AUDIT_REPORT_TEMPLATE = Template(
    """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>API Reliability Audit Report - {{ audit_id }}</title>
    <style>
      body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #0b1220; color: #f8fafc; }
      main { max-width: 1180px; margin: 0 auto; padding: 28px; }
      section { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14); border-radius: 16px; padding: 18px; margin: 14px 0; }
      h1, h2 { margin-top: 0; }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
      .card { background: rgba(255,255,255,0.07); border-radius: 12px; padding: 12px; }
      .label { color: #cbd5e1; font-size: 0.78rem; text-transform: uppercase; }
      .value { font-size: 1.5rem; font-weight: 800; margin-top: 6px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { text-align: left; border-bottom: 1px solid rgba(255,255,255,0.14); padding: 10px; vertical-align: top; }
      th { color: #cbd5e1; font-size: 0.8rem; text-transform: uppercase; }
      a { color: #93c5fd; }
      .pass { color: #86efac; font-weight: 700; }
      .fail { color: #fda4af; font-weight: 700; }
      .observed { color: #facc15; font-weight: 700; }
      .note { color: #cbd5e1; }
    </style>
  </head>
  <body>
    <main>
      <h1>48-Hour API Reliability Audit Report</h1>
      <p class="note">Sanitized metadata report. Raw response bodies, raw headers, trace logs, bearer tokens, and secret references are excluded.</p>
      <section>
        <h2>Audit Summary</h2>
        <div class="grid">
          <div class="card"><div class="label">Audit ID</div><div class="value">{{ audit_id }}</div></div>
          <div class="card"><div class="label">Client</div><div class="value">{{ client_name }}</div></div>
          <div class="card"><div class="label">Environment</div><div class="value">{{ environment }}</div></div>
          <div class="card"><div class="label">Expected cycles</div><div class="value">{{ expected_cycles }}</div></div>
          <div class="card"><div class="label">Completed cycles in data</div><div class="value">{{ completed_cycles }}</div></div>
          <div class="card"><div class="label">Retention expires</div><div class="value">{{ retention_expires_at }}</div></div>
        </div>
      </section>
      <section>
        <h2>Sanitized CSV Export</h2>
        {% if csv_href %}<p><a href="{{ csv_href }}">Download sanitized CSV export</a></p>{% else %}<p class="note">CSV export generated as a separate sanitized artifact.</p>{% endif %}
      </section>
      <section>
        <h2>Endpoint Results</h2>
        <table>
          <thead><tr><th>Cycle</th><th>Endpoint</th><th>Status</th><th>Available</th><th>Latency</th><th>Latency label</th><th>Error</th></tr></thead>
          <tbody>
          {% for row in rows %}
            <tr>
              <td>{{ row.check_cycle_id }}</td>
              <td>{{ row.method }} {{ row.path }}</td>
              <td>{{ row.status_code if row.status_code is not none else "Not available" }}</td>
              <td class="{{ 'pass' if row.available else 'fail' }}">{{ 'Yes' if row.available else 'No' }}</td>
              <td>{{ row.latency_ms if row.latency_ms is not none else "Not measured" }}{% if row.latency_ms is not none %} ms{% endif %}</td>
              <td class="{{ 'observed' if row.latency_status == 'observed_only' else row.latency_status }}">
                {% if row.latency_status == 'observed_only' %}Observed only{% else %}{{ row.latency_status|capitalize }}{% endif %}
              </td>
              <td>{{ row.error_category or '-' }}{% if row.error_summary %}: {{ row.error_summary }}{% endif %}</td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
      </section>
      <section>
        <h2>Privacy and Delivery Notes</h2>
        <ul>
          <li>Bearer token values are runtime-only and not present in this report.</li>
          <li>CSV columns are limited to the approved sanitized metadata contract.</li>
          <li>Report delivery must use private S3 presigned URLs; public permanent URLs are prohibited.</li>
          <li>Sanitized metadata retention is 90 days before automated post-retention CSV email delivery.</li>
        </ul>
      </section>
    </main>
  </body>
</html>
"""
)


def write_audit_html_report(config: AuditConfig, result: AuditResult, output_path: str | Path, csv_href: str | None = None) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    completed_cycles = len({row.check_cycle_id for row in result.endpoint_results})
    rows = [sanitized_row(row) for row in result.endpoint_results]
    content = AUDIT_REPORT_TEMPLATE.render(
        audit_id=html.escape(result.audit_id),
        client_name=html.escape(config.client_name),
        environment=html.escape(config.environment),
        expected_cycles=result.expected_check_cycles,
        completed_cycles=completed_cycles,
        retention_expires_at=result.retention_expires_at.isoformat(),
        csv_href=csv_href,
        rows=rows,
    )
    output.write_text(content, encoding="utf-8")
    return output
