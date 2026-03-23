from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter

from playwright.async_api import APIRequestContext

from reliabilitykit.chaos.profiles import ChaosEngine
from reliabilitykit.core.config import ChaosProfileConfig
from tests.api_scenarios.helpers.models import EndpointTarget


@dataclass
class ChaosRuntime:
    profile_name: str
    profile: ChaosProfileConfig
    engine: ChaosEngine


@dataclass
class ProbeResponse:
    status: int
    duration_ms: int
    body: str
    chaos_action: str


async def run_probe(
    api_context: APIRequestContext,
    target: EndpointTarget,
    chaos_runtime: ChaosRuntime | None = None,
) -> ProbeResponse:
    started = perf_counter()
    action = "pass"

    if chaos_runtime:
        decision = chaos_runtime.engine.decide()
        action = decision.action

        if decision.inject and action == "delay":
            await asyncio.sleep(max(decision.latency_ms, 0) / 1000)
        elif decision.inject and action == "hang":
            await asyncio.sleep(max(decision.hang_ms, target.timeout_ms + 100) / 1000)
            elapsed = int((perf_counter() - started) * 1000)
            return ProbeResponse(status=598, duration_ms=elapsed, body="chaos hang", chaos_action=action)
        elif decision.inject and action == "abort":
            elapsed = int((perf_counter() - started) * 1000)
            return ProbeResponse(status=599, duration_ms=elapsed, body="chaos abort", chaos_action=action)
        elif decision.inject and action == "fulfill":
            elapsed = int((perf_counter() - started) * 1000)
            return ProbeResponse(
                status=decision.status_code or 500,
                duration_ms=elapsed,
                body=decision.body or "chaos injected",
                chaos_action=action,
            )

    try:
        response = await api_context.fetch(
            target.endpoint,
            method=target.method.upper(),
            headers=target.headers,
            data=target.payload,
            timeout=target.timeout_ms,
        )
        elapsed = int((perf_counter() - started) * 1000)
        return ProbeResponse(
            status=response.status,
            duration_ms=elapsed,
            body=await response.text(),
            chaos_action=action,
        )
    except Exception as exc:
        elapsed = int((perf_counter() - started) * 1000)
        return ProbeResponse(status=408, duration_ms=elapsed, body=str(exc), chaos_action=action)
