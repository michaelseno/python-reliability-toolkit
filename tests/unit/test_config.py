from pathlib import Path

from reliabilitykit.core.config import load_config


def test_load_default_config_when_missing(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "missing.yaml")
    assert cfg.project.name
    assert cfg.storage.backend == "local"
