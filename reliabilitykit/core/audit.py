from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field, field_validator, model_validator

from reliabilitykit.core.scan_packs import resolve_scan_pack
from reliabilitykit.core.scenario_registry import ScenarioDefinition, get_scenario


AuditEnvironment = Literal["production", "staging", "development", "other"]
LatencyStatus = Literal["pass", "fail", "observed_only"]
DeliveryStatus = Literal["pending", "sent", "failed", "retry_pending"]
DeliveryMode = Literal["attachment", "presigned_s3_link"]
ScanStatus = Literal["pass", "fail", "warning", "not_run", "not_applicable", "incomplete"]

MAX_STANDARD_ENDPOINTS = 10
DEFAULT_DURATION_HOURS = 48
DEFAULT_CHECKS_PER_DAY = 5
MIN_CHECKS_PER_DAY = 1
MAX_CHECKS_PER_DAY = 24
DEFAULT_EXPECTED_CHECK_CYCLES = 10
RETENTION_DAYS = 90
REQUEST_TIMEOUT_SECONDS = 10
STANDARD_SCAN_PACK_ID = "core_reliability_scan"
BURST_MAX_CONCURRENT_REQUESTS = 3
BURST_MAX_TOTAL_REQUESTS = 5
BURST_MAX_DURATION_SECONDS = 10

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
    collect_raw_logs: bool = False
    include_raw_logs: bool = False
    persist_raw_logs: bool = False
    collect_raw_responses: bool = False
    include_raw_responses: bool = False
    persist_raw_responses: bool = False
    collect_stack_traces: bool = False
    include_stack_traces: bool = False
    persist_stack_traces: bool = False
    raw_data_exception_reference: str | None = None
    raw_data_written_demand_reference: str | None = None
    sanitized_metadata_retention_days: int = RETENTION_DAYS

    @model_validator(mode="after")
    def validate_raw_data_exception(self) -> "PrivacyPolicy":
        raw_requested = any(
            (
                self.store_raw_bodies,
                self.store_raw_headers,
                self.store_trace_logs,
                self.collect_raw_logs,
                self.include_raw_logs,
                self.persist_raw_logs,
                self.collect_raw_responses,
                self.include_raw_responses,
                self.persist_raw_responses,
                self.collect_stack_traces,
                self.include_stack_traces,
                self.persist_stack_traces,
            )
        )
        if raw_requested and not (self.raw_data_exception_reference and self.raw_data_written_demand_reference):
            raise ValueError("raw diagnostic artifact collection, inclusion, or persistence requires explicit client request and written approval references")
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
    scan_pack_id: str = STANDARD_SCAN_PACK_ID
    schedule_duration_hours: int = DEFAULT_DURATION_HOURS
    checks_per_day: int = DEFAULT_CHECKS_PER_DAY
    expected_check_cycles: int = DEFAULT_EXPECTED_CHECK_CYCLES
    check_frequency_agreement_reference: str | None = None
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


class ScenarioRuntimeDefinition(BaseModel):
    scenario_id: str
    scenario_name: str
    category: str
    rationale: str
    severity_if_failed: Literal["high", "medium", "low", "info"]
    remediation: str
    execution_type: str
    is_standard_mvp: bool = True


class ScanPackExecutionPlan(BaseModel):
    audit_id: str
    scan_pack_id: str
    scan_pack_name: str
    scan_pack_description: str
    scenario_count: int
    scenarios: list[ScenarioRuntimeDefinition]
    generated_at: datetime = Field(default_factory=utc_now)


class EndpointScanResult(BaseModel):
    audit_id: str
    check_cycle_id: str | None = None
    endpoint_id: str
    method: str
    path: str
    scan_pack_id: str
    scan_pack_name: str
    scenario_id: str
    scenario_name: str
    category: str
    severity_if_failed: Literal["high", "medium", "low", "info"]
    status: ScanStatus
    rationale: str
    expected_behavior: str | None = None
    observed_behavior: str | None = None
    evidence_summary: str | None = None
    remediation: str | None = None
    not_run_reason: str | None = None
    not_applicable_reason: str | None = None
    observed_at: datetime | None = None
    affected_cycle_ids: list[str] = Field(default_factory=list)
    sample_count: int = 0
    raw_data_included: bool = False
    raw_data_exception_reference: str | None = None


