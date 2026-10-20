"""Multi-source name register: hand-built sources, then (opt-in) the real Chadwick and Retrosheet files."""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path

import polars as pl
import pytest

from sabermetricspy.ids import PlayerRegister, default_register_path
from sabermetricspy.ids.names import (
    RETROSHEET_NOTICE,
    NameRegister,
    build_name_register,
    default_retrosheet_path,
    download_name_sources,
    load_name_register,
    read_retrosheet_biofile,
)

PEOPLE_COLUMNS = {
    "key_person": pl.Utf8,
    "key_uuid": pl.Utf8,
    "key_retro": pl.Utf8,
    "name_first": pl.Utf8,
    "name_given": pl.Utf8,
    "name_last": pl.Utf8,
    "name_nick": pl.Utf8,
    "name_matrilineal": pl.Utf8,
    "birth_year": pl.Int64,
    "birth_month": pl.Utf8,
    "birth_day": pl.Utf8,
    "mlb_played_first": pl.Int64,
}


def _people(rows: Sequence[Mapping[str, object]]) -> PlayerRegister:
    frame = pl.DataFrame(
        {c: [r.get(c) for r in rows] for c in PEOPLE_COLUMNS}, schema=PEOPLE_COLUMNS
    )
    return PlayerRegister(people=frame, fetched_on="2026-10-20", commit="chad123", path="fixture")


NAMES_COLUMNS = [
    "key_person",
    "name_last",
    "name_first",
    "name_given",
    "altname_type",
    "altname_last",
    "altname_first",
    "altname_given",
    "altname_nick",
    "altname_date_start",
    "altname_date_end",
]
BIO_COLUMNS = [
    "id",
    "lastname",
    "usename",
    "fullname",
    "birthdate",
    "birthname",
    "altname",
    "debut_p",
]


def _frame(columns: Sequence[str], rows: Sequence[Mapping[str, object]]) -> pl.DataFrame:
    return pl.DataFrame(
        {c: [r.get(c) for r in rows] for c in columns}, schema=dict.fromkeys(columns, pl.Utf8)
    )


PEOPLE = [
    {
        "key_person": "p0000001",
        "key_uuid": "u1",
        "key_retro": "aaroh101",
        "name_first": "Hank",
        "name_given": "Henry Louis",
        "name_last": "Aaron",
        "name_nick": "The Hammer",
        "birth_year": 1934,
        "birth_month": "2",
        "birth_day": "5",
        "mlb_played_first": 1954,
    },
    {
        "key_person": "p0000002",
        "key_uuid": "u2",
        "key_retro": "nunez001",
        "name_first": "José",
        "name_given": "José Luis",
        "name_last": "Núñez",
        "name_matrilineal": "García",
        "birth_year": 1990,
        "birth_month": "6",
        "birth_day": "1",
        "mlb_played_first": 2012,
    },
    {
        "key_person": "p0000003",
        "key_uuid": "u3",
        "key_retro": "smitj001",
        "name_first": "John",
        "name_given": "John",
        "name_last": "Smith",
        "birth_year": 1985,
        "birth_month": "3",
        "birth_day": "9",
        "mlb_played_first": 2005,
    },
    {
        "key_person": "p0000004",
        "key_uuid": "u4",
        "key_retro": "smitj002",
        "name_first": "John",
        "name_given": "John",
        "name_last": "Smith",
        "birth_year": 1950,
        "mlb_played_first": 1970,
    },
    {
        "key_person": "shared01",
        "key_uuid": "u5",
        "key_retro": None,
        "name_first": "Ann",
        "name_given": "Ann",
        "name_last": "Onea",
    },
    {
        "key_person": "shared01",
        "key_uuid": "u6",
        "key_retro": None,
        "name_first": "Bea",
        "name_given": "Bea",
        "name_last": "Twob",
    },
]
NAMES = [
    {
        "key_person": "p0000003",
        "name_last": "Smith",
        "name_first": "John",
        "name_given": "John",
        "altname_type": "alias",
        "altname_last": "Smythe",
        "altname_first": None,
        "altname_given": "Jonathan",
        "altname_date_start": "1999",
        "altname_date_end": "2003",
    },
    {
        "key_person": "p0000001",
        "name_last": "Aaron",
        "name_first": "Hank",
        "name_given": "Henry Louis",
        "altname_type": "alt-spelling",
        "altname_last": "Aron",
    },
    {
        "key_person": "shared01",
        "altname_type": "alias",
        "altname_last": "Shared",
        "altname_first": "S",
    },
    {
        "key_person": "gone0000",
        "altname_type": "alias",
        "altname_last": "Gone",
        "altname_first": "G",
    },
]
LINKS = [
    {"key_person": "p0000001", "source": "findagrave", "value": "123"},
    {"key_person": "p0000002", "source": "tsncardS", "value": "456"},
    {"key_person": "gone0000", "source": "findagrave", "value": "9"},
]
BIO = [
    {
        "id": "aaroh101",
        "lastname": "Aaron",
        "usename": "Hank",
        "fullname": "Henry Louis Aaron",
        "birthdate": "19340205",
        "debut_p": "19540413",
    },
    {
        "id": "nunez001",
        "lastname": "Nunez",
        "usename": "Jose",
        "fullname": "Jose Luis Nunez",
        "birthdate": "19900106",
        "debut_p": "20150401",
    },
    {
        "id": "smitj001",
        "lastname": "Smith",
        "usename": "Johnny",
        "fullname": "John Smith",
        "birthdate": "19850000",
        "birthname": "John Smithers",
        "altname": "Jack Smitty",
        "debut_p": "20050401",
    },
    {"id": "lastonly1", "lastname": "Aberdino", "fullname": "Aberdino", "debut_p": "19470911"},
    {
        "id": "retronly1",
        "lastname": "Zeta",
        "usename": "Zed",
        "fullname": "Zachary Zeta",
        "birthdate": "19700707",
        "debut_p": "19900101",
    },
]


