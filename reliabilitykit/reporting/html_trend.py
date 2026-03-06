from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Template

from reliabilitykit.core.models import RunRecord
from reliabilitykit.reporting.metrics import build_trend_metrics


TREND_TEMPLATE = Template(
    """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>ReliabilityKit Trends</title>
    <style>
      :root {
        --bg: #f6f8fb;
        --card: #ffffff;
        --text: #1f2937;
        --muted: #64748b;
        --border: #e5e7eb;
        --ok: #166534;
        --bad: #991b1b;
      }
      body { margin: 0; background: var(--bg); color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }
      .container { max-width: 1200px; margin: 24px auto; padding: 0 16px; }
      .grid { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 12px; }
      .card, .section { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 14px; }
      .label { margin: 0; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
      .value { margin: 6px 0 0 0; font-size: 22px; font-weight: 700; }
      h1, h2 { margin: 0 0 10px 0; }
      .section { margin-top: 16px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border-bottom: 1px solid var(--border); text-align: left; padding: 8px; }
      th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
      .bars { display: grid; gap: 8px; }
      .bar-row { display: grid; grid-template-columns: 220px 1fr 52px; gap: 8px; align-items: center; }
      .bar-track { background: #eef2f7; border-radius: 999px; height: 10px; overflow: hidden; }
      .bar-fill { height: 10px; background: #3b82f6; }
      .small { color: var(--muted); font-size: 12px; }
      .ok { color: var(--ok); }
      .bad { color: var(--bad); }
    </style>
  </head>
  <body>
    <div class="container">
      <section class="section">
        <h1>Reliability Trends</h1>
        <p class="small">Historical execution analytics for {{ metrics.run_count }} runs.</p>
      </section>

      <section class="grid">
        <article class="card"><p class="label">Pass Rate</p><p class="value">{{ metrics.pass_rate }}%</p></article>
        <article class="card"><p class="label">P50 Duration</p><p class="value">{{ metrics.p50_duration_ms }} ms</p></article>
        <article class="card"><p class="label">P95 Duration</p><p class="value">{{ metrics.p95_duration_ms }} ms</p></article>
        <article class="card"><p class="label">Median Duration</p><p class="value">{{ metrics.median_duration_ms }} ms</p></article>
        <article class="card"><p class="label">Runs</p><p class="value">{{ metrics.run_count }}</p></article>
      </section>

      <section class="section">
        <h2>Pass Rate by Run</h2>
        {% if metrics.series %}
        <div class="bars">
          {% for row in metrics.series %}
          <div class="bar-row">
            <div><span class="small">{{ row.run_id }}</span></div>
            <div class="bar-track"><div class="bar-fill" style="width: {{ row.pass_rate }}%"></div></div>
            <div>{{ row.pass_rate }}%</div>
          </div>
          {% endfor %}
        </div>
        {% else %}
        <p class="small">No runs available for this window.</p>
        {% endif %}
      </section>

      <section class="section">
        <h2>Failure Type Distribution</h2>
        {% if metrics.failure_distribution %}
        <table>
          <thead><tr><th>Failure Type</th><th>Count</th></tr></thead>
          <tbody>
            {% for failure_type, count in metrics.failure_distribution.items() %}
            <tr><td>{{ failure_type }}</td><td>{{ count }}</td></tr>
            {% endfor %}
          </tbody>
        </table>
        {% else %}
        <p class="small">No failed tests captured for this window.</p>
        {% endif %}
      </section>

      <section class="section">
        <h2>Chaos vs Baseline</h2>
        <table>
          <thead><tr><th>Group</th><th>Runs</th><th>Passed</th><th>Failed</th><th>Pass Rate</th></tr></thead>
          <tbody>
            <tr>
              <td>Baseline</td>
              <td>{{ metrics.chaos_summary.baseline.runs }}</td>
              <td class="ok">{{ metrics.chaos_summary.baseline.passed }}</td>
              <td class="bad">{{ metrics.chaos_summary.baseline.failed }}</td>
              <td>{{ metrics.chaos_summary.baseline.pass_rate }}%</td>
            </tr>
            <tr>
              <td>Chaos</td>
              <td>{{ metrics.chaos_summary.chaos.runs }}</td>
              <td class="ok">{{ metrics.chaos_summary.chaos.passed }}</td>
              <td class="bad">{{ metrics.chaos_summary.chaos.failed }}</td>
              <td>{{ metrics.chaos_summary.chaos.pass_rate }}%</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="section">
        <h2>Top Failing Tests</h2>
        {% if metrics.top_failing_tests %}
        <table>
          <thead><tr><th>Test</th><th>Failure Count</th></tr></thead>
          <tbody>
            {% for test_id, count in metrics.top_failing_tests %}
            <tr><td>{{ test_id }}</td><td>{{ count }}</td></tr>
            {% endfor %}
          </tbody>
        </table>
        {% else %}
        <p class="small">No failing tests for this window.</p>
        {% endif %}
      </section>

      <section class="section">
        <h2>Run History</h2>
        <table>
          <thead>
            <tr><th>Run ID</th><th>Status</th><th>Duration (ms)</th><th>Failed</th><th>Pass Rate</th><th>Chaos</th></tr>
          </thead>
          <tbody>
          {% for r in metrics.series %}
            <tr>
              <td>{{ r.run_id }}</td>
              <td>{{ r.status }}</td>
              <td>{{ r.duration_ms }}</td>
              <td>{{ r.failed }}</td>
              <td>{{ r.pass_rate }}%</td>
              <td>{{ r.chaos_profile }}</td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
      </section>
    </div>

    <script>
      window.__RK_TREND_DATA__ = {{ trend_json | safe }};
    </script>
  </body>
</html>
"""
)


def write_trend_report(runs: list[RunRecord], output_path: Path) -> None:
    metrics = build_trend_metrics(runs)
    trend_json = json.dumps(metrics)
    html = TREND_TEMPLATE.render(metrics=metrics, trend_json=trend_json)
    output_path.write_text(html, encoding="utf-8")
