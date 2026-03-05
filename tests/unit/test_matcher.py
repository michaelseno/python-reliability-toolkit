from reliabilitykit.chaos.matcher import target_matches
from reliabilitykit.core.config import ChaosTarget


def test_target_matches_expected_url() -> None:
    target = ChaosTarget(
        host="www.saucedemo.com",
        url_pattern="/checkout",
        methods=["GET"],
        resource_types=["document"],
    )
    assert target_matches(target, "https://www.saucedemo.com/checkout-step-one.html", "GET", "document")


def test_target_rejects_wrong_resource_type() -> None:
    target = ChaosTarget(url_pattern="/inventory", methods=["GET"], resource_types=["xhr"])
    assert not target_matches(target, "https://www.saucedemo.com/inventory.html", "GET", "document")