class AuditResult(BaseModel):
    audit_id: str
    check_cycle_id: str
    started_at: datetime
    ended_at: datetime
    expected_check_cycles: int = DEFAULT_EXPECTED_CHECK_CYCLES
    completed_check_cycles: int = 1
    endpoint_results: list[EndpointAuditResult] = Field(default_factory=list)
    scan_pack_id: str = STANDARD_SCAN_PACK_ID
    scan_pack_name: str = "Core Reliability Scan"
    scan_pack_description: str = "Baseline API reliability scan pack for productized MVP."
    scan_pack_scenario_count: int = 0
    scan_pack_plan: ScanPackExecutionPlan | None = None
    scan_results: list[EndpointScanResult] = Field(default_factory=list)
    overall_score: int | None = None
    overall_verdict: str | None = None
    verdict_rationale: str | None = None
    generated_at: datetime = Field(default_factory=utc_now)
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
    if config.scan_pack_id != STANDARD_SCAN_PACK_ID:
        raise AuditValidationError("standard audit only supports scan_pack_id core_reliability_scan")
    scan_pack = resolve_scan_pack(config.scan_pack_id)
    unapproved = [sid for sid in scan_pack.scenario_ids if sid not in resolve_scan_pack(STANDARD_SCAN_PACK_ID).scenario_ids]
    if unapproved:
        raise AuditValidationError("scan pack contains unapproved standard MVP scenarios")
    if config.schedule_duration_hours != DEFAULT_DURATION_HOURS:
        raise AuditValidationError("standard audit schedule duration must be 48 hours")
    if not MIN_CHECKS_PER_DAY <= config.checks_per_day <= MAX_CHECKS_PER_DAY:
        raise AuditValidationError("standard audit checks_per_day must be between 1 and 24")
    if config.checks_per_day > DEFAULT_CHECKS_PER_DAY and not config.check_frequency_agreement_reference:
        raise AuditValidationError("checks_per_day above the default 5 requires an operator/client agreement reference")
    expected_cycles = expected_check_cycles_for(config.schedule_duration_hours, config.checks_per_day)
    if config.expected_check_cycles != expected_cycles:
        raise AuditValidationError(
            f"standard audit expected_check_cycles must be {expected_cycles} for {config.schedule_duration_hours} hours at {config.checks_per_day} checks per day"
        )


def expected_check_cycles_for(schedule_duration_hours: int, checks_per_day: int) -> int:
    cycles = schedule_duration_hours * checks_per_day
    if cycles % 24 != 0:
        raise AuditValidationError("standard audit expected_check_cycles must resolve to whole check cycles")
    return cycles // 24


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


def build_scan_pack_execution_plan(config: AuditConfig) -> ScanPackExecutionPlan:
    pack = resolve_scan_pack(config.scan_pack_id)
    scenarios = []
    for scenario_id in pack.scenario_ids:
        scenario = get_scenario(scenario_id)
        scenarios.append(
            ScenarioRuntimeDefinition(
                scenario_id=scenario.scenario_id,
                scenario_name=scenario.scenario_name,
                category=scenario.category,
                rationale=scenario.description,
                severity_if_failed=scenario.severity_if_failed,  # type: ignore[arg-type]
                remediation=scenario.remediation,
                execution_type=scenario.execution_type,
            )
        )
    return ScanPackExecutionPlan(
        audit_id=config.audit_id,
        scan_pack_id=pack.pack_id,
        scan_pack_name=pack.name,
        scan_pack_description=pack.description,
        scenario_count=len(scenarios),
        scenarios=scenarios,
    )


