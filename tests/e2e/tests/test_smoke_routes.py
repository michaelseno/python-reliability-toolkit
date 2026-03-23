from __future__ import annotations

import pytest
from playwright.async_api import Page

from tests.e2e.data.route_data import SMOKE_ROUTES
from tests.e2e.flows.navigation_flows import open_and_assert_route
from tests.e2e.pages.home_page import HomePage


@pytest.mark.asyncio
@pytest.mark.legacy_ui
@pytest.mark.smoke
@pytest.mark.parametrize("path", SMOKE_ROUTES)
async def test_page_smoke_loads(path: str, page: Page) -> None:
    home_page = HomePage(page)
    await open_and_assert_route(home_page, path)
