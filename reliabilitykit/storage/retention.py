from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from reliabilitykit.core.audit import AuditResult, RetentionRecord, sanitize_text, utc_now
from reliabilitykit.reporting.audit import write_audit_csv
from reliabilitykit.storage.s3 import S3StorageBackend, build_audit_artifact_key


DEFAULT_ATTACHMENT_MB = 10.0
DEFAULT_SMTP_TIMEOUT_SECONDS = 20.0


class RetentionDeliveryError(RuntimeError):
    def __init__(self, category: str, message: str) -> None:
        self.category = category
        super().__init__(sanitize_text(message) or category)


@dataclass(frozen=True)
class SmtpDeliveryConfig:
    host: str
    port: int
    from_email: str
    failure_notify_email: str
    use_tls: bool
    use_ssl: bool
    username: str | None = None
    password: str | None = None
    from_name: str = "ReliabilityKit"
    timeout_seconds: float = DEFAULT_SMTP_TIMEOUT_SECONDS
    max_attachment_mb: float = DEFAULT_ATTACHMENT_MB

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "SmtpDeliveryConfig":
        data = env if env is not None else os.environ
        required = [
            "RELIABILITYKIT_SMTP_HOST",
            "RELIABILITYKIT_SMTP_PORT",
            "RELIABILITYKIT_SMTP_FROM_EMAIL",
            "RELIABILITYKIT_SMTP_USE_TLS",
            "RELIABILITYKIT_SMTP_USE_SSL",
            "RELIABILITYKIT_RETENTION_FAILURE_NOTIFY_EMAIL",
        ]
        missing = [key for key in required if not data.get(key)]
        if missing:
            raise RetentionDeliveryError("smtp_config_missing", f"Missing SMTP environment variables: {', '.join(missing)}")
        try:
            port = int(data["RELIABILITYKIT_SMTP_PORT"])
        except ValueError as exc:
            raise RetentionDeliveryError("smtp_config_invalid", "SMTP port must be a positive integer") from exc
        if port <= 0:
            raise RetentionDeliveryError("smtp_config_invalid", "SMTP port must be positive")
        use_tls = _parse_bool(data["RELIABILITYKIT_SMTP_USE_TLS"], "RELIABILITYKIT_SMTP_USE_TLS")
        use_ssl = _parse_bool(data["RELIABILITYKIT_SMTP_USE_SSL"], "RELIABILITYKIT_SMTP_USE_SSL")
        if use_tls and use_ssl:
            raise RetentionDeliveryError("smtp_config_invalid", "SMTP TLS and SSL cannot both be true")
        timeout = _parse_positive_float(data.get("RELIABILITYKIT_SMTP_TIMEOUT_SECONDS"), DEFAULT_SMTP_TIMEOUT_SECONDS, "SMTP timeout")
        max_mb = _parse_positive_float(data.get("RELIABILITYKIT_RETENTION_MAX_ATTACHMENT_MB"), DEFAULT_ATTACHMENT_MB, "retention max attachment MB")
        return cls(
            host=data["RELIABILITYKIT_SMTP_HOST"],
            port=port,
            from_email=data["RELIABILITYKIT_SMTP_FROM_EMAIL"],
            failure_notify_email=data["RELIABILITYKIT_RETENTION_FAILURE_NOTIFY_EMAIL"],
            use_tls=use_tls,
            use_ssl=use_ssl,
            username=data.get("RELIABILITYKIT_SMTP_USERNAME") or None,
            password=data.get("RELIABILITYKIT_SMTP_PASSWORD") or None,
            from_name=data.get("RELIABILITYKIT_SMTP_FROM_NAME") or "ReliabilityKit",
            timeout_seconds=timeout,
            max_attachment_mb=max_mb,
        )


