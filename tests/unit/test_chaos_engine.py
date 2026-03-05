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