@pytest.fixture(scope="module")
def register() -> NameRegister:
    return build_name_register(
        _people(PEOPLE),
        _frame(NAMES_COLUMNS, NAMES),
        _frame(["key_person", "source", "value"], LINKS),
        _frame(BIO_COLUMNS, BIO),
        retrosheet_sha256="abc123",
        retrosheet_file="biofile.zip",
    )


def _rows(register: NameRegister, source: str, name_type: str) -> pl.DataFrame:
    return register.names.filter((pl.col("source") == source) & (pl.col("name_type") == name_type))


def test_each_source_and_name_type_is_a_separate_row(register: NameRegister) -> None:
    names = register.names
    assert set(names["source"].unique()) == {
        "chadwick_people",
        "chadwick_names",
        "retrosheet_biofile",
    }
    nick = _rows(register, "chadwick_people", "nickname")
    assert nick["first"].to_list() == ["The Hammer"] and nick["last"].to_list() == ["Aaron"]
    matri = _rows(register, "chadwick_people", "matrilineal")
    assert matri["last"].to_list() == ["García"]
    given = _rows(register, "chadwick_people", "given")
    assert "Henry Louis" in given["first"].to_list()
    assert (
        "John" not in given["first"].to_list()
    )  # given equal to the common first name adds no row
    assert (
        _rows(register, "retrosheet_biofile", "full")["first"].to_list().count("Henry Louis") == 1
    )
    assert _rows(register, "retrosheet_biofile", "birth")["last"].to_list() == ["Smithers"]
    assert _rows(register, "retrosheet_biofile", "alias")["first"].to_list() == ["Jack"]


def test_alternate_names_keep_type_language_free_dates_and_fill_gaps_from_the_person(
    register: NameRegister,
) -> None:
    alias = _rows(register, "chadwick_names", "alias").filter(pl.col("key_uuid") == "u3")
    assert set(alias["last"].to_list()) == {"Smythe"}
    assert (
        "John" in alias["first"].to_list()
    )  # first part the alias does not change is the person's own
    assert "Jonathan" in alias["first"].to_list()
    assert alias["date_start"].drop_nulls().unique().to_list() == ["1999"]
    assert alias["date_end"].drop_nulls().unique().to_list() == ["2003"]
    assert _rows(register, "chadwick_names", "alt_spelling")["last"].to_list() == ["Aron"]


