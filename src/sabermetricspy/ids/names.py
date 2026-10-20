"""Multi-source player name register: Chadwick people and alternate names, Retrosheet biographical file.

Every name keeps the source it came from. Sources are never merged: where they disagree, `NameRegister.conflicts` lists both
values. Credit: the Chadwick Bureau Register (Open Data Commons Attribution License 1.0) and Retrosheet ("The information
used here was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at
www.retrosheet.org"). Neither source is bundled. Chadwick's files can be downloaded with `download_name_sources`; Retrosheet's
`biofile.zip` is downloaded by the caller from https://www.retrosheet.org/biofile.htm and passed as a zip, a CSV or a folder.
"""

from __future__ import annotations

import datetime
import hashlib
import io
import json
import os
import urllib.request
import warnings
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import polars as pl

from sabermetricspy.ids import (
    REGISTER_LICENSE,
    REGISTER_SHARDS,
    REGISTER_SOURCE,
    PlayerRegister,
    default_register_path,
    load_register,
    normalize_name,
)
from sabermetricspy.telemetry import profiled

RETROSHEET_FILE = "biofile0.csv"
RETROSHEET_ENV = "SABERMETRICSPY_RETROSHEET"
RETROSHEET_SOURCE = (
    "Retrosheet biographical file biofile0.csv (https://www.retrosheet.org/biofile.htm)"
)
RETROSHEET_NOTICE = (
    "The information used here was obtained free of charge from and is copyrighted by Retrosheet. "
    'Interested parties may contact Retrosheet at "www.retrosheet.org".'
)
CHADWICK_EXTRA_FILES: tuple[str, ...] = ("names.csv", "links.csv")
_PROVENANCE_FILE = "provenance.json"

NAME_COLUMNS = (
    "key_uuid",
    "key_retro",
    "source",
    "name_type",
    "first",
    "last",
    "norm_first",
    "norm_last",
    "norm_full",
    "date_start",
    "date_end",
)


def default_retrosheet_path() -> Path:
    """Directory holding `biofile0.csv`: `$SABERMETRICSPY_RETROSHEET`, else the user cache."""
    env = os.environ.get(RETROSHEET_ENV)
    return Path(env) if env else Path.home() / ".cache" / "sabermetricspy" / "retrosheet"


