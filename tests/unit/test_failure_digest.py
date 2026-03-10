from __future__ import annotations

from reliabilitykit.core.failure_digest import build_failure_digest


def test_build_failure_digest_extracts_timeout_headline_and_location() -> None:
    raw = """tests/e2e/tests/test_auth_negative.py:40:
tests/e2e/flows/auth_flows.py:14: in submit_forgot_and_assert_422
tests/e2e/pages/forgot_password_page.py:17: in submit_email
.venv/lib/python3.13/site-packages/playwright/_impl/_async_base.py:35: TimeoutError
playwright._impl._errors.TimeoutError: Timeout 30000ms exceeded while waiting for event \"response\"
"""

    digest, fingerprint = build_failure_digest(
        "tests/e2e/tests/test_auth_negative.py::test_forgot_password_returns_422_for_unknown_email[a@example.com]",
        "call",
        raw,
    )

    assert "Headline: TimeoutError: operation timed out after 30000ms" in digest
    assert "Phase: call" in digest
    assert "Location: tests/e2e/tests/test_auth_negative.py:40" in digest
    assert "Stack: tests/e2e/tests/test_auth_negative.py:40" in digest
    assert len(fingerprint) == 10