def test_reused_key_person_and_missing_person_are_reported_not_guessed(
    register: NameRegister,
) -> None:
    reasons = {
        (r["file"], r["key_person"]): r["reason"] for r in register.unresolved.iter_rows(named=True)
    }
    assert reasons[("names.csv", "shared01")] == "key_person belongs to several people"
    assert reasons[("names.csv", "gone0000")] == "no person with this key_person"
    assert reasons[("links.csv", "gone0000")] == "no person with this key_person"
    assert register.names.filter(pl.col("last") == "Shared").height == 0


def test_links_resolve_to_people_with_lowercase_sources(register: NameRegister) -> None:
    assert sorted(register.links["source"].unique().to_list()) == ["findagrave", "tsncards"]
    assert register.links.filter(pl.col("key_uuid") == "u2")["value"].to_list() == ["456"]


def test_people_known_only_by_last_name_are_listed_not_dropped(register: NameRegister) -> None:
    assert register.last_name_only["key_retro"].to_list() == ["lastonly1"]
    assert register.last_name_only["last"].to_list() == ["Aberdino"]
    assert register.names.filter(pl.col("key_retro") == "lastonly1").height == 0


def test_retrosheet_only_person_is_kept_without_a_chadwick_key(register: NameRegister) -> None:
    only = register.names.filter(pl.col("key_retro") == "retronly1")
    assert only.height > 0 and only["key_uuid"].null_count() == only.height
    hit = register.search("Zed", "Zeta")
    assert hit["key_retro"].to_list() == ["retronly1"] and hit["key_uuid"].to_list() == [None]


def test_search_finds_nicknames_aliases_and_accents_once_per_person(register: NameRegister) -> None:
    hammer = register.search("The Hammer", "Aaron")
    assert hammer["key_uuid"].to_list() == ["u1"]
    hank = register.search("Hank", "Aaron")
    assert hank.height == 1 and set(hank["sources"][0]) == {"chadwick_people", "retrosheet_biofile"}
    accent = register.search("Jose", "Nunez")
    assert accent["key_uuid"].to_list() == ["u2"]
    assert register.search("Jonathan", "Smythe")["key_uuid"].to_list() == ["u3"]
    assert register.search("John Louis", "Aaron").height == 0


def test_ambiguous_query_returns_every_person(register: NameRegister) -> None:
    both = register.search("John", "Smith")
    assert sorted(both["key_uuid"].to_list()) == ["u3", "u4"]


def test_single_person_request_raises_on_none_or_several(register: NameRegister) -> None:
    one = register.person("Hank", "Aaron")
    assert one["key_uuid"] == "u1" and one["key_retro"] == "aaroh101"
    assert set(one["sources"]) == {"chadwick_people", "retrosheet_biofile"}
    with pytest.raises(ValueError, match="matches 2 people") as err:
        register.person("John", "Smith")
    assert "u3" in str(err.value) and "u4" in str(err.value)
    with pytest.raises(ValueError, match="No person"):
        register.person("Nobody", "Here")


def test_names_that_normalize_to_nothing_raise(register: NameRegister) -> None:
    with pytest.raises(ValueError, match="Cannot normalize"):
        register.search("翔平", "大谷")


def test_conflicts_are_reported_with_both_values_and_never_merged(register: NameRegister) -> None:
    c = register.conflicts
    by = {(r["key_retro"], r["field"]): r for r in c.iter_rows(named=True)}
    swap = by[("nunez001", "birth_date")]
    assert (swap["chadwick"], swap["retrosheet"]) == ("1990-06-01", "1990-01-06")
    assert ("nunez001", "last_name") not in by  # accent only: Nuñez against Nunez is not a conflict
    assert ("aaroh101", "birth_date") not in by and ("aaroh101", "last_name") not in by
    assert (
        "smitj001",
        "birth_date",
    ) not in by  # partial Retrosheet date (year only) agrees on the year
    name = by[("smitj001", "first_name")]
    assert (name["chadwick"], name["retrosheet"]) == ("John", "Johnny")
    assert ("aaroh101", "first_name") not in by  # Hank equals the common first name
    assert ("nunez001", "first_year_vs_debut") in by
    year = by[("nunez001", "first_year_vs_debut")]
    assert (year["chadwick"], year["retrosheet"]) == ("2012", "2015")


