"""Shared loader for the golden fixture YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

GOLDEN_DIR = Path(__file__).parent / "golden"


def load_entries(name: str) -> list[dict[str, Any]]:
    raw = yaml.safe_load((GOLDEN_DIR / name).read_text(encoding="utf-8"))
    return list(raw["entries"])
