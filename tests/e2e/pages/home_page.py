from __future__ import annotations

from tests.e2e.components.header_component import HeaderComponent
from tests.e2e.components.language_component import LanguageComponent
from tests.e2e.components.notification_component import NotificationComponent
from tests.e2e.pages.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(self)
        self.language = LanguageComponent(self)
        self.notification = NotificationComponent(self)

    async def open(self) -> None:
        await self.goto("/")
