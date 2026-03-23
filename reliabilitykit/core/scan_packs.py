from __future__ import annotations

from pydantic import BaseModel, Field

from reliabilitykit.core.scenario_registry import get_scenario


class ScanPack(BaseModel):
    pack_id: str
    name: str
    description: str
    scenario_ids: list[str] = Field(default_factory=list)

    def marker_expression(self) -> str:
        markers = [get_scenario(scenario_id).pytest_marker for scenario_id in self.scenario_ids]
        return " or ".join(markers)


SCAN_PACKS: dict[str, ScanPack] = {
    "core_reliability_scan": ScanPack(
        pack_id="core_reliability_scan",
        name="Core Reliability Scan",
        description="Baseline API reliability scan pack for productized MVP.",
        scenario_ids=[
            "baseline_health",
            "repeated_stability",
            "burst_stability",
            "invalid_payload_handling",
            "missing_fields_validation",
            "auth_failure_handling",
            "timeout_sensitivity",
            "response_consistency",
        ],
    )
}


def resolve_scan_pack(pack_id: str) -> ScanPack:
    if pack_id not in SCAN_PACKS:
        available = ", ".join(sorted(SCAN_PACKS.keys()))
        raise ValueError(f"Unknown scan pack '{pack_id}'. Available: {available}")
    return SCAN_PACKS[pack_id]
