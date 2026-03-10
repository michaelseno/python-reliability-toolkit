from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re

import pytest
from playwright.async_api import Browser, BrowserContext, Page, Route, async_playwright

from reliabilitykit.chaos.injector import attach_chaos_routes
from reliabilitykit.core.config import load_config


def _safe_name(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return sanitized[:160] if sanitized else hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def _compact_entries(entries: list[dict], limit: int) -> list[dict]:
    deduped: list[dict] = []
    counts: dict[str, int] = {}
    for entry in entries:
        compact_key = json.dumps(
            {
                "kind": entry.get("kind"),
                "level": entry.get("level"),
                "message": entry.get("message"),
                "url": entry.get("url"),
                "method": entry.get("method"),
                "error": entry.get("error"),
            },
            sort_keys=True,
        )
        counts[compact_key] = counts.get(compact_key, 0) + 1
        if counts[compact_key] == 1:
            deduped.append(entry)

    if len(deduped) <= limit:
        return deduped

    dropped = len(deduped) - limit
    trimmed = deduped[-limit:]
    return [
        {
            "kind": "meta",
            "timestamp": datetime.now(UTC).isoformat(),
            "message": f"log stream trimmed to tail {limit} records",
            "dropped_count": dropped,
        },
        *trimmed,
    ]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


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
    capture_cfg = load_config().capture

    console_entries: list[dict] = []
    event_entries: list[dict] = []

    def on_console(msg) -> None:
        console_entries.append(
            {
                "kind": "console",
                "timestamp": datetime.now(UTC).isoformat(),
                "level": msg.type,
                "message": msg.text,
                "location": msg.location,
            }
        )

    def on_page_error(exc) -> None:
        event_entries.append(
            {
                "kind": "pageerror",
                "timestamp": datetime.now(UTC).isoformat(),
                "message": str(exc),
            }
        )

    def on_request_failed(req) -> None:
        failure_text = ""
        failure_value = req.failure
        if isinstance(failure_value, dict):
            failure_text = str(failure_value.get("errorText") or "")
        elif failure_value:
            failure_text = str(failure_value)
        event_entries.append(
            {
                "kind": "requestfailed",
                "timestamp": datetime.now(UTC).isoformat(),
                "method": req.method,
                "url": req.url,
                "error": failure_text,
            }
        )

    if capture_cfg.logs:
        page.on("console", on_console)
        page.on("pageerror", on_page_error)
        page.on("requestfailed", on_request_failed)

    trace_started = False
    if capture_cfg.trace:
        await page.context.tracing.start(screenshots=True, snapshots=True)
        trace_started = True

    yield
    run_dir = Path(rk_context["run_dir"])
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    safe = _safe_name(request.node.nodeid)

    if capture_cfg.logs:
        compact_console = _compact_entries(console_entries, limit=200)
        compact_events = _compact_entries(event_entries, limit=200)

        if compact_console:
            console_path = artifacts_dir / f"{safe}.console.jsonl"
            console_path.write_text(
                "\n".join(json.dumps(entry, sort_keys=True) for entry in compact_console) + "\n",
                encoding="utf-8",
            )
            rk_context["add_artifact"](
                "console_log",
                str(console_path.relative_to(run_dir)),
                size_bytes=console_path.stat().st_size,
            )

        if compact_events:
            events_path = artifacts_dir / f"{safe}.events.jsonl"
            events_path.write_text(
                "\n".join(json.dumps(entry, sort_keys=True) for entry in compact_events) + "\n",
                encoding="utf-8",
            )
            rk_context["add_artifact"](
                "event_log",
                str(events_path.relative_to(run_dir)),
                size_bytes=events_path.stat().st_size,
            )

    screenshot = artifacts_dir / f"{safe}.png"
    try:
        if capture_cfg.screenshot:
            await page.screenshot(path=str(screenshot), full_page=True)
            rk_context["add_artifact"](
                "screenshot",
                str(screenshot.relative_to(run_dir)),
                size_bytes=screenshot.stat().st_size,
            )
    except Exception:
        pass

    call_report = getattr(request.node, "rep_call", None)
    failed = bool(call_report and call_report.failed)
    if trace_started:
        try:
            if failed:
                trace_path = artifacts_dir / f"{safe}.trace.zip"
                await page.context.tracing.stop(path=str(trace_path))
                rk_context["add_artifact"](
                    "trace",
                    str(trace_path.relative_to(run_dir)),
                    size_bytes=trace_path.stat().st_size,
                )
            else:
                await page.context.tracing.stop()
        except Exception:
            pass
