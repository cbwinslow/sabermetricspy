"""Player-id crosswalk: loader, translation on every backend, name lookup, attribution, using a hand-built register."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import sabermetricspy.ids as ids_module
from sabermetricspy.ids import (
    ID_SYSTEMS,
    REGISTER_LICENSE,
    download_register,
    find_players,
    load_register,
    normalize_name,
    player_id,
    translate_ids,
    update_register,
)

HEADER = (
    "key_person,key_uuid,key_mlbam,key_retro,key_bbref,key_bbref_minors,key_fangraphs,key_npb,key_sr_nfl,"
    "key_sr_nba,key_sr_nhl,key_wikidata,name_last,name_first,name_given,name_suffix,name_matrilineal,name_nick,"
    "birth_year,birth_month,birth_day,death_year,death_month,death_day,pro_played_first,pro_played_last,"
    "mlb_played_first,mlb_played_last,col_played_first,col_played_last,pro_managed_first,pro_managed_last,"
    "mlb_managed_first,mlb_managed_last,col_managed_first,col_managed_last,pro_umpired_first,pro_umpired_last,"
    "mlb_umpired_first,mlb_umpired_last"
)
COLS = HEADER.split(",")


def _row(**values: str) -> str:
    uuid = values["key_uuid"]
    values.setdefault("key_person", uuid[:8])
    return ",".join(values.get(c, "") for c in COLS)


ROWS = {
    "people-0.csv": [
        _row(
            key_uuid="00000001-aaaa",
            key_mlbam="100",
            key_retro="aaaaa001",
            key_bbref="aaaaa01",
            key_fangraphs="11",
            name_last="Alpha",
            name_first="Al",
            name_given="Alan",
            birth_year="1980",
            pro_played_first="2001",
            pro_played_last="2010",
        ),
        _row(
            key_uuid="00000002-bbbb",
            key_mlbam="200",
            key_retro="nunez001",
            key_bbref="nunezj01",
            key_fangraphs="22",
            name_last="Núñez",
            name_first="José",
            name_given="José Luis",
            birth_year="1990",
            pro_played_first="2012",
            pro_played_last="2020",
        ),
        _row(
            key_uuid="00000003-cccc",
            key_mlbam="300",
            key_retro="grifk001",
            key_bbref="griffke01",
            key_fangraphs="33",
            name_last="Griffey",
            name_first="Ken",
            name_given="George Kenneth",
            name_suffix="Jr.",
            birth_year="1969",
            pro_played_first="1987",
            pro_played_last="2010",
        ),
        _row(
            key_uuid="00000004-dddd",
            key_mlbam="400",
            key_retro="grifk002",
            key_bbref="griffke02",
            key_fangraphs="44",
            name_last="Griffey",
            name_first="Ken",
            name_given="George Kenneth",
            name_suffix="Sr.",
            birth_year="1950",
            pro_played_first="1968",
            pro_played_last="1991",
        ),
    ],
    "people-1.csv": [
        _row(
            key_uuid="10000001-eeee",
            key_mlbam="500",
            key_retro="smitj001",
            key_bbref="smithjo01",
            key_fangraphs="55",
            name_last="Smith",
            name_first="John",
            name_given="John",
            birth_year="1985",
            pro_played_first="2005",
            pro_played_last="2015",
        ),
        _row(
            key_uuid="10000002-ffff",
            key_mlbam="600",
            key_retro="smitj002",
            key_bbref="smithjo01",
            key_fangraphs="66",
            name_last="Smith",
            name_first="John",
            name_given="John",
            birth_year="1950",
            pro_played_first="1970",
            pro_played_last="1980",
        ),
        _row(
            key_uuid="10000003-gggg",
            key_mlbam="",
            key_retro="nomlb001",
            key_bbref="",
            key_fangraphs="",
            name_last="Nomlb",
            name_first="Nora",
            name_given="Nora",
            birth_year="1995",
            pro_played_first="2016",
            pro_played_last="2017",
        ),
    ],
}
SHARDS = tuple(ROWS)


@pytest.fixture
def register_dir(tmp_path: Path) -> Path:
    for name, rows in ROWS.items():
        (tmp_path / name).write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    (tmp_path / "fetched.txt").write_text("2026-10-20", encoding="utf-8")
    return tmp_path


def _frame(retro: Sequence[str | None]) -> pl.DataFrame:
    return pl.DataFrame({"key_retro": retro, "pa": list(range(len(retro)))})


def test_loader_types_ids_and_reads_the_fetch_date(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    assert reg.people.schema["key_mlbam"] == pl.Int64
    assert reg.people.schema["key_fangraphs"] == pl.Int64
    assert reg.people.schema["key_retro"] == pl.Utf8
    assert reg.fetched_on == "2026-10-20"
    assert reg.commit is None
    assert reg.people.height == 7


def test_missing_shard_is_named(register_dir: Path) -> None:
    with pytest.raises(FileNotFoundError, match=r"people-2.csv"):
        load_register(register_dir, shards=(*SHARDS, "people-2.csv"))


def test_missing_default_register_says_how_to_get_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SABERMETRICSPY_REGISTER", str(tmp_path / "absent"))
    with pytest.raises(FileNotFoundError, match="download_register"):
        load_register()


def test_translate_retro_to_mlbam_keeps_order_and_rows(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    ids = ["grifk001", "aaaaa001", "grifk001", "nunez001"] * 250
    res = translate_ids(_frame(ids), "retro", "mlbam", register=reg)
    out = res.df
    assert out.height == 1000
    assert out["pa"].to_list() == list(range(1000))
    assert out["key_mlbam"].to_list() == [300, 100, 300, 200] * 250
    assert out["key_retro"].to_list() == ids
    assert res.unmatched == 0


def test_unknown_id_and_person_without_target_are_null_and_counted(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    res = translate_ids(
        _frame(["aaaaa001", "zzzzz999", "nomlb001", None]), "retro", "mlbam", register=reg
    )
    assert res.df["key_mlbam"].to_list() == [100, None, None, None]
    assert res.unmatched == 3


def test_attribution_travels_with_the_result(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    res = translate_ids(_frame(["aaaaa001"]), "retro", "mlbam", register=reg)
    assert "Chadwick Bureau" in res.source
    assert (
        res.license == REGISTER_LICENSE == "Open Data Commons Attribution License 1.0 (ODC-BY 1.0)"
    )
    assert res.fetched_on == "2026-10-20"


def test_id_shared_by_two_people_raises_naming_both(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    df = pl.DataFrame({"key_bbref": ["smithjo01"]})
    with pytest.raises(
        ValueError,
        match=r"smithjo01.*10000001-eeee.*10000002-ffff|smithjo01.*10000002-ffff.*10000001-eeee",
    ):
        translate_ids(df, "bbref", "mlbam", register=reg)


def test_shared_id_not_in_the_frame_does_not_raise(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    res = translate_ids(pl.DataFrame({"key_bbref": ["griffke01"]}), "bbref", "mlbam", register=reg)
    assert res.df["key_mlbam"].to_list() == [300]


def test_unknown_system_and_existing_output_column_raise(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    with pytest.raises(ValueError, match="supported systems"):
        translate_ids(_frame(["aaaaa001"]), "retro", "espn", register=reg)
    both = _frame(["aaaaa001"]).with_columns(pl.lit(1).alias("key_mlbam"))
    with pytest.raises(ValueError, match="already exists"):
        translate_ids(both, "retro", "mlbam", register=reg)


def _backends(base: pl.DataFrame) -> dict[str, Any]:
    return {
        "polars": base,
        "pandas": base.to_pandas(),
        "pyarrow": base.to_arrow(),
        "duckdb": duckdb.from_arrow(base.to_arrow()),
    }


@pytest.mark.parametrize("backend", ["polars", "pandas", "pyarrow", "duckdb"])
def test_every_backend_gives_the_same_answer(register_dir: Path, backend: str) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    ids = ["grifk001", "aaaaa001", "zzzzz999", "nunez001"] * 25
    res = translate_ids(_backends(_frame(ids))[backend], "retro", "mlbam", register=reg)
    out = res.df
    if backend == "pandas":
        assert isinstance(out, pd.DataFrame)
        got = pl.from_pandas(out)
    elif backend == "pyarrow":
        assert isinstance(out, pa.Table)
        got = pl.from_arrow(out)
    elif backend == "duckdb":
        assert "duckdb" in type(out).__module__
        got = pl.from_arrow(out.to_arrow_table())
    else:
        assert isinstance(out, pl.DataFrame)
        got = out
    assert isinstance(got, pl.DataFrame)
    assert got["key_mlbam"].to_list() == [300, 100, None, 200] * 25
    assert got["pa"].to_list() == list(range(100))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("José Núñez", "jose nunez"),
        ("Ken Griffey Jr.", "ken griffey"),
        ("Cal Ripken, III", "cal ripken"),
        ("O'Neill", "oneill"),
        ("Smith-Jones", "smith jones"),
        ("  Mixed   CASE ", "mixed case"),
    ],
)
def test_normalize_name(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected


def test_name_lookup_ignores_accents_and_finds_the_register_spelling(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    for first, last in (("Jose", "Nunez"), ("JOSÉ", "núñez"), ("Jose Luis", "Nunez")):
        found = find_players(first, last, register=reg)
        assert found["key_uuid"].to_list() == ["00000002-bbbb"]


def test_ambiguous_name_lists_everyone_and_single_id_request_raises(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    assert find_players("John", "Smith", register=reg).height == 2
    with pytest.raises(ValueError, match="matches 2 people") as err:
        player_id("mlbam", "John", "Smith", register=reg)
    assert "b.1985" in str(err.value)
    assert player_id("mlbam", "John", "Smith", birth_year=1985, register=reg) == 500
    assert player_id("retro", "John", "Smith", season=1975, register=reg) == "smitj002"


def test_generational_suffix_people_are_both_returned(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    assert find_players("Ken", "Griffey", register=reg).height == 2
    assert player_id("bbref", "Ken", "Griffey", birth_year=1969, register=reg) == "griffke01"


def test_no_match_and_missing_id_raise(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    assert find_players("Nobody", "Here", register=reg).height == 0
    with pytest.raises(ValueError, match="No player"):
        player_id("mlbam", "Nobody", "Here", register=reg)
    with pytest.raises(ValueError, match="no mlbam id"):
        player_id("mlbam", "Nora", "Nomlb", register=reg)


def test_all_id_systems_map_to_register_columns() -> None:
    assert set(ID_SYSTEMS.values()) <= set(COLS)


def _commit_dir(root: Path, commit: str, ids: str) -> None:
    """A fake register commit: `<root>/<commit>/data/people-*.csv`, one shard per entry in SHARDS."""
    data = root / commit / "data"
    data.mkdir(parents=True)
    for name in SHARDS:
        row = _row(
            key_uuid=f"{commit}-{name[7]}",
            key_mlbam=ids,
            key_retro=f"r{commit}{name[7]}",
            name_last="Zed",
            name_first="Zoe",
        )
        (data / name).write_text("\n".join([HEADER, row]) + "\n", encoding="utf-8")


def test_download_is_pinned_to_a_commit_and_records_it(tmp_path: Path) -> None:
    served = tmp_path / "served"
    _commit_dir(served, "c1", "111")
    _commit_dir(served, "c2", "222")
    template = served.as_uri() + "/{ref}/data"
    first = download_register(tmp_path / "one", commit="c1", base_url=template, shards=SHARDS)
    second = download_register(tmp_path / "two", commit="c2", base_url=template, shards=SHARDS)
    reg1, reg2 = load_register(first, shards=SHARDS), load_register(second, shards=SHARDS)
    assert reg1.commit == "c1" and reg2.commit == "c2"
    assert set(reg1.people["key_mlbam"].to_list()) == {111}
    assert set(reg2.people["key_mlbam"].to_list()) == {222}
    assert reg1.fetched_on is not None and len(reg1.fetched_on) == 10


def test_download_resolves_the_ref_to_a_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    served = tmp_path / "served"
    _commit_dir(served, "abc", "333")
    monkeypatch.setattr(ids_module, "_resolve_commit", lambda ref: "abc")  # pyright: ignore[reportUnknownLambdaType]
    dest = download_register(
        tmp_path / "d", base_url=served.as_uri() + "/{ref}/data", shards=SHARDS
    )
    assert load_register(dest, shards=SHARDS).commit == "abc"


def test_download_without_a_resolvable_commit_warns_and_records_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    served = tmp_path / "served"
    _commit_dir(served, "master", "444")
    monkeypatch.setattr(ids_module, "_resolve_commit", lambda ref: None)  # pyright: ignore[reportUnknownLambdaType]
    with pytest.warns(UserWarning, match="unpinned"):
        dest = download_register(
            tmp_path / "d", base_url=served.as_uri() + "/{ref}/data", shards=SHARDS
        )
    assert load_register(dest, shards=SHARDS).commit is None


def test_update_skips_download_when_commit_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    served = tmp_path / "served"
    _commit_dir(served, "c1", "111")
    dest = download_register(
        tmp_path / "d", commit="c1", base_url=served.as_uri() + "/{ref}/data", shards=SHARDS
    )
    monkeypatch.setattr(ids_module, "_resolve_commit", lambda ref: "c1")  # pyright: ignore[reportUnknownLambdaType]
    monkeypatch.setattr(ids_module, "download_register", _must_not_download)
    result = update_register(dest, shards=SHARDS)
    assert not result.updated and result.commit == "c1" and result.previous_commit == "c1"


def _must_not_download(*args: Any, **kwargs: Any) -> Path:
    raise AssertionError("download_register must not run when the commit is unchanged")


def test_update_downloads_when_a_newer_commit_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    served = tmp_path / "served"
    _commit_dir(served, "c1", "111")
    _commit_dir(served, "c2", "222")
    template = served.as_uri() + "/{ref}/data"
    dest = download_register(tmp_path / "d", commit="c1", base_url=template, shards=SHARDS)
    monkeypatch.setattr(ids_module, "_resolve_commit", lambda ref: "c2")  # pyright: ignore[reportUnknownLambdaType]
    monkeypatch.setattr(ids_module, "REGISTER_URL", template)
    real = download_register
    monkeypatch.setattr(
        ids_module,
        "download_register",
        lambda d, **kw: real(d, base_url=template, **kw),  # pyright: ignore[reportUnknownLambdaType]
    )
    result = update_register(dest, shards=SHARDS)
    assert result.updated and result.previous_commit == "c1" and result.commit == "c2"
    reg = load_register(dest, shards=SHARDS)
    assert reg.commit == "c2" and set(reg.people["key_mlbam"].to_list()) == {222}


def test_update_raises_when_upstream_cannot_be_reached_and_keeps_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    served = tmp_path / "served"
    _commit_dir(served, "c1", "111")
    dest = download_register(
        tmp_path / "d", commit="c1", base_url=served.as_uri() + "/{ref}/data", shards=SHARDS
    )
    monkeypatch.setattr(ids_module, "_resolve_commit", lambda ref: None)  # pyright: ignore[reportUnknownLambdaType]
    with pytest.raises(ConnectionError, match="left unchanged"):
        update_register(dest, shards=SHARDS)
    assert load_register(dest, shards=SHARDS).commit == "c1"


def test_failed_download_leaves_the_old_register_intact(tmp_path: Path) -> None:
    served = tmp_path / "served"
    _commit_dir(served, "c1", "111")
    _commit_dir(served, "c2", "222")
    (served / "c2" / "data" / SHARDS[-1]).unlink()
    template = served.as_uri() + "/{ref}/data"
    dest = download_register(tmp_path / "d", commit="c1", base_url=template, shards=SHARDS)
    with pytest.raises(OSError):
        download_register(dest, commit="c2", base_url=template, shards=SHARDS)
    reg = load_register(dest, shards=SHARDS)
    assert reg.commit == "c1" and set(reg.people["key_mlbam"].to_list()) == {111}


def _serve_two_commits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Two fake upstream commits on disk; downloads read from them instead of GitHub. Returns the URL template."""
    served = tmp_path / "served"
    _commit_dir(served, "c1", "111")
    _commit_dir(served, "c2", "222")
    template = served.as_uri() + "/{ref}/data"
    real = download_register
    monkeypatch.setattr(
        ids_module,
        "download_register",
        lambda d, **kw: real(d, base_url=template, **kw),  # pyright: ignore[reportUnknownLambdaType]
    )
    return template