def _endpoint_request(config: AuditConfig, endpoint: AuditEndpoint, check_cycle_id: str, timeout_seconds: int, auth_header: tuple[str, str] | None) -> EndpointAuditResult:
    headers: dict[str, str] = {}
    if auth_header:
        headers[auth_header[0]] = auth_header[1]
    request = Request(endpoint.url, method=endpoint.method, headers=headers)
    begin = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 operator-controlled URLs
            status_code = int(response.status)
            response.read(0)
        latency_ms = round((time.perf_counter() - begin) * 1000, 2)
        available = 200 <= status_code < 400
        return EndpointAuditResult(
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
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        latency_ms = round((time.perf_counter() - begin) * 1000, 2)
        return result_from_http_error(config, endpoint, check_cycle_id, exc, latency_ms)


def _scan_result_base(config: AuditConfig, endpoint: AuditEndpoint, plan: ScanPackExecutionPlan, scenario: ScenarioDefinition, check_cycle_id: str) -> dict[str, Any]:
    return {
        "audit_id": config.audit_id,
        "check_cycle_id": check_cycle_id,
        "endpoint_id": endpoint.endpoint_id,
        "method": endpoint.method,
        "path": endpoint.path,
        "scan_pack_id": plan.scan_pack_id,
        "scan_pack_name": plan.scan_pack_name,
        "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.scenario_name,
        "category": scenario.category,
        "severity_if_failed": scenario.severity_if_failed,
        "rationale": scenario.description,
        "remediation": scenario.remediation,
        "raw_data_included": False,
        "affected_cycle_ids": [check_cycle_id],
    }


def _result_from_samples(config: AuditConfig, endpoint: AuditEndpoint, plan: ScanPackExecutionPlan, scenario: ScenarioDefinition, check_cycle_id: str, samples: list[EndpointAuditResult], expected_behavior: str) -> EndpointScanResult:
    failed = [sample for sample in samples if not sample.available]
    slow = [sample for sample in samples if sample.latency_status == "fail"]
    status = "fail" if failed else "warning" if slow else "pass"
    status_codes = sorted({sample.status_code for sample in samples if sample.status_code is not None})
    evidence = f"{len(samples)} sanitized observation(s); available={len(samples) - len(failed)}/{len(samples)}; status_codes={status_codes or 'not_available'}"
    if scenario.scenario_id == "burst_stability":
        evidence = (
            f"Bounded burst check completed within approved limits; sanitized status and timing metadata only. "
            f"limits=max_total_requests={BURST_MAX_TOTAL_REQUESTS}, max_concurrency={BURST_MAX_CONCURRENT_REQUESTS}, "
            f"max_duration_seconds={BURST_MAX_DURATION_SECONDS}, no_extra_retries; available={len(samples) - len(failed)}/{len(samples)}."
        )
    return EndpointScanResult(
        **_scan_result_base(config, endpoint, plan, scenario, check_cycle_id),
        status=status,  # type: ignore[arg-type]
        expected_behavior=expected_behavior,
        observed_behavior=sanitize_text("; ".join(filter(None, [sample.error_category for sample in failed])) or "sanitized status metadata captured"),
        evidence_summary=sanitize_text(evidence, max_length=360),
        observed_at=max((sample.timestamp for sample in samples), default=utc_now()),
        sample_count=len(samples),
    )


def _not_applicable(config: AuditConfig, endpoint: AuditEndpoint, plan: ScanPackExecutionPlan, scenario: ScenarioDefinition, check_cycle_id: str, reason: str) -> EndpointScanResult:
    return EndpointScanResult(**_scan_result_base(config, endpoint, plan, scenario, check_cycle_id), status="not_applicable", not_applicable_reason=reason, evidence_summary=reason, sample_count=0)


def _run_scan_scenario(config: AuditConfig, endpoint: AuditEndpoint, plan: ScanPackExecutionPlan, scenario: ScenarioDefinition, check_cycle_id: str, timeout_seconds: int, auth_header: tuple[str, str] | None, baseline: EndpointAuditResult) -> EndpointScanResult:
    if scenario.scenario_id == "baseline_health":
        return _result_from_samples(config, endpoint, plan, scenario, check_cycle_id, [baseline], "Endpoint returns an available 2xx/3xx response within the configured threshold when supplied.")
    if scenario.scenario_id == "repeated_stability":
        samples = [_endpoint_request(config, endpoint, check_cycle_id, timeout_seconds, auth_header) for _ in range(2)]
        return _result_from_samples(config, endpoint, plan, scenario, check_cycle_id, samples, "Sequential short-interval requests remain available and latency-stable.")
    if scenario.scenario_id == "burst_stability":
        start = time.perf_counter()
        samples: list[EndpointAuditResult] = []
        with ThreadPoolExecutor(max_workers=BURST_MAX_CONCURRENT_REQUESTS) as executor:
            futures = [executor.submit(_endpoint_request, config, endpoint, check_cycle_id, min(timeout_seconds, BURST_MAX_DURATION_SECONDS), auth_header) for _ in range(BURST_MAX_TOTAL_REQUESTS)]
            for future in as_completed(futures, timeout=BURST_MAX_DURATION_SECONDS):
                samples.append(future.result())
                if time.perf_counter() - start > BURST_MAX_DURATION_SECONDS:
                    break
        if len(samples) < BURST_MAX_TOTAL_REQUESTS:
            return EndpointScanResult(**_scan_result_base(config, endpoint, plan, scenario, check_cycle_id), status="incomplete", not_run_reason="bounded stability result was not fully captured within approved 10 second limit", evidence_summary="Approved bounded check limits stopped execution; no capacity or throughput inference made.", observed_at=utc_now(), sample_count=len(samples))
        return _result_from_samples(config, endpoint, plan, scenario, check_cycle_id, samples, "Small bounded request group remains available; no load, stress, soak, or capacity objective is evaluated.")
    if scenario.scenario_id in {"invalid_payload_handling", "missing_fields_validation"}:
        return _not_applicable(config, endpoint, plan, scenario, check_cycle_id, "No approved endpoint-specific payload schema/contract was provided; destructive or synthetic payloads are not sent by default.")
    if scenario.scenario_id == "auth_failure_handling" and config.auth is None:
        return _not_applicable(config, endpoint, plan, scenario, check_cycle_id, "No bearer authentication configuration was provided for this endpoint.")
    if scenario.scenario_id == "auth_failure_handling":
        invalid_header = (config.auth.header_name, f"{config.auth.token_prefix} invalid-audit-token") if config.auth else None
        sample = _endpoint_request(config, endpoint, check_cycle_id, timeout_seconds, invalid_header)
        expected_auth_failure = sample.status_code in (401, 403)
        return EndpointScanResult(
            **_scan_result_base(config, endpoint, plan, scenario, check_cycle_id),
            status="pass" if expected_auth_failure else "fail",
            expected_behavior="Invalid bearer credentials return a controlled 401/403 response without exposing diagnostics.",
            observed_behavior=sanitize_text(f"sanitized auth-negative status={sample.status_code if sample.status_code is not None else 'not_available'}"),
            evidence_summary=sanitize_text(f"Auth-negative check used a synthetic invalid credential; sanitized status={sample.status_code if sample.status_code is not None else 'not_available'}; raw headers/tokens excluded."),
            observed_at=sample.timestamp,
            sample_count=1,
        )
    samples = [_endpoint_request(config, endpoint, check_cycle_id, timeout_seconds if scenario.scenario_id != "timeout_sensitivity" else min(timeout_seconds, 3), auth_header) for _ in range(2 if scenario.scenario_id == "response_consistency" else 1)]
    return _result_from_samples(config, endpoint, plan, scenario, check_cycle_id, samples, "Sanitized scenario observations meet expected status and timing behavior.")


def execute_check_cycle(config: AuditConfig, check_cycle_id: str, timeout_seconds: int = REQUEST_TIMEOUT_SECONDS) -> AuditResult:
    validate_audit_config(config)
    started = utc_now()
    auth_header = config.auth.resolve_header() if config.auth else None
    plan = build_scan_pack_execution_plan(config)
    results: list[EndpointAuditResult] = []
    scan_results: list[EndpointScanResult] = []
    for endpoint in [item for item in config.endpoints if item.enabled]:
        baseline = _endpoint_request(config, endpoint, check_cycle_id, timeout_seconds, auth_header)
        results.append(baseline)
        for scenario_id in resolve_scan_pack(config.scan_pack_id).scenario_ids:
            scan_results.append(_run_scan_scenario(config, endpoint, plan, get_scenario(scenario_id), check_cycle_id, timeout_seconds, auth_header, baseline))
    ended = utc_now()
    return AuditResult(
        audit_id=config.audit_id,
        check_cycle_id=check_cycle_id,
        started_at=started,
        ended_at=ended,
        expected_check_cycles=config.expected_check_cycles,
        completed_check_cycles=1,
        endpoint_results=results,
        scan_pack_id=plan.scan_pack_id,
        scan_pack_name=plan.scan_pack_name,
        scan_pack_description=plan.scan_pack_description,
        scan_pack_scenario_count=plan.scenario_count,
        scan_pack_plan=plan,
        scan_results=scan_results,
        retention_expires_at=ended + timedelta(days=config.retention.retention_days),
    )


def load_audit_config(path: str | Path) -> AuditConfig:
    import yaml

    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return AuditConfig.model_validate(raw)


def load_audit_result(path: str | Path) -> AuditResult:
    return AuditResult.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))