def _commit_for(api: str, ref: str) -> str | None:
    try:
        request = urllib.request.Request(
            api.format(ref=ref), headers={"Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(request, timeout=30) as resp:
            sha = json.loads(resp.read().decode("utf-8")).get("sha")
        return str(sha) if sha else None
    except (OSError, ValueError):
        return None


def _fetch(base: str, names: tuple[str, ...], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in names:
        with urllib.request.urlopen(f"{base}/{name}", timeout=120) as resp:
            (dest / name).write_bytes(resp.read())


@profiled(category="ids")
def download_name_sources(
    chadwick: str | Path | None = None,
    *,
    chadwick_commit: str | None = None,
    chadwick_url: str = "https://raw.githubusercontent.com/chadwickbureau/register/{ref}/data",
) -> Path:
    """Download Chadwick `names.csv` and `links.csv` into the register directory, pinned to a commit.

    The default directory is where `download_register` puts the people shards, and the commit recorded there is used
    unless `chadwick_commit` is given, so the three files come from one commit. Retrosheet's biographical file is not
    downloaded here: download `biofile.zip` from https://www.retrosheet.org/biofile.htm and pass its path to
    `load_name_register`.
    """
    cdir = Path(chadwick) if chadwick is not None else default_register_path()
    record = cdir / _PROVENANCE_FILE
    known = json.loads(record.read_text(encoding="utf-8")) if record.is_file() else {}
    commit = chadwick_commit or known.get("commit")
    if commit is None:
        commit = _commit_for(
            "https://api.github.com/repos/chadwickbureau/register/commits/{ref}", "master"
        )
    if commit is None:
        warnings.warn(
            "Could not look up the Chadwick commit; downloading unpinned master.",
            UserWarning,
            stacklevel=2,
        )
    _fetch(chadwick_url.format(ref=commit or "master"), CHADWICK_EXTRA_FILES, cdir)
    known.update({"names_commit": commit, "names_fetched_on": datetime.date.today().isoformat()})
    record.write_text(json.dumps(known, indent=2), encoding="utf-8")
    return cdir


def read_retrosheet_biofile(path: str | Path | None = None) -> tuple[pl.DataFrame, str, str]:
    """Read Retrosheet's `biofile0.csv` from a `biofile.zip`, a CSV file, or a folder holding either.

    Returns the table (all columns as text), the SHA-256 of the CSV bytes, and the file's location. The hash identifies
    exactly which release was read. Raises `FileNotFoundError` with the download address when nothing is found, and
    `ValueError` when a zip does not contain `biofile0.csv`.
    """
    target = Path(path) if path is not None else default_retrosheet_path()
    candidates = (
        [target] if target.is_file() else [target / RETROSHEET_FILE, target / "biofile.zip"]
    )
    found = next((c for c in candidates if c.is_file()), None)
    if found is None:
        raise FileNotFoundError(
            f"Retrosheet biographical file not found at {target}. Download biofile.zip from "
            f"https://www.retrosheet.org/biofile.htm and pass its path (the zip, biofile0.csv, or the folder holding either)."
        )
    if zipfile.is_zipfile(found):
        with zipfile.ZipFile(found) as archive:
            members = [
                m for m in archive.namelist() if m.rsplit("/", 1)[-1].lower() == RETROSHEET_FILE
            ]
            if not members:
                raise ValueError(
                    f"{found} does not contain {RETROSHEET_FILE}; it holds {archive.namelist()}."
                )
            data = archive.read(members[0])
    else:
        data = found.read_bytes()
    return (
        pl.read_csv(io.BytesIO(data), infer_schema=False),
        hashlib.sha256(data).hexdigest(),
        str(found),
    )


@dataclass(frozen=True)
class NameRegister:
    """Names from several sources with their provenance, plus the places the sources disagree.

    `names` has one row per name: `key_uuid` (Chadwick person, null when a Retrosheet id has no Chadwick person),
    `key_retro`, `source`, `name_type`, the name parts, their normalized forms and any date range. `links` holds external
    ids from Chadwick `links.csv`. `unresolved` lists Chadwick alternate-name and link rows whose `key_person` matched no
    person or several people. `conflicts` lists every field the sources disagree on, with both values.
    `last_name_only` lists people a source knows only by last name (historical players whose first name is unknown); a
    name needs a first and a last part to be searched, so they have no row in `names`, but they are not dropped.
    """

    names: pl.DataFrame
    links: pl.DataFrame
    unresolved: pl.DataFrame
    conflicts: pl.DataFrame
    last_name_only: pl.DataFrame
    chadwick_commit: str | None = None
    chadwick_fetched_on: str | None = None
    retrosheet_sha256: str | None = None
    retrosheet_file: str | None = None
    sources: tuple[str, ...] = (REGISTER_SOURCE, RETROSHEET_SOURCE)
    licenses: dict[str, str] = field(
        default_factory=lambda: {"chadwick": REGISTER_LICENSE, "retrosheet": RETROSHEET_NOTICE}
    )

    @profiled(category="ids")
    def search(self, first: str, last: str) -> pl.DataFrame:
        """Every person with a name matching `first` and `last` in any source, once each, with the names that matched.

        A name matches when its normalized first and last parts equal the query, or its normalized full name equals the
        normalized "first last". A query that normalizes to nothing raises `ValueError`. Columns: `key_uuid`,
        `key_retro`, `matched` (list of structs with `source`, `name_type`, `first`, `last`) and `sources`.
        """
        q_first, q_last = normalize_name(first), normalize_name(last)
        if not q_first or not q_last:
            raise ValueError(
                f"Cannot normalize the name {first!r} {last!r} to Latin letters; names are matched on Latin spellings."
            )
        q_full = normalize_name(f"{first} {last}")
        hits = self.names.filter(
            ((pl.col("norm_last") == q_last) & (pl.col("norm_first") == q_first))
            | (pl.col("norm_full") == q_full)
        )
        return (
            hits.with_columns(pl.coalesce("key_uuid", "key_retro").alias("_person"))
            .group_by("_person", maintain_order=True)
            .agg(
                pl.col("key_uuid").first(),
                pl.col("key_retro").drop_nulls().first(),
                pl.struct("source", "name_type", "first", "last").unique().alias("matched"),
                pl.col("source").unique().sort().alias("sources"),
            )
            .drop("_person")
        )

    def person(self, first: str, last: str) -> dict[str, Any]:
        """The one person matching a name: `key_uuid`, `key_retro` and the sources that matched.

        Raises `ValueError` when nobody matches, or when several people match (the error lists each with their ids).
        """
        found = self.search(first, last)
        if found.height == 0:
            raise ValueError(f"No person in the name register matches {first} {last}.")
        if found.height > 1:
            listing = "; ".join(
                f"{r['key_uuid'] or '-'} / {r['key_retro'] or '-'} ({', '.join(r['sources'])})"
                for r in found.iter_rows(named=True)
            )
            raise ValueError(
                f"{first} {last} matches {found.height} people; narrow the name or use the ids: {listing}"
            )
        row = found.row(0, named=True)
        return {
            "key_uuid": row["key_uuid"],
            "key_retro": row["key_retro"],
            "sources": row["sources"],
        }


def _normalized(values: pl.Series) -> pl.Series:
    """Normalize a string column once per distinct value."""
    filled = values.fill_null("")
    mapping = {v: normalize_name(v) for v in filled.unique().to_list()}
    return filled.replace_strict(mapping, return_dtype=pl.Utf8)


def _name_rows(
    frame: pl.DataFrame,
    *,
    source: str,
    name_type: pl.Expr | str,
    first: pl.Expr,
    last: pl.Expr,
    start: pl.Expr | None = None,
    end: pl.Expr | None = None,
) -> pl.DataFrame:
    type_expr = pl.lit(name_type) if isinstance(name_type, str) else name_type
    return frame.select(
        "key_uuid",
        "key_retro",
        pl.lit(source).alias("source"),
        type_expr.alias("name_type"),
        first.alias("first"),
        last.alias("last"),
        (start if start is not None else pl.lit(None, dtype=pl.Utf8)).alias("date_start"),
        (end if end is not None else pl.lit(None, dtype=pl.Utf8)).alias("date_end"),
    ).filter(pl.col("first").is_not_null() & pl.col("last").is_not_null())


_SPLIT_LAST = r"^(.*\S)\s+(\S+)$"


def _split_free_name(column: str) -> tuple[pl.Expr, pl.Expr]:
    """Split a free-text name such as 'Harry Frederick Winbigler' into given names and last name."""
    c = pl.col(column)
    first = c.str.extract(_SPLIT_LAST, 1)
    last = pl.coalesce(c.str.extract(_SPLIT_LAST, 2), c)
    return first, last


def _person_index(people: pl.DataFrame, key: str) -> pl.DataFrame:
    """`key` -> the one Chadwick person it belongs to (`n_people` says how many it matches)."""
    return (
        people.filter(pl.col(key).is_not_null())
        .group_by(key)
        .agg(
            pl.col("key_uuid").n_unique().alias("n_people"),
            pl.col("key_uuid").first().alias("_uuid"),
            pl.col("key_retro").first().alias("_retro"),
        )
    )


def _resolve(
    frame: pl.DataFrame, people: pl.DataFrame, key: str
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Attach `key_uuid`/`key_retro` through `key_person`; split off rows with no person or several."""
    joined = frame.join(_person_index(people, key), on=key, how="left")
    ok = joined.filter(pl.col("n_people") == 1).rename({"_uuid": "key_uuid", "_retro": "key_retro"})
    bad = joined.filter(pl.col("n_people").is_null() | (pl.col("n_people") != 1)).with_columns(
        pl.when(pl.col("n_people").is_null())
        .then(pl.lit("no person with this key_person"))
        .otherwise(pl.lit("key_person belongs to several people"))
        .alias("reason")
    )
    return ok.drop("n_people"), bad.drop("n_people", "_uuid", "_retro")


def _birth_text(year: pl.Expr, month: pl.Expr, day: pl.Expr) -> pl.Expr:
    def part(e: pl.Expr, width: int, na: str) -> pl.Expr:
        return e.cast(pl.Utf8).str.zfill(width).fill_null(na)

    return pl.concat_str(
        part(year, 4, "????"), part(month, 2, "??"), part(day, 2, "??"), separator="-"
    )


def _compact(series: pl.Series) -> pl.Series:
    return _normalized(series).str.replace_all(" ", "")


def _unique_on(df: pl.DataFrame, key: str) -> pl.DataFrame:
    """Rows whose `key` value appears exactly once."""
    singles = df.group_by(key).len().filter(pl.col("len") == 1).select(key)
    return df.join(singles, on=key, how="semi")


def _require_columns(df: pl.DataFrame, columns: tuple[str, ...], what: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(
            f"{what} is missing columns {missing}; the source file layout may have changed."
        )


_PEOPLE_NEEDED = (
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
)
_NAMES_NEEDED = (
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
)
_BIO_NEEDED = (
    "id",
    "lastname",
    "usename",
    "fullname",
    "birthdate",
    "birthname",
    "altname",
    "debut_p",
)


def _conflicts(people: pl.DataFrame, bio: pl.DataFrame) -> pl.DataFrame:
    """Fields on which Chadwick people and the Retrosheet biographical file disagree."""
    c = _unique_on(people.filter(pl.col("key_retro").is_not_null()), "key_retro")
    r = _unique_on(bio, "id")
    j = c.join(r, left_on="key_retro", right_on="id", how="inner")
    if j.height == 0:
        return pl.DataFrame(
            schema={
                "key_uuid": pl.Utf8,
                "key_retro": pl.Utf8,
                "field": pl.Utf8,
                "chadwick": pl.Utf8,
                "retrosheet": pl.Utf8,
            }
        )

    def whole(e: pl.Expr) -> pl.Expr:
        return e.cast(pl.Int64, strict=False)

    j = j.with_columns(
        whole(pl.col("birth_year")).alias("c_year"),
        whole(pl.col("birth_month")).alias("c_month"),
        whole(pl.col("birth_day")).alias("c_day"),
        whole(pl.col("birthdate").str.slice(0, 4)).alias("r_year"),
        pl.when(whole(pl.col("birthdate").str.slice(4, 2)) > 0)
        .then(whole(pl.col("birthdate").str.slice(4, 2)))
        .alias("r_month"),
        pl.when(whole(pl.col("birthdate").str.slice(6, 2)) > 0)
        .then(whole(pl.col("birthdate").str.slice(6, 2)))
        .alias("r_day"),
        _compact(j["name_last"]).alias("c_last"),
        _compact(j["lastname"]).alias("r_last"),
        _compact(j["usename"]).alias("r_use"),
        _compact(j["name_first"]).alias("c_first"),
        _compact(j["name_given"]).alias("c_given"),
        _compact(j["name_nick"]).alias("c_nick"),
        whole(pl.col("debut_p").str.slice(0, 4)).alias("r_debut_year"),
    )

    def differ(a: str, b: str) -> pl.Expr:
        return pl.col(a).is_not_null() & pl.col(b).is_not_null() & (pl.col(a) != pl.col(b))

    base = ["key_uuid", "key_retro"]

    def report(
        mask: pl.Expr, field_name: str, chadwick: pl.Expr, retrosheet: pl.Expr
    ) -> pl.DataFrame:
        return j.filter(mask).select(
            *base,
            pl.lit(field_name).alias("field"),
            chadwick.cast(pl.Utf8).alias("chadwick"),
            retrosheet.cast(pl.Utf8).alias("retrosheet"),
        )

    parts = [
        report(
            differ("c_year", "r_year") | differ("c_month", "r_month") | differ("c_day", "r_day"),
            "birth_date",
            _birth_text(pl.col("c_year"), pl.col("c_month"), pl.col("c_day")),
            _birth_text(pl.col("r_year"), pl.col("r_month"), pl.col("r_day")),
        ),
        report(
            (pl.col("c_last") != pl.col("r_last"))
            & (pl.col("c_last") != "")
            & (pl.col("r_last") != ""),
            "last_name",
            pl.col("name_last"),
            pl.col("lastname"),
        ),
        report(
            (pl.col("r_use") != "")
            & (pl.col("r_use") != pl.col("c_first"))
            & (pl.col("r_use") != pl.col("c_given"))
            & (pl.col("r_use") != pl.col("c_nick"))
            & pl.col("name_first").is_not_null(),
            "first_name",
            pl.col("name_first"),
            pl.col("usename"),
        ),
        report(
            differ("mlb_played_first", "r_debut_year"),
            "first_year_vs_debut",
            pl.col("mlb_played_first"),
            pl.col("r_debut_year"),
        ),
    ]
    return pl.concat(parts)


def _read_csv(path: Path) -> pl.DataFrame:
    return pl.read_csv(path, infer_schema=False)


def _provenance(directory: Path) -> dict[str, Any]:
    record = directory / _PROVENANCE_FILE
    return json.loads(record.read_text(encoding="utf-8")) if record.is_file() else {}


@profiled(category="ids")
def build_name_register(
    people: PlayerRegister,
    names: pl.DataFrame,
    links: pl.DataFrame,
    biofile: pl.DataFrame,
    *,
    chadwick_commit: str | None = None,
    chadwick_fetched_on: str | None = None,
    retrosheet_sha256: str | None = None,
    retrosheet_file: str | None = None,
) -> NameRegister:
    """Build the register from loaded sources: Chadwick people, `names.csv`, `links.csv` and Retrosheet `biofile0.csv`."""
    p = people.people
    _require_columns(p, _PEOPLE_NEEDED, "The Chadwick people table")
    _require_columns(names, _NAMES_NEEDED, "Chadwick names.csv")
    _require_columns(links, ("key_person", "source", "value"), "Chadwick links.csv")
    _require_columns(biofile, _BIO_NEEDED, "Retrosheet biofile0.csv")
    chadwick_people = "chadwick_people"
    parts: list[pl.DataFrame] = [
        _name_rows(
            p,
            source=chadwick_people,
            name_type="common",
            first=pl.col("name_first"),
            last=pl.col("name_last"),
        ),
        _name_rows(
            p.filter(pl.col("name_given") != pl.col("name_first")),
            source=chadwick_people,
            name_type="given",
            first=pl.col("name_given"),
            last=pl.col("name_last"),
        ),
        _name_rows(
            p,
            source=chadwick_people,
            name_type="nickname",
            first=pl.col("name_nick"),
            last=pl.col("name_last"),
        ),
        _name_rows(
            p,
            source=chadwick_people,
            name_type="matrilineal",
            first=pl.col("name_first"),
            last=pl.col("name_matrilineal"),
        ),
    ]

    alt, alt_bad = _resolve(
        names.with_columns(pl.col("altname_type").str.replace("-", "_")), p, "key_person"
    )
    last_alt = pl.coalesce("altname_last", "name_last")
    start, end = pl.col("altname_date_start"), pl.col("altname_date_end")
    parts += [
        _name_rows(
            alt,
            source="chadwick_names",
            name_type=pl.col("altname_type"),
            first=pl.coalesce("altname_first", "name_first"),
            last=last_alt,
            start=start,
            end=end,
        ),
        _name_rows(
            alt,
            source="chadwick_names",
            name_type=pl.col("altname_type"),
            first=pl.col("altname_given"),
            last=last_alt,
            start=start,
            end=end,
        ),
        _name_rows(
            alt,
            source="chadwick_names",
            name_type=pl.col("altname_type"),
            first=pl.col("altname_nick"),
            last=last_alt,
            start=start,
            end=end,
        ),
    ]
    link_rows, link_bad = _resolve(links, p, "key_person")
    link_rows = link_rows.select(
        "key_uuid", pl.col("source").str.to_lowercase().alias("source"), "value"
    )

    retro_index = _person_index(p, "key_retro")
    bio = biofile.join(retro_index, left_on="id", right_on="key_retro", how="left").with_columns(
        pl.col("id").alias("key_retro"),
        pl.when(pl.col("n_people") == 1).then(pl.col("_uuid")).alias("key_uuid"),
    )
    retro = "retrosheet_biofile"
    ends_with_last = pl.col("fullname").str.ends_with(pl.col("lastname"))
    full_first = (
        pl.when(ends_with_last)
        .then(
            pl.col("fullname")
            .str.slice(0, pl.col("fullname").str.len_chars() - pl.col("lastname").str.len_chars())
            .str.strip_chars()
        )
        .otherwise(pl.col("fullname"))
    )
    b_first, b_last = _split_free_name("birthname")
    a_first, a_last = _split_free_name("altname")
    parts += [
        _name_rows(
            bio, source=retro, name_type="common", first=pl.col("usename"), last=pl.col("lastname")
        ),
        _name_rows(bio, source=retro, name_type="full", first=full_first, last=pl.col("lastname")),
        _name_rows(bio, source=retro, name_type="birth", first=b_first, last=b_last),
        _name_rows(bio, source=retro, name_type="alias", first=a_first, last=a_last),
    ]

    table = pl.concat(parts, how="vertical_relaxed")
    table = table.with_columns(
        _normalized(table["first"]).alias("norm_first"),
        _normalized(table["last"]).alias("norm_last"),
        _normalized(
            table.select((pl.col("first") + pl.lit(" ") + pl.col("last")).alias("full"))["full"]
        ).alias("norm_full"),
    ).filter((pl.col("norm_first") != "") & (pl.col("norm_last") != ""))
    table = table.select(*NAME_COLUMNS).unique(maintain_order=True)

    unresolved = pl.concat(
        [
            alt_bad.select(pl.lit("names.csv").alias("file"), "key_person", "reason"),
            link_bad.select(pl.lit("links.csv").alias("file"), "key_person", "reason"),
        ],
        how="vertical_relaxed",
    )
    last_only = pl.concat(
        [
            p.filter(pl.col("name_first").is_null() & pl.col("name_last").is_not_null()).select(
                "key_uuid",
                "key_retro",
                pl.lit(chadwick_people).alias("source"),
                pl.col("name_last").alias("last"),
            ),
            bio.filter(
                pl.col("usename").is_null() | (pl.col("usename").str.strip_chars() == "")
            ).select(
                "key_uuid",
                "key_retro",
                pl.lit(retro).alias("source"),
                pl.col("lastname").alias("last"),
            ),
        ],
        how="vertical_relaxed",
    )
    return NameRegister(
        names=table,
        links=link_rows,
        unresolved=unresolved,
        conflicts=_conflicts(p, biofile),
        last_name_only=last_only,
        chadwick_commit=chadwick_commit or people.commit,
        chadwick_fetched_on=chadwick_fetched_on or people.fetched_on,
        retrosheet_sha256=retrosheet_sha256,
        retrosheet_file=retrosheet_file,
    )


@profiled(category="ids")
def load_name_register(
    chadwick: str | Path | None = None,
    retrosheet: str | Path | None = None,
    *,
    shards: tuple[str, ...] = REGISTER_SHARDS,
) -> NameRegister:
    """Load the Chadwick register directory (people shards, `names.csv`, `links.csv`) and Retrosheet's `biofile0.csv`.

    `chadwick` defaults to `default_register_path()`. `retrosheet` is Retrosheet's `biofile.zip`, `biofile0.csv`, or a folder
    holding either (default: `default_retrosheet_path()`). Raises `FileNotFoundError` saying how to obtain a missing file.
    """
    cdir = Path(chadwick) if chadwick is not None else default_register_path()
    for path in (cdir / f for f in CHADWICK_EXTRA_FILES):
        if not path.is_file():
            raise FileNotFoundError(
                f"Name source not found: {path}. Fetch the Chadwick files with download_name_sources()."
            )
    biofile, digest, location = read_retrosheet_biofile(retrosheet)
    people = load_register(cdir, shards=shards)
    c_prov = _provenance(cdir)
    return build_name_register(
        people,
        _read_csv(cdir / "names.csv"),
        _read_csv(cdir / "links.csv"),
        biofile,
        chadwick_commit=c_prov.get("names_commit") or people.commit,
        chadwick_fetched_on=c_prov.get("names_fetched_on") or people.fetched_on,
        retrosheet_sha256=digest,
        retrosheet_file=location,
    )


__all__ = [
    "CHADWICK_EXTRA_FILES",
    "NAME_COLUMNS",
    "RETROSHEET_NOTICE",
    "RETROSHEET_SOURCE",
    "NameRegister",
    "build_name_register",
    "default_retrosheet_path",
    "download_name_sources",
    "load_name_register",
    "read_retrosheet_biofile",
]
