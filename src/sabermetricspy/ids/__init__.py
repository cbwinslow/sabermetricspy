"""Player-id crosswalk and name lookup over the Chadwick Bureau Register.

The register (https://github.com/chadwickbureau/register) is published under the Open Data Commons Attribution License
1.0 by the Chadwick Bureau. It is not bundled: pass a local copy, or call `download_register` to fetch it.
"""

from __future__ import annotations

import datetime
import os
import re
import unicodedata
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Any

import polars as pl
from narwhals.typing import IntoFrame

from sabermetricspy.schema import to_polars_df
from sabermetricspy.telemetry import profiled

REGISTER_URL = "https://raw.githubusercontent.com/chadwickbureau/register/master/data"
REGISTER_SHARDS: tuple[str, ...] = tuple(f"people-{c}.csv" for c in "0123456789abcdef")
REGISTER_LICENSE = "Open Data Commons Attribution License 1.0 (ODC-BY 1.0)"
REGISTER_SOURCE = "Chadwick Bureau Register (https://github.com/chadwickbureau/register)"
REGISTER_ENV = "SABERMETRICSPY_REGISTER"
_FETCH_MARKER = "fetched.txt"

# Id system name -> register column.
ID_SYSTEMS: dict[str, str] = {
    "uuid": "key_uuid",
    "person": "key_person",
    "mlbam": "key_mlbam",
    "retro": "key_retro",
    "bbref": "key_bbref",
    "bbref_minors": "key_bbref_minors",
    "fangraphs": "key_fangraphs",
    "npb": "key_npb",
    "wikidata": "key_wikidata",
}
_INTEGER_SYSTEMS = frozenset({"mlbam", "fangraphs"})
_NAME_SUFFIXES = frozenset({"jr", "sr", "ii", "iii", "iv"})
_RESULT_COLUMNS = (
    "key_uuid",
    "key_mlbam",
    "key_retro",
    "key_bbref",
    "key_fangraphs",
    "name_first",
    "name_last",
    "name_given",
    "name_suffix",
    "birth_year",
    "pro_played_first",
    "pro_played_last",
    "mlb_played_first",
    "mlb_played_last",
)


def default_register_path() -> Path:
    """The register directory used when no path is given: `$SABERMETRICSPY_REGISTER`, else the user cache."""
    env = os.environ.get(REGISTER_ENV)
    if env:
        return Path(env)
    return Path.home() / ".cache" / "sabermetricspy" / "chadwick-register"


def _system_column(system: str) -> str:
    try:
        return ID_SYSTEMS[system]
    except KeyError:
        raise ValueError(
            f"Unknown id system {system!r}; supported systems: {sorted(ID_SYSTEMS)}"
        ) from None


def normalize_name(name: str) -> str:
    """Fold accents and case, drop punctuation and a trailing generational suffix (Jr., Sr., II, III, IV).

    Hyphens become spaces, so "Smith-Jones" and "Smith Jones" agree; apostrophes and periods are removed.
    """
    decomposed = unicodedata.normalize("NFKD", name)
    folded = "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()
    tokens = re.sub(r"[^a-z0-9 ]+", "", folded.replace("-", " ")).split()
    if len(tokens) > 1 and tokens[-1] in _NAME_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


@dataclass(frozen=True)
class PlayerRegister:
    """The Chadwick Register `people` table with where it came from."""

    people: pl.DataFrame
    release: str | None
    path: str
    source: str = REGISTER_SOURCE
    license: str = REGISTER_LICENSE

    @cached_property
    def normalized_names(self) -> pl.DataFrame:
        """Normalized first, given and last names, computed once per distinct spelling."""
        cols = {}
        for col in ("name_first", "name_given", "name_last"):
            values = self.people[col].fill_null("")
            mapping = {v: normalize_name(v) for v in values.unique().to_list()}
            cols[f"{col}_norm"] = values.replace_strict(mapping, return_dtype=pl.Utf8)
        return pl.DataFrame(cols)


def _typed_people(raw: pl.DataFrame) -> pl.DataFrame:
    year_cols = [
        c
        for c in raw.columns
        if c == "birth_year"
        or re.fullmatch(r"(pro|mlb|col)_(played|managed|umpired)_(first|last)", c)
    ]
    return raw.with_columns(
        *(pl.col(ID_SYSTEMS[s]).cast(pl.Int64, strict=False) for s in _INTEGER_SYSTEMS),
        *(pl.col(c).cast(pl.Int64, strict=False) for c in year_cols),
    )


