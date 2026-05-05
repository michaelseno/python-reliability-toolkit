from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from reliabilitykit.core.models import RunRecord
from reliabilitykit.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    def __init__(self, bucket: str, client: object | None = None) -> None:
        self.bucket = bucket
        self.client = client or self._load_boto3_client()

    @staticmethod
    def _load_boto3_client() -> object:
        try:
            import boto3  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise RuntimeError("boto3 is required for S3 delivery or inject a compatible client") from exc
        return boto3.client("s3")

    def prepare_run_dir(self, run_id: str, started_at: datetime) -> Path:
        raise NotImplementedError("S3 backend will be implemented in a later phase")

    def write_run(self, run: RunRecord, run_dir: Path) -> None:
        raise NotImplementedError("S3 backend will be implemented in a later phase")

    def list_runs(self) -> list[Path]:
        raise NotImplementedError("S3 backend will be implemented in a later phase")

    def upload_private_file(self, local_path: str | Path, key: str, content_type: str | None = None) -> str:
        path = Path(local_path)
        if not path.exists():
            raise FileNotFoundError(f"artifact not found: {path}")
        if self._looks_public_key_or_url(key):
            raise ValueError("S3 artifact key must be private object key, not a public URL")
        extra_args = {"ACL": "private"}
        if content_type:
            extra_args["ContentType"] = content_type
        self.client.upload_file(str(path), self.bucket, key, ExtraArgs=extra_args)
        return key

    def presign_get_url(self, key: str, expires_in_seconds: int = 604800) -> str:
        if expires_in_seconds <= 0:
            raise ValueError("presigned URL expiration must be positive")
        if self._looks_public_key_or_url(key):
            raise ValueError("cannot presign a public/permanent URL")
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )

    def upload_and_presign(self, local_path: str | Path, key: str, content_type: str | None = None, expires_in_seconds: int = 604800) -> str:
        self.upload_private_file(local_path, key, content_type)
        return self.presign_get_url(key, expires_in_seconds)

    @staticmethod
    def _looks_public_key_or_url(key: str) -> bool:
        parsed = urlparse(key)
        if parsed.scheme in {"http", "https"}:
            return True
        return "public-read" in key.lower()


def build_audit_artifact_key(prefix: str, audit_id: str, artifact_name: str, generated_at: datetime | None = None) -> str:
    safe_prefix = "/".join(part.strip("/") for part in prefix.split("/") if part.strip("/")) or "api-reliability-audits"
    safe_audit_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in audit_id)[:80]
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in artifact_name)[:120]
    stamp = (generated_at or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    return f"{safe_prefix}/{safe_audit_id}/{stamp}/{safe_name}"
