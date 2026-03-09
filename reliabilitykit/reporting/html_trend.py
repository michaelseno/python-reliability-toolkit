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
        --bg: #0b1220;
        --panel: rgba(255, 255, 255, 0.06);
        --panel2: rgba(255, 255, 255, 0.08);
        --border: rgba(255, 255, 255, 0.12);
        --text: rgba(255, 255, 255, 0.92);
        --muted: rgba(255, 255, 255, 0.65);
        --green: #27c07d;
        --red: #ff4d6d;
        --blue: #5aa7ff;
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        color: var(--text);
        font-family: "Space Grotesk", "Avenir Next", "Segoe UI", sans-serif;
        background:
          radial-gradient(1200px 600px at 10% -10%, rgba(90, 167, 255, 0.25), transparent 60%),
          radial-gradient(900px 500px at 90% 0%, rgba(39, 192, 125, 0.18), transparent 55%),
          radial-gradient(900px 600px at 20% 120%, rgba(255, 77, 109, 0.16), transparent 55%),
          var(--bg);
      }

      .container {
        max-width: 1240px;
        margin: 0 auto;
        padding: 22px;
      }

      .hero {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.05));
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
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
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 14px;
      }

      .label {
        margin: 0;
        font-size: 11px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.06em;
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
        border-collapse: separate;
        border-spacing: 0;
      }

      th,
      td {
        border-bottom: 1px solid rgba(255, 255, 255, 0.10);
        text-align: left;
        padding: 10px 8px;
      }

      th {
        color: rgba(255, 255, 255, 0.72);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        position: sticky;
        top: 0;
        background: rgba(11, 18, 32, 0.92);
      }

      tbody tr:hover td { background: rgba(255, 255, 255, 0.04); }

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
        background: rgba(255, 255, 255, 0.14);
        border-radius: 999px;
        height: 10px;
        overflow: hidden;
      }

      .bar-fill {
        height: 10px;
        background: linear-gradient(90deg, var(--blue), #2f8fff);
      }

      .bar-rate {
        text-align: right;
        font-size: 12px;
        font-weight: 700;
      }

      .table-wrap {
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid var(--border);
      }

      .chart-wrap {
        border: 1px solid var(--border);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.03);
        padding: 10px;
      }

      .chart-legend {
        display: flex;
        gap: 14px;
        margin-top: 8px;
        color: var(--muted);
        font-size: 12px;
      }

      .legend-swatch {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        display: inline-block;
        margin-right: 6px;
      }

      .legend-pass { background: var(--blue); }
      .legend-rel { background: var(--green); }

      .run-links a {
        color: var(--blue);
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
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.82);
        font-size: 11px;
        font-weight: 700;
      }

      .status-pass,
      .status-fail {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 999px;
        border: 1px solid var(--border);
        font-size: 11px;
        font-weight: 700;
      }

      .status-pass { color: var(--green); }
      .status-fail { color: var(--red); }

      .ok { color: var(--green); }
      .bad { color: var(--red); }

      @media (max-width: 980px) {
        .grid { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
      }

      @media (max-width: 720px) {
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
        <div class="chart-wrap">
          <svg id="trendChart" viewBox="0 0 1000 260" width="100%" role="img" aria-label="Pass rate and reliability trend chart"></svg>
          <div class="chart-legend">
            <span><span class="legend-swatch legend-pass"></span>Pass rate</span>
            <span><span class="legend-swatch legend-rel"></span>Run reliability</span>
          </div>
        </div>
        <p class="small" style="margin-top: 8px;">Line chart view with bar breakdown below.</p>
        {% if metrics.series %}
        <div style="margin-top: 10px;"></div>
        {% endif %}
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

      (function renderTrendChart() {
        const data = window.__RK_TREND_DATA__ || {};
        const series = Array.isArray(data.series) ? data.series : [];
        const chart = document.getElementById("trendChart");
        if (!chart) return;
        if (!series.length) {
          chart.innerHTML = '<text x="20" y="30" fill="rgba(255,255,255,0.65)" font-size="14">No runs available.</text>';
          return;
        }

        const width = 1000;
        const height = 260;
        const padding = { top: 16, right: 18, bottom: 30, left: 36 };
        const innerW = width - padding.left - padding.right;
        const innerH = height - padding.top - padding.bottom;

        const toX = (index) => padding.left + (series.length === 1 ? innerW / 2 : (innerW * index) / (series.length - 1));
        const toY = (value) => padding.top + innerH - (Math.max(0, Math.min(100, value)) / 100) * innerH;

        const pathFrom = (values) => values
          .map((value, index) => `${index === 0 ? "M" : "L"}${toX(index).toFixed(2)},${toY(value).toFixed(2)}`)
          .join(" ");

        const passValues = series.map((row) => Number(row.pass_rate || 0));
        const relValues = series.map((row) => Number(row.run_reliability_score || 0));

        const horizontalGuides = [0, 25, 50, 75, 100]
          .map((value) => `<line x1="${padding.left}" y1="${toY(value)}" x2="${width - padding.right}" y2="${toY(value)}" stroke="rgba(255,255,255,0.10)" stroke-width="1" />`)
          .join("");

        const xLabels = [0, Math.max(0, Math.floor((series.length - 1) / 2)), series.length - 1]
          .filter((value, index, arr) => arr.indexOf(value) === index)
          .map((index) => `<text x="${toX(index)}" y="${height - 8}" fill="rgba(255,255,255,0.65)" font-size="11" text-anchor="middle">${series[index].run_id.slice(-8)}</text>`)
          .join("");

        chart.innerHTML = `
          ${horizontalGuides}
          <path d="${pathFrom(passValues)}" fill="none" stroke="${"#5aa7ff"}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" />
          <path d="${pathFrom(relValues)}" fill="none" stroke="${"#27c07d"}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" />
          ${passValues.map((value, index) => `<circle cx="${toX(index)}" cy="${toY(value)}" r="3" fill="#5aa7ff"></circle>`).join("")}
          ${relValues.map((value, index) => `<circle cx="${toX(index)}" cy="${toY(value)}" r="3" fill="#27c07d"></circle>`).join("")}
          ${xLabels}
        `;
      })();
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
