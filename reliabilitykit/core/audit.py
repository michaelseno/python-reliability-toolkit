from __future__ import annotations

import json
import os
import re
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field, field_validator, model_validator


AuditEnvironment = Literal["production", "staging", "development", "other"]
LatencyStatus = Literal["pass", "fail", "observed_only"]
DeliveryStatus = Literal["pending", "sent", "failed", "retry_pending"]
DeliveryMode = Literal["attachment", "presigned_s3_link"]

MAX_STANDARD_ENDPOINTS = 10
DEFAULT_DURATION_HOURS = 48
DEFAULT_CHECKS_PER_DAY = 5
DEFAULT_EXPECTED_CHECK_CYCLES = 10
RETENTION_DAYS = 90
REQUEST_TIMEOUT_SECONDS = 10

SENSITIVE_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"Authorization:\s*[^\s,;]+", re.IGNORECASE),
    re.compile(r"(token|password|secret|api[_-]?key)=([^\s&]+)", re.IGNORECASE),
]


def utc_now() -> datetime:
    return datetime.now(UTC)


def sanitize_text(value: Any, *, max_length: int = 180) -> str | None:
    if value is None:
        return None
    text = str(value).replace("\r", " ").replace("\n", " ")
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub(lambda m: f"{m.group(1)}=<redacted>" if m.lastindex and m.lastindex >= 1 else "<redacted>", text)
    text = re.sub(r"https?://[^\s]+", "<url-redacted>", text)
    text = re.sub(r"[A-Za-z0-9_./+-]{24,}", "<redacted>", text)
    text = text.strip()
    return text[:max_length] if text else None


class AuditValidationError(ValueError):
    """Fail-closed audit validation error with operator-actionable text."""


