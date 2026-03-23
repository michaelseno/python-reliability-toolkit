from __future__ import annotations

from tests.api_scenarios.helpers.models import EndpointTarget


BASELINE_HEALTH_TARGET = EndpointTarget(
    base_url="https://api.practicesoftwaretesting.com",
    endpoint="/products",
    method="GET",
    expected_status=200,
    timeout_ms=3000,
)

REPEATED_STABILITY_TARGET = EndpointTarget(
    base_url="https://api.practicesoftwaretesting.com",
    endpoint="/products",
    method="GET",
    expected_status=200,
    timeout_ms=3000,
)

BURST_STABILITY_TARGET = EndpointTarget(
    base_url="https://api.practicesoftwaretesting.com",
    endpoint="/products",
    method="GET",
    expected_status=200,
    timeout_ms=3000,
)

INVALID_PAYLOAD_TARGET = EndpointTarget(
    base_url="https://api.practicesoftwaretesting.com",
    endpoint="/messages",
    method="POST",
    headers={"Content-Type": "application/json"},
    payload={"subject": "", "message": ""},
    expected_status=422,
    timeout_ms=4000,
)

MISSING_FIELDS_TARGET = EndpointTarget(
    base_url="https://api.practicesoftwaretesting.com",
    endpoint="/messages",
    method="POST",
    headers={"Content-Type": "application/json"},
    payload={"message": "missing subject"},
    expected_status=422,
    timeout_ms=4000,
)

AUTH_FAILURE_TARGET = EndpointTarget(
    base_url="https://api.practicesoftwaretesting.com",
    endpoint="/users/login",
    method="POST",
    headers={"Content-Type": "application/json"},
    payload={"email": "invalid@example.com", "password": "wrongpass"},
    expected_status=401,
    timeout_ms=4000,
)

TIMEOUT_SENSITIVITY_TARGET = EndpointTarget(
    base_url="https://api.practicesoftwaretesting.com",
    endpoint="/products",
    method="GET",
    expected_status=200,
    timeout_ms=50,
)

RESPONSE_CONSISTENCY_TARGET = EndpointTarget(
    base_url="https://api.practicesoftwaretesting.com",
    endpoint="/products",
    method="GET",
    expected_status=200,
    timeout_ms=3000,
)