def _parse_bool(value: str, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise RetentionDeliveryError("smtp_config_invalid", f"{name} must be true or false")


def _parse_positive_float(value: str | None, default: float, label: str) -> float:
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise RetentionDeliveryError("smtp_config_invalid", f"{label} must be positive") from exc
    if parsed <= 0:
        raise RetentionDeliveryError("smtp_config_invalid", f"{label} must be positive")
    return parsed


def export_retention_csv(record: RetentionRecord, output_dir: str | Path) -> Path:
    result = AuditResult.model_validate_json(Path(record.metadata_location).read_text(encoding="utf-8"))
    output = Path(output_dir) / f"{record.audit_id}_post_retention_sanitized.csv"
    return write_audit_csv(result, output)


def build_retention_email(record: RetentionRecord, config: SmtpDeliveryConfig, csv_path: Path, presigned_url: str | None = None) -> EmailMessage:
    msg = EmailMessage()
    sender = f"{config.from_name} <{config.from_email}>" if config.from_name else config.from_email
    msg["From"] = sender
    msg["To"] = record.client_email
    msg["Subject"] = f"Sanitized post-retention CSV for audit {record.audit_id}"
    if presigned_url:
        msg.set_content(
            "Your sanitized API reliability audit metadata has reached its 90-day retention point. "
            "Download the sanitized CSV using this private time-limited link:\n\n"
            f"{presigned_url}\n\nNo raw response bodies, raw headers, trace logs, or secrets are included."
        )
    else:
        msg.set_content(
            "Your sanitized API reliability audit metadata has reached its 90-day retention point. "
            "The sanitized CSV export is attached. No raw response bodies, raw headers, trace logs, or secrets are included."
        )
        msg.add_attachment(csv_path.read_bytes(), maintype="text", subtype="csv", filename=csv_path.name)
    return msg


def send_email(message: EmailMessage, config: SmtpDeliveryConfig, smtp_factory: object | None = None) -> None:
    factory = smtp_factory
    try:
        if factory is not None:
            smtp = factory(config)
        elif config.use_ssl:
            smtp = smtplib.SMTP_SSL(config.host, config.port, timeout=config.timeout_seconds)
        else:
            smtp = smtplib.SMTP(config.host, config.port, timeout=config.timeout_seconds)
        with smtp:
            if config.use_tls:
                smtp.starttls()
            if config.username and config.password:
                smtp.login(config.username, config.password)
            smtp.send_message(message)
    except smtplib.SMTPAuthenticationError as exc:
        raise RetentionDeliveryError("smtp_auth_failed", "SMTP authentication failed") from exc
    except smtplib.SMTPRecipientsRefused as exc:
        raise RetentionDeliveryError("smtp_recipient_refused", "SMTP recipient was refused") from exc
    except TimeoutError as exc:
        raise RetentionDeliveryError("smtp_timeout", "SMTP delivery timed out") from exc
    except Exception as exc:  # noqa: BLE001 must surface sanitized unexpected delivery failures
        raise RetentionDeliveryError("smtp_send_failed", exc.__class__.__name__) from exc


def process_retention_record(
    record: RetentionRecord,
    output_dir: str | Path,
    *,
    env: dict[str, str] | None = None,
    smtp_factory: object | None = None,
    s3_backend: S3StorageBackend | None = None,
    override_sent: bool = False,
) -> RetentionRecord:
    if record.delivery_status == "sent" and not override_sent:
        return record
    if not record.is_due():
        return record
    updated = record.model_copy(deep=True)
    updated.attempt_count += 1
    updated.last_attempt_at = utc_now()
    try:
        config = SmtpDeliveryConfig.from_env(env)
        csv_path = export_retention_csv(updated, output_dir)
        threshold_bytes = int(config.max_attachment_mb * 1024 * 1024)
        use_link = csv_path.stat().st_size > threshold_bytes or updated.delivery_mode == "presigned_s3_link"
        presigned_url = None
        if use_link:
            if s3_backend is None:
                raise RetentionDeliveryError("s3_delivery_unavailable", "S3 backend required for presigned-link retention delivery")
            key = build_audit_artifact_key("api-reliability-audits/retention", updated.audit_id, csv_path.name)
            presigned_url = s3_backend.upload_and_presign(csv_path, key, "text/csv")
            updated.delivery_mode = "presigned_s3_link"
            updated.export_csv_path_or_key = key
        else:
            updated.delivery_mode = "attachment"
            updated.export_csv_path_or_key = str(csv_path)
        message = build_retention_email(updated, config, csv_path, presigned_url)
        send_email(message, config, smtp_factory=smtp_factory)
        updated.delivery_status = "sent"
        updated.last_error_category = None
    except RetentionDeliveryError as exc:
        updated.delivery_status = "retry_pending"
        updated.last_error_category = exc.category
    return updated
