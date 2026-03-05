from __future__ import annotations

from collections.abc import AsyncIterator
import os
from pathlib import Path

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from reliabilitykit.chaos.injector import attach_chaos_routes
from reliabilitykit.core.config import load_config


@pytest.fixture
def rk_context(request: pytest.FixtureRequest) -> dict:
    try:
        return request.getfixturevalue("rk_test_context")
    except pytest.FixtureLookupError:
        return {
            "run_dir": ".",
            "add_artifact": lambda *args, **kwargs: None,
            "add_chaos_event": lambda *args, **kwargs: None,
        }


@pytest.fixture
async def browser() -> AsyncIterator[Browser]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser: Browser, request: pytest.FixtureRequest, rk_context: dict) -> AsyncIterator[BrowserContext]:
    ctx = await browser.new_context()
    marker = request.node.get_closest_marker("chaos")
    env_profile = os.getenv("RK_CHAOS_PROFILE")
    env_seed = os.getenv("RK_CHAOS_SEED")

    profile_name = None
    seed = None
    if marker:
        profile_name = marker.kwargs.get("profile")
        seed = marker.kwargs.get("seed")
    elif env_profile:
        profile_name = env_profile
        seed = int(env_seed) if env_seed else None

    if profile_name:
        config = load_config()
        profile = config.chaos.profiles[profile_name]
        await attach_chaos_routes(
            context=ctx,
            profile_name=profile_name,
            profile=profile,
            add_chaos_event=rk_context["add_chaos_event"],
            seed=seed,
        )
    yield ctx
    await ctx.close()


@pytest.fixture
async def page(context: BrowserContext) -> AsyncIterator[Page]:
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture(autouse=True)
async def capture_page_artifact(
    request: pytest.FixtureRequest,
    page: Page,
    rk_context: dict,
) -> AsyncIterator[None]:
    yield
    run_dir = Path(rk_context["run_dir"])
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    safe = request.node.nodeid.replace("/", "_").replace("::", "__")
    screenshot = artifacts_dir / f"{safe}.png"
    try:
        await page.screenshot(path=str(screenshot), full_page=True)
        rk_context["add_artifact"]("screenshot", str(screenshot))
    except Exception:
        pass
