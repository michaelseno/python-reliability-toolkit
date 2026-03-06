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
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ReliabilityKit Trends</title>
    <style>
      :root {
        --bg: #f4f6fb;
        --bg-accent: #dff4ff;
        --card: #ffffff;
        --card-soft: #f8fbff;
        --text: #10213d;
        --muted: #5a6f8d;
        --line: #d9e1ef;
        --brand: #0f62fe;
        --brand-soft: #dbe7ff;
        --ok: #146542;
        --bad: #9a2229;
        --shadow: 0 12px 28px rgba(16, 33, 61, 0.08);
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        background:
          radial-gradient(1400px 460px at 90% -5%, var(--bg-accent), transparent 52%),
          linear-gradient(180deg, #f7fafd 0%, var(--bg) 44%, var(--bg) 100%);
        color: var(--text);
        font-family: "Space Grotesk", "Avenir Next", "Segoe UI", sans-serif;
      }

      .container {
        max-width: 1240px;
        margin: 28px auto;
        padding: 0 16px 24px;
      }

      .hero {
        background: linear-gradient(120deg, #ffffff 0%, #f4f8ff 45%, #ffffff 100%);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 20px;
        box-shadow: var(--shadow);
      }

      .hero h1 {
        margin: 0;
        font-size: clamp(22px, 2.8vw, 34px);
      }

      .small {
        color: var(--muted);
        font-size: 13px;
        margin: 8px 0 0;
      }

      .grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(120px, 1fr));
        gap: 12px;
        margin-top: 16px;
      }

      .card,
      .section {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px;
        box-shadow: 0 8px 24px rgba(16, 33, 61, 0.05);
      }

      .label {
        margin: 0;
        font-size: 11px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: .06em;
      }

      .value {
        margin: 7px 0 0;
        font-size: 24px;
        font-weight: 700;
      }

      h2 {
        margin: 0;
        font-size: 18px;
      }

      .section {
        margin-top: 16px;
      }

      .section-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 10px;
      }

      table {
        width: 100%;
        border-collapse: collapse;
      }

      th,
      td {
        border-bottom: 1px solid var(--line);
        text-align: left;
        padding: 10px 8px;
      }

      th {
        color: var(--muted);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: .06em;
      }

      .bars {
        display: grid;
        gap: 10px;
      }

      .bar-row {
        display: grid;
        grid-template-columns: minmax(170px, 260px) 1fr 62px;
        gap: 8px;
        align-items: center;
      }

      .bar-id {
        font-size: 12px;
        color: var(--muted);
        overflow-wrap: anywhere;
      }

      .bar-track {
        background: #ecf2fb;
        border-radius: 999px;
        height: 10px;
        overflow: hidden;
      }

      .bar-fill {
        height: 10px;
        background: linear-gradient(90deg, #0f62fe, #2f8fff);
      }

      .bar-rate {
        text-align: right;
        font-size: 12px;
        font-weight: 700;
      }

      .table-wrap {
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid var(--line);
      }

      .run-links a {
        color: var(--brand);
        text-decoration: none;
        font-weight: 700;
      }

      .run-links a:hover { text-decoration: underline; }

      .run-links .aux {
        margin-top: 4px;
        font-size: 11px;
        color: var(--muted);
      }

      .run-links .aux a {
        font-weight: 600;
      }

      .pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        background: var(--brand-soft);
        color: var(--brand);
        font-size: 11px;
        font-weight: 700;
      }

      .status-pass {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 999px;
        background: #e7faef;
        color: var(--ok);
        font-size: 11px;
        font-weight: 700;
      }

      .status-fail {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 999px;
        background: #ffe9ea;
        color: var(--bad);
        font-size: 11px;
        font-weight: 700;
      }

      .ok { color: var(--ok); }
      .bad { color: var(--bad); }

      @media (max-width: 980px) {
        .grid { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
      }

      @media (max-width: 720px) {
        .container { margin-top: 16px; }
        .hero { border-radius: 14px; padding: 16px; }
        .grid { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
        .bar-row { grid-template-columns: 1fr; }
        .bar-rate { text-align: left; }
      }

      @media (max-width: 520px) {
        .grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <section class="hero">
        <h1>Reliability Trends</h1>
        <p class="small">Historical execution analytics and reliability trajectory for {{ metrics.run_count }} runs.</p>
      </section>

      <section class="grid">
        <article class="card"><p class="label">Pass Rate</p><p class="value">{{ metrics.pass_rate }}%</p></article>
        <article class="card"><p class="label">P50 Duration</p><p class="value">{{ metrics.p50_duration_ms }} ms</p></article>
        <article class="card"><p class="label">P95 Duration</p><p class="value">{{ metrics.p95_duration_ms }} ms</p></article>
        <article class="card"><p class="label">Median Duration</p><p class="value">{{ metrics.median_duration_ms }} ms</p></article>
        <article class="card"><p class="label">Runs</p><p class="value">{{ metrics.run_count }}</p></article>
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Pass Rate by Run</h2>
          <span class="pill">Timeline</span>
        </div>
        {% if metrics.series %}
        <div class="bars">
          {% for row in metrics.series %}
          <div class="bar-row">
            <div><span class="bar-id">{{ row.run_id }}</span></div>
            <div class="bar-track"><div class="bar-fill" style="width: {{ row.pass_rate }}%"></div></div>
            <div class="bar-rate">{{ row.pass_rate }}%</div>
          </div>
          {% endfor %}
        </div>
        {% else %}
        <p class="small">No runs available for this window.</p>
        {% endif %}
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Failure Type Distribution</h2>
          <span class="pill">Classifier</span>
        </div>
        {% if metrics.failure_distribution %}
        <div class="table-wrap">
        <table>
          <thead><tr><th>Failure Type</th><th>Count</th></tr></thead>
          <tbody>
            {% for failure_type, count in metrics.failure_distribution.items() %}
            <tr><td>{{ failure_type }}</td><td>{{ count }}</td></tr>
            {% endfor %}
          </tbody>
        </table>
        </div>
        {% else %}
        <p class="small">No failed tests captured for this window.</p>
        {% endif %}
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Chaos vs Baseline</h2>
          <span class="pill">Experiment Lens</span>
        </div>
        <div class="table-wrap">
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
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Top Failing Tests</h2>
          <span class="pill">Hotspots</span>
        </div>
        {% if metrics.top_failing_tests %}
        <div class="table-wrap">
        <table>
          <thead><tr><th>Test</th><th>Failure Count</th></tr></thead>
          <tbody>
            {% for test_id, count in metrics.top_failing_tests %}
            <tr><td>{{ test_id }}</td><td>{{ count }}</td></tr>
            {% endfor %}
          </tbody>
        </table>
        </div>
        {% else %}
        <p class="small">No failing tests for this window.</p>
        {% endif %}
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Run History</h2>
          <span class="pill">Latest {{ metrics.run_count }}</span>
        </div>
        <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Run ID</th><th>Status</th><th>Duration (ms)</th><th>Failed</th><th>Pass Rate</th><th>Chaos</th></tr>
          </thead>
          <tbody>
          {% for r in metrics.series %}
            <tr>
              <td>
                <div class="run-links">
                  <a href="{{ r.report_path }}">{{ r.run_id }}</a>
                  <div class="aux"><a href="{{ r.run_json_path }}">run.json</a></div>
                </div>
              </td>
              <td>{% if r.status == "passed" %}<span class="status-pass">passed</span>{% else %}<span class="status-fail">failed</span>{% endif %}</td>
              <td>{{ r.duration_ms }}</td>
              <td>{{ r.failed }}</td>
              <td>{{ r.pass_rate }}%</td>
              <td>{{ r.chaos_profile }}</td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
        </div>
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
