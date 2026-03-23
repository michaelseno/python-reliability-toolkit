from __future__ import annotations

import os

import pytest
from playwright.async_api import APIRequestContext, async_playwright

from reliabilitykit.core.config import load_config
from tests.api_scenarios.helpers.api_client import ChaosRuntime
from tests.api_scenarios.helpers.models import EndpointTarget


def _resolve_base_url(default_base_url: str) -> str:
    return os.getenv("RK_API_BASE_URL", default_base_url).rstrip("/")


@pytest.fixture
async def api_context() -> APIRequestContext:
    target_base_url = _resolve_base_url("https://api.practicesoftwaretesting.com")
    async with async_playwright() as p:
        context = await p.request.new_context(base_url=target_base_url)
        yield context
        await context.dispose()


@pytest.fixture
def chaos_runtime() -> ChaosRuntime | None:
    profile_name = os.getenv("RK_CHAOS_PROFILE")
    seed_raw = os.getenv("RK_CHAOS_SEED")
    if not profile_name:
        return None

    config = load_config()
    profile = config.chaos.profiles.get(profile_name)
    if not profile:
        return None

    from reliabilitykit.chaos.profiles import ChaosEngine

    return ChaosRuntime(
        profile_name=profile_name,
        profile=profile,
        engine=ChaosEngine(profile_name=profile_name, profile=profile, seed=int(seed_raw) if seed_raw else None),
    )


@pytest.fixture
def target_base_url() -> str:
    return _resolve_base_url("https://api.practicesoftwaretesting.com")


def with_target_base_url(target: EndpointTarget, base_url: str) -> EndpointTarget:
    return target.model_copy(update={"base_url": base_url})
