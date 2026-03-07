from __future__ import annotations

import importlib.util
from pathlib import Path

import typer

from reliabilitykit.core.config import load_config
from reliabilitykit.core.runner import execute_pytest_run


def run_tests(
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
    chaos: str | None = typer.Option(None, help="Chaos profile name"),
    seed: int | None = typer.Option(None, help="Chaos random seed"),
    browser: str = typer.Option("chromium", help="Browser label"),
    workers: str | None = typer.Option(None, help="pytest-xdist workers, e.g. 'auto' or '4'"),
    repeat: int = typer.Option(1, min=1, help="Execute full run N times regardless of pass/fail"),
    args: list[str] = typer.Argument(None, help="pytest args"),
) -> None:
    """Execute pytest through ReliabilityKit capture pipeline.

    Persists run.json, per-test records, and index metadata under storage root.

    Examples:
    - reliabilitykit run -- tests/e2e
    - reliabilitykit run --workers auto -- tests/e2e -v
    - reliabilitykit run --chaos latency_light --seed 21 -- tests/e2e -m chaos
    - reliabilitykit run --repeat 5 -- tests/e2e -m smoke
    """

    cfg = load_config(config)
    available_chaos_profiles = sorted(cfg.chaos.profiles.keys())
    if chaos and chaos not in cfg.chaos.profiles:
        available = ", ".join(available_chaos_profiles) if available_chaos_profiles else "none"
        raise typer.BadParameter(
            f"Unknown chaos profile '{chaos}'. Available profiles: {available}. "
            "Use 'reliabilitykit chaos list' to inspect configured profiles.",
            param_hint="--chaos",
        )

    pytest_args = args or ["tests/e2e"]
    resolved_workers = workers
    if workers and importlib.util.find_spec("xdist") is None:
        typer.echo("pytest-xdist is not installed; falling back to serial execution.")
        resolved_workers = None

    run_dir = Path(cfg.storage.local.path) / "runs"
    runs = []
    for attempt in range(1, repeat + 1):
        typer.echo(f"Starting run {attempt}/{repeat}...")
        run = execute_pytest_run(
            config=cfg,
            pytest_args=pytest_args,
            chaos_profile=chaos,
            chaos_seed=seed,
            browser=browser,
            workers=resolved_workers,
        )
        runs.append(run)
        typer.echo(f"Run complete: {run.run_id}")
        typer.echo(f"Status: {run.status} | Failed: {run.totals['failed']}")
        typer.echo(f"Output root: {run_dir}")

    failed_runs = sum(1 for run in runs if run.status != "passed")
    if repeat > 1:
        typer.echo(f"Completed {repeat} runs: passed={repeat - failed_runs} failed={failed_runs}")

    if failed_runs:
        raise typer.Exit(code=1)
