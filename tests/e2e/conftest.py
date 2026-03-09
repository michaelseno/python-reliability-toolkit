from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path

import pytest
from playwright.async_api import Browser, BrowserContext, Page, Route, async_playwright

from reliabilitykit.chaos.injector import attach_chaos_routes
from reliabilitykit.core.config import load_config


@pytest.fixture
def rk_context(request: pytest.FixtureRequest) -> dict:
    nodeid = request.node.nodeid

    def _context_file(run_dir: str) -> Path:
        key = hashlib.sha1(nodeid.encode("utf-8")).hexdigest()
        context_dir = Path(run_dir) / ".runtime_context"
        context_dir.mkdir(parents=True, exist_ok=True)
        return context_dir / f"{key}.jsonl"

    try:
        return request.getfixturevalue("rk_test_context")
    except pytest.FixtureLookupError:
        run_dir = os.getenv("RK_RUN_DIR", ".")

        def add_artifact(kind: str, path: str, size_bytes: int = 0, sha256: str | None = None) -> None:
            payload = {
                "type": "artifact",
                "kind": kind,
                "path": path,
                "size_bytes": size_bytes,
                "sha256": sha256,
            }
            with _context_file(run_dir).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")

        def add_chaos_event(profile: str, mode: str, url: str, method: str, action: str) -> None:
            payload = {
                "type": "chaos_event",
                "timestamp": datetime.now(UTC).isoformat(),
                "profile": profile,
                "mode": mode,
                "url": url,
                "method": method,
                "action": action,
            }
            with _context_file(run_dir).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")

        return {
            "run_dir": run_dir,
            "add_artifact": add_artifact,
            "add_chaos_event": add_chaos_event,
        }


@pytest.fixture
async def browser() -> AsyncIterator[Browser]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser: Browser, request: pytest.FixtureRequest, rk_context: dict) -> AsyncIterator[BrowserContext]:
    ctx = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
    )

    async def _drop_bot_challenge(route: Route) -> None:
        await route.abort()

    await ctx.route("**/cdn-cgi/challenge-platform/**", _drop_bot_challenge)
    await ctx.route("https://static.cloudflareinsights.com/**", _drop_bot_challenge)
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
        rk_context["add_artifact"]("screenshot", str(screenshot.relative_to(run_dir)))
    except Exception:
        pass
