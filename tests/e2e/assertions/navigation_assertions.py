from __future__ import annotations

from tests.e2e.pages.home_page import HomePage


async def assert_notification_visible(home_page: HomePage) -> None:
    assert await home_page.notification.is_visible()


async def assert_home_fallback(home_page: HomePage) -> None:
    assert home_page.page.url.startswith(home_page.base_url)
    assert await home_page.notification.is_visible()
