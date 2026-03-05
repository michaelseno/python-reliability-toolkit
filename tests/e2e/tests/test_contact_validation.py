from __future__ import annotations

import pytest
from playwright.async_api import Page, expect

from tests.e2e.data.contact_data import CONTACT_OPTIONAL_FIELDS, CONTACT_REQUIRED_FIELDS
from tests.e2e.flows.contact_flows import submit_empty_and_assert_required
from tests.e2e.pages.contact_page import ContactPage


@pytest.mark.asyncio
@pytest.mark.edge
@pytest.mark.parametrize("field_selector", CONTACT_REQUIRED_FIELDS)
async def test_contact_required_fields_mark_invalid(field_selector: str, page: Page) -> None:
    contact_page = ContactPage(page)
    await contact_page.open()
    await submit_empty_and_assert_required(contact_page, field_selector)


@pytest.mark.asyncio
@pytest.mark.positive
@pytest.mark.parametrize(("field_selector", "value"), CONTACT_OPTIONAL_FIELDS)
async def test_contact_optional_fields_accept_input(field_selector: str, value: str, page: Page) -> None:
    contact_page = ContactPage(page)
    await contact_page.open()
    await contact_page.fill(field_selector, value)
    await expect(contact_page.locator(field_selector)).to_have_value(value)