@lru_cache(maxsize=2)
def _read_register(path: str, shards: tuple[str, ...]) -> PlayerRegister:
    root = Path(path)
    paths = [root] if root.is_file() else [root / s for s in shards]
    for p in paths:
        if not p.is_file():
            raise FileNotFoundError(f"Register shard not found: {p}")
    raw = pl.concat([pl.read_csv(p, infer_schema=False) for p in paths], how="vertical")
    marker = root / _FETCH_MARKER if root.is_dir() else None
    release = marker.read_text(encoding="utf-8").strip() if marker and marker.is_file() else None
    return PlayerRegister(people=_typed_people(raw), release=release, path=str(root))


@profiled(category="ids")
def load_register(
    path: str | Path | None = None, *, shards: Sequence[str] = REGISTER_SHARDS
) -> PlayerRegister:
    """Load the register from a directory of `people-*.csv` shards (or a single CSV file).

    With no path, uses `default_register_path()`. Raises `FileNotFoundError` naming the first missing shard, and says
    how to obtain the register when the default location has none.
    """
    target = Path(path) if path is not None else default_register_path()
    if path is None and not target.exists():
        raise FileNotFoundError(
            f"No Chadwick Register at {target}. Pass a path to load_register(), set {REGISTER_ENV}, "
            "or fetch it with download_register()."
        )
    return _read_register(str(target), tuple(shards))


@profiled(category="ids")
def download_register(
    dest: str | Path | None = None,
    *,
    base_url: str = REGISTER_URL,
    shards: Sequence[str] = REGISTER_SHARDS,
) -> Path:
    """Download the register shards to `dest` (default: the user cache) and record the fetch date.

    The data is licensed ODC-BY 1.0; credit the Chadwick Bureau when you publish results that use it.
    """
    root = Path(dest) if dest is not None else default_register_path()
    root.mkdir(parents=True, exist_ok=True)
    for shard in shards:
        with urllib.request.urlopen(f"{base_url}/{shard}", timeout=120) as resp:
            (root / shard).write_bytes(resp.read())
    (root / _FETCH_MARKER).write_text(datetime.date.today().isoformat(), encoding="utf-8")
    _read_register.cache_clear()
    return root


def _as_register(register: PlayerRegister | str | Path | None) -> PlayerRegister:
    return register if isinstance(register, PlayerRegister) else load_register(register)


@dataclass(frozen=True)
class TranslationResult:
    """A frame with a translated id column, plus the register facts needed to cite and reproduce it."""

    df: Any
    source_system: str
    target_system: str
    unmatched: int
    release: str | None
    source: str = REGISTER_SOURCE
    license: str = REGISTER_LICENSE


def _person_label(row: dict[str, Any]) -> str:
    return f"{row['name_first']} {row['name_last']} ({row['key_uuid']})"


