from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
E2E_TESTS_DIR = ROOT / "tests" / "e2e" / "tests"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_e2e_tests_do_not_use_raw_playwright_locators() -> None:
    blocked_patterns = [
        re.compile(r"\bpage\.locator\("),
        re.compile(r"\bpage\.get_by_"),
        re.compile(r"\bpage\.wait_for_timeout\("),
    ]
    offenders: list[str] = []

    for file_path in sorted(E2E_TESTS_DIR.glob("test_*.py")):
        content = _read(file_path)
        if any(pattern.search(content) for pattern in blocked_patterns):
            offenders.append(str(file_path.relative_to(ROOT)))

    assert not offenders, (
        "Raw Playwright low-level calls found in tests. "
        "Move selectors/actions to pages/components/flows. Offenders: "
        + ", ".join(offenders)
    )
