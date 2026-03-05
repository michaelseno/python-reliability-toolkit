from __future__ import annotations

import asyncio

from playwright.async_api import BrowserContext, Route

from reliabilitykit.chaos.matcher import target_matches
from reliabilitykit.chaos.profiles import ChaosEngine
from reliabilitykit.core.config import ChaosProfileConfig


async def attach_chaos_routes(
    context: BrowserContext,
    profile_name: str,
    profile: ChaosProfileConfig,
    add_chaos_event,
    seed: int | None = None,
) -> None:
    engine = ChaosEngine(profile_name=profile_name, profile=profile, seed=seed)

    async def handler(route: Route) -> None:
        req = route.request
        resource_type = req.resource_type
        method = req.method.upper()
        url = req.url

        matched = any(target_matches(t, url=url, method=method, resource_type=resource_type) for t in profile.targets)
        if not matched:
            await route.continue_()
            return

        decision = engine.decide()
        add_chaos_event(profile_name, profile.mode, url, method, decision.action)

        if not decision.inject:
            await route.continue_()
            return
        if decision.action == "delay":
            await asyncio.sleep(max(decision.latency_ms, 0) / 1000)
            await route.continue_()
            return
        if decision.action == "fulfill":
            await route.fulfill(status=decision.status_code or 500, body="chaos injected")
            return
        if decision.action == "abort":
            await route.abort("failed")
            return

        await route.continue_()

    await context.route("**/*", handler)
