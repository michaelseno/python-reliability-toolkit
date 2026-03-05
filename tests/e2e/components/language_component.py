from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class LanguageComponent:
    TOGGLE_SELECTOR = "[data-test='language-select']"

    def __init__(self, base_page: BasePage) -> None:
        self.base_page = base_page

    async def is_toggle_visible(self) -> bool:
        return await self.base_page.locator(self.TOGGLE_SELECTOR).first.is_visible()
