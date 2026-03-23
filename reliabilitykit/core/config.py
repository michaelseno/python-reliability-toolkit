from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class LocalStorageConfig(BaseModel):
    path: str = ".reliabilitykit"


class StorageConfig(BaseModel):
    backend: Literal["local", "s3"] = "local"
    local: LocalStorageConfig = Field(default_factory=LocalStorageConfig)


class PytestConfig(BaseModel):
    args: list[str] = Field(default_factory=list)


class CaptureConfig(BaseModel):
    trace: bool = True
    video: bool = False
    screenshot: bool = True
    logs: bool = True


class ChaosTarget(BaseModel):
    host: str | None = None
    url_pattern: str
    methods: list[str] = Field(default_factory=lambda: ["GET"])
    resource_types: list[str] = Field(default_factory=lambda: ["xhr", "fetch"])


class LatencyRange(BaseModel):
    min: int = 100
    max: int = 500


class ChaosProfileConfig(BaseModel):
    mode: Literal["latency", "http_5xx", "http_status", "abort", "mixed", "malformed_json", "timeout_hang"]
    intent_class: Literal["resilience", "fault", "disruptive"] = "fault"
    probability: float = 0.2
    seed: int = 42
    latency_ms: LatencyRange = Field(default_factory=LatencyRange)
    hang_ms: int = 35000
    status_codes: list[int] = Field(default_factory=lambda: [500])
    targets: list[ChaosTarget] = Field(default_factory=list)


class ChaosConfig(BaseModel):
    enabled_default: bool = False
    profiles: dict[str, ChaosProfileConfig] = Field(default_factory=dict)


class ReportingConfig(BaseModel):
    trend_default_window_days: int = 14


class ClassificationConfig(BaseModel):
    ruleset_version: str = "v1"


class ProjectConfig(BaseModel):
    name: str = "reliability-toolkit"


class ReliabilityConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    pytest: PytestConfig = Field(default_factory=PytestConfig)
    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    chaos: ChaosConfig = Field(default_factory=ChaosConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)


def load_config(path: str | Path = "reliabilitykit.yaml") -> ReliabilityConfig:
    path = Path(path)
    if not path.exists():
        return ReliabilityConfig()
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return ReliabilityConfig.model_validate(data)
