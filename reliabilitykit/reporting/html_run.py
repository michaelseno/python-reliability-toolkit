from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from reliabilitykit.core.models import RunRecord


RUN_TEMPLATE = Template(
    """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <title>ReliabilityKit Run {{ run.run_id }}</title>
    <style>
      body { font-family: ui-sans-serif, sans-serif; margin: 24px; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
      th { background: #f5f5f5; }
    </style>
  </head>
  <body>
    <h1>Run {{ run.run_id }}</h1>
    <p>Status: <strong>{{ run.status }}</strong> | Duration: {{ run.duration_ms }} ms</p>
    <p>Project: {{ run.project }} | Started: {{ run.started_at }}</p>
    <h2>Totals</h2>
    <ul>
      <li>Passed: {{ totals.passed }}</li>
      <li>Failed: {{ totals.failed }}</li>
      <li>Skipped: {{ totals.skipped }}</li>
    </ul>
    <h2>Tests</h2>
    <table>
      <thead>
        <tr><th>NodeID</th><th>Status</th><th>Failure Type</th><th>Duration (ms)</th></tr>
      </thead>
      <tbody>
      {% for t in run.tests %}
        <tr>
          <td>{{ t.nodeid }}</td>
          <td>{{ t.status }}</td>
          <td>{{ t.failure_type }}</td>
          <td>{{ t.duration_ms }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </body>
</html>
"""
)


def write_run_report(run: RunRecord, output_path: Path) -> None:
    html = RUN_TEMPLATE.render(run=run, totals=run.totals)
    output_path.write_text(html, encoding="utf-8")