@profiled(category="ids")
def translate_ids(
    df: IntoFrame,
    source: str,
    target: str,
    *,
    column: str | None = None,
    output: str | None = None,
    register: PlayerRegister | str | Path | None = None,
) -> TranslationResult:
    """Add the `target` id system's id to a frame that carries `source` ids.

    Args:
        df: Any Polars, pandas, PyArrow or DuckDB frame.
        source: Id system of `column` (`mlbam`, `retro`, `bbref`, `fangraphs`, ...).
        target: Id system to add.
        column: Source id column; default `key_<source>`.
        output: New column name; default `key_<target>`.
        register: A loaded `PlayerRegister`, a path, or None for the default location.

    Every row and its order is kept. Rows whose id the register lacks, or whose person has no `target` id, get a null and
    are counted in `unmatched`. A source id that belongs to more than one person raises `ValueError`.
    """
    src_col = _system_column(source)
    tgt_col = _system_column(target)
    in_name = column or src_col
    out_name = output or tgt_col
    reg = _as_register(register)

    frame = to_polars_df(df)
    if in_name not in frame.columns:
        raise ValueError(f"Column {in_name!r} not found; pass column= for the {source} ids.")
    if out_name in frame.columns:
        raise ValueError(
            f"Column {out_name!r} already exists; pass output= to name the new column."
        )

    people = reg.people.filter(pl.col(src_col).is_not_null())
    key_dtype = people.schema[src_col]
    wanted = frame.select(pl.col(in_name).cast(key_dtype, strict=False).alias(src_col)).unique()
    present = people.join(wanted, on=src_col, how="inner")
    clashes = (
        present.group_by(src_col)
        .agg(pl.col("key_uuid").n_unique().alias("n"))
        .filter(pl.col("n") > 1)[src_col]
        .to_list()
    )
    if clashes:
        shown = clashes[:5]
        detail = "; ".join(
            f"{k!r}: "
            + ", ".join(
                _person_label(r)
                for r in present.filter(pl.col(src_col) == k)
                .unique("key_uuid")
                .iter_rows(named=True)
            )
            for k in shown
        )
        raise ValueError(f"{source} ids belong to more than one person in the register: {detail}")

    lookup = present.select(pl.col(src_col).alias("__key"), pl.col(tgt_col).alias(out_name)).unique(
        "__key"
    )
    keyed = frame.with_row_index("__row").with_columns(
        pl.col(in_name).cast(key_dtype, strict=False).alias("__key")
    )
    joined = keyed.join(lookup, on="__key", how="left").sort("__row").drop("__row", "__key")
    unmatched = int(joined[out_name].is_null().sum())

    if isinstance(df, pl.DataFrame):
        native: Any = joined
    else:
        table = joined.to_arrow()
        module = type(df).__module__
        if module.startswith("pandas"):
            native = table.to_pandas()
        elif "duckdb" in module:
            import duckdb

            native = duckdb.from_arrow(table)
        else:
            native = table
    return TranslationResult(
        df=native,
        source_system=source,
        target_system=target,
        unmatched=unmatched,
        release=reg.release,
        source=reg.source,
        license=reg.license,
    )


@profiled(category="ids")
def find_players(
    first: str,
    last: str,
    *,
    birth_year: int | None = None,
    season: int | None = None,
    register: PlayerRegister | str | Path | None = None,
) -> pl.DataFrame:
    """Every register person whose normalized name matches, narrowed by birth year or an active season.

    A person matches when the normalized last name equals `last` and the normalized first or given name equals `first`.
    `season` keeps people whose professional playing years include that season. Returns ids, names and playing years.
    """
    reg = _as_register(register)
    norm = reg.normalized_names
    people = reg.people
    mask = (norm["name_last_norm"] == normalize_name(last)) & (
        (norm["name_first_norm"] == normalize_name(first))
        | (norm["name_given_norm"] == normalize_name(first))
    )
    out = people.filter(mask)
    if birth_year is not None:
        out = out.filter(pl.col("birth_year") == birth_year)
    if season is not None:
        out = out.filter(
            (pl.col("pro_played_first") <= season) & (pl.col("pro_played_last") >= season)
        )
    return out.select(*(c for c in _RESULT_COLUMNS if c in out.columns))


def player_id(
    system: str,
    first: str,
    last: str,
    *,
    birth_year: int | None = None,
    season: int | None = None,
    register: PlayerRegister | str | Path | None = None,
) -> int | str:
    """The single `system` id for a name; raises when no person, several people, or no such id matches."""
    column = _system_column(system)
    found = find_players(first, last, birth_year=birth_year, season=season, register=register)
    if found.height == 0:
        raise ValueError(f"No player in the register matches {first} {last}.")
    if found.height > 1:
        listing = "; ".join(
            f"{r['name_first']} {r['name_last']} b.{r['birth_year']} "
            f"{r['pro_played_first']}-{r['pro_played_last']} ({r['key_uuid']})"
            for r in found.iter_rows(named=True)
        )
        raise ValueError(
            f"{first} {last} matches {found.height} people; narrow with birth_year or season: {listing}"
        )
    if column not in found.columns:
        full = _as_register(register).people.filter(pl.col("key_uuid") == found["key_uuid"][0])
        value = full[column][0]
    else:
        value = found[column][0]
    if value is None:
        raise ValueError(f"{first} {last} has no {system} id in the register.")
    return value


__all__ = [
    "ID_SYSTEMS",
    "REGISTER_LICENSE",
    "REGISTER_SHARDS",
    "REGISTER_SOURCE",
    "PlayerRegister",
    "TranslationResult",
    "default_register_path",
    "download_register",
    "find_players",
    "load_register",
    "normalize_name",
    "player_id",
    "translate_ids",
]
