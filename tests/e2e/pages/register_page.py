from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class RegisterPage(BasePage):
    SUBMIT = "[data-test='register-submit']"

    async def open(self) -> None:
        await self.goto("/auth/register")

    async def submit_empty(self) -> None:
        await self.click(self.SUBMIT)