def test_provenance_and_credits_travel_with_the_register(register: NameRegister) -> None:
    assert register.chadwick_commit == "chad123" and register.chadwick_fetched_on == "2026-10-20"
    assert register.retrosheet_sha256 == "abc123" and register.retrosheet_file == "biofile.zip"
    assert "Chadwick Bureau" in register.sources[0] and "Retrosheet" in register.sources[1]
    assert "ODC-BY" in register.licenses["chadwick"]
    assert register.licenses["retrosheet"] == RETROSHEET_NOTICE
    assert "copyrighted by Retrosheet" in RETROSHEET_NOTICE


# --- files: pinned download and loading ------------------------------------------------------------------------


FULL_PEOPLE_HEADER = "key_person,key_uuid,key_mlbam,key_retro,key_bbref,key_bbref_minors,key_fangraphs,key_npb,key_sr_nfl,key_sr_nba,key_sr_nhl,key_wikidata,name_last,name_first,name_given,name_suffix,name_matrilineal,name_nick,birth_year,birth_month,birth_day,death_year,death_month,death_day,pro_played_first,pro_played_last,mlb_played_first,mlb_played_last,col_played_first,col_played_last,pro_managed_first,pro_managed_last,mlb_managed_first,mlb_managed_last,col_managed_first,col_managed_last,pro_umpired_first,pro_umpired_last,mlb_umpired_first,mlb_umpired_last"


def _write_chadwick(directory: Path, tag: str) -> None:
    directory.mkdir(parents=True)
    header = FULL_PEOPLE_HEADER
    for name in ("people-0.csv", "people-1.csv"):
        (directory / name).write_text(header + "\n", encoding="utf-8")
    row = {
        "key_person": "p1",
        "name_last": "Smith",
        "name_first": "John",
        "name_given": "John",
        "altname_type": "alias",
        "altname_last": tag,
    }
    (directory / "names.csv").write_text(
        ",".join(NAMES_COLUMNS) + "\n" + ",".join(row.get(c, "") for c in NAMES_COLUMNS) + "\n",
        encoding="utf-8",
    )
    (directory / "links.csv").write_text(
        "key_person,source,value\np1,findagrave,1\n", encoding="utf-8"
    )


def test_download_pins_the_chadwick_files_to_a_commit(tmp_path: Path) -> None:
    served = tmp_path / "served"
    _write_chadwick(served / "c1" / "data", "One")
    _write_chadwick(served / "c2" / "data", "Two")
    cdir = download_name_sources(
        tmp_path / "c", chadwick_commit="c2", chadwick_url=served.as_uri() + "/{ref}/data"
    )
    assert "Two" in (cdir / "names.csv").read_text("utf-8")
    assert json.loads((cdir / "provenance.json").read_text("utf-8"))["names_commit"] == "c2"


BIO_CSV = ",".join(BIO_COLUMNS) + "\nx1,Last,First,First Last,19000101,,,19200101\n"


def test_retrosheet_biofile_reads_from_a_csv_a_folder_or_the_official_zip(tmp_path: Path) -> None:
    csv = tmp_path / "loose" / "biofile0.csv"
    csv.parent.mkdir()
    csv.write_bytes(BIO_CSV.encode())  # bytes, so Windows does not turn \n into \r\n
    archive = tmp_path / "biofile.zip"
    with zipfile.ZipFile(
        archive, "w"
    ) as z:  # the official zip holds eight files; biofile0.csv is one of them
        z.writestr("biofile.csv", "PLAYERID,LAST\nx1,Last\n")
        z.writestr("biofile0.csv", BIO_CSV)
        z.writestr("relatives.csv", "id1,relation,id2\n")
    zip_dir = tmp_path / "zipdir"
    zip_dir.mkdir()
    (zip_dir / "biofile.zip").write_bytes(archive.read_bytes())
    results = [read_retrosheet_biofile(x) for x in (csv, csv.parent, archive, zip_dir)]
    for frame, digest, location in results:
        assert frame["id"].to_list() == ["x1"] and frame.columns == BIO_COLUMNS
        assert digest == hashlib.sha256(BIO_CSV.encode()).hexdigest()
        assert location
    assert (
        len({digest for _, digest, _ in results}) == 1
    )  # same release, same hash, however it is supplied


def test_retrosheet_hash_changes_when_the_file_changes(tmp_path: Path) -> None:
    csv = tmp_path / "biofile0.csv"
    csv.write_bytes(BIO_CSV.encode())
    before = read_retrosheet_biofile(csv)[1]
    csv.write_bytes((BIO_CSV + "x2,Other,Name,Name Other,19100101,,,19300101\n").encode())
    assert read_retrosheet_biofile(csv)[1] != before


