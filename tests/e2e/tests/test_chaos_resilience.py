from __future__ import annotations

import pytest
from playwright.async_api import Page

from tests.e2e.pages.contact_page import ContactPage
from tests.e2e.pages.home_page import HomePage
from tests.e2e.pages.login_page import LoginPage


@pytest.mark.asyncio
@pytest.mark.legacy_ui
@pytest.mark.chaos(profile="latency_light", seed=21)
async def test_chaos_latency_still_shows_home_content(page: Page) -> None:
    home_page = HomePage(page)
    await home_page.open()
    await home_page.expect_visible("[data-test='search-query']")
    await home_page.expect_visible("[data-test='product-name']")


@pytest.mark.asyncio
@pytest.mark.legacy_ui
@pytest.mark.chaos(profile="checkout_fault", seed=7)
async def test_chaos_fault_still_shows_login_form(page: Page) -> None:
    login_page = LoginPage(page)
    await login_page.open()
    await login_page.expect_visible("[data-test='login-form']")
    await login_page.expect_visible("[data-test='email']")


@pytest.mark.asyncio
@pytest.mark.legacy_ui
@pytest.mark.chaos(profile="checkout_fault", seed=11)
async def test_chaos_fault_still_shows_contact_form(page: Page) -> None:
    contact_page = ContactPage(page)
    await contact_page.open()
    await contact_page.expect_visible("[data-test='contact-submit']")
    await contact_page.expect_visible("[data-test='message']")
