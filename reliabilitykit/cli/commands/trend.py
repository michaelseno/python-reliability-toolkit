from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import typer

from reliabilitykit.core.config import load_config
from reliabilitykit.core.models import RunRecord
from reliabilitykit.reporting.html_dashboard import write_dashboard_report
from reliabilitykit.storage.local import LocalStorageBackend


def _write_trend_redirect(path: Path, target: str = "dashboard.html") -> None:
    html = f"""<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta http-equiv=\"refresh\" content=\"0; url={target}\" />
    <title>ReliabilityKit Trend</title>
  </head>
  <body>
    <p>Trend view is integrated into the unified dashboard. Open <a href=\"{target}\">{target}</a>.</p>
  </body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def trend_report(
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
    window_days: int | None = typer.Option(
        None,
        help="Trend lookback window in days (defaults to config.reporting.trend_default_window_days)",
    ),
) -> None:
    """Render integrated trend experience via unified dashboard.

    Trend analytics are now integrated into dashboard. This command still generates
    trend.html as a compatibility redirect to dashboard.html.

    Examples:
    - reliabilitykit trend
    - reliabilitykit trend --window-days 30
    """

    cfg = load_config(config)
    resolved_window_days = window_days or cfg.reporting.trend_default_window_days
    storage = LocalStorageBackend(Path(cfg.storage.local.path))

    cutoff = datetime.now(UTC) - timedelta(days=resolved_window_days)
    runs: list[RunRecord] = []
    for run_json_path in storage.list_runs():
        data = json.loads(run_json_path.read_text(encoding="utf-8"))
        run = RunRecord.model_validate(data)
        if run.started_at >= cutoff:
            runs.append(run)

    runs.sort(key=lambda r: r.started_at)
    dashboard_output = Path(cfg.storage.local.path) / "dashboard.html"
    write_dashboard_report(runs, dashboard_output)

    trend_output = Path(cfg.storage.local.path) / "trend.html"
    _write_trend_redirect(trend_output, target="dashboard.html")

    typer.echo(f"Dashboard generated: {dashboard_output}")
    typer.echo(f"Trend compatibility redirect generated: {trend_output}")
