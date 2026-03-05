from __future__ import annotations

from playwright.async_api import Response


def assert_invalid_class(class_name: str) -> None:
    assert "is-invalid" in class_name


def assert_response_status(response: Response, expected_status: int) -> None:
    assert response.status == expected_status
