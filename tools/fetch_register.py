"""Standalone downloader for the Chadwick Bureau Register (maintainer tool; not part of the installed package).

sabermetricspy is computation-only and never touches the network (ADR-0003, ADR-0068). This script is the old
`download_register` / `update_register` logic from sabermetricspy 1.x, kept here until it moves to `chadwickpy`.

    python tools/fetch_register.py <destination directory> [--ref master] [--commit SHA]

It downloads the 16 `people-*.csv` shards to the directory, pinned to one commit, and writes `provenance.json`
(fetch date and commit) next to them, which `sabermetricspy.ids.load_register` reads for attribution. The register is
licensed ODC-BY 1.0: credit the Chadwick Bureau when you publish results that use it.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import tempfile
import urllib.request
from pathlib import Path

REPO = "chadwickbureau/register"
URL = f"https://raw.githubusercontent.com/{REPO}/{{ref}}/data"
API = f"https://api.github.com/repos/{REPO}/commits/{{ref}}"
SHARDS = tuple(f"people-{c}.csv" for c in "0123456789abcdef")


def resolve_commit(ref: str) -> str | None:
    """The commit SHA a ref points to, from the GitHub API, or None when it cannot be reached."""
    try:
        request = urllib.request.Request(
            API.format(ref=ref), headers={"Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(request, timeout=30) as resp:
            sha = json.loads(resp.read().decode("utf-8")).get("sha")
        return str(sha) if sha else None
    except (OSError, ValueError):
        return None


def download(dest: Path, ref: str = "master", commit: str | None = None) -> Path:
    """Fetch every shard into a scratch directory first, so a failure never leaves a mixed old/new register."""
    dest.mkdir(parents=True, exist_ok=True)
    pinned = commit or resolve_commit(ref)
    base = URL.format(ref=pinned or ref)
    with tempfile.TemporaryDirectory(dir=dest, prefix=".download-") as scratch_name:
        scratch = Path(scratch_name)
        for shard in SHARDS:
            with urllib.request.urlopen(f"{base}/{shard}", timeout=120) as resp:
                (scratch / shard).write_bytes(resp.read())
        for shard in SHARDS:
            os.replace(scratch / shard, dest / shard)
    record = {
        "fetched_on": datetime.date.today().isoformat(),
        "ref": ref,
        "commit": pinned,
        "repository": REPO,
    }
    (dest / "provenance.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return dest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download the Chadwick Bureau Register (maintainer tool)"
    )
    parser.add_argument("dest", type=Path)
    parser.add_argument("--ref", default="master")
    parser.add_argument("--commit", default=None)
    args = parser.parse_args()
    print(download(args.dest, args.ref, args.commit))