def test_retrosheet_errors_say_where_to_get_the_file_and_what_is_wrong(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match=r"retrosheet\.org/biofile\.htm"):
        read_retrosheet_biofile(tmp_path / "nothing_here")
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("relatives.csv", "id1,relation,id2\n")
    with pytest.raises(ValueError, match=r"does not contain biofile0\.csv"):
        read_retrosheet_biofile(bad)


def test_load_reports_a_missing_file_and_how_to_fetch_it(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="download_name_sources"):
        load_name_register(tmp_path / "none", tmp_path / "also_none")


def test_load_builds_from_local_files(tmp_path: Path) -> None:
    cdir = tmp_path / "c"
    _write_chadwick(cdir, "Local")
    columns = FULL_PEOPLE_HEADER.split(",")
    values = {
        "key_person": "p1",
        "key_uuid": "u1",
        "key_mlbam": "1",
        "key_retro": "smitj001",
        "name_last": "Smith",
        "name_first": "John",
        "name_given": "John",
    }
    people_row = ",".join(values.get(c, "") for c in columns)
    (cdir / "people-0.csv").write_text(
        FULL_PEOPLE_HEADER + "\n" + people_row + "\n", encoding="utf-8"
    )
    archive = tmp_path / "biofile.zip"
    bio = ",".join(BIO_COLUMNS) + "\nsmitj001,Smith,John,John Smith,19000101,,,19200101\n"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("biofile0.csv", bio)
    reg = load_name_register(cdir, archive, shards=("people-0.csv", "people-1.csv"))
    assert reg.search("John", "Smith").height == 1
    assert reg.search("John", "Local").height == 1  # alias from the alternate-names file
    assert reg.retrosheet_sha256 == hashlib.sha256(bio.encode()).hexdigest()
    assert reg.retrosheet_file == str(archive)


# --- real files (opt-in) ---------------------------------------------------------------------------------------

_RETRO_DIR = default_retrosheet_path()
_REAL = (default_register_path() / "names.csv").is_file() and (
    (_RETRO_DIR / "biofile0.csv").is_file() or (_RETRO_DIR / "biofile.zip").is_file()
)


@pytest.mark.skipif(
    not _REAL,
    reason="Chadwick names.csv or the Retrosheet biofile not found; see download_name_sources() and read_retrosheet_biofile()",
)
def test_real_sources_build_find_known_players_and_report_conflicts() -> None:
    """Checks on the real files. Figures below were measured 2026-10-20 on Chadwick master and on a copy of Retrosheet's
    `biofile0.csv` obtained through the Chadwick Bureau's mirror (commit 118094bb); they have not yet been re-measured on a
    file downloaded from retrosheet.org itself.

    The counts below are loose bounds, not pinned values, because the Chadwick register changes weekly. On that date: 27,049
    Retrosheet people; 756,290 name rows; conflicts: 291 birth dates, 298 first names, 46 last names (accents ignored) and
    606 first years against debut year; one `names.csv` row had no matching person.
    """
    reg = load_name_register()
    searchable = set(
        reg.names.filter(pl.col("source") == "retrosheet_biofile")["key_retro"].to_list()
    )
    last_only = set(
        reg.last_name_only.filter(pl.col("source") == "retrosheet_biofile")["key_retro"].to_list()
    )
    assert 25_000 < len(searchable) < 28_500
    assert 1_000 < len(last_only) < 1_500  # 1,196 on 2026-10-20: known only by last name
    assert not searchable & last_only
    assert len(searchable | last_only) > 27_000  # every Retrosheet person is accounted for (27,049)
    assert reg.names.height > 600_000
    by_field = dict(reg.conflicts.group_by("field").len().iter_rows())
    assert {"birth_date", "first_name", "last_name", "first_year_vs_debut"} <= set(by_field)
    assert all(count > 0 for count in by_field.values())
    trout = reg.search("Mike", "Trout")
    assert trout["key_retro"].to_list() == ["troum001"]
    assert set(trout["sources"][0]) == {"chadwick_people", "retrosheet_biofile"}
    assert reg.search("Hank", "Aaron")["key_retro"].to_list() == ["aaroh101"]
    assert reg.unresolved.height < 100
