from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class NotificationComponent:
    SELECTOR = "[data-test='notification-bar']"

    def __init__(self, base_page: BasePage) -> None:
        self.base_page = base_page

    async def is_visible(self) -> bool:
        return await self.base_page.locator(self.SELECTOR).first.is_visible()
