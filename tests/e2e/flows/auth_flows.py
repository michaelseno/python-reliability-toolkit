from __future__ import annotations

from tests.e2e.assertions.form_assertions import assert_response_status
from tests.e2e.pages.forgot_password_page import ForgotPasswordPage
from tests.e2e.pages.login_page import LoginPage


async def submit_invalid_login_and_assert_401(login_page: LoginPage, email: str, password: str) -> None:
    response = await login_page.submit_credentials(email, password)
    assert_response_status(response, 401)


async def submit_forgot_and_assert_422(forgot_page: ForgotPasswordPage, email: str) -> None:
    response = await forgot_page.submit_email(email)
    assert_response_status(response, 422)
    await forgot_page.expect_invalid_email_message()
