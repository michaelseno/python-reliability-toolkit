from __future__ import annotations

import typer

from reliabilitykit.cli.commands.chaos import list_chaos_profiles, show_chaos_profile
from reliabilitykit.cli.commands.dashboard import dashboard_report
from reliabilitykit.cli.commands.inspect import inspect_runs
from reliabilitykit.cli.commands.report import report_run
from reliabilitykit.cli.commands.run import run_tests
from reliabilitykit.cli.commands.trend import trend_report

app = typer.Typer(
    help=(
        "ReliabilityKit CLI for execution, inspection, and reliability reporting. "
        "Use the dashboard command for a unified historical + latest view."
    )
)
chaos_app = typer.Typer(help="Chaos profile discovery and utilities.")

app.command("run")(run_tests)
app.command("inspect")(inspect_runs)
app.command("report")(report_run)
app.command("trend")(trend_report)
app.command("dashboard")(dashboard_report)
chaos_app.command("list")(list_chaos_profiles)
chaos_app.command("show")(show_chaos_profile)
app.add_typer(chaos_app, name="chaos")


if __name__ == "__main__":
    app()
