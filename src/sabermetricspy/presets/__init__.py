"""Declarative YAML SourceTranslator and custom YAML metric compiler."""

from __future__ import annotations

import ast
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import narwhals as nw
import yaml
from narwhals.typing import IntoFrame
from pydantic import BaseModel, ConfigDict, Field

from sabermetricspy.registry import REGISTRY, EvalContext, MetricSpec
from sabermetricspy.schema import safe_div
from sabermetricspy.telemetry import profiled
from sabermetricspy.types.enums import Category, Direction, ImplKind


class BoolToIntRule(BaseModel):
    """Rule converting a boolean/flag column into a 0/1 integer count column."""

    model_config = ConfigDict(frozen=True)

    source_col: str
    target_col: str


class ValueRule(BaseModel):
    """Rule mapping categorical/code values in `source_col` into a 0/1 count in `target_col`."""

    model_config = ConfigDict(frozen=True)

    source_col: str
    values: tuple[Any, ...]
    target_col: str


class RangeRule(BaseModel):
    """Rule mapping a numeric `source_col` within `[min_val, max_val]` into a 0/1 count in `target_col`."""

    model_config = ConfigDict(frozen=True)

    source_col: str
    min_val: float
    max_val: float
    target_col: str


class SourceTranslator(BaseModel):
    """Declarative YAML-backed translator converting any provider dataset into canonical Tier 2 columns."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str = ""
    column_map: dict[str, str] = Field(default_factory=dict)
    constant_rules: dict[str, int | float] = Field(default_factory=dict)
    boolean_to_int_rules: tuple[BoolToIntRule, ...] = ()
    value_rules: tuple[ValueRule, ...] = ()
    range_rules: tuple[RangeRule, ...] = ()

    def transform_nw(
        self, nw_df: nw.DataFrame[Any] | nw.LazyFrame[Any]
    ) -> nw.DataFrame[Any] | nw.LazyFrame[Any]:
        """Apply declarative translation rules to a Narwhals DataFrame or LazyFrame."""
        existing = set(nw_df.columns)
        upper_to_actual = {c.upper(): c for c in existing}

        def _resolve_col(col_name: str) -> str | None:
            if col_name in existing:
                return col_name
            return upper_to_actual.get(col_name.upper())

        exprs: list[nw.Expr] = []
        created_cols: set[str] = set()

        # 1. Direct column mappings (add alias column without destroying raw column)
        for src, dst in self.column_map.items():
            actual = _resolve_col(src)
            if actual is not None and dst not in existing:
                exprs.append(nw.col(actual).alias(dst))
                created_cols.add(dst)

        # 2. Constant rules (e.g. pitches = 1 per pitch row)
        for dst, const_val in self.constant_rules.items():
            if dst not in existing:
                exprs.append(nw.lit(const_val).alias(dst))
                created_cols.add(dst)

        # 3. Boolean-to-integer rules
        for b_rule in self.boolean_to_int_rules:
            actual = _resolve_col(b_rule.source_col)
            if actual is not None:
                exprs.append(nw.col(actual).cast(nw.Int64).alias(b_rule.target_col))
                created_cols.add(b_rule.target_col)

        # 4. Categorical / event-code value rules
        for v_rule in self.value_rules:
            actual = _resolve_col(v_rule.source_col)
            if actual is not None:
                exprs.append(
                    nw.when(nw.col(actual).is_in(list(v_rule.values)))
                    .then(1)
                    .otherwise(0)
                    .alias(v_rule.target_col)
                )
                created_cols.add(v_rule.target_col)

        # 5. Numeric range rules
        for r_rule in self.range_rules:
            actual = _resolve_col(r_rule.source_col)
            if actual is not None:
                c_f = nw.col(actual).cast(nw.Float64)
                cond = (~c_f.is_null()) & (c_f >= r_rule.min_val) & (c_f <= r_rule.max_val)
                exprs.append(nw.when(cond).then(1).otherwise(0).alias(r_rule.target_col))
                created_cols.add(r_rule.target_col)

        if exprs:
            nw_df = nw_df.with_columns(*exprs)

        # 6. Post-translation derived composite columns for play-by-play and pitch-level sources
        cols_now = set(nw_df.columns)
        upper_now = {c.upper(): c for c in cols_now}
        post_exprs: list[nw.Expr] = []

        # Retrosheet destination runs scored & steals/CS
        dest_cols = [
            upper_now[k]
            for k in ("BAT_DEST_ID", "RUN1_DEST_ID", "RUN2_DEST_ID", "RUN3_DEST_ID")
            if k in upper_now
        ]
        if dest_cols and "r" not in cols_now:
            runs_expr = nw.lit(0)
            for dc in dest_cols:
                runs_expr = runs_expr + nw.when(nw.col(dc) >= 4).then(1).otherwise(0)
            post_exprs.append(runs_expr.alias("r"))
            post_exprs.append(runs_expr.alias("runs_on_play"))

        sb_cols = [upper_now[f"RUN{i}_SB_FL"] for i in (1, 2, 3) if f"RUN{i}_SB_FL" in upper_now]
        if sb_cols and "sb" not in cols_now:
            sb_expr = nw.lit(0)
            for sc in sb_cols:
                sb_expr = sb_expr + nw.col(sc).cast(nw.Int64)
            post_exprs.append(sb_expr.alias("sb"))

        cs_cols = [upper_now[f"RUN{i}_CS_FL"] for i in (1, 2, 3) if f"RUN{i}_CS_FL" in upper_now]
        if cs_cols and "cs" not in cols_now:
            cs_expr = nw.lit(0)
            for cc in cs_cols:
                cs_expr = cs_expr + nw.col(cc).cast(nw.Int64)
            post_exprs.append(cs_expr.alias("cs"))

        if {"OUTS_CT", "BASE1_RUN_ID", "BASE2_RUN_ID", "BASE3_RUN_ID"}.issubset(upper_now):
            post_exprs.extend(
                [
                    nw.col(upper_now["OUTS_CT"]).cast(nw.Int64).alias("outs_before"),
                    (
                        (~nw.col(upper_now["BASE1_RUN_ID"]).is_null())
                        & (nw.col(upper_now["BASE1_RUN_ID"]) != "")
                    ).alias("on_1b"),
                    (
                        (~nw.col(upper_now["BASE2_RUN_ID"]).is_null())
                        & (nw.col(upper_now["BASE2_RUN_ID"]) != "")
                    ).alias("on_2b"),
                    (
                        (~nw.col(upper_now["BASE3_RUN_ID"]).is_null())
                        & (nw.col(upper_now["BASE3_RUN_ID"]) != "")
                    ).alias("on_3b"),
                ]
            )

        # Statcast zone/swing/contact/barrel composites
        if {"pitches", "zone_pitches", "swings", "whiffs"}.issubset(cols_now):
            is_z = nw.col("zone_pitches") == 1
            # A pitch without a tracked location is neither in nor out of the zone.
            has_loc = "located_pitches" in cols_now
            is_out = (nw.col("located_pitches") == 1) & ~is_z if has_loc else ~is_z
            is_sw = nw.col("swings") == 1
            is_ct = is_sw & (nw.col("whiffs") == 0)
            out_pitches = (
                nw.col("located_pitches") - nw.col("zone_pitches")
                if has_loc
                else nw.col("pitches") - nw.col("zone_pitches")
            )
            post_exprs.extend(
                [
                    out_pitches.alias("out_zone_pitches"),
                    (nw.col("swings") - nw.col("whiffs")).alias("contacts"),
                    nw.when(is_z & is_sw).then(1).otherwise(0).alias("zone_swings"),
                    nw.when(is_out & is_sw).then(1).otherwise(0).alias("out_zone_swings"),
                    nw.when(is_z & is_ct).then(1).otherwise(0).alias("zone_contacts"),
                    nw.when(is_out & is_ct).then(1).otherwise(0).alias("out_zone_contacts"),
                ]
            )

        if "launch_speed" in cols_now:
            ls = nw.col("launch_speed").cast(nw.Float64)
            has_ls = ~ls.is_null()
            post_exprs.extend(
                [
                    nw.when(has_ls).then(ls).otherwise(0.0).alias("ev_sum"),
                    nw.when(has_ls).then(1).otherwise(0).alias("ev_count"),
                ]
            )
            if "launch_angle" in cols_now and "barrels" not in cols_now:
                la = nw.col("launch_angle").cast(nw.Float64)
                has_la = ~la.is_null()
                min_la = nw.when(ls >= 98.0).then(26.0 - (ls - 98.0)).otherwise(999.0)
                max_la = nw.when(ls >= 98.0).then(30.0 + (ls - 98.0) * 1.2).otherwise(-999.0)
                is_barrel = (
                    has_ls
                    & has_la
                    & (ls >= 98.0)
                    & (la >= min_la)
                    & (la <= max_la)
                    & (la >= 8.0)
                    & (la <= 50.0)
                )
                post_exprs.append(nw.when(is_barrel).then(1).otherwise(0).alias("barrels"))

        # Statcast expected stats (xBA, xSLG, xwOBA) additive sums
        if "estimated_ba_using_speedangle" in cols_now and "xba_sum" not in cols_now:
            xba_c = nw.col("estimated_ba_using_speedangle").cast(nw.Float64)
            post_exprs.append(nw.when(~xba_c.is_null()).then(xba_c).otherwise(0.0).alias("xba_sum"))
        if "estimated_slg_using_speedangle" in cols_now and "xslg_sum" not in cols_now:
            xslg_c = nw.col("estimated_slg_using_speedangle").cast(nw.Float64)
            post_exprs.append(
                nw.when(~xslg_c.is_null()).then(xslg_c).otherwise(0.0).alias("xslg_sum")
            )
        if "estimated_woba_using_speedangle" in cols_now and "xwoba_sum" not in cols_now:
            xw_c = nw.col("estimated_woba_using_speedangle").cast(nw.Float64)
            has_xw = ~xw_c.is_null()
            post_exprs.extend(
                [
                    nw.when(has_xw).then(xw_c).otherwise(0.0).alias("xwoba_sum"),
                    nw.when(has_xw).then(1).otherwise(0).alias("xwoba_count"),
                ]
            )

        # Pitch-tracking kinematics & physics (velocity, spin, extension, IVB, HB, effective speed, VAA)
        if "release_speed" in cols_now and "velo_sum" not in cols_now:
            v0 = nw.col("release_speed").cast(nw.Float64)
            has_v0 = ~v0.is_null()
            post_exprs.extend(
                [
                    nw.when(has_v0).then(v0).otherwise(0.0).alias("velo_sum"),
                    nw.when(has_v0).then(1).otherwise(0).alias("velo_count"),
                ]
            )
        if "release_spin_rate" in cols_now and "spin_sum" not in cols_now:
            sp_c = nw.col("release_spin_rate").cast(nw.Float64)
            has_sp = ~sp_c.is_null()
            post_exprs.extend(
                [
                    nw.when(has_sp).then(sp_c).otherwise(0.0).alias("spin_sum"),
                    nw.when(has_sp).then(1).otherwise(0).alias("spin_count"),
                ]
            )
        if "release_extension" in cols_now and "ext_sum" not in cols_now:
            ext_c = nw.col("release_extension").cast(nw.Float64)
            has_ext = ~ext_c.is_null()
            post_exprs.extend(
                [
                    nw.when(has_ext).then(ext_c).otherwise(0.0).alias("ext_sum"),
                    nw.when(has_ext).then(1).otherwise(0).alias("ext_count"),
                ]
            )
        if {"pfx_x", "pfx_z"}.issubset(cols_now) and "ivb_sum" not in cols_now:
            px = nw.col("pfx_x").cast(nw.Float64)
            pz = nw.col("pfx_z").cast(nw.Float64)
            has_brk = (~px.is_null()) & (~pz.is_null())
            post_exprs.extend(
                [
                    nw.when(has_brk).then(pz * 12.0).otherwise(0.0).alias("ivb_sum"),
                    nw.when(has_brk).then(px * 12.0).otherwise(0.0).alias("hb_sum"),
                    nw.when(has_brk).then(1).otherwise(0).alias("break_count"),
                ]
            )
        if "effective_speed" in cols_now and "eff_velo_sum" not in cols_now:
            ev_c = nw.col("effective_speed").cast(nw.Float64)
            has_ev = ~ev_c.is_null()
            post_exprs.extend(
                [
                    nw.when(has_ev).then(ev_c).otherwise(0.0).alias("eff_velo_sum"),
                    nw.when(has_ev).then(1).otherwise(0).alias("eff_velo_count"),
                ]
            )
        if {"vy0", "vz0", "ay", "az"}.issubset(cols_now) and "vaa_sum" not in cols_now:
            vy0 = nw.col("vy0").cast(nw.Float64)
            vz0 = nw.col("vz0").cast(nw.Float64)
            ay = nw.col("ay").cast(nw.Float64)
            az = nw.col("az").cast(nw.Float64)
            has_kin = (~vy0.is_null()) & (~vz0.is_null()) & (~ay.is_null()) & (~az.is_null())
            # 9-parameter kinematics from y0 = 50.0 ft to home plate front y_f = 1.417 ft (delta_y = -48.583 ft)
            vy_f = -((vy0 * vy0 - 97.166 * ay) ** 0.5)
            t_flight = safe_div(vy_f - vy0, ay)
            vz_f = vz0 + az * t_flight
            # u = vz_f / (-vy_f); VAA (deg) = arctan(u) * (180 / pi) via 5th-order Taylor series (error < 0.0001 deg)
            u = safe_div(vz_f, -vy_f)
            atan_u = u - (u**3.0) / 3.0 + (u**5.0) / 5.0
            vaa_deg = atan_u * 57.29577951308232
            post_exprs.extend(
                [
                    nw.when(has_kin).then(vaa_deg).otherwise(0.0).alias("vaa_sum"),
                    nw.when(has_kin).then(1).otherwise(0).alias("vaa_count"),
                ]
            )

        if post_exprs:
            nw_df = nw_df.with_columns(*post_exprs)

        # Derive PA if ab and bb exist and pa is still missing
        cols_final = set(nw_df.columns)
        if "pa" not in cols_final and {"ab", "bb"}.issubset(cols_final):
            pa_e = nw.col("ab") + nw.col("bb")
            for opt_c in ("hbp", "sf", "sh", "ci"):
                if opt_c in cols_final:
                    pa_e = pa_e + nw.col(opt_c)
            nw_df = nw_df.with_columns(pa_e.alias("pa"))

        return nw_df

    @profiled(category="translator")
    def transform(self, df: IntoFrame) -> Any:
        """Transform any native DataFrame (Polars, DuckDB, PyArrow, pandas) using this YAML translator."""
        nw_df = nw.from_native(df)
        out_nw = self.transform_nw(nw_df)
        return nw.to_native(out_nw)


@lru_cache(maxsize=1)
def _load_bundled_translators() -> dict[str, SourceTranslator]:
    pkg_files = resources.files("sabermetricspy")
    yaml_path = pkg_files.joinpath("data/presets/sources.yaml")
    raw: dict[str, Any] = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    presets_raw: dict[str, Any] = raw.get("presets", {})
    return {
        k.lower(): SourceTranslator.model_validate({"name": k, **v}) for k, v in presets_raw.items()
    }


SOURCE_TRANSLATOR_REGISTRY: dict[str, SourceTranslator] = dict(_load_bundled_translators())


def register_source_translator(translator: SourceTranslator) -> None:
    """Register a custom SourceTranslator into the preset registry at runtime."""
    SOURCE_TRANSLATOR_REGISTRY[translator.name.lower()] = translator


def load_source_translator_yaml(path_or_yaml: str | Path) -> list[SourceTranslator]:
    """Load and register one or more declarative SourceTranslators from a YAML file or YAML string."""
    if isinstance(path_or_yaml, Path):
        text = path_or_yaml.read_text(encoding="utf-8")
    elif "\n" not in path_or_yaml and Path(path_or_yaml).exists():
        text = Path(path_or_yaml).read_text(encoding="utf-8")
    else:
        text = path_or_yaml

    raw: dict[str, Any] = yaml.safe_load(text)
    presets_block = raw.get("presets", raw)
    loaded: list[SourceTranslator] = []
    if "name" in presets_block and isinstance(presets_block["name"], str):
        tr = SourceTranslator.model_validate(presets_block)
        register_source_translator(tr)
        loaded.append(tr)
    else:
        for k, v in presets_block.items():
            tr = SourceTranslator.model_validate({"name": k, **v})
            register_source_translator(tr)
            loaded.append(tr)
    return loaded


def get_source_translator(name_or_path: str | Path | SourceTranslator) -> SourceTranslator:
    """Resolve a built-in preset name ('retrosheetpy_events', 'statcast', 'lahman_batting'), YAML path, or SourceTranslator."""
    if isinstance(name_or_path, SourceTranslator):
        return name_or_path
    if isinstance(name_or_path, Path) or "\n" in name_or_path or Path(name_or_path).exists():
        loaded = load_source_translator_yaml(name_or_path)
        return loaded[0]
    key = str(name_or_path).strip().lower()
    if key in SOURCE_TRANSLATOR_REGISTRY:
        return SOURCE_TRANSLATOR_REGISTRY[key]
    raise KeyError(
        f"Unknown source preset {name_or_path!r}. Available presets: {sorted(SOURCE_TRANSLATOR_REGISTRY.keys())}"
    )


def prepare_retrosheet_events(df: IntoFrame) -> Any:
    """Convert a `retrosheetpy` play-by-play `events` table using the declarative `retrosheetpy_events` YAML translator."""
    return get_source_translator("retrosheetpy_events").transform(df)


def prepare_statcast_pitches(df: IntoFrame) -> Any:
    """Convert a Baseball Savant Statcast table using the declarative `statcast` YAML translator."""
    return get_source_translator("statcast").transform(df)


def _compile_arithmetic_ast(node: ast.AST) -> nw.Expr:
    """Safely compile a restricted arithmetic AST into a Narwhals expression."""
    if isinstance(node, ast.Expression):
        return _compile_arithmetic_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return nw.lit(float(node.value))
    if isinstance(node, ast.Name):
        return nw.col(node.id.lower())
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_compile_arithmetic_ast(node.operand)
    if isinstance(node, ast.BinOp):
        left = _compile_arithmetic_ast(node.left)
        right = _compile_arithmetic_ast(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return safe_div(left, right)
        if isinstance(node.op, ast.Pow):
            return left**right
    raise ValueError(f"Unsupported expression syntax in YAML metric formula: {ast.dump(node)}")


def load_custom_metrics_yaml(
    path_or_yaml: str | Path, *, overwrite: bool = True
) -> list[MetricSpec]:
    """Load and register custom user-defined metrics from a YAML file or YAML string.

    Each metric entry in `metrics:` compiles its `formula` arithmetic expression directly
    into a zero-denominator-safe Narwhals vectorized expression.
    """
    if isinstance(path_or_yaml, Path):
        text = path_or_yaml.read_text(encoding="utf-8")
    elif "\n" not in path_or_yaml and Path(path_or_yaml).exists():
        text = Path(path_or_yaml).read_text(encoding="utf-8")
    else:
        text = path_or_yaml
    raw: dict[str, Any] = yaml.safe_load(text)
    metrics_list: list[dict[str, Any]] = raw.get("metrics", [])
    registered_specs: list[MetricSpec] = []

    for item in metrics_list:
        formula_str = str(item["formula"])
        tree = ast.parse(formula_str, mode="eval")
        compiled_expr = _compile_arithmetic_ast(tree)

        spec = MetricSpec(
            metric=str(item["name"]).lower(),
            display_name=str(item.get("display_name", item["name"])),
            category=Category(str(item.get("category", "batting")).lower()),
            kind=ImplKind(str(item.get("kind", "deterministic")).lower()),
            required_columns=tuple(str(c).lower() for c in item.get("required_columns", ())),
            optional_columns=tuple(str(c).lower() for c in item.get("optional_columns", ())),
            requires=tuple(str(r).lower() for r in item.get("requires", ())),
            direction=Direction(str(item.get("direction", "higher_is_better")).lower()),
            formula_latex=str(item.get("formula_latex", formula_str)),
            citation=str(item.get("citation", "Custom YAML Metric")),
            description=str(item.get("description", "")),
        )

        def _make_builder(expr: nw.Expr) -> Any:
            def _builder(ctx: EvalContext) -> nw.Expr:
                return expr

            return _builder

        REGISTRY.register(spec, _make_builder(compiled_expr), overwrite=overwrite)
        registered_specs.append(spec)

    return registered_specs
