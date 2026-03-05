from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class ContactPage(BasePage):
    SUBMIT = "[data-test='contact-submit']"

    async def open(self) -> None:
        await self.goto("/contact")

    async def submit_empty(self) -> None:
        await self.click(self.SUBMIT)

    async def fill_optional_fields(self, first_name: str, last_name: str, email: str) -> None:
        await self.fill("[data-test='first-name']", first_name)
        await self.fill("[data-test='last-name']", last_name)
        await self.fill("[data-test='email']", email)
