from __future__ import annotations

from playwright.async_api import Locator, Page, expect


class BasePage:
    def __init__(self, page: Page, base_url: str = "https://practicesoftwaretesting.com") -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    async def goto(self, path: str) -> None:
        await self.page.goto(f"{self.base_url}{path}", wait_until="domcontentloaded")

    def locator(self, selector: str) -> Locator:
        return self.page.locator(selector)

    async def click(self, selector: str) -> None:
        await self.locator(selector).click()

    async def fill(self, selector: str, value: str) -> None:
        await self.locator(selector).fill(value)

    async def class_name(self, selector: str) -> str:
        value = await self.locator(selector).get_attribute("class")
        return value or ""

    async def expect_visible(self, selector: str) -> None:
        await expect(self.locator(selector).first).to_be_visible()
