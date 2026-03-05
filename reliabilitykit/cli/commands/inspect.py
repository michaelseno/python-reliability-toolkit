from __future__ import annotations

import json
from pathlib import Path

import typer

from reliabilitykit.core.config import load_config


def inspect_runs(
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
    last: int = typer.Option(20, help="Number of runs to show"),
    status: str | None = typer.Option(None, help="Filter by run status"),
) -> None:
    cfg = load_config(config)
    index_file = Path(cfg.storage.local.path) / "index" / "runs_index.jsonl"
    if not index_file.exists():
        typer.echo("No runs indexed yet.")
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

    for row in rows:
        typer.echo(
            f"{row['run_id']} status={row['status']} failed={row['failed']} "
            f"duration_ms={row['duration_ms']} chaos={row.get('chaos_profile') or 'none'}"
        )
