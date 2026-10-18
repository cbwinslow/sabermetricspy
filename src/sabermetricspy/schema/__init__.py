"""Canonical column resolution (YAML-driven), safe division expressions, and baseball innings-to-outs utilities."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from importlib import resources
from pathlib import Path
from typing import Any, cast

import narwhals as nw
import polars as pl
import yaml
from narwhals.typing import IntoFrame


def to_polars_df(df: IntoFrame) -> pl.DataFrame:
    """Convert any Narwhals-compatible frame into a Polars DataFrame."""
    if isinstance(df, pl.DataFrame):
        return df.clone()
    nw_df = nw.from_native(df)
    if isinstance(nw_df, nw.LazyFrame):
        nw_df = nw_df.collect()
    res = pl.from_arrow(nw_df.to_arrow())
    return cast(pl.DataFrame, res)


def _load_bundled_aliases() -> dict[str, str]:
    """Load the default column alias map from bundled `data/presets/aliases.yaml`."""
    pkg_files = resources.files("sabermetricspy")
    yaml_path = pkg_files.joinpath("data/presets/aliases.yaml")
    raw: dict[str, Any] = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    canonical_map: dict[str, Iterable[str]] = raw.get("canonical_aliases", {})
    lookup: dict[str, str] = {}
    for canonical_col, aliases in canonical_map.items():
        target = str(canonical_col).lower()
        lookup[target] = target
        for alias in aliases:
            lookup[str(alias).lower()] = target
    return lookup


# Dynamic YAML-initialized column alias dictionary (extensible at runtime)
COLUMN_ALIAS_REGISTRY: dict[str, str] = _load_bundled_aliases()


def get_column_aliases() -> dict[str, str]:
    """Return a copy of the active column alias lookup dictionary (alias_lower -> canonical_lower)."""
    return dict(COLUMN_ALIAS_REGISTRY)


def register_column_aliases(mapping: Mapping[str, str | Iterable[str]]) -> None:
    """Register custom column aliases into the nomenclature registry at runtime.

    Accepts either:
    - `{source_alias: canonical_column}` (e.g. `{"dinger_ct": "hr", "free_passes": "bb"}`), OR
    - `{canonical_column: [alias1, alias2, ...]}` (matching `aliases.yaml` structure).
    """
    for k, v in mapping.items():
        if isinstance(v, str):
            COLUMN_ALIAS_REGISTRY[k.lower()] = v.lower()
        else:
            target = k.lower()
            for alias in v:
                COLUMN_ALIAS_REGISTRY[str(alias).lower()] = target


def register_column_aliases_yaml(path_or_yaml: str | Path) -> None:
    """Load and register custom column nomenclature aliases from a YAML file or YAML string."""
    if isinstance(path_or_yaml, Path):
        text = path_or_yaml.read_text(encoding="utf-8")
    elif "\n" not in path_or_yaml and Path(path_or_yaml).exists():
        text = Path(path_or_yaml).read_text(encoding="utf-8")
    else:
        text = path_or_yaml

    raw: dict[str, Any] = yaml.safe_load(text)
    aliases_block = raw.get("canonical_aliases", raw.get("aliases", raw))
    if isinstance(aliases_block, Mapping):
        register_column_aliases(aliases_block)


def safe_div(numerator: nw.Expr | float, denominator: nw.Expr | float) -> nw.Expr:
    """Construct a zero-denominator-safe division expression in Narwhals.

    Returns NaN when the denominator is 0 or null, preventing ZeroDivisionError
    or +/-inf across Polars, DuckDB, PyArrow, and pandas.
    """
    num_f = (
        nw.lit(float(numerator))
        if isinstance(numerator, (int, float))
        else numerator.cast(nw.Float64)
    )
    if isinstance(denominator, (int, float)):
        if denominator == 0:
            return nw.lit(float("nan"))
        return num_f / float(denominator)
    den_f = denominator.cast(nw.Float64)
    return (
        nw.when((den_f != 0.0) & (~den_f.is_null()))
        .then(num_f / den_f)
        .otherwise(float("nan"))
    )


def ip_notation_to_outs_scalar(ip_val: float | int | str | None) -> int | None:
    """Convert a single baseball innings-pitched value (e.g. 6.2 or '6.2') to integer outs (20).

    Raises ValueError if the fractional digit is not .0, .1, or .2 (unless it is a true third
    like .333 or .667).
    """
    if ip_val is None or (isinstance(ip_val, float) and math.isnan(ip_val)):
        return None
    if isinstance(ip_val, str):
        ip_str = ip_val.strip()
        if not ip_str:
            return None
        if "." in ip_str:
            whole_s, frac_s = ip_str.split(".", 1)
            whole = int(whole_s) if whole_s else 0
            if frac_s in ("0", "00"):
                return whole * 3
            if frac_s == "1":
                return whole * 3 + 1
            if frac_s == "2":
                return whole * 3 + 2
        val_f = float(ip_str)
    else:
        val_f = float(ip_val)

    whole = math.floor(val_f + 1e-9)
    rem = round(val_f - whole, 4)
    if abs(rem - 0.0) < 1e-3:
        return whole * 3
    if abs(rem - 0.1) < 1e-3 or abs(rem - (1.0 / 3.0)) < 1e-2:
        return whole * 3 + 1
    if abs(rem - 0.2) < 1e-3 or abs(rem - (2.0 / 3.0)) < 1e-2:
        return whole * 3 + 2
    raise ValueError(
        f"Invalid baseball innings-pitched notation: {ip_val!r}. Remainder must be .0, .1, or .2."
    )


def outs_to_ip_notation_scalar(outs: int | float | None) -> str | None:
    """Format integer outs (e.g. 20) into standard baseball IP notation ('6.2')."""
    if outs is None or (isinstance(outs, float) and math.isnan(outs)):
        return None
    outs_int = round(outs)
    full_innings, partial_outs = divmod(outs_int, 3)
    return f"{full_innings}.{partial_outs}"


def ip_expr_to_outs(col_name: str = "ip") -> nw.Expr:
    """Vectorized Narwhals expression converting baseball IP float (e.g. 6.2) into integer outs (20)."""
    ip_col = nw.col(col_name).cast(nw.Float64)
    whole_innings = (ip_col - (ip_col % 1.0)).round(0).cast(nw.Int64)
    rem = (ip_col - whole_innings.cast(nw.Float64)).round(2)
    partial_outs = (
        nw.when((rem >= 0.09) & (rem <= 0.15))
        .then(1)
        .when((rem >= 0.19) & (rem <= 0.25))
        .then(2)
        .when((rem >= 0.30) & (rem <= 0.36))
        .then(1)
        .when((rem >= 0.64) & (rem <= 0.69))
        .then(2)
        .otherwise(0)
    )
    return whole_innings * 3 + partial_outs


def normalize_columns(
    nw_df: nw.DataFrame[Any] | nw.LazyFrame[Any],
    column_map: Mapping[str, str] | None = None,
) -> nw.DataFrame[Any] | nw.LazyFrame[Any]:
    """Normalize input dataframe column names to canonical Tier 2 lower_snake_case names.

    Uses the dynamic YAML-backed `COLUMN_ALIAS_REGISTRY` plus any caller-provided `column_map`.
    Also automatically derives `outs` from `ip`, `b1` (singles), `ubb` (unintentional walks),
    `pa` (plate appearances), `bbe` (batted ball events), and `contacts` when their components exist.
    """
    existing_cols = list(nw_df.columns)
    rename_dict: dict[str, str] = {}
    target_seen: set[str] = set()

    # 1. Apply explicit user column_map first
    if column_map:
        for src_col, dst_col in column_map.items():
            if src_col in existing_cols:
                rename_dict[src_col] = dst_col
                target_seen.add(dst_col)

    # 2. Apply YAML-initialized COLUMN_ALIAS_REGISTRY lookup for remaining columns
    for col in existing_cols:
        if col in rename_dict:
            continue
        lower = col.lower()
        canonical = COLUMN_ALIAS_REGISTRY.get(lower, lower)
        if canonical not in target_seen and canonical not in existing_cols:
            if col != canonical:
                rename_dict[col] = canonical
            target_seen.add(canonical)
        elif col == canonical:
            target_seen.add(canonical)

    if rename_dict:
        nw_df = nw_df.rename(rename_dict)

    cols_after = set(nw_df.columns)
    derived_exprs: list[nw.Expr] = []

    # Auto-convert baseball IP notation to integer outs if `outs` is not already present
    if "outs" not in cols_after and "ip" in cols_after:
        derived_exprs.append(ip_expr_to_outs("ip").alias("outs"))
        cols_after.add("outs")

    # Auto-derive singles `b1` if `h`, `b2`, `b3`, `hr` exist and `b1` is missing
    if "b1" not in cols_after and {"h", "b2", "b3", "hr"}.issubset(cols_after):
        derived_exprs.append(
            (nw.col("h") - nw.col("b2") - nw.col("b3") - nw.col("hr")).alias("b1")
        )
        cols_after.add("b1")

    # Auto-derive unintentional walks `ubb` if `bb` exists and `ubb` is missing
    if "ubb" not in cols_after and "bb" in cols_after:
        if "ibb" in cols_after:
            derived_exprs.append((nw.col("bb") - nw.col("ibb")).alias("ubb"))
        else:
            derived_exprs.append(nw.col("bb").alias("ubb"))
        cols_after.add("ubb")

    # Auto-derive plate appearances `pa` if missing and `ab`, `bb` exist
    if "pa" not in cols_after and {"ab", "bb"}.issubset(cols_after):
        pa_expr = nw.col("ab") + nw.col("bb")
        for opt_col in ("hbp", "sf", "sh"):
            if opt_col in cols_after:
                pa_expr = pa_expr + nw.col(opt_col)
        derived_exprs.append(pa_expr.alias("pa"))
        cols_after.add("pa")

    # Auto-derive batted ball events `bbe` if missing and `gb`, `fb`, `ld` exist
    if "bbe" not in cols_after and {"gb", "fb", "ld"}.issubset(cols_after):
        bbe_expr = nw.col("gb") + nw.col("fb") + nw.col("ld")
        if "pu" in cols_after:
            bbe_expr = bbe_expr + nw.col("pu")
        derived_exprs.append(bbe_expr.alias("bbe"))
        cols_after.add("bbe")

    # Auto-derive contacts if swings and whiffs exist
    if "contacts" not in cols_after and {"swings", "whiffs"}.issubset(cols_after):
        derived_exprs.append((nw.col("swings") - nw.col("whiffs")).alias("contacts"))
        cols_after.add("contacts")

    if derived_exprs:
        nw_df = nw_df.with_columns(*derived_exprs)

    return nw_df
