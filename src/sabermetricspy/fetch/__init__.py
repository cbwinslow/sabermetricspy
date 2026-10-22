"""Fetch the seasonal tables the metrics read, to your own machine, when you ask (ADR-0069).

This is the only place the package touches the network, and only when you call it or run
`sabermetrics constants update`. Nothing is fetched on import or in the background, and nothing fetched here is
shipped or redistributed: the files land in your cache directory (`constants.default_cache_dir()`), which
`constants_dir()` reads when you have not pointed it elsewhere. The sources mirror R's `baseballr`:

- FanGraphs Guts! constants (`baseballr::fg_guts`) -> `guts.csv`
- FanGraphs park factors (`baseballr::fg_park`) -> `park_fip.yaml` and `park_factors.yaml`
- MLB Stats API league totals -> `league_war.yaml`

You are responsible for using FanGraphs' data under their terms of service. Rerun `update_constants` as seasons
pass: it only fetches seasons it does not hold yet, plus the latest two, which still change.
"""

from __future__ import annotations

import csv
import datetime
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from sabermetricspy.constants import GUTS_FILE, default_cache_dir, use_constants
from sabermetricspy.telemetry import profiled

GUTS_PAGE = "https://www.fangraphs.com/tools/guts?type=cn"
PARK_PAGE = "https://www.fangraphs.com/tools/guts?type=pf&season={season}"
MLB_TEAM_STATS = (
    "https://statsapi.mlb.com/api/v1/teams/stats?stats=season&group={group}"
    "&season={season}&sportIds=1&gameType=R"
)
USER_AGENT = "sabermetricspy (https://github.com/cbwinslow/sabermetricspy)"
FIRST_SEASON = 1990
"""First season of the park and league tables (the Guts! table starts in 1871)."""
REFRESH_SEASONS = 2
"""The latest seasons are refetched on every update because their totals still move."""

# FanGraphs names the park by team nickname; one abbreviation per franchise (Expos are WSN, Devil Rays TBR).
TEAM_ABBR: dict[str, str] = {
    "Angels": "LAA",
    "Astros": "HOU",
    "Athletics": "OAK",
    "Blue Jays": "TOR",
    "Braves": "ATL",
    "Brewers": "MIL",
    "Cardinals": "STL",
    "Cleveland": "CLE",
    "Cubs": "CHC",
    "Devil Rays": "TBR",
    "Diamondbacks": "ARI",
    "Dodgers": "LAD",
    "Expos": "WSN",
    "Giants": "SFG",
    "Guardians": "CLE",
    "Indians": "CLE",
    "Mariners": "SEA",
    "Marlins": "MIA",
    "Mets": "NYM",
    "Nationals": "WSN",
    "Orioles": "BAL",
    "Padres": "SDP",
    "Phillies": "PHI",
    "Pirates": "PIT",
    "Rangers": "TEX",
    "Rays": "TBR",
    "Red Sox": "BOS",
    "Reds": "CIN",
    "Rockies": "COL",
    "Royals": "KCR",
    "Tigers": "DET",
    "Twins": "MIN",
    "White Sox": "CHW",
    "Yankees": "NYY",
}

_NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


class FetchError(RuntimeError):
    """A table could not be fetched or its layout was not the expected one."""


class UpdateReport(BaseModel):
    """What `update_constants` did: the directory and, per file, the seasons it fetched."""

    model_config = ConfigDict(frozen=True)

    directory: Path
    fetched: dict[str, list[int]]
    skipped: dict[str, list[int]]


def _get(url: str, *, retries: int = 3) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            time.sleep(2.0 * (attempt + 1))
    raise FetchError(f"Could not fetch {url}: {last}")


