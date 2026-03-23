from __future__ import annotations

import pytest
from playwright.async_api import Page

from tests.e2e.assertions.navigation_assertions import assert_home_fallback
from tests.e2e.data.route_data import HEADER_HREF_CASES, HOME_CORE_SELECTORS
from tests.e2e.flows.navigation_flows import assert_header_href
from tests.e2e.pages.home_page import HomePage


@pytest.mark.asyncio
@pytest.mark.legacy_ui
@pytest.mark.positive
@pytest.mark.parametrize(("selector", "expected_href"), HEADER_HREF_CASES)
async def test_header_links_have_expected_hrefs(selector: str, expected_href: str, page: Page) -> None:
    home_page = HomePage(page)
    await assert_header_href(home_page, selector, expected_href)


@pytest.mark.asyncio
@pytest.mark.legacy_ui
@pytest.mark.positive
@pytest.mark.parametrize("selector", HOME_CORE_SELECTORS)
async def test_home_core_controls_are_present(selector: str, page: Page) -> None:
    home_page = HomePage(page)
    await home_page.open()
    await home_page.expect_visible(selector)


@pytest.mark.asyncio
@pytest.mark.legacy_ui
@pytest.mark.edge
async def test_unknown_route_falls_back_to_home(page: Page) -> None:
    home_page = HomePage(page)
    await home_page.goto("/non-existent-route-for-rk")
    await assert_home_fallback(home_page)
