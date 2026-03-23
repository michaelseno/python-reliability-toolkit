from __future__ import annotations

import importlib.util
from pathlib import Path

import typer

from reliabilitykit.core.scan_packs import resolve_scan_pack
from reliabilitykit.core.config import load_config
from reliabilitykit.core.runner import execute_pytest_run


def run_tests(
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
    chaos: str | None = typer.Option(None, help="Chaos profile name"),
    seed: int | None = typer.Option(None, help="Chaos random seed"),
    chaos_profile: str | None = typer.Option(None, "--chaos-profile", help="Chaos profile name alias"),
    chaos_seed: int | None = typer.Option(None, "--chaos-seed", help="Chaos random seed alias"),
    browser: str = typer.Option("chromium", help="Browser label"),
    surface: str = typer.Option("api", help="Execution surface: api or legacy_ui"),
    scan_pack: str = typer.Option("core_reliability_scan", help="Scenario pack ID for api surface"),
    workers: str | None = typer.Option(None, help="pytest-xdist workers, e.g. 'auto' or '4'"),
    repeat: int = typer.Option(1, min=1, help="Execute full run N times regardless of pass/fail"),
    args: list[str] = typer.Argument(None, help="pytest args"),
) -> None:
    """Execute pytest through ReliabilityKit capture pipeline.

    Persists run.json, per-test records, and index metadata under storage root.

    Examples:
    - reliabilitykit run --surface api --scan-pack core_reliability_scan
    - reliabilitykit run --workers auto -- tests/e2e -v
    - reliabilitykit run --chaos latency_light --seed 21 -- tests/e2e -m chaos
    - reliabilitykit run --repeat 5 -- tests/e2e -m smoke
    """

    cfg = load_config(config)
    resolved_chaos = chaos_profile or chaos
    resolved_seed = chaos_seed if chaos_seed is not None else seed
    available_chaos_profiles = sorted(cfg.chaos.profiles.keys())
    if resolved_chaos and resolved_chaos not in cfg.chaos.profiles:
        available = ", ".join(available_chaos_profiles) if available_chaos_profiles else "none"
        raise typer.BadParameter(
            f"Unknown chaos profile '{resolved_chaos}'. Available profiles: {available}. "
            "Use 'reliabilitykit chaos list' to inspect configured profiles.",
            param_hint="--chaos",
        )

    if surface not in {"api", "legacy_ui"}:
        raise typer.BadParameter("Surface must be one of: api, legacy_ui", param_hint="--surface")

    pytest_args = args or []

    has_marker_filter = "-m" in pytest_args
    has_target_path = any(not arg.startswith("-") for arg in pytest_args)
    pack = None
    if surface == "api":
        try:
            pack = resolve_scan_pack(scan_pack)
        except ValueError as exc:
            raise typer.BadParameter(str(exc), param_hint="--scan-pack") from exc

    if not has_target_path:
        pytest_args.append("tests/api_scenarios/tests" if surface == "api" else "tests/e2e/tests")

    if surface == "api" and not has_marker_filter:
        assert pack is not None
        pytest_args.extend(["-m", f"api_scenario and ({pack.marker_expression()})"])
    elif surface == "legacy_ui" and not has_marker_filter:
        pytest_args.extend(["-m", "legacy_ui"])

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
            chaos_profile=resolved_chaos,
            chaos_seed=resolved_seed,
            browser=browser,
            workers=resolved_workers,
            surface=surface,
            scan_pack=scan_pack if surface == "api" else None,
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
