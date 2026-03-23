from __future__ import annotations

import asyncio
from statistics import median

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


def _intent_class(chaos_runtime: ChaosRuntime | None) -> str:
    if not chaos_runtime:
        return "baseline"
    return chaos_runtime.profile.intent_class


def _error_rate(statuses: list[int], allowed_statuses: set[int]) -> float:
    if not statuses:
        return 1.0
    errors = sum(1 for status in statuses if status not in allowed_statuses)
    return errors / len(statuses)


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_baseline_health
async def test_baseline_health(api_context: APIRequestContext, target_base_url: str, chaos_runtime: ChaosRuntime | None) -> None:
    target = with_target_base_url(BASELINE_HEALTH_TARGET, target_base_url)
    probe = await run_probe(api_context, target, chaos_runtime=chaos_runtime)
    intent = _intent_class(chaos_runtime)

    if intent == "baseline":
        assert probe.status == target.expected_status
        assert probe.duration_ms <= target.timeout_ms
        return

    if intent == "resilience":
        assert probe.status in {target.expected_status, 429}
        assert probe.duration_ms <= target.timeout_ms + 1200
        return

    if intent == "fault":
        assert probe.status in {target.expected_status, 429, 503}
        assert probe.duration_ms <= target.timeout_ms + 1500
        return

    assert probe.status == target.expected_status


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_repeated_stability
async def test_repeated_stability(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(REPEATED_STABILITY_TARGET, target_base_url)
    probes = [await run_probe(api_context, target, chaos_runtime=chaos_runtime) for _ in range(10)]
    statuses = [probe.status for probe in probes]
    durations = [probe.duration_ms for probe in probes]
    intent = _intent_class(chaos_runtime)

    if intent == "baseline":
        assert _error_rate(statuses, {target.expected_status}) == 0.0
        assert max(durations) <= target.timeout_ms
        return

    if intent == "resilience":
        assert _error_rate(statuses, {target.expected_status, 429}) <= 0.10
        assert median(durations) <= target.timeout_ms + 1200
        return

    if intent == "fault":
        assert _error_rate(statuses, {target.expected_status, 429, 503}) <= 0.25
        assert median(durations) <= target.timeout_ms + 1500
        return

    assert _error_rate(statuses, {target.expected_status}) == 0.0


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_burst_stability
async def test_burst_stability(api_context: APIRequestContext, target_base_url: str, chaos_runtime: ChaosRuntime | None) -> None:
    target = with_target_base_url(BURST_STABILITY_TARGET, target_base_url)
    intent = _intent_class(chaos_runtime)
    batch_size = 20
    probes = await asyncio.gather(
        *[run_probe(api_context, target, chaos_runtime=chaos_runtime) for _ in range(batch_size)]
    )
    statuses = [probe.status for probe in probes]
    durations = [probe.duration_ms for probe in probes]

    if intent == "baseline":
        assert _error_rate(statuses, {target.expected_status}) <= 0.05
        assert median(durations) <= target.timeout_ms
        return

    if intent == "resilience":
        assert _error_rate(statuses, {target.expected_status, 429}) <= 0.15
        assert median(durations) <= target.timeout_ms + 1200
        return

    if intent == "fault":
        assert _error_rate(statuses, {target.expected_status, 429, 503}) <= 0.35
        assert median(durations) <= target.timeout_ms + 1500
        return

    assert _error_rate(statuses, {target.expected_status}) <= 0.05


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_invalid_payload_handling
async def test_invalid_payload_handling(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(INVALID_PAYLOAD_TARGET, target_base_url)
    intent = _intent_class(chaos_runtime)
    probe = await run_probe(api_context, target, chaos_runtime=chaos_runtime)

    if intent == "baseline":
        assert probe.status == target.expected_status
        return
    if intent in {"resilience", "fault"}:
        assert probe.status in {400, 422, 429}
        return

    assert probe.status == target.expected_status


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_missing_fields_validation
async def test_missing_fields_validation(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(MISSING_FIELDS_TARGET, target_base_url)
    intent = _intent_class(chaos_runtime)
    probe = await run_probe(api_context, target, chaos_runtime=chaos_runtime)

    if intent == "baseline":
        assert probe.status == target.expected_status
        return
    if intent in {"resilience", "fault"}:
        assert probe.status in {400, 422, 429}
        return

    assert probe.status == target.expected_status


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_auth_failure_handling
async def test_auth_failure_handling(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(AUTH_FAILURE_TARGET, target_base_url)
    intent = _intent_class(chaos_runtime)
    probe = await run_probe(api_context, target, chaos_runtime=chaos_runtime)

    if intent == "baseline":
        assert probe.status == target.expected_status
        return
    if intent in {"resilience", "fault"}:
        assert probe.status in {401, 403, 429}
        return

    assert probe.status == target.expected_status


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_timeout_sensitivity
async def test_timeout_sensitivity(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(TIMEOUT_SENSITIVITY_TARGET, target_base_url)
    intent = _intent_class(chaos_runtime)
    probes = [await run_probe(api_context, target, chaos_runtime=chaos_runtime) for _ in range(5)]
    statuses = [probe.status for probe in probes]
    timeout_like = sum(1 for status in statuses if status in {408, 598})

    if intent == "baseline":
        assert timeout_like >= 4
        assert all(status not in {500, 503, 599} for status in statuses)
        return

    if intent in {"resilience", "fault"}:
        assert timeout_like >= 3
        assert all(status not in {599} for status in statuses)
        return

    assert timeout_like >= 4


@pytest.mark.asyncio
@pytest.mark.api_scenario
@pytest.mark.scenario_response_consistency
async def test_response_consistency(
    api_context: APIRequestContext,
    target_base_url: str,
    chaos_runtime: ChaosRuntime | None,
) -> None:
    target = with_target_base_url(RESPONSE_CONSISTENCY_TARGET, target_base_url)
    intent = _intent_class(chaos_runtime)
    probes = [await run_probe(api_context, target, chaos_runtime=chaos_runtime) for _ in range(5)]
    statuses = {probe.status for probe in probes}

    if intent == "baseline":
        assert statuses == {target.expected_status}
        return

    if intent == "resilience":
        assert statuses.issubset({target.expected_status, 429})
        assert len(statuses) <= 2
        return

    if intent == "fault":
        assert statuses.issubset({target.expected_status, 429, 503})
        assert len(statuses) <= 3
        return

    assert statuses == {target.expected_status}
