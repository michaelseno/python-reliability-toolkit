from __future__ import annotations

import hashlib
import re


_LOCATION_RE = re.compile(r"^([^\n:]+\.py):(\d+):")
_STACK_RE = re.compile(r"^([^\n:]+\.py):(\d+):")


def _looks_like_user_frame(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    if "/.venv/" in lowered or "/site-packages/" in lowered:
        return False
    return lowered.startswith("tests/") or lowered.startswith("reliabilitykit/")


def _extract_exception_type(raw: str) -> str:
    for line in reversed([line.strip() for line in raw.splitlines() if line.strip()]):
        if ":" in line:
            left = line.split(":", 1)[0].strip()
            if left and all(ch.isalnum() or ch in "._" for ch in left):
                return left.split(".")[-1]
    return "Error"


def _extract_primary_location(lines: list[str]) -> str | None:
    for line in lines:
        match = _LOCATION_RE.match(line.strip())
        if not match:
            continue
        path, line_no = match.groups()
        if _looks_like_user_frame(path):
            return f"{path}:{line_no}"
    return None


def _collect_stack_preview(lines: list[str], limit: int = 4) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for line in lines:
        match = _STACK_RE.match(line.strip())
        if not match:
            continue
        path, line_no = match.groups()
        if not _looks_like_user_frame(path):
            continue
        frame = f"{path}:{line_no}"
        if frame in seen:
            continue
        output.append(frame)
        seen.add(frame)
        if len(output) >= limit:
            break
    return output


def build_failure_digest(nodeid: str, phase: str, raw_message: str) -> tuple[str, str]:
    lines = [line.rstrip() for line in raw_message.splitlines()]
    non_empty = [line for line in lines if line.strip()]
    exception_type = _extract_exception_type(raw_message)
    primary_location = _extract_primary_location(non_empty) or nodeid
    stack_preview = _collect_stack_preview(non_empty)

    timeout_match = re.search(r"Timeout\s+(\d+)ms\s+exceeded", raw_message, re.IGNORECASE)
    if timeout_match:
        timeout_ms = timeout_match.group(1)
        headline = f"{exception_type}: operation timed out after {timeout_ms}ms"
    else:
        last_line = non_empty[-1] if non_empty else exception_type
        headline = last_line if len(last_line) <= 180 else f"{last_line[:177]}..."

    fingerprint_source = "|".join([exception_type, phase, primary_location, *stack_preview[:2]])
    fingerprint = hashlib.sha1(fingerprint_source.encode("utf-8")).hexdigest()[:10]

    digest_lines = [
        f"Headline: {headline}",
        f"Phase: {phase}",
        f"Location: {primary_location}",
        f"Fingerprint: {fingerprint}",
    ]
    if stack_preview:
        digest_lines.append(f"Stack: {' -> '.join(stack_preview)}")

    return "\n".join(digest_lines), fingerprint