def _page_rows(url: str) -> list[dict[str, Any]]:
    """The table behind a FanGraphs tools page, from the JSON the page embeds."""
    html = _get(url).decode("utf-8", errors="replace")
    match = _NEXT_DATA.search(html)
    if match is None:
        raise FetchError(f"{url}: the page no longer embeds its data; update sabermetricspy.fetch.")
    try:
        queries = json.loads(match.group(1))["props"]["pageProps"]["dehydratedState"]["queries"]
        rows = queries[0]["state"]["data"]
    except (KeyError, IndexError, ValueError) as exc:
        raise FetchError(f"{url}: unexpected page layout ({exc!r}).") from exc
    if not isinstance(rows, list):
        raise FetchError(f"{url}: expected a list of rows.")
    return [row for row in rows if isinstance(row, dict)]


def fetch_guts() -> list[dict[str, Any]]:
    """The FanGraphs Guts! constants table, one row per season from 1871 (`baseballr::fg_guts`)."""
    rows = _page_rows(GUTS_PAGE)
    needed = {"Season", "wOBA", "wOBAScale", "wBB", "wHBP", "w1B", "w2B", "w3B", "wHR", "cFIP"}
    if not rows or not needed <= set(rows[0]):
        raise FetchError(
            f"Guts! table is missing columns {sorted(needed - set(rows[0] if rows else []))}."
        )
    return rows


def fetch_park_rows(season: int) -> list[dict[str, Any]]:
    """FanGraphs park factors for one season, one row per team (`baseballr::fg_park`); empty before the season."""
    return _page_rows(PARK_PAGE.format(season=season))


def _outs(innings: str) -> int:
    whole, _, frac = innings.partition(".")
    return int(whole) * 3 + int(frac or 0)


def fetch_league_totals(season: int) -> dict[str, int] | None:
    """MLB games, plate appearances, runs and outs for a regular season, or None when it has no team lines yet."""
    splits: dict[str, list[dict[str, Any]]] = {}
    for group in ("hitting", "pitching"):
        body = json.loads(_get(MLB_TEAM_STATS.format(group=group, season=season)))
        splits[group] = body["stats"][0]["splits"]
    if not splits["hitting"]:
        return None
    games = sum(s["stat"]["gamesPlayed"] for s in splits["hitting"])
    if games % 2:
        raise FetchError(f"{season}: team games sum to an odd number ({games}).")
    return {
        "games": games // 2,
        "pa": sum(s["stat"]["plateAppearances"] for s in splits["hitting"]),
        "runs": sum(s["stat"]["runs"] for s in splits["hitting"]),
        "outs": sum(_outs(s["stat"]["inningsPitched"]) for s in splits["pitching"]),
    }


