from __future__ import annotations

from tests.e2e.assertions.form_assertions import assert_invalid_class
from tests.e2e.pages.contact_page import ContactPage


async def submit_empty_and_assert_required(contact_page: ContactPage, selector: str) -> None:
    await contact_page.submit_empty()
    class_name = await contact_page.class_name(selector)
    assert_invalid_class(class_name)
