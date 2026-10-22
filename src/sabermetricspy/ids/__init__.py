"""Player-id crosswalk and name lookup over the Chadwick Bureau Register.

The register (https://github.com/chadwickbureau/register) is published under the Open Data Commons Attribution License
1.0 by the Chadwick Bureau. It is not bundled and this library never downloads it (ADR-0003, ADR-0068): download it yourself, then pass the path to
`load_register` or set `$SABERMETRICSPY_REGISTER`.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Any

import narwhals as nw
import polars as pl
from narwhals.typing import IntoFrame

from sabermetricspy.telemetry import profiled

REGISTER_REPO_URL = "https://github.com/chadwickbureau/register"
REGISTER_SHARDS: tuple[str, ...] = tuple(f"people-{c}.csv" for c in "0123456789abcdef")
REGISTER_LICENSE = "Open Data Commons Attribution License 1.0 (ODC-BY 1.0)"
REGISTER_SOURCE = "Chadwick Bureau Register (https://github.com/chadwickbureau/register)"
REGISTER_ENV = "SABERMETRICSPY_REGISTER"
_PROVENANCE_FILE = "provenance.json"
_LEGACY_MARKER = "fetched.txt"

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
# Latin letters that Unicode does not decompose into a base letter and an accent.
_TRANSLITERATION = str.maketrans(
    {
        "ø": "o",  # o with stroke
        "đ": "d",  # d with stroke
        "ð": "d",  # eth
        "ł": "l",  # l with stroke
        "ħ": "h",  # h with stroke
        "ŧ": "t",  # t with stroke
        "ı": "i",  # noqa: RUF001 (dotless i)
        "æ": "ae",
        "œ": "oe",
        "þ": "th",
    }
)
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

    Hyphens and any whitespace separate name parts ("Smith-Jones" and "Smith Jones" agree); apostrophes and periods are
    removed. Letters Unicode cannot split from an accent (o with stroke, l with stroke, ae, ...) use their usual Latin
    spelling. Characters with no Latin form are dropped, so a name in another script normalizes to "".
    """
    decomposed = unicodedata.normalize("NFKD", name)
    folded = "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()
    folded = folded.translate(_TRANSLITERATION)
    spaced = re.sub(r"[\s\-]+", " ", folded)
    tokens = re.sub(r"[^a-z0-9 ]+", "", spaced).split()
    if len(tokens) > 1 and tokens[-1] in _NAME_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


@dataclass(frozen=True)
class PlayerRegister:
    """The Chadwick Register `people` table with where it came from.

    `fetched_on` and `commit` come from an optional `provenance.json` next to the shards (written by whatever downloaded
    them); both are None when it is absent.
    """

    people: pl.DataFrame
    fetched_on: str | None
    commit: str | None
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


def _read_provenance(root: Path) -> tuple[str | None, str | None]:
    """(fetched_on, commit) from `provenance.json`, or from the legacy marker file."""
    record = root / _PROVENANCE_FILE
    if record.is_file():
        data = json.loads(record.read_text(encoding="utf-8"))
        return data.get("fetched_on"), data.get("commit")
    legacy = root / _LEGACY_MARKER
    if legacy.is_file():
        return legacy.read_text(encoding="utf-8").strip() or None, None
    return None, None


@lru_cache(maxsize=4)
def _read_register(
    path: str, shards: tuple[str, ...], state: tuple[tuple[int, int], ...]
) -> PlayerRegister:
    """Parse the files; `state` (size, mtime) per file is part of the cache key so edits are noticed."""
    root = Path(path)
    paths = [root] if root.is_file() else [root / s for s in shards]
    raw = pl.concat([pl.read_csv(p, infer_schema=False) for p in paths], how="vertical")
    fetched_on, commit = _read_provenance(root) if root.is_dir() else (None, None)
    return PlayerRegister(
        people=_typed_people(raw), fetched_on=fetched_on, commit=commit, path=str(root)
    )


