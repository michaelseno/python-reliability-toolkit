from __future__ import annotations

import pytest
from playwright.async_api import Page, expect


BASE_URL = "https://www.saucedemo.com/"
VALID_USER = "standard_user"
VALID_PASS = "secret_sauce"


async def login(page: Page, username: str, password: str) -> None:
    await page.goto(BASE_URL)
    await page.locator('[data-test="username"]').fill(username)
    await page.locator('[data-test="password"]').fill(password)
    await page.locator('[data-test="login-button"]').click()


@pytest.mark.asyncio
async def test_positive_checkout_success(page: Page) -> None:
    await login(page, VALID_USER, VALID_PASS)
    await expect(page).to_have_url("https://www.saucedemo.com/inventory.html")
    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click()
    await page.locator('[data-test="shopping-cart-link"]').click()
    await page.locator('[data-test="checkout"]').click()
    await page.locator('[data-test="firstName"]').fill("John")
    await page.locator('[data-test="lastName"]').fill("Doe")
    await page.locator('[data-test="postalCode"]').fill("90210")
    await page.locator('[data-test="continue"]').click()
    await page.locator('[data-test="finish"]').click()
    await expect(page.locator('[data-test="complete-header"]')).to_have_text("Thank you for your order!")


@pytest.mark.asyncio
async def test_negative_invalid_login(page: Page) -> None:
    await login(page, "locked_out_user", "wrong_password")
    await expect(page.locator('[data-test="error"]')).to_contain_text("Username and password do not match")


@pytest.mark.asyncio
async def test_edge_cart_persists_during_navigation(page: Page) -> None:
    await login(page, VALID_USER, VALID_PASS)
    await page.locator('[data-test="add-to-cart-sauce-labs-bike-light"]').click()
    await page.locator('[data-test="shopping-cart-link"]').click()
    await expect(page.locator('[data-test="inventory-item"]')).to_have_count(1)
    await page.go_back()
    await page.go_forward()
    await expect(page.locator('[data-test="inventory-item"]')).to_have_count(1)


@pytest.mark.asyncio
@pytest.mark.chaos(profile="latency_light", seed=21)
async def test_chaos_latency_inventory_cart_flow(page: Page) -> None:
    await login(page, VALID_USER, VALID_PASS)
    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click()
    await page.locator('[data-test="shopping-cart-link"]').click()
    await expect(page.locator('[data-test="inventory-item"]')).to_have_count(1)


@pytest.mark.asyncio
@pytest.mark.chaos(profile="checkout_fault", seed=7)
async def test_chaos_fault_checkout_failure_signal(page: Page) -> None:
    await login(page, VALID_USER, VALID_PASS)
    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click()
    await page.locator('[data-test="shopping-cart-link"]').click()
    await page.locator('[data-test="checkout"]').click()
    await page.locator('[data-test="firstName"]').fill("Jane")
    await page.locator('[data-test="lastName"]').fill("Roe")
    await page.locator('[data-test="postalCode"]').fill("10001")
    await page.locator('[data-test="continue"]').click()
    await expect(page).to_have_url("https://www.saucedemo.com/checkout-step-two.html")
