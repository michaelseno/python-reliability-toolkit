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
        max-width: 1240px;
        margin: 0 auto;
        padding: 22px;
      }

      .hero {
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.05));
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
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
        background: var(--panel2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 10px;
      }

      .meta-chip .label,
      .label {
        margin: 0;
        color: var(--muted);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
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
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 12px;
      }

      .value {
        margin: 7px 0 0;
        font-size: 22px;
        font-weight: 700;
      }

      .section {
        margin-top: 16px;
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px;
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

      .small { margin: 0; color: var(--muted); font-size: 13px; }

      table { width: 100%; border-collapse: separate; border-spacing: 0; }

      th,
      td {
        border-bottom: 1px solid rgba(255, 255, 255, 0.10);
        text-align: left;
        padding: 10px 8px;
        vertical-align: top;
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

      .table-wrap {
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid var(--border);
      }

      .badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        border: 1px solid var(--border);
      }

      .ok { color: var(--green); }
      .bad { color: var(--red); }
      .warn { color: var(--amber); }

      .failure-list {
        display: grid;
        gap: 12px;
      }

      .failure-card {
        border: 1px solid rgba(255, 77, 109, 0.45);
        border-left: 4px solid var(--red);
        border-radius: 12px;
        padding: 12px;
        background: rgba(255, 77, 109, 0.08);
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
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
        background: rgba(255, 255, 255, 0.04);
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
        background: rgba(0, 0, 0, 0.25);
        color: #e7eefc;
        font-family: "JetBrains Mono", "SF Mono", "Menlo", monospace;
        font-size: 12px;
        overflow-x: auto;
        border: 1px solid rgba(255, 255, 255, 0.12);
      }

      details { margin: 0; }
      summary { cursor: pointer; color: var(--blue); font-weight: 600; }

      .muted { color: var(--muted); }

      .list-inline {
        margin: 8px 0 0;
        padding-left: 18px;
      }

      a {
        color: var(--blue);
        text-decoration: none;
      }

      a:hover { text-decoration: underline; }

      @media (max-width: 1060px) {
        .grid { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
        .meta-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      }

      @media (max-width: 720px) {
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
