from __future__ import annotations

import pytest
from playwright.async_api import Page

from tests.e2e.assertions.form_assertions import assert_invalid_class
from tests.e2e.data.register_data import REGISTER_REQUIRED_FIELDS
from tests.e2e.pages.register_page import RegisterPage


@pytest.mark.asyncio
@pytest.mark.edge
@pytest.mark.parametrize("field_selector", REGISTER_REQUIRED_FIELDS)
async def test_register_required_fields_mark_invalid(field_selector: str, page: Page) -> None:
    register_page = RegisterPage(page)
    await register_page.open()
    await register_page.submit_empty()
    class_name = await register_page.class_name(field_selector)
    assert_invalid_class(class_name)
