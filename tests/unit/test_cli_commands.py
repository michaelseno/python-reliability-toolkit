from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from reliabilitykit.cli.main import app


runner = CliRunner()


def _config_with_chaos(path: Path) -> None:
    path.write_text(
        """
project:
  name: reliability-toolkit
chaos:
  profiles:
    latency_light:
      mode: latency
      intent_class: resilience
      probability: 0.3
      seed: 21
      latency_ms:
        min: 200
        max: 500
      targets:
        - host: api.example.com
          url_pattern: /products
          methods: [GET]
          resource_types: [xhr, fetch]
    checkout_fault:
      mode: mixed
      intent_class: fault
      probability: 0.4
      seed: 7
      status_codes: [500, 503]
      targets:
        - host: api.example.com
          url_pattern: /users
          methods: [GET, POST]
          resource_types: [xhr, fetch]
""".strip(),
        encoding="utf-8",
    )


def test_chaos_list_shows_profiles(tmp_path: Path) -> None:
    config_path = tmp_path / "reliabilitykit.yaml"
    _config_with_chaos(config_path)

    result = runner.invoke(app, ["chaos", "list", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "latency_light" in result.output
    assert "checkout_fault" in result.output
    assert "fault_injection=resilience" in result.output
    assert "mode=latency" in result.output


def test_run_rejects_unknown_chaos_profile(tmp_path: Path) -> None:
    config_path = tmp_path / "reliabilitykit.yaml"
    _config_with_chaos(config_path)

    result = runner.invoke(
        app,
        ["run", "--config", str(config_path), "--chaos", "missing_profile", "--", "tests/unit/test_classifier.py"],
    )

    assert result.exit_code != 0
    assert "Unknown chaos profile 'missing_profile'" in result.output
    assert "latency_light" in result.output


def test_chaos_show_outputs_profile_details(tmp_path: Path) -> None:
    config_path = tmp_path / "reliabilitykit.yaml"
    _config_with_chaos(config_path)

    result = runner.invoke(app, ["chaos", "show", "latency_light", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "latency_light fault_injection=resilience mode=latency" in result.output
    assert "targets:" in result.output
    assert "pattern=/products" in result.output


def test_chaos_show_rejects_unknown_profile(tmp_path: Path) -> None:
    config_path = tmp_path / "reliabilitykit.yaml"
    _config_with_chaos(config_path)

    result = runner.invoke(app, ["chaos", "show", "unknown_profile", "--config", str(config_path)])

    assert result.exit_code != 0
    assert "Unknown chaos profile 'unknown_profile'" in result.output
    assert "checkout_fault" in result.output