class AuditEndpoint(BaseModel):
    endpoint_id: str
    method: str
    path: str
    base_url: str
    expected_latency_ms: int | None = None
    enabled: bool = True
    notes: str | None = None

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        method = value.strip().upper()
        if not method:
            raise ValueError("method is required")
        if not re.fullmatch(r"[A-Z]+", method):
            raise ValueError("method must contain letters only")
        return method

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = value.strip()
        if not path.startswith("/"):
            raise ValueError("path must start with '/'")
        return path

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        base_url = value.strip()
        if not (base_url.startswith("https://") or base_url.startswith("http://")):
            raise ValueError("base_url must be http(s)")
        return base_url.rstrip("/")

    @field_validator("expected_latency_ms")
    @classmethod
    def validate_latency(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("expected_latency_ms must be positive when provided")
        return value

    @property
    def identity(self) -> str:
        return f"{self.method} {self.path}"

    @property
    def url(self) -> str:
        return urljoin(f"{self.base_url}/", self.path.lstrip("/"))


class BearerAuthConfig(BaseModel):
    auth_type: Literal["bearer_token"] = "bearer_token"
    token_secret_reference: str
    header_name: str = "Authorization"
    token_prefix: str = "Bearer"

    def resolve_header(self) -> tuple[str, str] | None:
        token = os.environ.get(self.token_secret_reference)
        if not token:
            return None
        return self.header_name, f"{self.token_prefix} {token}"


class PrivacyPolicy(BaseModel):
    store_raw_bodies: bool = False
    store_raw_headers: bool = False
    store_trace_logs: bool = False
    raw_data_exception_reference: str | None = None
    raw_data_written_demand_reference: str | None = None
    sanitized_metadata_retention_days: int = RETENTION_DAYS

    @model_validator(mode="after")
    def validate_raw_data_exception(self) -> "PrivacyPolicy":
        raw_requested = self.store_raw_bodies or self.store_raw_headers or self.store_trace_logs
        if raw_requested and not (self.raw_data_exception_reference and self.raw_data_written_demand_reference):
            raise ValueError("raw data storage requires written demand and approval references")
        if self.sanitized_metadata_retention_days != RETENTION_DAYS:
            raise ValueError("sanitized metadata retention must be 90 days")
        return self


class RetentionPolicy(BaseModel):
    enabled: bool = True
    retention_days: int = RETENTION_DAYS
    delivery_mode: DeliveryMode = "attachment"

    @field_validator("retention_days")
    @classmethod
    def validate_retention_days(cls, value: int) -> int:
        if value != RETENTION_DAYS:
            raise ValueError("retention_days must be 90")
        return value


class AuditConfig(BaseModel):
    audit_id: str
    client_name: str
    client_email: str
    environment: AuditEnvironment = "staging"
    production_waiver_reference: str | None = None
    internal_approval_reference: str | None = None
    endpoints: list[AuditEndpoint]
    auth: BearerAuthConfig | None = None
    schedule_duration_hours: int = DEFAULT_DURATION_HOURS
    checks_per_day: int = DEFAULT_CHECKS_PER_DAY
    expected_check_cycles: int = DEFAULT_EXPECTED_CHECK_CYCLES
    privacy_policy: PrivacyPolicy = Field(default_factory=PrivacyPolicy)
    resilience_burst_requested: bool = False
    resilience_burst_approval_reference: str | None = None
    report_artifact_prefix: str = "api-reliability-audits"
    retention: RetentionPolicy = Field(default_factory=RetentionPolicy)
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_config(self) -> "AuditConfig":
        validate_audit_config(self)
        return self

    @field_validator("client_email")
    @classmethod
    def validate_client_email(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("client_email must be a valid email-like address")
        return value


class EndpointAuditResult(BaseModel):
    audit_id: str
    check_cycle_id: str
    endpoint_id: str
    method: str
    path: str
    timestamp: datetime
    status_code: int | None = None
    available: bool
    latency_ms: float | None = None
    expected_latency_ms: int | None = None
    latency_status: LatencyStatus = "observed_only"
    error_category: str | None = None
    error_summary: str | None = None

    @model_validator(mode="after")
    def enforce_latency_status(self) -> "EndpointAuditResult":
        if self.expected_latency_ms is None:
            self.latency_status = "observed_only"
        elif self.latency_ms is not None:
            self.latency_status = "pass" if self.latency_ms <= self.expected_latency_ms else "fail"
        return self


class AuditResult(BaseModel):
    audit_id: str
    check_cycle_id: str
    started_at: datetime
    ended_at: datetime
    expected_check_cycles: int = DEFAULT_EXPECTED_CHECK_CYCLES
    completed_check_cycles: int = 1
    endpoint_results: list[EndpointAuditResult] = Field(default_factory=list)
    report_html_s3_key: str | None = None
    csv_s3_key: str | None = None
    retention_expires_at: datetime


class RetentionRecord(BaseModel):
    audit_id: str
    client_email: str
    metadata_location: str
    retention_started_at: datetime
    retention_expires_at: datetime
    export_csv_path_or_key: str | None = None
    delivery_mode: DeliveryMode = "attachment"
    delivery_status: DeliveryStatus = "pending"
    last_attempt_at: datetime | None = None
    last_error_category: str | None = None
    attempt_count: int = 0

    def is_due(self, now: datetime | None = None) -> bool:
        return (now or utc_now()) >= self.retention_expires_at


def endpoint_identities(config: AuditConfig) -> list[str]:
    return [endpoint.identity for endpoint in config.endpoints if endpoint.enabled]


def validate_audit_config(config: AuditConfig) -> None:
    enabled = [endpoint for endpoint in config.endpoints if endpoint.enabled]
    if not enabled:
        raise AuditValidationError("at least one enabled endpoint is required")
    identities = [endpoint.identity for endpoint in enabled]
    duplicates = sorted({identity for identity in identities if identities.count(identity) > 1})
    if duplicates:
        raise AuditValidationError(f"duplicate endpoint identities are not allowed: {', '.join(duplicates)}")
    if len(set(identities)) > MAX_STANDARD_ENDPOINTS:
        raise AuditValidationError("standard audit supports no more than 10 unique METHOD + PATH endpoints")
    if config.environment == "production" and not config.production_waiver_reference:
        raise AuditValidationError("production audits require a written waiver/agreement reference")
    if config.environment == "production" and not config.internal_approval_reference:
        raise AuditValidationError("production audits require an internal approval checklist reference")
    if config.resilience_burst_requested and not config.resilience_burst_approval_reference:
        raise AuditValidationError("resilience/burst testing requires separate written approval")
    if config.schedule_duration_hours != DEFAULT_DURATION_HOURS:
        raise AuditValidationError("standard audit schedule duration must be 48 hours")
    if config.checks_per_day != DEFAULT_CHECKS_PER_DAY:
        raise AuditValidationError("standard audit checks_per_day must be 5")
    if config.expected_check_cycles != DEFAULT_EXPECTED_CHECK_CYCLES:
        raise AuditValidationError("standard audit expected_check_cycles must be approximately 10")


def make_retention_record(config: AuditConfig, metadata_location: str, started_at: datetime | None = None) -> RetentionRecord:
    start = started_at or utc_now()
    return RetentionRecord(
        audit_id=config.audit_id,
        client_email=config.client_email,
        metadata_location=metadata_location,
        retention_started_at=start,
        retention_expires_at=start + timedelta(days=config.retention.retention_days),
        delivery_mode=config.retention.delivery_mode,
    )


def result_from_http_error(config: AuditConfig, endpoint: AuditEndpoint, check_cycle_id: str, exc: Exception, latency_ms: float | None = None) -> EndpointAuditResult:
    status_code = exc.code if isinstance(exc, HTTPError) else None
    category = "http_error" if isinstance(exc, HTTPError) else "network_error"
    if isinstance(exc, TimeoutError):
        category = "timeout"
    if status_code in (401, 403):
        category = "auth_failure"
    return EndpointAuditResult(
        audit_id=config.audit_id,
        check_cycle_id=check_cycle_id,
        endpoint_id=endpoint.endpoint_id,
        method=endpoint.method,
        path=endpoint.path,
        timestamp=utc_now(),
        status_code=status_code,
        available=False,
        latency_ms=latency_ms,
        expected_latency_ms=endpoint.expected_latency_ms,
        error_category=category,
        error_summary=sanitize_text(exc.__class__.__name__),
    )


def execute_check_cycle(config: AuditConfig, check_cycle_id: str, timeout_seconds: int = REQUEST_TIMEOUT_SECONDS) -> AuditResult:
    validate_audit_config(config)
    started = utc_now()
    auth_header = config.auth.resolve_header() if config.auth else None
    results: list[EndpointAuditResult] = []
    for endpoint in [item for item in config.endpoints if item.enabled]:
        headers: dict[str, str] = {}
        if auth_header:
            headers[auth_header[0]] = auth_header[1]
        request = Request(endpoint.url, method=endpoint.method, headers=headers)
        begin = time.perf_counter()
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 operator-controlled URLs
                status_code = int(response.status)
                response.read(0)  # Avoid persisting/processing response body.
            latency_ms = round((time.perf_counter() - begin) * 1000, 2)
            available = 200 <= status_code < 400
            results.append(
                EndpointAuditResult(
                    audit_id=config.audit_id,
                    check_cycle_id=check_cycle_id,
                    endpoint_id=endpoint.endpoint_id,
                    method=endpoint.method,
                    path=endpoint.path,
                    timestamp=utc_now(),
                    status_code=status_code,
                    available=available,
                    latency_ms=latency_ms,
                    expected_latency_ms=endpoint.expected_latency_ms,
                    error_category=None if available else "http_error",
                    error_summary=None if available else "Non-success HTTP status",
                )
            )
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            latency_ms = round((time.perf_counter() - begin) * 1000, 2)
            results.append(result_from_http_error(config, endpoint, check_cycle_id, exc, latency_ms))
    ended = utc_now()
    return AuditResult(
        audit_id=config.audit_id,
        check_cycle_id=check_cycle_id,
        started_at=started,
        ended_at=ended,
        expected_check_cycles=config.expected_check_cycles,
        completed_check_cycles=1,
        endpoint_results=results,
        retention_expires_at=ended + timedelta(days=config.retention.retention_days),
    )


def load_audit_config(path: str | Path) -> AuditConfig:
    import yaml

    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return AuditConfig.model_validate(raw)


def load_audit_result(path: str | Path) -> AuditResult:
    return AuditResult.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))
