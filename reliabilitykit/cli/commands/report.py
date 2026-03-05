from __future__ import annotations

import json
from pathlib import Path

import typer

from reliabilitykit.core.config import load_config
from reliabilitykit.core.models import RunRecord
from reliabilitykit.reporting.html_run import write_run_report
from reliabilitykit.storage.local import LocalStorageBackend


def report_run(
    run_id: str = typer.Option(..., help="Run ID to render"),
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
) -> None:
    cfg = load_config(config)
    storage = LocalStorageBackend(Path(cfg.storage.local.path))
    run_path = storage.find_run(run_id)
    if run_path is None:
        raise typer.BadParameter(f"Run not found: {run_id}")

    run = RunRecord.model_validate(json.loads(run_path.read_text(encoding="utf-8")))
    output_path = run_path.parent / "report.html"
    write_run_report(run, output_path)
    typer.echo(f"Run report generated: {output_path}")
