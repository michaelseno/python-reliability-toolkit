from __future__ import annotations

import pytest
from playwright.async_api import Page

from tests.e2e.assertions.form_assertions import assert_invalid_class
from tests.e2e.data.auth_data import FORGOT_EMAIL_CASES, INVALID_LOGIN_CASES
from tests.e2e.flows.auth_flows import submit_forgot_and_assert_422, submit_invalid_login_and_assert_401
from tests.e2e.pages.forgot_password_page import ForgotPasswordPage
from tests.e2e.pages.login_page import LoginPage


@pytest.mark.asyncio
@pytest.mark.negative
@pytest.mark.parametrize("field_selector", ["[data-test='email']", "[data-test='password']"])
async def test_login_required_fields_mark_invalid(field_selector: str, page: Page) -> None:
    login_page = LoginPage(page)
    await login_page.open()
    await login_page.submit_empty()
    class_name = await login_page.class_name(field_selector)
    assert_invalid_class(class_name)


@pytest.mark.asyncio
@pytest.mark.negative
@pytest.mark.parametrize(("email", "password"), INVALID_LOGIN_CASES)
async def test_login_invalid_credentials_return_401(email: str, password: str, page: Page) -> None:
    login_page = LoginPage(page)
    await login_page.open()
    await submit_invalid_login_and_assert_401(login_page, email, password)
    assert "/auth/login" in page.url


@pytest.mark.asyncio
@pytest.mark.negative
@pytest.mark.parametrize("email", FORGOT_EMAIL_CASES)
async def test_forgot_password_returns_422_for_unknown_email(email: str, page: Page) -> None:
    forgot_page = ForgotPasswordPage(page)
    await forgot_page.open()
    await submit_forgot_and_assert_422(forgot_page, email)
