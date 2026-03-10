from __future__ import annotations

import random
from dataclasses import dataclass

from reliabilitykit.core.config import ChaosProfileConfig


@dataclass
class ChaosDecision:
    inject: bool
    action: str
    latency_ms: int = 0
    hang_ms: int = 0
    status_code: int | None = None
    body: str | None = None
    content_type: str | None = None


class ChaosEngine:
    def __init__(self, profile_name: str, profile: ChaosProfileConfig, seed: int | None = None) -> None:
        self.profile_name = profile_name
        self.profile = profile
        self.random = random.Random(seed if seed is not None else profile.seed)

    def decide(self) -> ChaosDecision:
        inject = self.random.random() <= self.profile.probability
        if not inject:
            return ChaosDecision(inject=False, action="pass")

        mode = self.profile.mode
        if mode == "latency":
            ms = self.random.randint(self.profile.latency_ms.min, self.profile.latency_ms.max)
            return ChaosDecision(inject=True, action="delay", latency_ms=ms)
        if mode in {"http_5xx", "http_status"}:
            code = self.random.choice(self.profile.status_codes)
            return ChaosDecision(inject=True, action="fulfill", status_code=code)
        if mode == "abort":
            return ChaosDecision(inject=True, action="abort")
        if mode == "malformed_json":
            code = self.random.choice(self.profile.status_codes) if self.profile.status_codes else 200
            return ChaosDecision(
                inject=True,
                action="fulfill",
                status_code=code,
                body='{"chaos": "broken-json"',
                content_type="application/json",
            )
        if mode == "timeout_hang":
            return ChaosDecision(inject=True, action="hang", hang_ms=max(self.profile.hang_ms, 0))

        mixed_action = self.random.choice(["delay", "fulfill", "abort"])
        if mixed_action == "delay":
            ms = self.random.randint(self.profile.latency_ms.min, self.profile.latency_ms.max)
            return ChaosDecision(inject=True, action="delay", latency_ms=ms)
        if mixed_action == "fulfill":
            code = self.random.choice(self.profile.status_codes)
            return ChaosDecision(inject=True, action="fulfill", status_code=code)
        return ChaosDecision(inject=True, action="abort")
