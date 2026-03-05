from __future__ import annotations

from playwright.async_api import Response

from tests.e2e.pages.base_page import BasePage


class LoginPage(BasePage):
    EMAIL = "[data-test='email']"
    PASSWORD = "[data-test='password']"
    SUBMIT = "[data-test='login-submit']"

    async def open(self) -> None:
        await self.goto("/auth/login")

    async def submit_empty(self) -> None:
        await self.click(self.SUBMIT)

    async def submit_credentials(self, email: str, password: str) -> Response:
        await self.fill(self.EMAIL, email)
        await self.fill(self.PASSWORD, password)
        async with self.page.expect_response(
            lambda r: r.url.endswith("/users/login") and r.request.method == "POST"
        ) as response_info:
            await self.click(self.SUBMIT)
        return await response_info.value
