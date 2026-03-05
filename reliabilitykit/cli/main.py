from __future__ import annotations

import typer

from reliabilitykit.cli.commands.inspect import inspect_runs
from reliabilitykit.cli.commands.report import report_run
from reliabilitykit.cli.commands.run import run_tests
from reliabilitykit.cli.commands.trend import trend_report

app = typer.Typer(help="ReliabilityKit CLI")

app.command("run")(run_tests)
app.command("inspect")(inspect_runs)
app.command("report")(report_run)
app.command("trend")(trend_report)


if __name__ == "__main__":
    app()
