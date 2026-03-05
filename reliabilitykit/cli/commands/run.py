from __future__ import annotations

from pathlib import Path

import typer

from reliabilitykit.core.config import load_config
from reliabilitykit.core.runner import execute_pytest_run


def run_tests(
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
    chaos: str | None = typer.Option(None, help="Chaos profile name"),
    seed: int | None = typer.Option(None, help="Chaos random seed"),
    browser: str = typer.Option("chromium", help="Browser label"),
    args: list[str] = typer.Argument(None, help="pytest args"),
) -> None:
    cfg = load_config(config)
    pytest_args = args or ["tests/e2e"]
    run = execute_pytest_run(
        config=cfg,
        pytest_args=pytest_args,
        chaos_profile=chaos,
        chaos_seed=seed,
        browser=browser,
    )
    run_dir = Path(cfg.storage.local.path) / "runs"
    typer.echo(f"Run complete: {run.run_id}")
    typer.echo(f"Status: {run.status} | Failed: {run.totals['failed']}")
    typer.echo(f"Output root: {run_dir}")
