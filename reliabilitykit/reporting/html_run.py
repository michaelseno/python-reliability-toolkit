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
    <title>ReliabilityKit Run {{ run.run_id }}</title>
    <style>
      :root {
        --bg: #f6f8fb;
        --card: #ffffff;
        --text: #1f2937;
        --muted: #64748b;
        --ok-bg: #dcfce7;
        --ok-text: #166534;
        --bad-bg: #fee2e2;
        --bad-text: #991b1b;
        --warn-bg: #fef3c7;
        --warn-text: #92400e;
        --border: #e5e7eb;
      }
      body {
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
      }
      .container { max-width: 1200px; margin: 24px auto; padding: 0 16px; }
      .hero { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
      .title { margin: 0 0 8px 0; }
      .meta { color: var(--muted); margin: 0; }
      .grid { display: grid; grid-template-columns: repeat(6, minmax(120px, 1fr)); gap: 12px; margin-top: 16px; }
      .card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 12px; }
      .label { margin: 0; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
      .value { margin: 6px 0 0 0; font-size: 20px; font-weight: 700; }
      .section { margin-top: 16px; background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border-bottom: 1px solid var(--border); text-align: left; padding: 8px; vertical-align: top; }
      th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
      .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }
      .ok { background: var(--ok-bg); color: var(--ok-text); }
      .bad { background: var(--bad-bg); color: var(--bad-text); }
      .warn { background: var(--warn-bg); color: var(--warn-text); }
      .muted { color: var(--muted); }
      details { margin: 0; }
      summary { cursor: pointer; color: var(--muted); }
      .list-inline { margin: 0; padding-left: 18px; }
    </style>
  </head>
  <body>
    <div class="container">
      <section class="hero">
        <h1 class="title">Run {{ run.run_id }}</h1>
        <p class="meta">Project: {{ run.project }} | Started: {{ run.started_at }} | Ended: {{ run.ended_at }}</p>
      </section>

      <section class="grid">
        <article class="card"><p class="label">Status</p><p class="value"><span class="badge {{ status_class(run.status) }}">{{ run.status }}</span></p></article>
        <article class="card"><p class="label">Pass Rate</p><p class="value">{{ metrics.pass_rate }}%</p></article>
        <article class="card"><p class="label">Duration</p><p class="value">{{ run.duration_ms }} ms</p></article>
        <article class="card"><p class="label">Failed Tests</p><p class="value">{{ metrics.totals.failed }}</p></article>
        <article class="card"><p class="label">Artifacts</p><p class="value">{{ metrics.total_artifacts }}</p></article>
        <article class="card"><p class="label">Chaos</p><p class="value">{{ run.chaos_profile or "none" }}</p></article>
      </section>

      <section class="section">
        <h2>Failure Distribution</h2>
        {% if metrics.failure_distribution %}
        <ul class="list-inline">
          {% for failure_type, count in metrics.failure_distribution.items() %}
          <li><span class="badge bad">{{ failure_type }}</span> {{ count }}</li>
          {% endfor %}
        </ul>
        {% else %}
        <p class="muted">No failures in this run.</p>
        {% endif %}
      </section>

      <section class="section">
        <h2>Top Slow Tests</h2>
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
      </section>

      <section class="section">
        <h2>Tests</h2>
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
                  <summary>view</summary>
                  <pre>{{ t.error_message[:500] }}</pre>
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
