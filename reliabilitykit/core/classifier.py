from __future__ import annotations

from reliabilitykit.core.models import FailureType


def classify_failure(message: str | None) -> tuple[FailureType, float]:
    if not message:
        return "unknown", 0.0

    lower = message.lower()
    if "assertionerror" in lower or "assert " in lower or "assertion failed" in lower:
        return "assertion_failure", 0.9
    if "timeout" in lower and "selector" in lower:
        return "timeout_selector", 0.85
    if "timeout" in lower and "navigation" in lower:
        return "timeout_navigation", 0.85
    if "net::" in lower or "connection" in lower:
        return "network_error", 0.8
    if "500" in lower or "503" in lower:
        return "http_5xx", 0.75
    if "browser" in lower and "closed" in lower:
        return "browser_crash", 0.7
    if "module not found" in lower or "importerror" in lower:
        return "environment_error", 0.8
    return "unknown", 0.2
