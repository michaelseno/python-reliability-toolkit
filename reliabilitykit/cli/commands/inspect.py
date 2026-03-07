from __future__ import annotations

import json
from pathlib import Path

import typer

from reliabilitykit.core.config import load_config
from reliabilitykit.core.models import RunRecord
from reliabilitykit.reporting.metrics import build_trend_metrics
from reliabilitykit.storage.local import LocalStorageBackend


def inspect_runs(
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
    last: int = typer.Option(20, help="Number of runs to show"),
    status: str | None = typer.Option(None, help="Filter by run status"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON output"),
) -> None:
    """Print compact run history from local index.

    Useful for quick triage and locating run IDs to drill into dashboard/report.

    Examples:
    - reliabilitykit inspect
    - reliabilitykit inspect --last 50
    - reliabilitykit inspect --status failed
    - reliabilitykit inspect --status failed --json
    """

    cfg = load_config(config)
    index_file = Path(cfg.storage.local.path) / "index" / "runs_index.jsonl"
    if not index_file.exists():
        typer.echo("[]" if json_output else "No runs indexed yet.")
        return

    rows = []
    for line in index_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))

    rows = list(reversed(rows))
    if status:
        rows = [row for row in rows if row.get("status") == status]
    rows = rows[:last]

    if json_output:
        storage = LocalStorageBackend(Path(cfg.storage.local.path))
        runs: list[RunRecord] = []
        run_json_paths: dict[str, str] = {}

        for row in rows:
            run_id = row["run_id"]
            run_path = storage.find_run(run_id)
            if run_path is None:
                continue
            run_json_paths[run_id] = str(run_path)
            run_data = json.loads(run_path.read_text(encoding="utf-8"))
            runs.append(RunRecord.model_validate(run_data))

        reliability_scores = {}
        if runs:
            metrics = build_trend_metrics(sorted(runs, key=lambda run: run.started_at))
            reliability_scores = {
                row["run_id"]: row.get("run_reliability_score") for row in metrics["series"]
            }

        payload = []
        for row in rows:
            run_id = row["run_id"]
            payload.append(
                {
                    **row,
                    "run_reliability_score": reliability_scores.get(run_id),
                    "run_json_path": run_json_paths.get(run_id),
                }
            )

        typer.echo(json.dumps(payload, indent=2))
        return

    for row in rows:
        typer.echo(
            f"{row['run_id']} status={row['status']} failed={row['failed']} "
            f"duration_ms={row['duration_ms']} chaos={row.get('chaos_profile') or 'none'}"
        )
