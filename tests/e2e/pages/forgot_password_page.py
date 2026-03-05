from __future__ import annotations

from playwright.async_api import Response, expect

from tests.e2e.pages.base_page import BasePage


class ForgotPasswordPage(BasePage):
    EMAIL = "[data-test='email']"
    SUBMIT = "[data-test='forgot-password-submit']"

    async def open(self) -> None:
        await self.goto("/auth/forgot-password")

    async def submit_email(self, email: str) -> Response:
        await self.fill(self.EMAIL, email)
        async with self.page.expect_response(
            lambda r: r.url.endswith("/users/forgot-password") and r.request.method == "POST"
        ) as response_info:
            await self.click(self.SUBMIT)
        return await response_info.value

    async def expect_invalid_email_message(self) -> None:
        await expect(self.page.get_by_text("The selected email is invalid.")).to_be_visible()
