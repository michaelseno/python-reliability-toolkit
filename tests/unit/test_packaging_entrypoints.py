from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_installed_cli_scripts_are_packaged() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    script_files = pyproject["tool"]["setuptools"]["script-files"]

    assert "scripts/reliabilitykit" in script_files
    assert "scripts/rk" in script_files


def test_installed_cli_scripts_dispatch_to_typer_app() -> None:
    for script_name in ("reliabilitykit", "rk"):
        script = ROOT / "scripts" / script_name
        script_text = script.read_text(encoding="utf-8")

        assert "from reliabilitykit.cli.main import app" in script_text
        assert "direct_url.json" in script_text
        assert "sys.exit(app())" in script_text
