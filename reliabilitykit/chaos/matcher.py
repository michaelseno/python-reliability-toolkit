from __future__ import annotations

from urllib.parse import urlparse

from reliabilitykit.core.config import ChaosTarget


def target_matches(target: ChaosTarget, url: str, method: str, resource_type: str) -> bool:
    parsed = urlparse(url)
    if target.host and parsed.netloc != target.host:
        return False
    if target.url_pattern not in parsed.path:
        return False
    if target.methods and method.upper() not in [m.upper() for m in target.methods]:
        return False
    if target.resource_types and resource_type not in target.resource_types:
        return False
    return True