@profiled(category="ids")
def load_register(
    path: str | Path | None = None,
    *,
    shards: Sequence[str] = REGISTER_SHARDS,
) -> PlayerRegister:
    """Load the register from a directory of `people-*.csv` shards (or a single CSV file) you have downloaded.

    With no path, reads `$SABERMETRICSPY_REGISTER`, else `default_register_path()`. The library performs no network
    access: get the register yourself from https://github.com/chadwickbureau/register (ODC-BY 1.0) and, if you want
    the result to report where it came from, put a `provenance.json` next to the shards.
    Raises `FileNotFoundError` naming the first missing shard. A register already loaded from the same files is reused;
    a changed file is read again.
    """
    target = Path(path) if path is not None else default_register_path()
    if not target.exists():
        raise FileNotFoundError(
            f"No Chadwick Register at {target}. Download it from {REGISTER_REPO_URL}, then pass its path to "
            f"load_register() or set {REGISTER_ENV}."
        )
    root = target.resolve()
    paths = [root] if root.is_file() else [root / s for s in shards]
    for p in paths:
        if not p.is_file():
            raise FileNotFoundError(f"Register shard not found: {p}")
    state = tuple((p.stat().st_size, p.stat().st_mtime_ns) for p in paths)
    return _read_register(str(root), tuple(shards), state)


def _as_register(register: PlayerRegister | str | Path | None) -> PlayerRegister:
    return register if isinstance(register, PlayerRegister) else load_register(register)


@dataclass(frozen=True)
class TranslationResult:
    """A frame with a translated id column, plus the register facts needed to cite and reproduce it."""

    df: Any
    source_system: str
    target_system: str
    unmatched: int
    fetched_on: str | None
    commit: str | None
    source: str = REGISTER_SOURCE
    license: str = REGISTER_LICENSE


def _person_label(row: dict[str, Any]) -> str:
    return f"{row['name_first']} {row['name_last']} ({row['key_uuid']})"


def _column_values(df: IntoFrame, column: str) -> pl.Series:
    """One column of any frame as a Polars Series, without converting the other columns."""
    nw_df = nw.from_native(df)
    one = nw_df.select(column)
    if isinstance(one, nw.LazyFrame):
        one = one.collect()
    frame = pl.from_arrow(one.to_arrow())
    assert isinstance(frame, pl.DataFrame)
    return frame[column]


def _exact_keys(values: pl.Series, key_dtype: pl.DataType) -> pl.Series:
    """Cast ids to the register's id type; anything that is not exactly an id becomes null.

    Integral floats are accepted for integer systems, fractional ones are not; text is trimmed.
    """
    s = values
    if key_dtype.is_integer():
        if s.dtype == pl.String:
            s = s.str.strip_chars()
        elif s.dtype.is_float():
            s = pl.select(
                pl.when(s.is_finite() & (s == s.floor())).then(s).otherwise(None)
            ).to_series()
        return s.cast(key_dtype, strict=False)
    if s.dtype != pl.String:
        s = s.cast(pl.String, strict=False)
    return s.str.strip_chars()


