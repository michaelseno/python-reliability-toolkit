from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from reliabilitykit.core.models import RunRecord


TREND_TEMPLATE = Template(
    """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <title>ReliabilityKit Trends</title>
    <style>
      body { font-family: ui-sans-serif, sans-serif; margin: 24px; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
      th { background: #f5f5f5; }
    </style>
  </head>
  <body>
    <h1>Reliability Trends</h1>
    <p>Total runs: {{ runs|length }}</p>
    <p>Pass rate: {{ pass_rate }}%</p>
    <h2>Run History</h2>
    <table>
      <thead>
        <tr><th>Run ID</th><th>Status</th><th>Duration (ms)</th><th>Failed</th><th>Chaos</th></tr>
      </thead>
      <tbody>
      {% for r in runs %}
        <tr>
          <td>{{ r.run_id }}</td>
          <td>{{ r.status }}</td>
          <td>{{ r.duration_ms }}</td>
          <td>{{ r.totals.failed }}</td>
          <td>{{ r.chaos_profile or "none" }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </body>
</html>
"""
)


def write_trend_report(runs: list[RunRecord], output_path: Path) -> None:
    if not runs:
        pass_rate = 0.0
    else:
        passed = sum(1 for run in runs if run.status == "passed")
        pass_rate = round(100 * passed / len(runs), 2)
    html = TREND_TEMPLATE.render(runs=runs, pass_rate=pass_rate)
    output_path.write_text(html, encoding="utf-8")
