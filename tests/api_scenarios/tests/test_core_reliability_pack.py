from __future__ import annotations

import asyncio

import pytest
from playwright.async_api import APIRequestContext

from tests.api_scenarios.conftest import with_target_base_url
from tests.api_scenarios.data.targets import (
    AUTH_FAILURE_TARGET,
    BASELINE_HEALTH_TARGET,
    BURST_STABILITY_TARGET,
    INVALID_PAYLOAD_TARGET,
    MISSING_FIELDS_TARGET,
    REPEATED_STABILITY_TARGET,
    RESPONSE_CONSISTENCY_TARGET,
    TIMEOUT_SENSITIVITY_TARGET,
)
from tests.api_scenarios.helpers.api_client import ChaosRuntime, run_probe


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_baseline_health
async def test_baseline_health(api_context: APIRequestContext, target_base_url: str, chaos_runtime: ChaosRuntime | None) -> None:
    target = with_target_base_url(BASELINE_HEALTH_TARGET, target_base_url)
    probe = await run_probe(api_context, target, chaos_runtime=chaos_runtime)
    assert probe.status < 500


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_repeated_stability
async def test_repeated_stability(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(REPEATED_STABILITY_TARGET, target_base_url)
    probes = [await run_probe(api_context, target, chaos_runtime=chaos_runtime) for _ in range(5)]
    failures = [probe for probe in probes if probe.status >= 500]
    assert len(failures) <= 1


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_burst_stability
async def test_burst_stability(api_context: APIRequestContext, target_base_url: str, chaos_runtime: ChaosRuntime | None) -> None:
    target = with_target_base_url(BURST_STABILITY_TARGET, target_base_url)
    probes = await asyncio.gather(
        *[run_probe(api_context, target, chaos_runtime=chaos_runtime) for _ in range(8)]
    )
    failures = [probe for probe in probes if probe.status >= 500]
    assert len(failures) <= 2


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_invalid_payload_handling
async def test_invalid_payload_handling(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(INVALID_PAYLOAD_TARGET, target_base_url)
    probe = await run_probe(api_context, target, chaos_runtime=chaos_runtime)
    assert probe.status in {400, 401, 403, 422, 429, 500, 503}


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_missing_fields_validation
async def test_missing_fields_validation(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(MISSING_FIELDS_TARGET, target_base_url)
    probe = await run_probe(api_context, target, chaos_runtime=chaos_runtime)
    assert probe.status in {400, 401, 403, 422, 429, 500, 503}


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_auth_failure_handling
async def test_auth_failure_handling(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(AUTH_FAILURE_TARGET, target_base_url)
    probe = await run_probe(api_context, target, chaos_runtime=chaos_runtime)
    assert probe.status in {400, 401, 403, 429, 500, 503}


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_timeout_sensitivity
async def test_timeout_sensitivity(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(TIMEOUT_SENSITIVITY_TARGET, target_base_url)
    probe = await run_probe(api_context, target, chaos_runtime=chaos_runtime)
    assert probe.duration_ms >= 0
    assert probe.status in {200, 408, 429, 500, 503, 598, 599}


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_response_consistency
async def test_response_consistency(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(RESPONSE_CONSISTENCY_TARGET, target_base_url)
    probes = [await run_probe(api_context, target, chaos_runtime=chaos_runtime) for _ in range(3)]
    statuses = {probe.status for probe in probes}
    assert len(statuses) <= 2