def _default_register(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("SABERMETRICSPY_REGISTER", str(tmp_path / "default"))
    monkeypatch.setenv("SABERMETRICSPY_AUTO_UPDATE", "1")
    return tmp_path / "default"


def test_default_register_is_downloaded_automatically_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _serve_two_commits(tmp_path, monkeypatch)
    root = _default_register(tmp_path, monkeypatch)
    monkeypatch.setattr(ids_module, "_resolve_commit", lambda ref: "c1")  # pyright: ignore[reportUnknownLambdaType]
    monkeypatch.setattr(ids_module, "REGISTER_SHARDS", SHARDS)
    reg = load_register(shards=SHARDS)
    assert reg.commit == "c1" and root.is_dir()


def test_default_register_updates_itself_when_upstream_has_a_newer_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template = _serve_two_commits(tmp_path, monkeypatch)
    root = _default_register(tmp_path, monkeypatch)
    download_register(root, commit="c1", base_url=template, shards=SHARDS)
    record = json.loads((root / "provenance.json").read_text(encoding="utf-8"))
    record["checked_on"] = "2020-01-01"  # last checked long ago
    (root / "provenance.json").write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(ids_module, "_resolve_commit", lambda ref: "c2")  # pyright: ignore[reportUnknownLambdaType]
    reg = load_register(shards=SHARDS)
    assert reg.commit == "c2" and set(reg.people["key_mlbam"].to_list()) == {222}


def test_default_register_is_looked_up_at_most_once_a_day(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template = _serve_two_commits(tmp_path, monkeypatch)
    root = _default_register(tmp_path, monkeypatch)
    download_register(root, commit="c1", base_url=template, shards=SHARDS)  # checked today

    def boom(ref: str) -> str:
        raise AssertionError("upstream must not be contacted twice in one day")

    monkeypatch.setattr(ids_module, "_resolve_commit", boom)
    assert load_register(shards=SHARDS).commit == "c1"


def test_offline_default_register_uses_the_copy_it_has_and_warns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template = _serve_two_commits(tmp_path, monkeypatch)
    root = _default_register(tmp_path, monkeypatch)
    download_register(root, commit="c1", base_url=template, shards=SHARDS)
    record = json.loads((root / "provenance.json").read_text(encoding="utf-8"))
    record["checked_on"] = "2020-01-01"
    (root / "provenance.json").write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(ids_module, "_resolve_commit", lambda ref: None)  # pyright: ignore[reportUnknownLambdaType]
    with pytest.warns(UserWarning, match="using the copy already"):
        reg = load_register(shards=SHARDS)
    assert reg.commit == "c1"


def test_offline_with_no_register_raises_file_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _default_register(tmp_path, monkeypatch)
    monkeypatch.setattr(ids_module, "_resolve_commit", lambda ref: None)  # pyright: ignore[reportUnknownLambdaType]
    with pytest.raises(FileNotFoundError, match="could not be downloaded"):
        load_register(shards=SHARDS)


def test_explicit_path_and_opt_out_never_touch_the_network(
    register_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(ref: str) -> str:
        raise AssertionError("no network expected")

    monkeypatch.setattr(ids_module, "_resolve_commit", boom)
    load_register(register_dir, shards=SHARDS)  # explicit path
    monkeypatch.setenv("SABERMETRICSPY_REGISTER", str(register_dir))
    monkeypatch.setenv("SABERMETRICSPY_AUTO_UPDATE", "0")
    load_register(shards=SHARDS)  # default location, opted out


def test_cache_follows_the_files(register_dir: Path, tmp_path: Path) -> None:
    first = load_register(register_dir, shards=SHARDS)
    assert load_register(register_dir, shards=SHARDS) is first
    shard = register_dir / "people-1.csv"
    shard.write_text(shard.read_text("utf-8").replace("Nomlb", "Changed"), encoding="utf-8")
    again = load_register(register_dir, shards=SHARDS)
    assert again is not first
    assert "Changed" in again.people["name_last"].to_list()


def test_relative_path_in_two_directories_loads_each_register(
    register_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = tmp_path / "other"
    other.mkdir()
    for name, rows in ROWS.items():
        (other / name).write_text("\n".join([HEADER, *rows[:1]]) + "\n", encoding="utf-8")
    monkeypatch.chdir(register_dir)
    here = load_register(".", shards=SHARDS)
    monkeypatch.chdir(other)
    there = load_register(".", shards=SHARDS)
    assert here.people.height == 7 and there.people.height == 2


# --- the caller's frame is preserved ---------------------------------------------------------------------------


def test_pandas_keeps_index_columns_and_gets_nullable_integers(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    frame = pd.DataFrame(
        {"key_retro": ["aaaaa001", "zzzzz999", "nunez001"], "n": [1.5, 2.5, 3.5]},
        index=[10, 20, 30],
    )
    out = translate_ids(frame, "retro", "mlbam", register=reg).df
    assert list(out.index) == [10, 20, 30]
    assert list(out.columns) == ["key_retro", "n", "key_mlbam"]
    assert out["n"].tolist() == [1.5, 2.5, 3.5]
    assert str(out["key_mlbam"].dtype) == "Int64"
    assert out["key_mlbam"].tolist()[0] == 100 and pd.isna(out["key_mlbam"].iloc[1])
    assert list(frame.columns) == ["key_retro", "n"]  # the input is not modified


def test_lazy_frame_stays_lazy(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    out = translate_ids(_frame(["aaaaa001", "nunez001"]).lazy(), "retro", "mlbam", register=reg).df
    assert isinstance(out, pl.LazyFrame)
    assert out.collect()["key_mlbam"].to_list() == [100, 200]


@pytest.mark.parametrize("helper", ["__key", "__row", "k", "v", "i"])
def test_columns_named_like_helpers_survive(register_dir: Path, helper: str) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    frame = _frame(["aaaaa001", "nunez001"]).with_columns(pl.Series(helper, [7, 8]))
    out = translate_ids(frame, "retro", "mlbam", register=reg).df
    assert out[helper].to_list() == [7, 8]
    assert out["key_mlbam"].to_list() == [100, 200]


def test_duckdb_and_pyarrow_keep_other_columns_exactly(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    base = _frame(["aaaaa001", "nunez001"]).with_columns(pl.Series("x", [1, 2], dtype=pl.Int32))
    arrow = translate_ids(base.to_arrow(), "retro", "mlbam", register=reg).df
    assert arrow.schema.field("x").type == pa.int32()
    rel = translate_ids(duckdb.from_arrow(base.to_arrow()), "retro", "mlbam", register=reg).df
    assert rel.columns == ["key_retro", "pa", "x", "key_mlbam"]


# --- exact id matching -----------------------------------------------------------------------------------------


def test_fractional_and_padded_ids(register_dir: Path) -> None:
    reg = load_register(register_dir, shards=SHARDS)
    floats = pl.DataFrame({"key_mlbam": [100.0, 100.7, float("nan"), None]})
    out = translate_ids(floats, "mlbam", "retro", register=reg)
    assert out.df["key_retro"].to_list() == ["aaaaa001", None, None, None]
    padded = pl.DataFrame({"key_retro": [" aaaaa001 ", "aaaaa001\t"]})
    assert translate_ids(padded, "retro", "mlbam", register=reg).df["key_mlbam"].to_list() == [
        100,
        100,
    ]
    text = pl.DataFrame({"key_mlbam": [" 100", "100.5", "abc"]})
    assert translate_ids(text, "mlbam", "retro", register=reg).df["key_retro"].to_list() == [
        "aaaaa001",
        None,
        None,
    ]


# --- names that cannot be normalized ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Bj\u00f8rn", "bjorn"),
        ("\u0141ukasz", "lukasz"),
        ("D\u00e6hli", "daehli"),
        ("\u0110uri\u0107", "duric"),
        ("S\u00f8ren \u00d8rsted", "soren orsted"),
        ("Jose\tAbreu", "jose abreu"),
        ("Stra\u00dfe", "strasse"),
    ],
)
def test_normalize_name_folds_stroked_letters_and_tabs(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected


def test_non_latin_query_raises_and_empty_register_names_never_match(register_dir: Path) -> None:
    extra = _row(key_uuid="20000001-hhhh", key_mlbam="700", name_last="", name_first="")
    shard = register_dir / "people-1.csv"
    shard.write_text(shard.read_text("utf-8") + extra + "\n", encoding="utf-8")
    reg = load_register(register_dir, shards=SHARDS)
    with pytest.raises(ValueError, match="Cannot normalize"):
        find_players("\u7fd4\u5e73", "\u5927\u8c37", register=reg)
    with pytest.raises(ValueError, match="Cannot normalize"):
        player_id("mlbam", "...", "---", register=reg)
    assert find_players("Al", "Alpha", register=reg).height == 1


def test_calls_are_recorded_by_telemetry(register_dir: Path) -> None:
    import sabermetricspy as sp

    with sp.telemetry.session() as tracker:
        reg = load_register(register_dir, shards=SHARDS)
        translate_ids(_frame(["aaaaa001"]), "retro", "mlbam", register=reg)
        find_players("Al", "Alpha", register=reg)
    names = {s.name for s in tracker.spans if s.category == "ids"}
    assert {"load_register", "translate_ids", "find_players"} <= names
