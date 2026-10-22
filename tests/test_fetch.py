"""`sabermetricspy.fetch` writes the tables the metrics read; the network is replaced by recorded-shape payloads."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
import yaml

import sabermetricspy as sp
from sabermetricspy import fetch
from sabermetricspy.constants import (
    constants_dir,
    default_cache_dir,
    get_league_war_constants,
    get_woba_weights,
)
from sabermetricspy.fetch import FetchError, update_constants
from sabermetricspy.types.context import ConstantsNotFoundError

GUTS_ROW: dict[str, object] = {
    "Season": 2030,
    "wOBA": 0.32,
    "wOBAScale": 1.2,
    "wBB": 0.7,
    "wHBP": 0.73,
    "w1B": 0.9,
    "w2B": 1.27,
    "w3B": 1.6,
    "wHR": 2.05,
    "runSB": 0.2,
    "runCS": -0.41,
    "R/PA": 0.12,
    "R/W": 9.8,
    "cFIP": 3.1,
}


def _page(rows: list[dict[str, object]]) -> bytes:
    data = {"props": {"pageProps": {"dehydratedState": {"queries": [{"state": {"data": rows}}]}}}}
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script></html>'.encode()


def _park(season: int, team: str = "Yankees") -> dict[str, object]:
    return {
        "Season": season,
        "Team": team,
        "Basic (5yr)": 101.26,
        "1yr": 102.0,
        "HR": 104.44,
        "FIP": 102.9,
    }


def _team(games: int, ip: str) -> dict[str, object]:
    return {
        "stat": {"gamesPlayed": games, "plateAppearances": 6000, "runs": 700, "inningsPitched": ip}
    }


class Net:
    """Stands in for `fetch._get` and records which URLs were requested."""

    def __init__(self, last_season: int, park_team: str = "Yankees") -> None:
        self.calls: list[str] = []
        self.last_season = last_season
        self.park_team = park_team

    def __call__(self, url: str, *, retries: int = 3) -> bytes:
        self.calls.append(url)
        if "type=cn" in url:
            return _page([GUTS_ROW])
        if "type=pf" in url:
            season = int(url.rsplit("=", 1)[1])
            return _page([_park(season, self.park_team)] if season <= self.last_season else [])
        season = int(url.split("season=")[1].split("&")[0])
        if season > self.last_season:
            return json.dumps({"stats": [{"splits": []}]}).encode()
        splits = [_team(162, "1450.1"), _team(162, "1449.2")]
        return json.dumps({"stats": [{"splits": splits}]}).encode()


def _no_sleep(_seconds: float) -> None:
    return None


def _const(payload: bytes) -> Callable[..., bytes]:
    def get(_url: str, *, retries: int = 3) -> bytes:
        return payload

    return get


@pytest.fixture(autouse=True)
def _restore_constants(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(fetch.time, "sleep", _no_sleep)
    try:
        before: Path | None = constants_dir()
    except ConstantsNotFoundError:
        before = None
    yield
    sp.use_constants(before)


def test_update_writes_tables_the_loaders_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fetch, "_get", Net(last_season=2030))
    report = update_constants(tmp_path, first_season=2029, through=2030)

    assert report.fetched["guts.csv"] == [2030]
    assert report.fetched["park_fip.yaml"] == [2029, 2030]
    assert get_woba_weights(2030).w_hr == 2.05
    assert sp.get_fip_park_factor("NYY", 2030) == 102.0
    assert get_league_war_constants(2030).games == 162
    # 1450.1 and 1449.2 innings are 4351 and 4349 outs
    assert get_league_war_constants(2030).outs == 8700
    park = yaml.safe_load((tmp_path / "park_factors.yaml").read_text(encoding="utf-8"))["parks"][
        "NYY"
    ]
    assert park["season"] == 2030 and park["basic_5yr"] == 101.3 and park["hr_factor"] == 104.4


def test_rerun_fetches_only_missing_seasons_and_the_latest_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    net = Net(last_season=2030)
    monkeypatch.setattr(fetch, "_get", net)
    update_constants(tmp_path, first_season=2026, through=2030)
    net.calls.clear()

    report = update_constants(tmp_path, first_season=2026, through=2031)

    assert report.skipped["park_fip.yaml"] == [2026, 2027, 2028, 2029]
    assert report.fetched["park_fip.yaml"] == [2030]  # 2031 has no data yet; 2030 is refetched
    park_calls = [c for c in net.calls if "type=pf" in c]
    assert sorted(c.rsplit("=", 1)[1] for c in park_calls) == ["2030", "2031"]


def test_unknown_park_team_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fetch, "_get", Net(last_season=2030, park_team="Seals"))
    with pytest.raises(FetchError, match="Seals"):
        update_constants(tmp_path, first_season=2030, through=2030)


def test_changed_page_layout_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fetch, "_get", _const(b"<html>no data here</html>"))
    with pytest.raises(FetchError, match="no longer embeds"):
        fetch.fetch_guts()


def test_guts_missing_columns_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fetch, "_get", _const(_page([{"Season": 2030}])))
    with pytest.raises(FetchError, match="missing columns"):
        fetch.fetch_guts()


def test_cache_directory_is_read_without_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.delenv("SABERMETRICSPY_CONSTANTS", raising=False)
    sp.use_constants(None)
    with pytest.raises(ConstantsNotFoundError, match="constants update"):
        constants_dir()

    monkeypatch.setattr(fetch, "_get", Net(last_season=2030))
    update_constants(default_cache_dir(), first_season=2030, through=2030, use=False)
    assert constants_dir() == default_cache_dir()
    assert get_woba_weights(2030).lg_woba == 0.32
