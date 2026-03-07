from __future__ import annotations

import json

import typer

from reliabilitykit.core.config import load_config


def list_chaos_profiles(
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON output"),
) -> None:
    """List available chaos profiles from configuration.

    Examples:
    - reliabilitykit chaos list
    - reliabilitykit chaos list --json
    - reliabilitykit chaos list --config reliabilitykit.yaml
    """

    cfg = load_config(config)
    profiles = cfg.chaos.profiles

    if not profiles:
        typer.echo("[]" if json_output else "No chaos profiles configured.")
        return

    rows = []
    for name in sorted(profiles):
        profile = profiles[name]
        rows.append(
            {
                "name": name,
                "mode": profile.mode,
                "probability": profile.probability,
                "seed": profile.seed,
                "targets": len(profile.targets),
            }
        )

    if json_output:
        typer.echo(json.dumps(rows, indent=2))
        return

    for row in rows:
        typer.echo(
            f"{row['name']} mode={row['mode']} probability={row['probability']} "
            f"seed={row['seed']} targets={row['targets']}"
        )


def show_chaos_profile(
    profile: str = typer.Argument(..., help="Chaos profile name"),
    config: str = typer.Option("reliabilitykit.yaml", help="Path to config file"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON output"),
) -> None:
    """Show full details for one chaos profile.

    Examples:
    - reliabilitykit chaos show latency_light
    - reliabilitykit chaos show checkout_fault --json
    """

    cfg = load_config(config)
    profiles = cfg.chaos.profiles
    if profile not in profiles:
        available = ", ".join(sorted(profiles.keys())) if profiles else "none"
        raise typer.BadParameter(
            f"Unknown chaos profile '{profile}'. Available profiles: {available}.",
            param_hint="profile",
        )

    item = profiles[profile]
    payload = {
        "name": profile,
        "mode": item.mode,
        "probability": item.probability,
        "seed": item.seed,
        "latency_ms": {"min": item.latency_ms.min, "max": item.latency_ms.max},
        "status_codes": item.status_codes,
        "targets": [target.model_dump(mode="json") for target in item.targets],
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2))
        return

    typer.echo(
        f"{payload['name']} mode={payload['mode']} probability={payload['probability']} "
        f"seed={payload['seed']} targets={len(payload['targets'])}"
    )
    typer.echo(
        f"latency_ms={payload['latency_ms']['min']}-{payload['latency_ms']['max']} "
        f"status_codes={payload['status_codes']}"
    )
    if not payload["targets"]:
        typer.echo("targets: none")
        return
    typer.echo("targets:")
    for index, target in enumerate(payload["targets"], start=1):
        typer.echo(
            f"  {index}. host={target.get('host') or '*'} pattern={target['url_pattern']} "
            f"methods={target['methods']} resource_types={target['resource_types']}"
        )
