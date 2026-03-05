from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import typer

from reliabilitykit.core.config import load_config
from reliabilitykit.core.models import RunRecord
from reliabilitykit.reporting.html_trend import write_trend_report
from reliabilitykit.storage.local import LocalStorageBackend


def trend_report(
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
    window_days: int = typer.Option(14, help="Trend lookback window in days"),
) -> None:
    cfg = load_config(config)
    storage = LocalStorageBackend(Path(cfg.storage.local.path))

    cutoff = datetime.now(UTC) - timedelta(days=window_days)
    runs: list[RunRecord] = []
    for run_json_path in storage.list_runs():
        data = json.loads(run_json_path.read_text(encoding="utf-8"))
        run = RunRecord.model_validate(data)
        if run.started_at >= cutoff:
            runs.append(run)

    runs.sort(key=lambda r: r.started_at)
    output = Path(cfg.storage.local.path) / "trend.html"
    write_trend_report(runs, output)
    typer.echo(f"Trend report generated: {output}")
