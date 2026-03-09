from reliabilitykit.core.classifier import classify_failure


def test_classifier_assertion() -> None:
    failure, confidence = classify_failure("AssertionError: expected foo")
    assert failure == "assertion_failure"
    assert confidence > 0.5


def test_classifier_unknown() -> None:
    failure, confidence = classify_failure("some unexpected text")
    assert failure == "unknown"
    assert confidence <= 0.2


def test_classifier_timeout_waiting_for_response_maps_to_network_error() -> None:
    failure, confidence = classify_failure('Timeout 30000ms exceeded while waiting for event "response"')
    assert failure == "network_error"
    assert confidence >= 0.8
