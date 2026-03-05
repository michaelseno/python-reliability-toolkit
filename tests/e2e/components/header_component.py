from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class HeaderComponent:
    def __init__(self, base_page: BasePage) -> None:
        self.base_page = base_page

    async def href(self, selector: str) -> str:
        value = await self.base_page.locator(selector).first.get_attribute("href")
        return value or ""
