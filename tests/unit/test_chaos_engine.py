from reliabilitykit.chaos.profiles import ChaosEngine
from reliabilitykit.core.config import ChaosProfileConfig, ChaosTarget


def _profile(mode: str) -> ChaosProfileConfig:
    return ChaosProfileConfig(
        mode=mode,
        probability=0.7,
        seed=42,
        status_codes=[500, 503],
        targets=[ChaosTarget(url_pattern="/checkout")],
    )


def test_chaos_engine_is_seeded_and_deterministic() -> None:
    profile = _profile("mixed")
    a = ChaosEngine("mixed", profile, seed=7)
    b = ChaosEngine("mixed", profile, seed=7)

    seq_a = [a.decide().action for _ in range(20)]
    seq_b = [b.decide().action for _ in range(20)]
    assert seq_a == seq_b


def test_chaos_engine_http5xx_returns_codes() -> None:
    profile = _profile("http_5xx")
    engine = ChaosEngine("http_5xx", profile, seed=1)

    seen_code = None
    for _ in range(50):
        decision = engine.decide()
        if decision.inject:
            seen_code = decision.status_code
            break

    assert seen_code in {500, 503}


def test_chaos_engine_http_status_supports_429() -> None:
    profile = ChaosProfileConfig(
        mode="http_status",
        probability=1.0,
        seed=42,
        status_codes=[429],
        targets=[ChaosTarget(url_pattern="/products")],
    )
    engine = ChaosEngine("http_status", profile, seed=1)

    decision = engine.decide()
    assert decision.inject is True
    assert decision.action == "fulfill"
    assert decision.status_code == 429


def test_chaos_engine_malformed_json_returns_invalid_json_payload() -> None:
    profile = ChaosProfileConfig(
        mode="malformed_json",
        probability=1.0,
        seed=42,
        status_codes=[200],
        targets=[ChaosTarget(url_pattern="/products")],
    )
    engine = ChaosEngine("malformed_json", profile, seed=1)

    decision = engine.decide()
    assert decision.inject is True
    assert decision.action == "fulfill"
    assert decision.status_code == 200
    assert decision.content_type == "application/json"
    assert decision.body is not None


def test_chaos_engine_timeout_hang_uses_profile_hang_ms() -> None:
    profile = ChaosProfileConfig(
        mode="timeout_hang",
        probability=1.0,
        seed=42,
        hang_ms=45000,
        targets=[ChaosTarget(url_pattern="/checkout")],
    )
    engine = ChaosEngine("timeout_hang", profile, seed=1)

    decision = engine.decide()
    assert decision.inject is True
    assert decision.action == "hang"
    assert decision.hang_ms == 45000
