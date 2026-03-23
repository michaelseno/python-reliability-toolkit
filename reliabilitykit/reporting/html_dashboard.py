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
        --bg: #0b1220;
        --panel: rgba(255, 255, 255, 0.06);
        --panel2: rgba(255, 255, 255, 0.08);
        --border: rgba(255, 255, 255, 0.12);
        --text: rgba(255, 255, 255, 0.92);
        --muted: rgba(255, 255, 255, 0.65);
        --green: #27c07d;
        --red: #ff4d6d;
        --amber: #f6b73c;
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
        max-width: 1420px;
        margin: 0 auto;
        padding: 18px;
      }

      .shell {
        display: grid;
        grid-template-columns: 320px minmax(0, 1fr);
        gap: 12px;
      }

      .panel {
        border: 1px solid var(--border);
        border-radius: 14px;
        background: var(--panel);
      }

      .sidebar {
        padding: 12px;
        position: sticky;
        top: 12px;
        height: calc(100vh - 24px);
        display: flex;
        flex-direction: column;
      }

      h1 { margin: 0; font-size: 20px; }
      h2 { margin: 0; font-size: 16px; }
      .muted { color: var(--muted); }
      .small { margin: 0; font-size: 12px; color: var(--muted); }

      .small.badge {
        display: inline-block;
        padding: 4px 8px;
        border: 1px solid var(--border);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.04);
      }

      .top-head {
        margin-bottom: 10px;
      }

      .toolbar {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin: 10px 0;
      }

      .btn {
        cursor: pointer;
        border: 1px solid var(--border);
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.88);
        font-size: 11px;
        padding: 6px 8px;
      }

      .btn.active {
        background: rgba(90, 167, 255, 0.2);
        border-color: rgba(90, 167, 255, 0.35);
      }

      .search {
        width: 100%;
        padding: 8px 10px;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: rgba(0, 0, 0, 0.2);
        color: var(--text);
        outline: none;
      }

      .run-list {
        list-style: none;
        margin: 10px 0 0;
        padding: 0;
        overflow-y: auto;
        flex: 1;
      }

      .run-item {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        margin-bottom: 8px;
        padding: 8px;
        background: rgba(255, 255, 255, 0.03);
        cursor: pointer;
      }

      .run-item.active {
        border-color: rgba(90, 167, 255, 0.45);
        background: rgba(90, 167, 255, 0.15);
      }

      .run-item .id { font-size: 12px; font-weight: 700; }
      .run-item .meta { font-size: 11px; color: var(--muted); margin-top: 4px; }

      .main {
        display: grid;
        gap: 12px;
      }

      .analytics {
        padding: 12px;
      }

      .kpis {
        display: grid;
        grid-template-columns: repeat(7, minmax(120px, 1fr));
        gap: 10px;
      }

      .card {
        border: 1px solid var(--border);
        border-radius: 12px;
        background: var(--panel2);
        padding: 10px;
      }

      .summary-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(120px, 1fr));
        gap: 10px;
      }

      .summary-list {
        margin: 8px 0 0;
        padding-left: 18px;
      }

      .summary-list li { margin-bottom: 6px; }

      .label { margin: 0; color: var(--muted); font-size: 11px; text-transform: uppercase; }
      .value { margin: 6px 0 0; font-size: 24px; font-weight: 800; }

      .charts {
        margin-top: 10px;
        display: grid;
        grid-template-columns: 340px 1fr;
        gap: 10px;
      }

      .chart-box {
        border: 1px solid var(--border);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.03);
        padding: 10px;
      }

      .chart-box.span-all {
        grid-column: 1 / -1;
      }

      .legend {
        margin-top: 8px;
        font-size: 12px;
        color: var(--muted);
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
        font-size: 12px;
        vertical-align: top;
      }

      th {
        color: rgba(255, 255, 255, 0.72);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }

      .table-wrap {
        overflow-x: auto;
        border: 1px solid var(--border);
        border-radius: 12px;
      }

      .section {
        padding: 12px;
      }

      .section-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 8px;
      }

      .collapsible {
        border: 1px solid var(--border);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.02);
        padding: 8px;
      }

      .collapsible summary {
        cursor: pointer;
        font-size: 12px;
        color: var(--blue);
        font-weight: 700;
        list-style: none;
      }

      .collapsible summary::-webkit-details-marker { display: none; }

      .collapsible-body {
        margin-top: 10px;
      }

      .status {
        border-radius: 999px;
        border: 1px solid var(--border);
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 700;
      }
      .status.pass { color: var(--green); }
      .status.fail { color: var(--red); }

      .test-row { cursor: pointer; }
      .test-row:hover td { background: rgba(255, 255, 255, 0.04); }
      .detail-row { display: none; }
      .detail-row.open { display: table-row; }
      .detail-box { padding: 10px; }

      .artifact-grid {
        margin-top: 8px;
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 8px;
      }

      .artifact-grid a {
        border: 1px solid var(--border);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.04);
        display: block;
        overflow: hidden;
        color: #d9eaff;
        text-decoration: none;
      }

      .artifact-grid img {
        width: 100%;
        display: block;
      }

      pre {
        max-height: 240px;
        overflow: auto;
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 8px;
        margin: 6px 0 0;
        color: #e7eefc;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 12px;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        word-break: break-word;
      }

      @media (max-width: 1180px) {
        .shell { grid-template-columns: 1fr; }
        .sidebar { position: static; height: auto; }
        .charts { grid-template-columns: 1fr; }
      }

      @media (max-width: 760px) {
        .kpis { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
        .summary-grid { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="shell">
        <aside class="panel sidebar">
          <div class="top-head">
            <h1>Reliability Dashboard</h1>
            <p class="small">Entry point for run triage and historical reliability context.</p>
          </div>

          <div class="toolbar" id="timeframe-buttons">
            <button class="btn" data-days="7">7d</button>
            <button class="btn" data-days="14">14d</button>
            <button class="btn" data-days="30">30d</button>
            <button class="btn" data-days="90">90d</button>
            <button class="btn active" data-days="all">All</button>
          </div>

          <input id="run-search" class="search" placeholder="Search run id or fault injection" />
          <ul id="run-list" class="run-list"></ul>
          <button id="load-more" class="btn">Load more runs</button>
        </aside>

        <main class="main">
          <section class="panel analytics">
            <div class="section-head" style="margin-bottom:10px;">
              <h2>Window Analytics</h2>
              <span class="small badge" id="analytics-coverage-badge">Loaded details 0/0 runs</span>
            </div>
            <div class="kpis">
              <article class="card"><p class="label">Runs</p><p class="value" id="kpi-runs">{{ metrics.run_count }}</p></article>
              <article class="card"><p class="label">Window Pass Rate</p><p class="value" id="kpi-pass-rate">{{ metrics.pass_rate }}%</p></article>
              <article class="card"><p class="label">Window Reliability</p><p class="value" id="kpi-reliability">{{ metrics.run_reliability_avg }}%</p></article>
              <article class="card"><p class="label">Baseline Reliability</p><p class="value" id="kpi-baseline-rel">-</p></article>
              <article class="card"><p class="label">Fault-Injected Reliability</p><p class="value" id="kpi-fault-rel">-</p></article>
              <article class="card"><p class="label">Reliability Delta</p><p class="value" id="kpi-rel-delta">-</p></article>
              <article class="card"><p class="label">P95 Duration</p><p class="value" id="kpi-p95-duration">{{ metrics.p95_duration_ms }} ms</p></article>
            </div>

            <div class="charts">
              <article class="chart-box">
                <h2>Failure Type Distribution</h2>
                <svg id="failureDonut" viewBox="0 0 260 220" width="100%" role="img" aria-label="Failure type donut chart"></svg>
                <div id="failureLegend" class="legend"></div>
              </article>

              <article class="chart-box">
                <h2>Reliability Lanes</h2>
                <svg id="trendChart" viewBox="0 0 860 220" width="100%" role="img" aria-label="Pass rate and reliability over time"></svg>
                <div class="legend" id="trendLegend">Blue = pass rate, Green = baseline reliability, Red = fault-injected reliability</div>
              </article>

              <article class="chart-box span-all">
                <h2>Duration Trend</h2>
                <svg id="latencyChart" viewBox="0 0 860 220" width="100%" role="img" aria-label="Run duration over time"></svg>
                <div class="legend" id="latencyLegend">Green = baseline duration, Amber = fault-injected duration</div>
              </article>
            </div>
          </section>

          <section class="panel section">
            <div class="section-head">
              <h2>Recurring Failure Clusters</h2>
              <span class="small">Grouped by digest fingerprint</span>
            </div>
            <details class="collapsible">
              <summary>Show recurring failure clusters</summary>
              <div class="collapsible-body">
                <div class="table-wrap">
                  <table>
                    <thead><tr><th>Fingerprint</th><th>Occurrences</th><th>Runs</th><th>Type</th><th>Top Tests</th></tr></thead>
                    <tbody id="failure-cluster-body">
                      {% for row in metrics.failure_clusters %}
                        <tr>
                          <td><code>{{ row.fingerprint }}</code></td>
                          <td>{{ row.occurrences }}</td>
                          <td>{{ row.runs_affected }}</td>
                          <td>{{ row.failure_type }}</td>
                          <td>
                            {% for test in row.top_tests %}
                              <div>{{ test.nodeid }} ({{ test.count }})</div>
                            {% endfor %}
                          </td>
                        </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </div>
                <p class="small" id="failure-cluster-empty" style="display:none; margin-top:8px;">No recurring failure clusters detected yet.</p>
              </div>
            </details>
          </section>

          <section class="panel section">
            <div class="section-head">
              <h2 id="selected-run-title">Selected Run Intelligence</h2>
              <div>
                <button class="btn" id="open-run-report">Open report</button>
              </div>
            </div>
            <p class="small" id="selected-run-meta">Pick a run from the sidebar.</p>

            <div class="summary-grid" style="margin-top:10px;">
              <article class="card"><p class="label">Reliability Score</p><p class="value" id="selected-score">-</p></article>
              <article class="card"><p class="label">Risk Level</p><p class="value" id="selected-risk">-</p></article>
              <article class="card"><p class="label">Run Type</p><p class="value" id="selected-run-type">-</p></article>
              <article class="card"><p class="label">Fault Injection</p><p class="value" id="selected-chaos">-</p></article>
            </div>

            <div class="summary-grid" style="margin-top:10px; grid-template-columns: repeat(2, minmax(120px, 1fr));">
              <article class="card">
                <p class="label">Key Findings</p>
                <ul class="summary-list" id="selected-findings"></ul>
              </article>
              <article class="card">
                <p class="label">Recommendations</p>
                <ul class="summary-list" id="selected-recommendations"></ul>
              </article>
            </div>

            <div style="margin-top:10px;" class="card">
              <p class="label">Failure Classification Summary</p>
              <ul class="summary-list" id="selected-failure-summary"></ul>
            </div>

            <div class="toolbar">
              <div>
                <button class="btn active" data-test-filter="ALL">All</button>
                <button class="btn" data-test-filter="FAILED">Failed</button>
                <button class="btn" data-test-filter="PASSED">Passed</button>
              </div>
              <input id="test-search" class="search" style="max-width: 380px;" placeholder="Search tests" />
            </div>

            <div class="table-wrap">
              <table>
                <thead>
                  <tr><th>Scenario</th><th>Status</th><th>Insight</th><th>Duration</th><th>Failure Type</th></tr>
                </thead>
                <tbody id="selected-tests-body"></tbody>
              </table>
            </div>
          </section>
        </main>
      </div>
    </div>

    <script>
      let trendData = {{ trend_json | safe }};
      const runsById = new Map(Object.entries({{ runs_by_id_json | safe }}));
      let runSeries = (trendData.series || []).slice().sort((a, b) => b.started_at.localeCompare(a.started_at));
      const runJsonPathById = new Map(runSeries.map((row) => [row.run_id, row.run_json_path]));
      const runReportPathById = new Map(runSeries.map((row) => [row.run_id, row.report_path]));

      const FAILURE_LABELS = {
        assertion_failure: "Assertion Failure",
        timeout_navigation: "Navigation Timeout",
        timeout_selector: "Selector Timeout",
        network_error: "Network Error",
        http_5xx: "HTTP 5xx",
        browser_crash: "Browser Crash",
        environment_error: "Environment Error",
        unknown: "Unknown",
        timeout_failure: "Timeout Failure",
        validation_failure: "Validation Failure",
        intermittent_failure: "Intermittent Failure",
        chaos_triggered_failure: "Fault-Injected Failure",
        unknown_failure: "Unknown Failure",
      };

      let selectedRunId = runSeries.length ? runSeries[0].run_id : null;
      let visibleRunCount = 50;
      let timeframeDays = null;
      let currentTestFilter = "ALL";

      function round2(value) {
        return Math.round((Number(value) || 0) * 100) / 100;
      }

      function toNumber(value) {
        if (typeof value === "number" && Number.isFinite(value)) return value;
        if (typeof value === "string") {
          const cleaned = value.trim().replace(/%$/, "");
          const parsed = Number.parseFloat(cleaned);
          if (Number.isFinite(parsed)) return parsed;
        }
        return 0;
      }

      function toInt(value) {
        const parsed = toNumber(value);
        if (Number.isFinite(parsed)) return Math.round(parsed);
        return 0;
      }

      function deriveRunJsonPath(runId, startedAt) {
        if (!runId) return "";
        const fromDate = (date) => {
          if (!date || Number.isNaN(date.getTime())) return "";
          const yyyy = String(date.getUTCFullYear()).padStart(4, "0");
          const mm = String(date.getUTCMonth() + 1).padStart(2, "0");
          const dd = String(date.getUTCDate()).padStart(2, "0");
          return `runs/${yyyy}/${mm}/${dd}/${runId}/run.json`;
        };

        const started = startedAt ? new Date(startedAt) : null;
        if (started && !Number.isNaN(started.getTime())) {
          return fromDate(started);
        }

        const match = /^([0-9]{4})([0-9]{2})([0-9]{2})T/.exec(String(runId));
        if (!match) return "";
        const [, y, m, d] = match;
        return `runs/${y}/${m}/${d}/${runId}/run.json`;
      }

      function recomputePassRate(run) {
        const tests = Array.isArray(run?.tests) ? run.tests : [];
        if (!tests.length) return 0;
        const passed = tests.filter((test) => test.status === "passed").length;
        return round2((passed / tests.length) * 100);
      }

      function seriesRowFromRun(run) {
        const passRate = recomputePassRate(run);
        const failed = Array.isArray(run?.tests) ? run.tests.filter((test) => test.status === "failed").length : Number(run?.failed || 0);
        const startedAt = run?.started_at || run?.startedAt || new Date().toISOString();
        const runId = run?.run_id || run?.runId || "unknown-run";

        if (!runJsonPathById.get(runId) && startedAt) {
          const path = deriveRunJsonPath(runId, startedAt);
          if (path) {
            runJsonPathById.set(runId, path);
            runReportPathById.set(runId, path.replace(/run\\.json$/, "report.html"));
          }
        }

        return {
          run_id: runId,
          started_at: startedAt,
          status: run?.status || (failed > 0 ? "failed" : "passed"),
          duration_ms: toInt(run?.duration_ms),
          failed,
          pass_rate: passRate,
          run_reliability_score: toNumber(run?.run_reliability_score || run?.reliability_score || passRate),
          chaos_profile: run?.chaos_profile || "none",
          chaos_intent: run?.chaos_intent || "none",
          report_path: runReportPathById.get(runId) || run?.report_path || "",
          run_json_path: runJsonPathById.get(runId) || run?.run_json_path || "",
        };
      }

      function refreshKpisFromSeries() {
        const runs = getFilteredRuns();
        const runCount = runs.length;
        const avgPassRate = runCount ? round2(runs.reduce((acc, row) => acc + toNumber(row.pass_rate || 0), 0) / runCount) : 0;
        const avgReliability = runCount
          ? round2(runs.reduce((acc, row) => acc + toNumber(row.run_reliability_score || 0), 0) / runCount)
          : 0;

        const baselineRuns = runs.filter((row) => !row.chaos_profile || row.chaos_profile === "none");
        const faultRuns = runs.filter((row) => row.chaos_profile && row.chaos_profile !== "none");
        const baselineReliability = baselineRuns.length
          ? round2(baselineRuns.reduce((acc, row) => acc + toNumber(row.run_reliability_score || 0), 0) / baselineRuns.length)
          : null;
        const faultReliability = faultRuns.length
          ? round2(faultRuns.reduce((acc, row) => acc + toNumber(row.run_reliability_score || 0), 0) / faultRuns.length)
          : null;
        const reliabilityDelta = (baselineReliability !== null && faultReliability !== null)
          ? round2(baselineReliability - faultReliability)
          : null;

        const durations = runs
          .map((row) => toInt(row.duration_ms))
          .filter((value) => value > 0)
          .sort((a, b) => a - b);
        const p95Index = durations.length ? Math.floor((durations.length - 1) * 0.95) : 0;
        const p95Duration = durations.length ? durations[p95Index] : 0;

        const runsNode = document.getElementById("kpi-runs");
        const passRateNode = document.getElementById("kpi-pass-rate");
        const reliabilityNode = document.getElementById("kpi-reliability");
        const baselineReliabilityNode = document.getElementById("kpi-baseline-rel");
        const faultReliabilityNode = document.getElementById("kpi-fault-rel");
        const reliabilityDeltaNode = document.getElementById("kpi-rel-delta");
        const p95Node = document.getElementById("kpi-p95-duration");
        if (runsNode) runsNode.textContent = String(runCount);
        if (passRateNode) passRateNode.textContent = `${avgPassRate}%`;
        if (reliabilityNode) reliabilityNode.textContent = `${avgReliability}%`;
        if (baselineReliabilityNode) baselineReliabilityNode.textContent = baselineReliability === null ? "-" : `${baselineReliability}%`;
        if (faultReliabilityNode) faultReliabilityNode.textContent = faultReliability === null ? "-" : `${faultReliability}%`;
        if (reliabilityDeltaNode) {
          reliabilityDeltaNode.textContent = reliabilityDelta === null ? "-" : `${reliabilityDelta}%`;
          reliabilityDeltaNode.style.color = reliabilityDelta === null
            ? "var(--text)"
            : (reliabilityDelta >= 0 ? "var(--green)" : "var(--red)");
        }
        if (p95Node) p95Node.textContent = `${p95Duration} ms`;
      }

      async function fetchJson(path) {
        try {
          const response = await fetch(path, { cache: "no-store" });
          if (!response.ok) return null;
          return await response.json();
        } catch (error) {
          return null;
        }
      }

      function ingestSeriesRows(rows) {
        if (!Array.isArray(rows) || !rows.length) return false;
        const byId = new Map(runSeries.map((row) => [row.run_id, row]));
        for (const row of rows) {
          if (!row || !row.run_id) continue;
          const normalized = {
            ...row,
            failed: toNumber(row.failed || 0),
            pass_rate: toNumber(row.pass_rate || 0),
            run_reliability_score: toNumber(row.run_reliability_score || 0),
            chaos_profile: row.chaos_profile || "none",
            chaos_intent: row.chaos_intent || "none",
          };
          byId.set(normalized.run_id, normalized);
          if (normalized.run_json_path) runJsonPathById.set(normalized.run_id, normalized.run_json_path);
          if (normalized.report_path) runReportPathById.set(normalized.run_id, normalized.report_path);
        }
        runSeries = [...byId.values()].sort((a, b) => String(b.started_at || "").localeCompare(String(a.started_at || "")));
        return true;
      }

      async function hydrateFromS3Index() {
        const latest = await fetchJson("index/latest_runs.json");
        const latestRows = Array.isArray(latest?.runs)
          ? latest.runs
          : Array.isArray(latest?.latest_runs)
            ? latest.latest_runs
            : Array.isArray(latest)
              ? latest
              : [];

        if (latestRows.length) {
          const rows = latestRows.map((row) => {
            const runId = row.run_id || row.runId;
            const startedAt = row.started_at || row.startedAt;
            const chaosProfile = row.chaos_profile || row.chaosProfile || "none";
            const runJsonPath = row.run_json_path || row.runJsonPath;
            const reportPath = row.report_path || row.reportPath;
            if (runId && runJsonPath) runJsonPathById.set(runId, runJsonPath);
            if (runId && reportPath) runReportPathById.set(runId, reportPath);
            return {
              run_id: runId,
              started_at: startedAt,
              status: row.status || "passed",
              duration_ms: toInt(row.duration_ms),
              failed: toInt(row.failed),
              pass_rate: row.pass_rate,
              run_reliability_score: toNumber(row.run_reliability_score || row.reliability_score || 0),
              chaos_profile: chaosProfile,
              chaos_intent: row.chaos_intent || row.fault_injection || "none",
              run_json_path: runJsonPath || runJsonPathById.get(runId) || deriveRunJsonPath(runId, startedAt),
              report_path: reportPath || runReportPathById.get(runId) || "",
            };
          }).filter((row) => row.run_id);
          ingestSeriesRows(rows);
        }

        const analytics = await fetchJson("index/window_analytics_30d.json");
        if (analytics && Array.isArray(analytics.series) && analytics.series.length) {
          trendData = { ...trendData, ...analytics };
          ingestSeriesRows(analytics.series);
        }

        refreshKpisFromSeries();
      }

      async function backfillSeriesFromRunJson(limit = 250) {
        const candidates = runSeries.slice(0, limit);
        const updates = [];
        for (const row of candidates) {
          const runId = row.run_id;
          const existing = runsById.get(runId);
          if (existing) {
            updates.push(seriesRowFromRun(existing));
            continue;
          }

          const runJsonPath = row.run_json_path || runJsonPathById.get(runId) || deriveRunJsonPath(runId, row.started_at);
          if (!runJsonPath) continue;
          const payload = await fetchJson(runJsonPath);
          if (!payload || !payload.run_id) continue;
          runsById.set(payload.run_id, payload);
          runJsonPathById.set(payload.run_id, runJsonPath);
          runReportPathById.set(payload.run_id, runJsonPath.replace(/run\\.json$/, "report.html"));
          updates.push(seriesRowFromRun(payload));
        }
        if (updates.length) {
          ingestSeriesRows(updates);
          refreshKpisFromSeries();
          renderDashboardPanels();
        }
      }

      async function ensureRunLoaded(runId) {
        if (runsById.has(runId)) return runsById.get(runId);
        const runJsonPath = runJsonPathById.get(runId);
        if (!runJsonPath) return null;
        const payload = await fetchJson(runJsonPath);
        if (!payload || !payload.run_id) return null;
        runsById.set(payload.run_id, payload);

        const row = seriesRowFromRun(payload);
        ingestSeriesRows([row]);
        refreshKpisFromSeries();
        renderDashboardPanels();
        return payload;
      }

      function extractFingerprint(errorMessage) {
        if (!errorMessage) return null;
        const match = String(errorMessage).match(/(?:^|\\n)Fingerprint:\\s*([0-9a-f]{6,40})\\s*$/im);
        if (!match) return null;
        return String(match[1]).toLowerCase();
      }

      function mean(values) {
        if (!values.length) return 0;
        return values.reduce((acc, value) => acc + value, 0) / values.length;
      }

      function stddev(values) {
        if (values.length <= 1) return 0;
        const avg = mean(values);
        const variance = mean(values.map((value) => (value - avg) ** 2));
        return Math.sqrt(variance);
      }

      function windowRunsFromRows(rows) {
        return rows
          .map((row) => runsById.get(row.run_id))
          .filter((run) => run && Array.isArray(run.tests));
      }

      function renderAnalyticsCoverageBadge(rows) {
        const badge = document.getElementById("analytics-coverage-badge");
        if (!badge) return;
        const total = Array.isArray(rows) ? rows.length : 0;
        const loaded = Array.isArray(rows)
          ? rows.reduce((acc, row) => acc + (runsById.has(row.run_id) ? 1 : 0), 0)
          : 0;
        badge.textContent = `Loaded details ${loaded}/${total} runs`;
      }

      function computeTopReliabilityRisks(rows) {
        const runs = windowRunsFromRows(rows);
        const byTest = new Map();
        for (const run of runs) {
          for (const test of run.tests) {
            if (!byTest.has(test.nodeid)) byTest.set(test.nodeid, []);
            byTest.get(test.nodeid).push({ run, test });
          }
        }

        const output = [];
        for (const [nodeid, entries] of byTest.entries()) {
          const ordered = entries
            .slice()
            .sort((a, b) => String(a.run.started_at || "").localeCompare(String(b.run.started_at || "")));
          const executed = ordered.filter((item) => item.test.status === "passed" || item.test.status === "failed");
          if (!executed.length) continue;

          const statuses = executed.map((item) => item.test.status);
          const passes = statuses.filter((status) => status === "passed").length;
          const passRate = passes / executed.length;
          const transitions = statuses.slice(1).reduce((acc, status, index) => acc + (status !== statuses[index] ? 1 : 0), 0);
          const flakeRate = statuses.length > 1 ? transitions / (statuses.length - 1) : 0;

          let chaosExecutions = 0;
          let chaosFailures = 0;
          let baselineExecutions = 0;
          let baselineFailures = 0;
          for (const item of executed) {
            const hasChaos = Boolean(item.run.chaos_profile && item.run.chaos_profile !== "none");
            if (hasChaos) {
              chaosExecutions += 1;
              if (item.test.status === "failed") chaosFailures += 1;
            } else {
              baselineExecutions += 1;
              if (item.test.status === "failed") baselineFailures += 1;
            }
          }

          const chaosFailRate = chaosExecutions ? chaosFailures / chaosExecutions : 0;
          const baselineFailRate = baselineExecutions ? baselineFailures / baselineExecutions : 0;
          const chaosSensitivity = Math.max(0, Math.min(1, chaosFailRate - baselineFailRate));

          const durations = executed.map((item) => toNumber(item.test.duration_ms || 0)).filter((value) => value >= 0);
          const avgDuration = mean(durations);
          const durationCv = durations.length > 1 && avgDuration > 0 ? stddev(durations) / avgDuration : 0;
          const durationStability = 1 - Math.max(0, Math.min(1, durationCv));

          const reliability = round2(((passRate * 0.70) + ((1 - flakeRate) * 0.15) + ((1 - chaosSensitivity) * 0.10) + (durationStability * 0.05)) * 100);

          output.push({
            nodeid,
            reliability_score: Math.max(0, Math.min(100, reliability)),
            pass_rate: round2(passRate * 100),
            flake_rate: round2(flakeRate * 100),
            chaos_sensitivity: round2(chaosSensitivity * 100),
            executions: executed.length,
          });
        }

        output.sort((a, b) => {
          if (a.reliability_score !== b.reliability_score) return a.reliability_score - b.reliability_score;
          if (a.executions !== b.executions) return b.executions - a.executions;
          return a.nodeid.localeCompare(b.nodeid);
        });
        return output.slice(0, 10);
      }

      function computeFailureClusters(rows) {
        const runs = windowRunsFromRows(rows);
        const clusters = new Map();
        for (const run of runs) {
          const hasChaos = Boolean(run.chaos_profile && run.chaos_profile !== "none");
          for (const test of run.tests) {
            if (test.status !== "failed") continue;
            const fingerprint = extractFingerprint(test.error_message);
            if (!fingerprint) continue;

            if (!clusters.has(fingerprint)) {
              clusters.set(fingerprint, {
                fingerprint,
                occurrences: 0,
                failureTypes: new Map(),
                tests: new Map(),
                runs: new Set(),
              });
            }
            const cluster = clusters.get(fingerprint);
            cluster.occurrences += 1;
            cluster.runs.add(run.run_id);
            const normalizedType = normalizeFailureType(test.failure_type || "unknown", hasChaos);
            cluster.failureTypes.set(normalizedType, (cluster.failureTypes.get(normalizedType) || 0) + 1);
            cluster.tests.set(test.nodeid, (cluster.tests.get(test.nodeid) || 0) + 1);
          }
        }

        return [...clusters.values()]
          .map((row) => {
            const topFailure = [...row.failureTypes.entries()].sort((a, b) => b[1] - a[1])[0];
            const topTests = [...row.tests.entries()]
              .sort((a, b) => b[1] - a[1])
              .slice(0, 3)
              .map(([nodeid, count]) => ({ nodeid, count }));
            return {
              fingerprint: row.fingerprint,
              occurrences: row.occurrences,
              runs_affected: row.runs.size,
              failure_type: topFailure ? topFailure[0] : "unknown",
              top_tests: topTests,
            };
          })
          .sort((a, b) => {
            if (a.occurrences !== b.occurrences) return b.occurrences - a.occurrences;
            if (a.runs_affected !== b.runs_affected) return b.runs_affected - a.runs_affected;
            return a.fingerprint.localeCompare(b.fingerprint);
          })
          .slice(0, 10);
      }

      function computeFailureDistribution(rows) {
        const distribution = {};
        const runs = windowRunsFromRows(rows);
        for (const run of runs) {
          const hasChaos = Boolean(run.chaos_profile && run.chaos_profile !== "none");
          for (const test of run.tests) {
            if (test.status !== "failed") continue;
            const key = normalizeFailureType(test.failure_type || "unknown", hasChaos);
            distribution[key] = (distribution[key] || 0) + 1;
          }
        }
        return distribution;
      }

      function renderReliabilityRiskTable(rows) {
        const tbody = document.getElementById("reliability-risk-body");
        const empty = document.getElementById("reliability-risk-empty");
        if (!tbody || !empty) return;
        if (!rows.length) {
          tbody.innerHTML = "";
          empty.style.display = "block";
          return;
        }

        empty.style.display = "none";
        tbody.innerHTML = rows.map((row) => `
          <tr>
            <td>${esc(row.nodeid)}</td>
            <td>${esc(round2(row.reliability_score))}%</td>
            <td>${esc(round2(row.pass_rate))}%</td>
            <td>${esc(round2(row.flake_rate))}%</td>
            <td>${esc(round2(row.chaos_sensitivity))}%</td>
          </tr>
        `).join("");
      }

      function renderFailureClusterTable(rows) {
        const tbody = document.getElementById("failure-cluster-body");
        const empty = document.getElementById("failure-cluster-empty");
        if (!tbody || !empty) return;
        if (!rows.length) {
          tbody.innerHTML = "";
          empty.style.display = "block";
          return;
        }

        empty.style.display = "none";
        tbody.innerHTML = rows.map((row) => {
          const tests = (row.top_tests || []).map((test) => `<div>${esc(test.nodeid)} (${esc(test.count)})</div>`).join("");
          return `
            <tr>
              <td><code>${esc(row.fingerprint)}</code></td>
              <td>${esc(row.occurrences)}</td>
              <td>${esc(row.runs_affected)}</td>
              <td>${esc(failureLabel(row.failure_type))}</td>
              <td>${tests}</td>
            </tr>
          `;
        }).join("");
      }

      function renderDashboardPanels() {
        const windowRows = getFilteredRuns();
        refreshKpisFromSeries();
        renderAnalyticsCoverageBadge(windowRows);
        renderFailureDonut(computeFailureDistribution(windowRows));
        renderTrendChart(windowRows);
        renderLatencyChart(windowRows);
        renderReliabilityRiskTable(computeTopReliabilityRisks(windowRows));
        renderFailureClusterTable(computeFailureClusters(windowRows));
      }

      function esc(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#039;");
      }

      function failureLabel(value) {
        if (!value || value === "-") return "-";
        return FAILURE_LABELS[value] || value.split("_").map((part) => part[0].toUpperCase() + part.slice(1)).join(" ");
      }

      function normalizeArtifactPath(path) {
        if (!path) return "";
        if (path.startsWith("http://") || path.startsWith("https://")) return path;
        let clean = path;
        if (clean.startsWith(".reliabilitykit/")) clean = clean.slice(".reliabilitykit/".length);
        if (clean.startsWith("/")) clean = clean.slice(1);
        return clean;
      }

      function artifactHref(runId, artifactPath) {
        const clean = normalizeArtifactPath(artifactPath);
        if (!clean) return "";
        if (clean.startsWith("runs/")) return clean;

        const runJsonPath = runJsonPathById.get(runId) || "";
        const base = runJsonPath.endsWith("/run.json") ? runJsonPath.slice(0, -9) : "";
        if (clean.startsWith("artifacts/") && base) return `${base}/${clean}`;
        return clean;
      }

      function isLogArtifact(kind) {
        const normalized = String(kind || "").toLowerCase();
        return normalized === "console_log" || normalized === "event_log" || normalized === "failure_raw";
      }

      function isTraceArtifact(kind) {
        return String(kind || "").toLowerCase() === "trace";
      }

      function isScreenshotArtifact(kind) {
        return String(kind || "").toLowerCase() === "screenshot";
      }

      async function previewLog(detailId, href) {
        if (!href) return;
        const container = document.getElementById(`log-preview-${detailId}`);
        if (!container) return;
        container.textContent = "Loading log preview...";
        try {
          const response = await fetch(href);
          if (!response.ok) {
            container.textContent = `Unable to load preview (${response.status}).`;
            return;
          }
          const text = await response.text();
          const lines = text.split("\\n").slice(0, 25).join("\\n");
          container.textContent = lines || "(empty log file)";
        } catch (error) {
          container.textContent = "Preview unavailable in this environment.";
        }
      }

      function getFilteredRuns() {
        const query = (document.getElementById("run-search").value || "").trim().toLowerCase();
        const now = new Date();
        return runSeries.filter((row) => {
          if (timeframeDays !== null) {
            const started = new Date(row.started_at);
            const diffDays = (now - started) / (1000 * 60 * 60 * 24);
            if (diffDays > timeframeDays) return false;
          }

          if (!query) return true;
          const text = `${row.run_id} ${row.chaos_profile || "none"}`.toLowerCase();
          return text.includes(query);
        });
      }

      function renderRunSidebar() {
        const list = document.getElementById("run-list");
        const rows = getFilteredRuns();
        const shown = rows.slice(0, visibleRunCount);

        list.innerHTML = shown.map((row) => {
          const statusClass = row.status === "passed" ? "pass" : "fail";
          const active = row.run_id === selectedRunId ? "active" : "";
          return `
            <li class="run-item ${active}" data-run-id="${esc(row.run_id)}">
              <div class="id">${esc(row.run_id)}</div>
              <div class="meta">
                <span class="status ${statusClass}">${esc(row.status)}</span>
                pass ${esc(row.pass_rate)}% • failed ${esc(row.failed)} • ${esc(row.chaos_intent || "none")}
              </div>
            </li>
          `;
        }).join("");

        for (const item of list.querySelectorAll(".run-item")) {
          item.addEventListener("click", () => {
            selectedRunId = item.dataset.runId;
            renderRunSidebar();
            void renderSelectedRun();
          });
        }

        document.getElementById("load-more").style.display = rows.length > shown.length ? "block" : "none";

        if (!selectedRunId && shown.length) {
          selectedRunId = shown[0].run_id;
          void renderSelectedRun();
        }
      }

      function summarizeRun(run) {
        const tests = Array.isArray(run.tests) ? run.tests : [];
        const passed = tests.filter((test) => test.status === "passed").length;
        const failed = tests.filter((test) => test.status === "failed").length;
        const passRate = tests.length ? ((passed / tests.length) * 100).toFixed(2) : "0.00";
        return { tests, passed, failed, passRate };
      }

      function scenarioNameFromTest(test) {
        const base = (test?.name || test?.nodeid || "scenario").replace(/^test_/, "").split("[")[0];
        return base
          .split("_")
          .filter(Boolean)
          .map((part) => part[0].toUpperCase() + part.slice(1))
          .join(" ");
      }

      function normalizeFailureType(rawType, hasChaos) {
        const mapping = {
          timeout_navigation: "timeout_failure",
          timeout_selector: "timeout_failure",
          network_error: "intermittent_failure",
          http_5xx: "validation_failure",
          assertion_failure: "assertion_failure",
          browser_crash: "unknown_failure",
          environment_error: "unknown_failure",
          unknown: "unknown_failure",
        };
        const normalized = mapping[rawType] || "unknown_failure";
        if (hasChaos && normalized !== "unknown_failure") return "chaos_triggered_failure";
        return normalized;
      }

      function scenarioInsight(test, normalizedFailure) {
        if (test.status === "passed") return `Stable, avg ${toInt(test.duration_ms)} ms`;
        if (normalizedFailure === "chaos_triggered_failure") return "Unstable under fault injection";
        if (normalizedFailure === "timeout_failure") return "Timeout sensitivity detected";
        if (normalizedFailure === "validation_failure") return "Validation behavior is inconsistent";
        return `Failure observed (${failureLabel(normalizedFailure)})`;
      }

      function runRiskLevel(score) {
        if (score >= 85) return "Low Risk";
        if (score >= 65) return "Moderate Risk";
        return "High Risk";
      }

      function buildRunIntelligence(run, summary) {
        const hasChaos = Boolean(run.chaos_profile && run.chaos_profile !== "none");
        const chaosEvents = summary.tests.reduce((acc, test) => acc + ((test.chaos_events || []).length || 0), 0);
        const failureCounts = {};
        for (const test of summary.tests) {
          if (test.status !== "failed") continue;
          const normalized = normalizeFailureType(test.failure_type || "unknown", hasChaos);
          failureCounts[normalized] = (failureCounts[normalized] || 0) + 1;
        }

        const score = Math.max(0, Math.min(100, Number(summary.passRate) - Math.min(25, summary.failed * 3) - Math.min(15, chaosEvents * 0.5)));
        const findings = [];
        const recommendations = [];
        if (summary.failed === 0) findings.push("All executed scenarios passed in this run.");
        else findings.push(`${summary.failed}/${summary.tests.length} scenarios failed.`);

        if (hasChaos) findings.push(`Fault injection '${run.chaos_intent || "fault"}' was active via profile '${run.chaos_profile}'.`);
        else findings.push("Run executed under baseline conditions without fault injection.");

        if (failureCounts.chaos_triggered_failure) findings.push("Reliability drops under injected fault conditions.");
        if (failureCounts.timeout_failure) findings.push("Timeout-sensitive behavior detected.");
        if (failureCounts.validation_failure) findings.push("Input validation handling is inconsistent.");

        recommendations.push("Prioritize highest-frequency failure category and retest with same seed.");
        if (failureCounts.validation_failure) recommendations.push("Add stronger input validation guards for malformed payloads.");
        if (failureCounts.timeout_failure) recommendations.push("Tune timeout thresholds and add retry/backoff for transient failures.");
        if (hasChaos) recommendations.push("Compare this run against nearest baseline run to quantify fault-injection impact.");
        else recommendations.push("Run one fault-injection lane to validate resilience under fault conditions.");

        return {
          score: Math.round(score),
          risk: runRiskLevel(score),
          runType: hasChaos ? "fault_injected" : "baseline",
          chaosProfile: run.chaos_intent || "none",
          findings: findings.slice(0, 5),
          recommendations: recommendations.slice(0, 5),
          failureSummary: Object.entries(failureCounts).sort((a, b) => b[1] - a[1]),
        };
      }

      async function renderSelectedRun() {
        if (!selectedRunId) return;
        let run = runsById.get(selectedRunId);
        if (!run) {
          run = await ensureRunLoaded(selectedRunId);
        }
        if (!run) {
          document.getElementById("selected-run-title").textContent = `Selected Run: ${selectedRunId}`;
          document.getElementById("selected-run-meta").textContent = "Run details unavailable (run.json not found yet).";
          document.getElementById("selected-tests-body").innerHTML = "";
          const resetIds = [
            ["selected-score", "-"],
            ["selected-risk", "-"],
            ["selected-run-type", "-"],
            ["selected-chaos", "-"],
          ];
          for (const [id, value] of resetIds) {
            const node = document.getElementById(id);
            if (node) node.textContent = value;
          }
          const findings = document.getElementById("selected-findings");
          const recommendations = document.getElementById("selected-recommendations");
          const failureSummary = document.getElementById("selected-failure-summary");
          if (findings) findings.innerHTML = "";
          if (recommendations) recommendations.innerHTML = "";
          if (failureSummary) failureSummary.innerHTML = "";
          return;
        }

        const summary = summarizeRun(run);
        const intelligence = buildRunIntelligence(run, summary);
        document.getElementById("selected-run-title").textContent = `Selected Run: ${run.run_id}`;
        document.getElementById("selected-run-meta").textContent =
          `started ${run.started_at} • ended ${run.ended_at} • status ${run.status} • pass ${summary.passRate}% • tests ${summary.tests.length}`;

        const selectedScore = document.getElementById("selected-score");
        const selectedRisk = document.getElementById("selected-risk");
        const selectedRunType = document.getElementById("selected-run-type");
        const selectedChaos = document.getElementById("selected-chaos");
        const selectedFindings = document.getElementById("selected-findings");
        const selectedRecommendations = document.getElementById("selected-recommendations");
        const selectedFailureSummary = document.getElementById("selected-failure-summary");

        if (selectedScore) selectedScore.textContent = `${intelligence.score}/100`;
        if (selectedRisk) selectedRisk.textContent = intelligence.risk;
        if (selectedRunType) selectedRunType.textContent = intelligence.runType;
        if (selectedChaos) selectedChaos.textContent = intelligence.chaosProfile;
        if (selectedFindings) {
          selectedFindings.innerHTML = intelligence.findings.map((item) => `<li>${esc(item)}</li>`).join("");
        }
        if (selectedRecommendations) {
          selectedRecommendations.innerHTML = intelligence.recommendations.map((item) => `<li>${esc(item)}</li>`).join("");
        }
        if (selectedFailureSummary) {
          if (intelligence.failureSummary.length) {
            selectedFailureSummary.innerHTML = intelligence.failureSummary
              .map(([failureType, count]) => `<li>${esc(failureLabel(failureType))} -> ${esc(count)} occurrence${count === 1 ? "" : "s"}</li>`)
              .join("");
          } else {
            selectedFailureSummary.innerHTML = "<li>No classified failures in this run.</li>";
          }
        }

        const reportPath = runReportPathById.get(run.run_id) || "";
        document.getElementById("open-run-report").onclick = () => {
          if (reportPath) window.location.href = reportPath;
        };

        renderSelectedRunTests(run);
      }

      function renderSelectedRunTests(run) {
        const tbody = document.getElementById("selected-tests-body");
        const query = (document.getElementById("test-search").value || "").trim().toLowerCase();
        const tests = (Array.isArray(run.tests) ? run.tests : [])
          .slice()
          .sort((a, b) => {
            if (a.status === b.status) return a.nodeid.localeCompare(b.nodeid);
            return a.status === "failed" ? -1 : 1;
          })
          .filter((test) => {
            if (currentTestFilter !== "ALL" && test.status.toUpperCase() !== currentTestFilter) return false;
            if (!query) return true;
            const full = `${test.nodeid} ${test.failure_type || ""}`.toLowerCase();
            return full.includes(query);
          });

        tbody.innerHTML = tests.map((test, index) => {
          const isFailed = test.status === "failed";
          const statusClass = isFailed ? "fail" : "pass";
          const hasChaos = Boolean(run.chaos_profile && run.chaos_profile !== "none");
          const normalizedFailure = normalizeFailureType(test.failure_type || "unknown", hasChaos && isFailed);
          const failure = isFailed ? failureLabel(normalizedFailure) : "-";
          const scenario = scenarioNameFromTest(test);
          const insight = scenarioInsight(test, normalizedFailure);
          const detailId = `detail-${index}`;

          const artifacts = Array.isArray(test.artifacts) ? test.artifacts : [];
          const screenshotArtifacts = artifacts.filter((artifact) => isScreenshotArtifact(artifact.kind));
          const logArtifacts = artifacts.filter((artifact) => isLogArtifact(artifact.kind));
          const traceArtifacts = artifacts.filter((artifact) => isTraceArtifact(artifact.kind));

          const artifactHtml = screenshotArtifacts.length
            ? `<div class="artifact-grid">${screenshotArtifacts.map((artifact) => {
                const href = artifactHref(run.run_id, artifact.path || "");
                return `<a href="${esc(href)}" target="_blank" rel="noopener noreferrer"><img src="${esc(href)}" alt="${esc(test.nodeid)}" /><div style=\"padding:6px 8px;font-size:11px;\">${esc(artifact.kind || "artifact")}</div></a>`;
              }).join("")}</div>`
            : '<p class="small">No screenshot artifacts.</p>';

          const logLinks = [...logArtifacts, ...traceArtifacts].map((artifact, artifactIndex) => {
            const href = artifactHref(run.run_id, artifact.path || "");
            const button = isTraceArtifact(artifact.kind)
              ? ""
              : `<button class=\"btn\" data-preview-target=\"${esc(detailId)}\" data-preview-href=\"${esc(href)}\">Preview</button>`;
            return `<div style=\"display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:6px;\"><a href=\"${esc(href)}\" target=\"_blank\" rel=\"noopener noreferrer\">${esc(artifact.kind || "artifact")} ${artifactIndex + 1}</a>${button}</div>`;
          }).join("");

          const logsHtml = logLinks
            ? `<div>${logLinks}</div><pre id="log-preview-${esc(detailId)}">Select a log artifact preview.</pre>`
            : '<p class="small">No logs or trace artifacts.</p>';

          const errorHtml = test.error_message ? `<pre>${esc(String(test.error_message))}</pre>` : '<p class="small">No error details.</p>';

          return `
            <tr class="test-row" data-detail-id="${detailId}">
              <td>${esc(scenario)}</td>
              <td><span class="status ${statusClass}">${esc(test.status)}</span></td>
              <td>${esc(insight)}</td>
              <td>${esc(test.duration_ms || 0)} ms</td>
              <td>${esc(failure)}</td>
            </tr>
            <tr id="${detailId}" class="detail-row">
              <td colspan="5" class="detail-box">
                <strong>Failure Summary</strong>
                ${errorHtml}
                <div style="margin-top:8px;"><strong>Logs & Trace</strong></div>
                ${logsHtml}
                <div style="margin-top:8px;"><strong>Screenshots</strong></div>
                ${artifactHtml}
              </td>
            </tr>
          `;
        }).join("");

        for (const row of tbody.querySelectorAll(".test-row")) {
          row.addEventListener("click", () => {
            const detailId = row.dataset.detailId;
            const detail = document.getElementById(detailId);
            if (detail) detail.classList.toggle("open");
          });
        }

        for (const button of tbody.querySelectorAll("button[data-preview-href]")) {
          button.addEventListener("click", (event) => {
            event.stopPropagation();
            const detailId = button.dataset.previewTarget;
            const href = button.dataset.previewHref;
            previewLog(detailId, href);
          });
        }
      }

      function renderFailureDonut(distribution) {
        const svg = document.getElementById("failureDonut");
        const legend = document.getElementById("failureLegend");
        const entries = Object.entries(distribution || trendData.failure_distribution || {});
        if (!entries.length) {
          svg.innerHTML = '<text x="10" y="20" fill="rgba(255,255,255,0.65)" font-size="13">No failures in selected window.</text>';
          legend.textContent = "";
          return;
        }

        const total = entries.reduce((acc, item) => acc + Number(item[1]), 0);
        const colors = ["#ff4d6d", "#f6b73c", "#5aa7ff", "#27c07d", "#a58cff", "#62d4c8", "#ff8e5a"];
        const cx = 90;
        const cy = 95;
        const radius = 72;
        const strokeWidth = 34;

        let offset = 0;
        const circles = entries.map(([key, value], index) => {
          const fraction = Number(value) / total;
          const length = 2 * Math.PI * radius * fraction;
          const circumference = 2 * Math.PI * radius;
          const node = `<circle cx="${cx}" cy="${cy}" r="${radius}" fill="none" stroke="${colors[index % colors.length]}" stroke-width="${strokeWidth}" stroke-dasharray="${length} ${circumference - length}" stroke-dashoffset="${-offset}" transform="rotate(-90 ${cx} ${cy})"></circle>`;
          offset += length;
          return node;
        }).join("");

        svg.innerHTML = `
          <g>${circles}</g>
          <circle cx="${cx}" cy="${cy}" r="${radius - strokeWidth / 2}" fill="rgba(11,18,32,0.95)"></circle>
          <text x="${cx}" y="${cy - 4}" text-anchor="middle" fill="#fff" font-size="18" font-weight="700">${total}</text>
          <text x="${cx}" y="${cy + 16}" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="11">failures</text>
        `;

        legend.innerHTML = entries.map(([key, value], index) => {
          const color = colors[index % colors.length];
          return `<div><span style="display:inline-block;width:10px;height:10px;border-radius:999px;background:${color};margin-right:6px;"></span>${esc(failureLabel(key))}: ${esc(value)}</div>`;
        }).join("");
      }

      function renderTrendChart(seriesRows) {
        const chart = document.getElementById("trendChart");
        const legendNode = document.getElementById("trendLegend");
        const series = (Array.isArray(seriesRows) ? seriesRows : runSeries).slice().reverse();
        if (!series.length) {
          chart.innerHTML = '<text x="20" y="24" fill="rgba(255,255,255,0.65)" font-size="13">No run history available.</text>';
          if (legendNode) legendNode.textContent = "Blue = pass rate, Green = baseline reliability, Red = fault-injected reliability";
          return;
        }

        const width = 860;
        const height = 220;
        const pad = { top: 12, right: 16, bottom: 28, left: 30 };
        const innerW = width - pad.left - pad.right;
        const innerH = height - pad.top - pad.bottom;

        const toX = (index) => pad.left + (series.length === 1 ? innerW / 2 : (innerW * index) / (series.length - 1));
        const toY = (value) => pad.top + innerH - (Math.max(0, Math.min(100, Number(value) || 0)) / 100) * innerH;
        const pathFrom = (values) => values.map((value, index) => `${index === 0 ? "M" : "L"}${toX(index)},${toY(value)}`).join(" ");
        const pathFromSparse = (values) => {
          let d = "";
          let open = false;
          for (let index = 0; index < values.length; index += 1) {
            const value = values[index];
            if (value === null || value === undefined) {
              open = false;
              continue;
            }
            d += `${open ? "L" : "M"}${toX(index)},${toY(value)} `;
            open = true;
          }
          return d.trim();
        };

        const pass = series.map((row) => row.pass_rate || 0);
        const baselineRel = series.map((row) => (!row.chaos_profile || row.chaos_profile === "none") ? (row.run_reliability_score || 0) : null);
        const faultRel = series.map((row) => (row.chaos_profile && row.chaos_profile !== "none") ? (row.run_reliability_score || 0) : null);

        const guides = [0, 25, 50, 75, 100].map((value) =>
          `<line x1="${pad.left}" y1="${toY(value)}" x2="${width - pad.right}" y2="${toY(value)}" stroke="rgba(255,255,255,0.1)" stroke-width="1" />`
        ).join("");

        chart.innerHTML = `
          ${guides}
          <path d="${pathFrom(pass)}" fill="none" stroke="#5aa7ff" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="6 4" stroke-opacity="0.85" />
          <path d="${pathFromSparse(baselineRel)}" fill="none" stroke="#27c07d" stroke-width="3.2" stroke-linecap="round" />
          <path d="${pathFromSparse(faultRel)}" fill="none" stroke="#ff6d5a" stroke-width="3.2" stroke-linecap="round" />
          ${pass.map((value, index) => `<circle cx="${toX(index)}" cy="${toY(value)}" r="2.2" fill="#5aa7ff" fill-opacity="0.75"></circle>`).join("")}
          ${baselineRel.map((value, index) => value === null ? "" : `<circle cx="${toX(index)}" cy="${toY(value)}" r="2.8" fill="#27c07d"></circle>`).join("")}
          ${faultRel.map((value, index) => value === null ? "" : `<circle cx="${toX(index)}" cy="${toY(value)}" r="2.8" fill="#ff6d5a"></circle>`).join("")}
        `;

        if (legendNode) {
          const baselineValues = baselineRel.filter((value) => value !== null);
          const faultValues = faultRel.filter((value) => value !== null);
          const baselineAvg = baselineValues.length ? round2(baselineValues.reduce((acc, value) => acc + Number(value), 0) / baselineValues.length) : null;
          const faultAvg = faultValues.length ? round2(faultValues.reduce((acc, value) => acc + Number(value), 0) / faultValues.length) : null;
          const delta = (baselineAvg !== null && faultAvg !== null) ? round2(baselineAvg - faultAvg) : null;
          legendNode.textContent = `Blue = pass rate, Green = baseline (${baselineAvg ?? "-"}%), Red = fault-injected (${faultAvg ?? "-"}%), Delta = ${delta ?? "-"}%`;
        }
      }

      function renderLatencyChart(seriesRows) {
        const chart = document.getElementById("latencyChart");
        const legendNode = document.getElementById("latencyLegend");
        if (!chart) return;

        const series = (Array.isArray(seriesRows) ? seriesRows : runSeries).slice().reverse();
        if (!series.length) {
          chart.innerHTML = '<text x="20" y="24" fill="rgba(255,255,255,0.65)" font-size="13">No duration history available.</text>';
          if (legendNode) legendNode.textContent = "Green = baseline duration, Amber = fault-injected duration";
          return;
        }

        const width = 860;
        const height = 220;
        const pad = { top: 12, right: 16, bottom: 28, left: 42 };
        const innerW = width - pad.left - pad.right;
        const innerH = height - pad.top - pad.bottom;

        const values = series.map((row) => Math.max(0, toInt(row.duration_ms || 0)));
        const maxValue = Math.max(...values, 1);
        const minTop = 5000;
        const chartMax = Math.max(minTop, Math.ceil(maxValue * 1.1));

        const toX = (index) => pad.left + (series.length === 1 ? innerW / 2 : (innerW * index) / (series.length - 1));
        const toY = (value) => pad.top + innerH - ((Math.max(0, Math.min(chartMax, Number(value) || 0)) / chartMax) * innerH);

        const pathFromSparse = (valuesList) => {
          let d = "";
          let open = false;
          for (let index = 0; index < valuesList.length; index += 1) {
            const value = valuesList[index];
            if (value === null || value === undefined) {
              open = false;
              continue;
            }
            d += `${open ? "L" : "M"}${toX(index)},${toY(value)} `;
            open = true;
          }
          return d.trim();
        };

        const baselineDur = series.map((row) => (!row.chaos_profile || row.chaos_profile === "none") ? toInt(row.duration_ms || 0) : null);
        const faultDur = series.map((row) => (row.chaos_profile && row.chaos_profile !== "none") ? toInt(row.duration_ms || 0) : null);

        const guideLabels = [0.0, 0.25, 0.5, 0.75, 1.0].map((ratio) => {
          const value = Math.round(chartMax * ratio);
          const y = toY(value);
          return `<line x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}" stroke="rgba(255,255,255,0.1)" stroke-width="1" /><text x="${pad.left - 6}" y="${y + 4}" text-anchor="end" fill="rgba(255,255,255,0.65)" font-size="10">${value}</text>`;
        }).join("");

        chart.innerHTML = `
          ${guideLabels}
          <path d="${pathFromSparse(baselineDur)}" fill="none" stroke="#27c07d" stroke-width="3" stroke-linecap="round" />
          <path d="${pathFromSparse(faultDur)}" fill="none" stroke="#f6b73c" stroke-width="3" stroke-linecap="round" />
          ${baselineDur.map((value, index) => value === null ? "" : `<circle cx="${toX(index)}" cy="${toY(value)}" r="2.7" fill="#27c07d"></circle>`).join("")}
          ${faultDur.map((value, index) => value === null ? "" : `<circle cx="${toX(index)}" cy="${toY(value)}" r="2.7" fill="#f6b73c"></circle>`).join("")}
        `;

        if (legendNode) {
          const baselineValues = baselineDur.filter((value) => value !== null);
          const faultValues = faultDur.filter((value) => value !== null);
          const baselineP95 = baselineValues.length
            ? baselineValues.slice().sort((a, b) => a - b)[Math.floor((baselineValues.length - 1) * 0.95)]
            : null;
          const faultP95 = faultValues.length
            ? faultValues.slice().sort((a, b) => a - b)[Math.floor((faultValues.length - 1) * 0.95)]
            : null;
          legendNode.textContent = `Green = baseline duration (p95 ${baselineP95 ?? "-"} ms), Amber = fault-injected duration (p95 ${faultP95 ?? "-"} ms)`;
        }
      }

      function wireEvents() {
        document.getElementById("run-search").addEventListener("input", () => {
          visibleRunCount = 50;
          renderRunSidebar();
          renderDashboardPanels();
        });

        document.getElementById("load-more").addEventListener("click", () => {
          visibleRunCount += 50;
          renderRunSidebar();
        });

        for (const button of document.querySelectorAll("#timeframe-buttons .btn")) {
          button.addEventListener("click", () => {
            for (const other of document.querySelectorAll("#timeframe-buttons .btn")) {
              other.classList.remove("active");
            }
            button.classList.add("active");

            const raw = button.dataset.days;
            timeframeDays = raw === "all" ? null : Number(raw);
            visibleRunCount = 50;
            renderRunSidebar();
            renderDashboardPanels();
          });
        }

        for (const button of document.querySelectorAll("button[data-test-filter]")) {
          button.addEventListener("click", () => {
            currentTestFilter = button.dataset.testFilter;
            for (const other of document.querySelectorAll("button[data-test-filter]")) {
              other.classList.remove("active");
            }
            button.classList.add("active");
            void renderSelectedRun();
          });
        }

        document.getElementById("test-search").addEventListener("input", () => {
          void renderSelectedRun();
        });
      }

      async function bootstrapDashboard() {
        await hydrateFromS3Index();
        await backfillSeriesFromRunJson();
        wireEvents();
        renderRunSidebar();
        await renderSelectedRun();
        renderDashboardPanels();
      }

      void bootstrapDashboard();

      window.__RK_DASHBOARD_DATA__ = trendData;
    </script>
  </body>
</html>
"""
)


def write_dashboard_report(runs: list[RunRecord], output_path: Path) -> None:
    metrics = build_trend_metrics(runs)
    trend_json = json.dumps(metrics)
    runs_by_id_json = json.dumps({run.run_id: run.model_dump(mode="json") for run in runs})
    html = DASHBOARD_TEMPLATE.render(
        metrics=metrics,
        trend_json=trend_json,
        runs_by_id_json=runs_by_id_json,
    )
    output_path.write_text(html, encoding="utf-8")
