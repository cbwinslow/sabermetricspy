"""Every script in examples/ runs to completion, so the examples cannot drift from the API."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = sorted((Path(__file__).parent.parent / "examples").glob("*.py"))


@pytest.mark.parametrize("script", EXAMPLES, ids=lambda p: p.name)
def test_example_runs(script: Path) -> None:
    env = {**os.environ, "PYTHONUTF8": "1"}
    done = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", str(script)],
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
        check=False,
    )
    assert done.returncode == 0, done.stderr[-2000:]
