from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from reliabilitykit.core.models import RunRecord
from reliabilitykit.reporting.metrics import build_run_metrics


def _status_class(status: str) -> str:
    if status == "passed":
        return "ok"
    if status == "failed":
        return "bad"
    return "warn"


RUN_TEMPLATE = Template(
    """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ReliabilityKit Run {{ run.run_id }}</title>
    <style>
      :root {
        --bg: #f3f5f9;
        --bg-accent: #e8f0ff;
        --card: #ffffff;
        --card-soft: #f8fbff;
        --text: #11203a;
        --muted: #5e6e87;
        --line: #d9e1ef;
        --brand: #0f62fe;
        --brand-soft: #dbe7ff;
        --ok-bg: #e4f9ee;
        --ok-text: #12633f;
        --bad-bg: #fde9ea;
        --bad-text: #982328;
        --warn-bg: #fff3dc;
        --warn-text: #8f5f15;
        --shadow: 0 14px 30px rgba(19, 44, 88, 0.08);
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        background:
          radial-gradient(1200px 400px at 5% -10%, var(--bg-accent), transparent 50%),
          linear-gradient(180deg, #f7f9fd 0%, var(--bg) 40%, var(--bg) 100%);
        color: var(--text);
        font-family: "Space Grotesk", "Avenir Next", "Segoe UI", sans-serif;
      }

      .container {
        max-width: 1240px;
        margin: 28px auto;
        padding: 0 16px 24px;
      }

      .hero {
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 22px;
        background:
          linear-gradient(120deg, #ffffff 0%, #f4f8ff 48%, #ffffff 100%);
        box-shadow: var(--shadow);
      }

      .hero-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }

      .kicker {
        margin: 0;
        color: var(--muted);
        font-size: 12px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .title {
        margin: 4px 0 0;
        font-size: clamp(20px, 2.8vw, 30px);
        line-height: 1.2;
      }

      .meta {
        margin: 8px 0 0;
        color: var(--muted);
        font-size: 14px;
      }

      .meta-grid {
        margin-top: 16px;
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 10px;
      }

      .meta-chip {
        background: var(--card-soft);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 10px;
      }

      .meta-chip .label {
        margin: 0;
        color: var(--muted);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      .meta-chip .value {
        margin: 5px 0 0;
        font-size: 13px;
        font-weight: 700;
        overflow-wrap: anywhere;
      }

      .grid {
        display: grid;
        grid-template-columns: repeat(6, minmax(120px, 1fr));
        gap: 12px;
        margin-top: 16px;
      }

      .card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 12px;
        box-shadow: 0 8px 20px rgba(17, 32, 58, 0.04);
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
        font-size: 22px;
        font-weight: 700;
      }

      .section {
        margin-top: 16px;
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 8px 24px rgba(17, 32, 58, 0.04);
      }

      .section h2 {
        margin: 0 0 4px;
        font-size: 18px;
      }

      .section-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 12px;
      }

      .small {
        margin: 0;
        color: var(--muted);
        font-size: 13px;
      }

      table { width: 100%; border-collapse: collapse; }

      th,
      td {
        border-bottom: 1px solid var(--line);
        text-align: left;
        padding: 10px 8px;
        vertical-align: top;
      }

      th {
        color: var(--muted);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: .06em;
        position: sticky;
        top: 0;
        background: #fff;
      }

      .table-wrap {
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid var(--line);
      }

      .badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
      }

      .ok { background: var(--ok-bg); color: var(--ok-text); }
      .bad { background: var(--bad-bg); color: var(--bad-text); }
      .warn { background: var(--warn-bg); color: var(--warn-text); }

      .failure-list {
        display: grid;
        gap: 12px;
      }

      .failure-card {
        border: 1px solid #f7c9cb;
        border-left: 4px solid #ce3843;
        border-radius: 12px;
        padding: 12px;
        background: #fff8f8;
      }

      .failure-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 10px;
      }

      .failure-name {
        margin: 0;
        font-size: 14px;
        font-weight: 700;
        overflow-wrap: anywhere;
      }

      .failure-meta {
        margin: 8px 0 0;
        color: var(--muted);
        font-size: 12px;
      }

      .thumb-grid {
        margin-top: 10px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 8px;
      }

      .thumb {
        display: block;
        border: 1px solid var(--line);
        border-radius: 10px;
        overflow: hidden;
        background: #fff;
      }

      .thumb img {
        display: block;
        width: 100%;
        aspect-ratio: 16 / 10;
        object-fit: cover;
      }

      .thumb span {
        display: block;
        padding: 6px 8px;
        font-size: 11px;
        color: var(--muted);
      }

      pre {
        margin: 10px 0 0;
        padding: 10px;
        border-radius: 10px;
        background: #132038;
        color: #e7eefc;
        font-family: "JetBrains Mono", "SF Mono", "Menlo", monospace;
        font-size: 12px;
        overflow-x: auto;
      }

      details { margin: 0; }
      summary { cursor: pointer; color: var(--brand); font-weight: 600; }

      .muted { color: var(--muted); }

      .list-inline {
        margin: 8px 0 0;
        padding-left: 18px;
      }

      a {
        color: var(--brand);
        text-decoration: none;
      }

      a:hover { text-decoration: underline; }

      @media (max-width: 1060px) {
        .grid { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
        .meta-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      }

      @media (max-width: 720px) {
        .container { margin-top: 16px; }
        .hero { padding: 16px; border-radius: 14px; }
        .hero-top { flex-direction: column; align-items: flex-start; }
        .grid,
        .meta-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .value { font-size: 19px; }
      }

      @media (max-width: 520px) {
        .grid,
        .meta-grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <section class="hero">
        <div class="hero-top">
          <div>
            <p class="kicker">Reliability Toolkit</p>
            <h1 class="title">Run {{ run.run_id }}</h1>
            <p class="meta">{{ run.project }} execution report for deep reliability triage.</p>
          </div>
          <span class="badge {{ status_class(run.status) }}">{{ run.status }}</span>
        </div>
        <section class="meta-grid">
          <article class="meta-chip"><p class="label">Started</p><p class="value">{{ run.started_at }}</p></article>
          <article class="meta-chip"><p class="label">Ended</p><p class="value">{{ run.ended_at }}</p></article>
          <article class="meta-chip"><p class="label">Pytest</p><p class="value">{{ run.environment.pytest_version or "n/a" }}</p></article>
          <article class="meta-chip"><p class="label">Host</p><p class="value">{{ run.environment.host or "unknown" }}</p></article>
          <article class="meta-chip"><p class="label">Python</p><p class="value">{{ run.environment.python_version }}</p></article>
          <article class="meta-chip"><p class="label">Chaos Profile</p><p class="value">{{ run.chaos_profile or "none" }}</p></article>
        </section>
      </section>

      <section class="grid">
        <article class="card"><p class="label">Status</p><p class="value"><span class="badge {{ status_class(run.status) }}">{{ run.status }}</span></p></article>
        <article class="card"><p class="label">Pass Rate</p><p class="value">{{ metrics.pass_rate }}%</p></article>
        <article class="card"><p class="label">Duration</p><p class="value">{{ run.duration_ms }} ms</p></article>
        <article class="card"><p class="label">Failed Tests</p><p class="value">{{ metrics.totals.failed }}</p></article>
        <article class="card"><p class="label">Artifacts</p><p class="value">{{ metrics.total_artifacts }}</p></article>
        <article class="card"><p class="label">Chaos Events</p><p class="value">{{ metrics.chaos_events }}</p></article>
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Failures First</h2>
          <p class="small">Immediate triage for failed scenarios.</p>
        </div>
        {% if metrics.failed_tests %}
        <div class="failure-list">
          {% for t in metrics.failed_tests %}
          <article class="failure-card">
            <div class="failure-head">
              <p class="failure-name">{{ t.nodeid }}</p>
              <span class="badge bad">{{ t.failure_type }}</span>
            </div>
            <p class="failure-meta">Duration: {{ t.duration_ms }} ms | Chaos events: {{ t.chaos_events|length }}</p>
            {% if t.error_message %}
            <details open>
              <summary>Error details</summary>
              <pre>{{ t.error_message[:1500] }}</pre>
            </details>
            {% endif %}
            {% if t.artifacts %}
            {% set screenshots = t.artifacts | selectattr("kind", "equalto", "screenshot") | list %}
            {% if screenshots %}
            <div class="thumb-grid">
              {% for artifact in screenshots %}
              <a class="thumb" href="{{ artifact.path }}">
                <img src="{{ artifact.path }}" alt="Screenshot for {{ t.name }}" loading="lazy" />
                <span>{{ artifact.kind }}</span>
              </a>
              {% endfor %}
            </div>
            {% endif %}
            <ul class="list-inline">
              {% for artifact in t.artifacts %}
              <li><a href="{{ artifact.path }}">{{ artifact.kind }}</a></li>
              {% endfor %}
            </ul>
            {% endif %}
          </article>
          {% endfor %}
        </div>
        {% else %}
        <p class="small">No failed tests in this run.</p>
        {% endif %}
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Failure Distribution</h2>
          <p class="small">Grouped by classifier output.</p>
        </div>
        {% if metrics.failure_distribution %}
        <ul class="list-inline">
          {% for failure_type, count in metrics.failure_distribution.items() %}
          <li><span class="badge bad">{{ failure_type }}</span> {{ count }}</li>
          {% endfor %}
        </ul>
        {% else %}
        <p class="small">No failure categories in this run.</p>
        {% endif %}
      </section>

      <section class="section">
        <div class="section-head">
          <h2>Top Slow Tests</h2>
          <p class="small">Longest executions by duration.</p>
        </div>
        <div class="table-wrap">
        <table>
          <thead>
            <tr><th>NodeID</th><th>Status</th><th>Duration</th></tr>
          </thead>
          <tbody>
            {% for test in metrics.top_slowest %}
            <tr>
              <td>{{ test.nodeid }}</td>
              <td><span class="badge {{ status_class(test.status) }}">{{ test.status }}</span></td>
              <td>{{ test.duration_ms }} ms</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <h2>All Tests</h2>
          <p class="small">Expandable diagnostics, artifacts, and chaos events.</p>
        </div>
        <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>NodeID</th>
              <th>Status</th>
              <th>Failure Type</th>
              <th>Duration</th>
              <th>Error</th>
              <th>Artifacts</th>
              <th>Chaos Events</th>
            </tr>
          </thead>
          <tbody>
          {% for t in run.tests %}
            <tr>
              <td>{{ t.nodeid }}</td>
              <td><span class="badge {{ status_class(t.status) }}">{{ t.status }}</span></td>
              <td>{{ t.failure_type }}</td>
              <td>{{ t.duration_ms }} ms</td>
              <td>
                {% if t.error_message %}
                <details>
                  <summary>View error</summary>
                  <pre>{{ t.error_message[:1500] }}</pre>
                </details>
                {% else %}
                <span class="muted">-</span>
                {% endif %}
              </td>
              <td>
                {% if t.artifacts %}
                <ul class="list-inline">
                  {% for artifact in t.artifacts %}
                  <li><a href="{{ artifact.path }}">{{ artifact.kind }}</a></li>
                  {% endfor %}
                </ul>
                {% else %}
                <span class="muted">none</span>
                {% endif %}
              </td>
              <td>{{ t.chaos_events|length }}</td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
        </div>
      </section>
    </div>
  </body>
</html>
"""
)


def write_run_report(run: RunRecord, output_path: Path) -> None:
    metrics = build_run_metrics(run)
    html = RUN_TEMPLATE.render(run=run, metrics=metrics, status_class=_status_class)
    output_path.write_text(html, encoding="utf-8")
