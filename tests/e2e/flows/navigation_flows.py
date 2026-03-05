from __future__ import annotations

from tests.e2e.assertions.navigation_assertions import assert_notification_visible
from tests.e2e.pages.home_page import HomePage


async def open_and_assert_route(home_page: HomePage, path: str) -> None:
    await home_page.goto(path)
    await assert_notification_visible(home_page)


async def assert_header_href(home_page: HomePage, selector: str, expected_href: str) -> None:
    await home_page.open()
    href = await home_page.header.href(selector)
    assert href == expected_href
