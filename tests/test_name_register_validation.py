"""The name register refuses source tables whose layout changed, naming the missing columns."""

from __future__ import annotations

import polars as pl
import pytest

from sabermetricspy.ids import PlayerRegister
from sabermetricspy.ids.names import build_name_register


def _people(columns: list[str]) -> PlayerRegister:
    frame = pl.DataFrame({c: ["x"] for c in columns})
    return PlayerRegister(people=frame, fetched_on=None, commit=None, path="fixture")


FULL_PEOPLE = [
    "key_person",
    "key_uuid",
    "key_retro",
    "name_first",
    "name_given",
    "name_last",
    "name_nick",
    "name_matrilineal",
    "birth_year",
    "birth_month",
    "birth_day",
    "mlb_played_first",
]
FULL_NAMES = [
    "key_person",
    "name_last",
    "name_first",
    "altname_type",
    "altname_last",
    "altname_first",
    "altname_given",
    "altname_nick",
    "altname_date_start",
    "altname_date_end",
]
FULL_LINKS = ["key_person", "source", "value"]
FULL_BIO = ["id", "lastname", "usename", "fullname", "birthdate", "birthname", "altname", "debut_p"]


def _frame(columns: list[str]) -> pl.DataFrame:
    return pl.DataFrame({c: pl.Series([], dtype=pl.Utf8) for c in columns})


@pytest.mark.parametrize(
    ("which", "drop", "label"),
    [
        ("people", "name_nick", "Chadwick people table"),
        ("names", "altname_nick", "names.csv"),
        ("links", "value", "links.csv"),
        ("bio", "usename", "biofile0.csv"),
    ],
)
def test_missing_source_columns_are_named(which: str, drop: str, label: str) -> None:
    columns = {
        "people": FULL_PEOPLE,
        "names": FULL_NAMES,
        "links": FULL_LINKS,
        "bio": FULL_BIO,
    }
    columns[which] = [c for c in columns[which] if c != drop]
    with pytest.raises(ValueError, match=rf"{label}.*{drop}"):
        build_name_register(
            _people(columns["people"]),
            _frame(columns["names"]),
            _frame(columns["links"]),
            _frame(columns["bio"]),
        )


def test_complete_but_empty_sources_build_an_empty_register() -> None:
    reg = build_name_register(
        _people(FULL_PEOPLE).__class__(
            people=pl.DataFrame(
                {c: pl.Series([], dtype=pl.Utf8) for c in FULL_PEOPLE}
            ).with_columns(
                pl.col("birth_year").cast(pl.Int64), pl.col("mlb_played_first").cast(pl.Int64)
            ),
            fetched_on=None,
            commit=None,
            path="fixture",
        ),
        _frame(FULL_NAMES),
        _frame(FULL_LINKS),
        _frame(FULL_BIO),
    )
    assert reg.names.height == 0 and reg.conflicts.height == 0 and reg.unresolved.height == 0
