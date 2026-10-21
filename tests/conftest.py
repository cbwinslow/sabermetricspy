"""Tests never touch the network unless they opt in."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _no_register_auto_update(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SABERMETRICSPY_AUTO_UPDATE", "0")
