from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
import webbrowser

import typer

from reliabilitykit.core.config import load_config
from reliabilitykit.core.models import RunRecord
from reliabilitykit.reporting.html_dashboard import write_dashboard_report
from reliabilitykit.storage.local import LocalStorageBackend


def dashboard_report(
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
    window_days: int | None = typer.Option(
        None,
        help="Trend lookback window in days (defaults to config.reporting.trend_default_window_days)",
    ),
    output: str | None = typer.Option(None, help="Output HTML path (defaults to <storage>/dashboard.html)"),
    open_browser: bool = typer.Option(False, "--open", help="Open the generated dashboard in browser"),
) -> None:
    """Generate unified reliability dashboard.

    Includes latest run triage, historical trends, chaos-vs-baseline split,
    and on-demand loading of run.json details from the run history table.

    Examples:
    - reliabilitykit dashboard
    - reliabilitykit dashboard --window-days 30
    - reliabilitykit dashboard --open
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

    if output:
        output_path = Path(output)
    else:
        output_path = Path(cfg.storage.local.path) / "dashboard.html"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_dashboard_report(runs, output_path)
    typer.echo(f"Dashboard generated: {output_path}")

    if open_browser:
        webbrowser.open(output_path.resolve().as_uri())
        typer.echo("Opened dashboard in browser.")
