from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Template

from reliabilitykit.core.models import RunRecord
from reliabilitykit.reporting.metrics import build_trend_metrics


DASHBOARD_TEMPLATE = Template(
    """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ReliabilityKit Dashboard</title>
    <style>
      :root {
        --bg: #f4f6fb;
        --bg-accent: #def2ff;
        --card: #ffffff;
        --line: #d9e1ef;
        --text: #10213d;
        --muted: #5a6f8d;
        --brand: #0f62fe;
        --ok: #146542;
        --bad: #9a2229;
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        color: var(--text);
        font-family: "Space Grotesk", "Avenir Next", "Segoe UI", sans-serif;
        background:
          radial-gradient(1300px 440px at 8% -8%, var(--bg-accent), transparent 48%),
          linear-gradient(180deg, #f8fbff 0%, var(--bg) 42%, var(--bg) 100%);
      }

      .container {
        max-width: 1280px;
        margin: 24px auto;
        padding: 0 16px 24px;
      }

      .hero,
      .section,
      .card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 14px;
      }

      .hero {
        padding: 18px;
        background: linear-gradient(120deg, #fff 0%, #f4f8ff 45%, #fff 100%);
      }

      .hero h1 {
        margin: 0;
        font-size: clamp(22px, 2.6vw, 34px);
      }

      .small {
        margin: 8px 0 0;
        color: var(--muted);
        font-size: 13px;
      }

      .grid {
        margin-top: 14px;
        display: grid;
        grid-template-columns: repeat(6, minmax(120px, 1fr));
        gap: 10px;
      }

      .card {
        padding: 10px 12px;
      }

      .label {
        margin: 0;
        color: var(--muted);
        font-size: 11px;
        letter-spacing: .06em;
        text-transform: uppercase;
      }

      .value {
        margin: 8px 0 0;
        font-size: 22px;
        font-weight: 700;
      }

      .section {
        margin-top: 14px;
        padding: 14px;
      }

      .section-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 10px;
      }

      h2 {
        margin: 0;
        font-size: 18px;
      }

      .pill {
        display: inline-block;
        border-radius: 999px;
        padding: 3px 10px;
        background: #dbe7ff;
        color: var(--brand);
        font-size: 11px;
        font-weight: 700;
      }

      .table-wrap {
        border: 1px solid var(--line);
        border-radius: 10px;
        overflow-x: auto;
      }

      table {
        width: 100%;
        border-collapse: collapse;
      }

      th,
      td {
        border-bottom: 1px solid var(--line);
        text-align: left;
        padding: 9px 8px;
        font-size: 13px;
      }

      th {
        color: var(--muted);
        font-size: 11px;
        letter-spacing: .06em;
        text-transform: uppercase;
      }

      .status-pass,
      .status-fail {
        display: inline-block;
        border-radius: 999px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 700;
      }

      .status-pass { background: #e7faef; color: var(--ok); }
      .status-fail { background: #ffe9ea; color: var(--bad); }

      .btn {
        border: 1px solid #b8c9e8;
        border-radius: 8px;
        background: #edf3ff;
        color: #12366f;
        font-size: 12px;
        font-weight: 700;
        padding: 4px 8px;
        cursor: pointer;
      }

      .btn:hover { background: #dfebff; }

      .split {
        display: grid;
        grid-template-columns: 1.4fr 1fr;
        gap: 10px;
      }

      .kv {
        margin: 8px 0 0;
        display: grid;
        grid-template-columns: repeat(3, minmax(120px, 1fr));
        gap: 8px;
      }

      .kv .card { padding: 10px; }

      .list {
        margin: 8px 0 0;
        padding-left: 18px;
      }

      .muted { color: var(--muted); }
      .ok { color: var(--ok); }
      .bad { color: var(--bad); }

      pre {
        margin: 8px 0 0;
        max-height: 200px;
        overflow: auto;
        border-radius: 8px;
        padding: 10px;
        background: #122137;
        color: #e7eefc;
        font-size: 12px;
        font-family: "JetBrains Mono", "SF Mono", "Menlo", monospace;
      }

      .warn {
        margin-top: 8px;
        color: #8a5b12;
        background: #fff3dc;
        border: 1px solid #f1d9ab;
        border-radius: 8px;
        padding: 8px;
        font-size: 12px;
      }

      @media (max-width: 1040px) {
        .grid { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
        .split { grid-template-columns: 1fr; }
      }

      @media (max-width: 680px) {
        .grid { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
        .kv { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      }

      @media (max-width: 520px) {
        .grid,
        .kv { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <section class="hero">
        <h1>Reliability Dashboard</h1>
        <p class="small">Unified latest-run triage + historical reliability context for {{ metrics.run_count }} runs.</p>
      </section>

      <section class="grid">
        <article class="card"><p class="label">Window Pass Rate</p><p class="value">{{ metrics.pass_rate }}%</p></article>
        <article class="card"><p class="label">Window Reliability</p><p class="value">{{ metrics.run_reliability_avg }}%</p></article>
        <article class="card"><p class="label">Runs</p><p class="value">{{ metrics.run_count }}</p></article>
        <article class="card"><p class="label">P50 Duration</p><p class="value">{{ metrics.p50_duration_ms }} ms</p></article>
        <article class="card"><p class="label">P95 Duration</p><p class="value">{{ metrics.p95_duration_ms }} ms</p></article>
        <article class="card"><p class="label">Chaos Pass Rate</p><p class="value">{{ metrics.chaos_summary.chaos.pass_rate }}%</p></article>
        <article class="card"><p class="label">Baseline Pass Rate</p><p class="value">{{ metrics.chaos_summary.baseline.pass_rate }}%</p></article>
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Selected Run</h2>
          <span class="pill">Load any run below</span>
        </div>
        <p class="small" id="selected-meta">No run selected.</p>
        <div class="kv">
          <article class="card"><p class="label">Status</p><p class="value" id="selected-status">-</p></article>
          <article class="card"><p class="label">Pass Rate</p><p class="value" id="selected-pass-rate">-</p></article>
          <article class="card"><p class="label">Reliability</p><p class="value" id="selected-reliability">-</p></article>
          <article class="card"><p class="label">Duration</p><p class="value" id="selected-duration">-</p></article>
          <article class="card"><p class="label">Total Tests</p><p class="value" id="selected-total">-</p></article>
          <article class="card"><p class="label">Failed</p><p class="value" id="selected-failed">-</p></article>
          <article class="card"><p class="label">Chaos Profile</p><p class="value" id="selected-chaos">-</p></article>
        </div>
        <div id="fetch-warn"></div>
        <div class="split">
          <article class="card">
            <p class="label">Failure Type Distribution</p>
            <ul class="list" id="selected-failure-types"><li class="muted">none</li></ul>
          </article>
          <article class="card">
            <p class="label">Failed Tests</p>
            <ul class="list" id="selected-failed-tests"><li class="muted">none</li></ul>
          </article>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Least Reliable Tests (Window)</h2>
          <span class="pill">Reliability Engine</span>
        </div>
        {% if metrics.top_reliability_risks %}
        <div class="table-wrap">
          <table>
            <thead><tr><th>Test</th><th>Reliability</th><th>Pass Rate</th><th>Flake Rate</th><th>Chaos Sensitivity</th><th>Failure Diversity</th></tr></thead>
            <tbody>
            {% for row in metrics.top_reliability_risks %}
              <tr>
                <td>{{ row.nodeid }}</td>
                <td>{{ row.reliability_score }}%</td>
                <td>{{ row.pass_rate }}%</td>
                <td>{{ row.flake_rate }}%</td>
                <td>{{ row.chaos_sensitivity }}%</td>
                <td>{{ row.failure_diversity }}</td>
              </tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
        {% else %}
        <p class="small">No reliability risk data for this window.</p>
        {% endif %}
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Window Failure Type Distribution</h2>
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
          <h2>Top Failing Tests (Window)</h2>
          <span class="pill">Hotspots</span>
        </div>
        {% if metrics.top_failing_tests %}
        <div class="table-wrap">
          <table>
            <thead><tr><th>Test</th><th>Failures</th></tr></thead>
            <tbody>
            {% for test_id, count in metrics.top_failing_tests %}
              <tr><td>{{ test_id }}</td><td>{{ count }}</td></tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
        {% else %}
        <p class="small">No failing tests captured for this window.</p>
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
              <tr><th>Run ID</th><th>Status</th><th>Duration (ms)</th><th>Failed</th><th>Pass Rate</th><th>Reliability</th><th>Chaos</th><th>Action</th></tr>
            </thead>
            <tbody>
            {% for r in metrics.series | reverse %}
              <tr>
                <td>{{ r.run_id }}</td>
                <td>{% if r.status == "passed" %}<span class="status-pass">passed</span>{% else %}<span class="status-fail">failed</span>{% endif %}</td>
                <td>{{ r.duration_ms }}</td>
                <td>{{ r.failed }}</td>
                <td>{{ r.pass_rate }}%</td>
                <td>{{ r.run_reliability_score }}%</td>
                <td>{{ r.chaos_profile }}</td>
                <td><button class="btn" data-run-json="{{ r.run_json_path }}">Load</button></td>
              </tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <script>
      const trendData = {{ trend_json | safe }};
      const initialRun = {{ latest_run_json | safe }};
      const runReliabilityById = new Map((trendData.series || []).map((row) => [row.run_id, row.run_reliability_score]));

      function escapeHtml(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#039;");
      }

      function summarizeRun(run) {
        const tests = Array.isArray(run.tests) ? run.tests : [];
        const total = tests.length;
        const failed = tests.filter((t) => t.status === "failed");
        const passed = tests.filter((t) => t.status === "passed").length;
        const passRate = total ? ((passed / total) * 100).toFixed(2) : "0.00";

        const distribution = {};
        for (const test of failed) {
          const key = test.failure_type || "unknown";
          distribution[key] = (distribution[key] || 0) + 1;
        }

        return { total, failed, passRate, distribution };
      }

      function renderRun(run) {
        if (!run) {
          return;
        }

        const summary = summarizeRun(run);
        document.getElementById("selected-meta").textContent = `${run.run_id} | started ${run.started_at} | ended ${run.ended_at}`;
        document.getElementById("selected-status").textContent = run.status || "-";
        document.getElementById("selected-pass-rate").textContent = `${summary.passRate}%`;
        const runReliability = runReliabilityById.get(run.run_id);
        document.getElementById("selected-reliability").textContent = runReliability !== undefined ? `${runReliability}%` : "-";
        document.getElementById("selected-duration").textContent = `${run.duration_ms || 0} ms`;
        document.getElementById("selected-total").textContent = String(summary.total);
        document.getElementById("selected-failed").textContent = String(summary.failed.length);
        document.getElementById("selected-chaos").textContent = run.chaos_profile || "none";

        const distEl = document.getElementById("selected-failure-types");
        const distEntries = Object.entries(summary.distribution).sort((a, b) => b[1] - a[1]);
        distEl.innerHTML = distEntries.length
          ? distEntries.map(([name, count]) => `<li>${escapeHtml(name)}: ${count}</li>`).join("")
          : '<li class="muted">none</li>';

        const failedEl = document.getElementById("selected-failed-tests");
        failedEl.innerHTML = summary.failed.length
          ? summary.failed.slice(0, 10).map((test) => {
              const confidence = typeof test.classification_confidence === "number"
                ? ` (confidence ${test.classification_confidence.toFixed(2)})`
                : "";
              const error = test.error_message ? `<pre>${escapeHtml(String(test.error_message).slice(0, 600))}</pre>` : "";
              return `<li><strong>${escapeHtml(test.nodeid)}</strong> - ${escapeHtml(test.failure_type || "unknown")}${confidence}${error}</li>`;
            }).join("")
          : '<li class="muted">none</li>';

        document.getElementById("fetch-warn").innerHTML = "";
      }

      async function loadRun(path) {
        try {
          const response = await fetch(path);
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
          const run = await response.json();
          renderRun(run);
        } catch (err) {
          document.getElementById("fetch-warn").innerHTML =
            '<div class="warn">Could not load run.json on demand. If opening this file directly, serve the storage root with an HTTP server (for example: <code>python -m http.server -d .reliabilitykit 8000</code>) and open <code>http://localhost:8000/dashboard.html</code>.</div>';
        }
      }

      for (const button of document.querySelectorAll("button[data-run-json]")) {
        button.addEventListener("click", () => loadRun(button.dataset.runJson));
      }

      if (initialRun) {
        renderRun(initialRun);
      }

      window.__RK_DASHBOARD_DATA__ = trendData;
    </script>
  </body>
</html>
"""
)


def write_dashboard_report(runs: list[RunRecord], output_path: Path) -> None:
    metrics = build_trend_metrics(runs)
    latest = runs[-1] if runs else None
    trend_json = json.dumps(metrics)
    latest_run_json = json.dumps(latest.model_dump(mode="json") if latest else None)
    html = DASHBOARD_TEMPLATE.render(
        metrics=metrics,
        trend_json=trend_json,
        latest_run_json=latest_run_json,
    )
    output_path.write_text(html, encoding="utf-8")