def _attach(df: Any, name: str, values: pl.Series) -> Any:
    """Return `df` with one column added, keeping its type, its other columns and its index."""
    module = type(df).__module__
    if isinstance(df, pl.DataFrame):
        return df.with_columns(values.alias(name))
    if isinstance(df, pl.LazyFrame):
        return df.collect().with_columns(values.alias(name)).lazy()
    if module.startswith("pandas"):
        import pandas as pd
        import pyarrow as pa

        out = df.copy()
        mapper = {pa.int64(): pd.Int64Dtype()}.get
        out[name] = values.to_arrow().to_pandas(types_mapper=mapper).array
        return out
    if module.startswith("pyarrow"):
        return df.append_column(name, values.to_arrow())
    if "duckdb" in module:
        import duckdb

        return duckdb.from_arrow(df.to_arrow_table().append_column(name, values.to_arrow()))
    table = nw.from_native(df).to_arrow()
    return table.append_column(name, values.to_arrow())


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
        df: Any Polars (eager or lazy), pandas, PyArrow or DuckDB frame.
        source: Id system of `column` (`mlbam`, `retro`, `bbref`, `fangraphs`, ...).
        target: Id system to add.
        column: Source id column; default `key_<source>`.
        output: New column name; default `key_<target>`.
        register: A loaded `PlayerRegister`, a path, or None for the default location.

    The result is the caller's own frame type with exactly one column added: other columns, dtypes, row order and
    (for pandas) the index are untouched. DuckDB input returns a DuckDB relation; a Polars LazyFrame stays lazy.
    Ids must match exactly. Rows whose id the register lacks, or whose person has no `target` id, get a null and are
    counted in `unmatched`. A source id that belongs to more than one person raises `ValueError`.
    """
    src_col = _system_column(source)
    tgt_col = _system_column(target)
    in_name = column or src_col
    out_name = output or tgt_col
    reg = _as_register(register)

    names = nw.from_native(df).collect_schema().names()
    if in_name not in names:
        raise ValueError(f"Column {in_name!r} not found; pass column= for the {source} ids.")
    if out_name in names:
        raise ValueError(
            f"Column {out_name!r} already exists; pass output= to name the new column."
        )

    people = reg.people.filter(pl.col(src_col).is_not_null())
    keys = _exact_keys(_column_values(df, in_name), people.schema[src_col])
    wanted = pl.DataFrame({src_col: keys}).drop_nulls().unique()
    present = people.join(wanted, on=src_col, how="inner")
    clashes = (
        present.group_by(src_col)
        .agg(pl.col("key_uuid").n_unique().alias("n"))
        .filter(pl.col("n") > 1)[src_col]
        .to_list()
    )
    if clashes:
        detail = "; ".join(
            f"{k!r}: "
            + ", ".join(
                _person_label(r)
                for r in present.filter(pl.col(src_col) == k)
                .unique("key_uuid")
                .iter_rows(named=True)
            )
            for k in clashes[:5]
        )
        raise ValueError(f"{source} ids belong to more than one person in the register: {detail}")

    lookup = present.select(pl.col(src_col).alias("k"), pl.col(tgt_col).alias("v")).unique("k")
    mapped = (
        pl.DataFrame({"k": keys})
        .with_row_index("i")
        .join(lookup, on="k", how="left")
        .sort("i")["v"]
        .alias(out_name)
    )
    return TranslationResult(
        df=_attach(df, out_name, mapped),
        source_system=source,
        target_system=target,
        unmatched=int(mapped.is_null().sum()),
        fetched_on=reg.fetched_on,
        commit=reg.commit,
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
    A name that normalizes to nothing (for example one written only in another script) raises `ValueError`, and register
    rows with an empty normalized name never match. `season` keeps people whose professional playing years include that
    season. Returns ids, names and playing years.
    """
    first_norm, last_norm = normalize_name(first), normalize_name(last)
    if not first_norm or not last_norm:
        raise ValueError(
            f"Cannot normalize the name {first!r} {last!r} to Latin letters; the register is matched on "
            "Latin spellings."
        )
    reg = _as_register(register)
    norm = reg.normalized_names
    mask = (
        (norm["name_last_norm"] == last_norm)
        & (norm["name_last_norm"] != "")
        & ((norm["name_first_norm"] == first_norm) | (norm["name_given_norm"] == first_norm))
    )
    out = reg.people.filter(mask)
    if birth_year is not None:
        out = out.filter(pl.col("birth_year") == birth_year)
    if season is not None:
        out = out.filter(
            (pl.col("pro_played_first") <= season) & (pl.col("pro_played_last") >= season)
        )
    return out.select(*(c for c in _RESULT_COLUMNS if c in out.columns))


@profiled(category="ids")
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
    "find_players",
    "load_register",
    "normalize_name",
    "player_id",
    "translate_ids",
]
