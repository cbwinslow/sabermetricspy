"""Every script in examples/ runs to completion, so the examples cannot drift from the API."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from sabermetricspy.constants import constants_dir

HAVE_FULL = (Path(__file__).parent / "_local_full_constants").is_dir()
EXAMPLES = sorted((Path(__file__).parent.parent / "examples").glob("*.py"))


@pytest.mark.parametrize("script", EXAMPLES, ids=lambda p: p.name)
def test_example_runs(script: Path) -> None:
    env = {**os.environ, "PYTHONUTF8": "1", "SABERMETRICSPY_CONSTANTS": str(constants_dir())}
    done = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
        env=env,
        check=False,
    )
    if done.returncode != 0 and "ConstantsNotFoundError" in done.stderr and not HAVE_FULL:
        pytest.skip("needs seasons beyond the one-season sample constants")
    assert done.returncode == 0, done.stderr[-2000:]