def _write_atomic(path: Path, text: str) -> None:
    """Write beside the target, then replace it, so a failed update never leaves a half-written table."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _csv_text(rows: list[dict[str, Any]]) -> str:
    columns = list(rows[0])
    lines: list[str] = []

    class _Sink:
        def write(self, chunk: str) -> int:
            lines.append(chunk)
            return len(chunk)

    writer = csv.DictWriter(_Sink(), fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return "".join(lines)


def _read_seasons(path: Path) -> dict[int, Any]:
    if not path.is_file():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {int(k): v for k, v in raw.get("seasons", {}).items()}


def _write_seasons(path: Path, header: list[str], seasons: dict[int, Any]) -> None:
    body = yaml.safe_dump({"seasons": {k: seasons[k] for k in sorted(seasons)}}, sort_keys=False)
    _write_atomic(path, "\n".join(header) + "\n" + body)


def _wanted(held: set[int], first: int, last: int) -> list[int]:
    """Seasons to fetch: those not held, plus the latest `REFRESH_SEASONS`."""
    refresh = set(range(last - REFRESH_SEASONS + 1, last + 1))
    return [s for s in range(first, last + 1) if s not in held or s in refresh]


def _update_seasons(
    path: Path,
    header: list[str],
    first: int,
    last: int,
    pause: float,
    fetch_one: Callable[[int], Any | None],
) -> tuple[list[int], list[int]]:
    table = _read_seasons(path)
    wanted = _wanted(set(table), first, last)
    fetched: list[int] = []
    for season in wanted:
        entry = fetch_one(season)
        if entry is None:
            continue
        table[season] = entry
        fetched.append(season)
        time.sleep(pause)
    if fetched:
        _write_seasons(path, header, table)
    return fetched, [s for s in range(first, last + 1) if s not in wanted]


@profiled(category="constants")
def update_constants(
    directory: str | Path | None = None,
    *,
    first_season: int = FIRST_SEASON,
    through: int | None = None,
    pause: float = 1.0,
    use: bool = True,
) -> UpdateReport:
    """Fetch the Guts! constants, park factors and league totals into `directory` (default: the cache directory).

    Safe to rerun every season: Guts! is refetched whole (one request), park and league tables only for seasons not
    held yet plus the latest two. `pause` seconds separate requests to the same site. With `use=True` the directory
    becomes the active constants directory for this session (`use_constants`).
    """
    dest = Path(directory) if directory is not None else default_cache_dir()
    last = through if through is not None else datetime.date.today().year
    today = datetime.date.today().isoformat()
    fetched: dict[str, list[int]] = {}
    skipped: dict[str, list[int]] = {}

    guts = fetch_guts()
    _write_atomic(dest / GUTS_FILE, _csv_text(guts))
    fetched[GUTS_FILE] = sorted(int(r["Season"]) for r in guts)
    time.sleep(pause)

    def park_rows(season: int) -> list[dict[str, Any]] | None:
        rows = fetch_park_rows(season)
        return rows or None

    parks: dict[int, list[dict[str, Any]]] = {}

    def fip_by_team(season: int) -> dict[str, int] | None:
        rows = park_rows(season)
        if rows is None:
            return None
        unknown = sorted({str(r["Team"]) for r in rows} - set(TEAM_ABBR))
        if unknown:
            raise FetchError(f"{season}: park table has teams with no abbreviation: {unknown}.")
        parks[season] = rows
        return {
            TEAM_ABBR[str(r["Team"])]: int(float(r["FIP"]))
            for r in sorted(rows, key=lambda r: TEAM_ABBR[str(r["Team"])])
        }

    fip_header = [
        "# FanGraphs park factors, the FIP column (100 = neutral), by season and team: the park input of FIP- and pitcher WAR.",
        f"# Fetched by sabermetricspy.fetch on {today} from {PARK_PAGE.format(season='<season>')}; whole numbers as published.",
    ]
    fetched["park_fip.yaml"], skipped["park_fip.yaml"] = _update_seasons(
        dest / "park_fip.yaml", fip_header, first_season, last, pause, fip_by_team
    )

    if parks:
        latest = max(parks)
        entries = {
            TEAM_ABBR[str(r["Team"])]: {
                "park_id": TEAM_ABBR[str(r["Team"])],
                "team_id": TEAM_ABBR[str(r["Team"])],
                "season": latest,
                "basic_5yr": round(float(r["Basic (5yr)"]), 1),
                "basic_1yr": round(float(r["1yr"]), 1),
                "hr_factor": round(float(r["HR"]), 1),
            }
            for r in parks[latest]
        }
        header = (
            f"# FanGraphs park factors for {latest}, fetched by sabermetricspy.fetch on {today}.\n"
        )
        _write_atomic(
            dest / "park_factors.yaml", header + yaml.safe_dump({"parks": entries}, sort_keys=True)
        )
        fetched["park_factors.yaml"] = [latest]

    war_header = [
        "# League inputs to the FanGraphs position-player WAR replacement and runs-per-win formulas.",
        "# games = MLB games, pa = plate appearances, runs and outs = MLB totals (outs = innings x 3).",
        f"# Fetched by sabermetricspy.fetch on {today} from the MLB Stats API team totals (regular season, 30 teams summed).",
    ]
    fetched["league_war.yaml"], skipped["league_war.yaml"] = _update_seasons(
        dest / "league_war.yaml", war_header, first_season, last, pause, fetch_league_totals
    )

    if use:
        use_constants(dest)
    return UpdateReport(directory=dest, fetched=fetched, skipped=skipped)
