"""Two-stage additive calculation engine, rolling-window engine, telemetry profile, and multi-backend benchmarker."""

from __future__ import annotations

import inspect
import statistics
import time
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import narwhals as nw
import polars as pl
from narwhals.typing import IntoFrame
from pydantic import BaseModel, ConfigDict

import sabermetricspy.metrics as _metrics_init  # noqa: F401 # pyright: ignore[reportUnusedImport]
from sabermetricspy.constants import DEFAULT_SEASON, resolve_context
from sabermetricspy.presets import SourceTranslator, get_source_translator
from sabermetricspy.registry import REGISTRY, EvalContext, MetricSpec
from sabermetricspy.schema import normalize_columns, to_polars_df
from sabermetricspy.telemetry import profiled
from sabermetricspy.types.context import SeasonContext
from sabermetricspy.types.enums import Metric, MetricSuite


class ExecutionProfile(BaseModel):
    """Frozen nanosecond-precision stage timing and throughput telemetry for a calculation."""

    model_config = ConfigDict(frozen=True)

    backend: str
    rows_in: int
    rows_out: int
    metrics_evaluated: int
    translation_ms: float
    normalization_ms: float
    aggregation_ms: float
    dag_eval_ms: float
    total_ms: float
    rows_per_sec: float


def _detect_backend_name(df: Any) -> str:
    mod = type(df).__module__.lower()
    if "polars" in mod:
        return "polars"
    if "duckdb" in mod:
        return "duckdb"
    if "pyarrow" in mod:
        return "pyarrow"
    if "pandas" in mod:
        return "pandas"
    return mod.split(".")[0]


def _safe_row_count(nw_df: nw.DataFrame[Any] | nw.LazyFrame[Any]) -> int:
    if isinstance(nw_df, nw.DataFrame):
        return len(nw_df)
    return 0


def _is_duckdb(nw_df: Any) -> bool:
    implementation: Any = getattr(nw_df, "implementation", None)
    return isinstance(nw_df, nw.LazyFrame) and getattr(implementation, "name", "") == "DUCKDB"


def _duckdb_to_polars(nw_df: Any) -> pl.DataFrame:
    """Read a DuckDB relation into memory once, as Polars via Arrow (ADR-0056)."""
    return cast(pl.DataFrame, pl.from_arrow(nw.to_native(nw_df).to_arrow_table()))


class _ContextProbe:
    """Stands in for `EvalContext` and records whether a builder reads the season constants."""

    def __init__(self, real: EvalContext) -> None:
        self._real = real
        self.used = False

    @property
    def season_context(self) -> SeasonContext:
        self.used = True
        return self._real.season_context

    @property
    def weights(self) -> Any:
        self.used = True
        return self._real.weights

    @property
    def available_columns(self) -> frozenset[str]:
        return self._real.available_columns


def _season_column(nw_df: nw.DataFrame[Any] | nw.LazyFrame[Any]) -> str | None:
    return next((c for c in nw_df.columns if c.lower() == "season"), None)


def _is_year_text(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 4 and value.isdigit()


def _season_range(nw_df: nw.DataFrame[Any] | nw.LazyFrame[Any]) -> tuple[int, int] | None:
    """The (earliest, latest) season in the `season` column, or None when it does not hold years.

    Uses only `min` and `max`, which every backend supports. Integer and integral float columns and columns of
    four-digit text are years; dates, other text and all-null columns are not.
    """
    col = _season_column(nw_df)
    if col is None:
        return None
    dtype = nw_df.collect_schema()[col]
    if not (dtype.is_integer() or dtype.is_float() or dtype == nw.String):
        return None
    stats = nw_df.select(nw.col(col).min().alias("lo"), nw.col(col).max().alias("hi"))
    if isinstance(stats, nw.LazyFrame):
        stats = stats.collect()
    lo, hi = stats.row(0)
    if lo is None or hi is None:
        return None
    if isinstance(lo, str) or isinstance(hi, str):
        return (int(lo), int(hi)) if _is_year_text(lo) and _is_year_text(hi) else None
    if lo != lo or hi != hi or lo != int(lo) or hi != int(hi):  # NaN or fractional
        return None
    return int(lo), int(hi)


def _default_season(nw_df: nw.DataFrame[Any] | nw.LazyFrame[Any]) -> int:
    """The season to use when the caller named none: the frame's single season, else `DEFAULT_SEASON`."""
    found = _season_range(nw_df)
    return found[0] if found is not None and found[0] == found[1] else DEFAULT_SEASON


def _user_stacklevel() -> int:
    """Stack level of the first caller outside this package, so warnings point at the user's code."""
    level = 1
    current = inspect.currentframe()
    frame = current.f_back if current is not None else None
    while frame is not None and frame.f_globals.get("__name__", "").startswith("sabermetricspy."):
        frame = frame.f_back
        level += 1
    return level


def _check_season(
    nw_df: nw.DataFrame[Any] | nw.LazyFrame[Any],
    dag: Sequence[Any],
    inferred: bool,
    eval_ctx: EvalContext,
) -> None:
    """Refuse or flag season constants that do not match the data.

    Raises when a frame holds several seasons, or one season different from the context's, and a
    requested metric reads the season constants. Warns when the caller named no season, the frame
    holds no usable season, and a metric reads the constants, because `DEFAULT_SEASON` is then a guess.
    """
    seasons = _season_range(nw_df)
    if seasons is None and not inferred:
        return
    dependent: list[str] = []
    for reg in dag:
        probe = _ContextProbe(eval_ctx)
        reg.builder(probe)
        if probe.used:
            dependent.append(reg.spec.name)
    if not dependent:
        return
    names = ", ".join(dependent)
    col = _season_column(nw_df)
    if seasons is not None and seasons[0] != seasons[1]:
        raise ValueError(
            f"Column {col!r} holds more than one season, but one call applies a single "
            f"season's constants to every row (metrics affected: {names}). "
            "Calculate each season separately with context=SeasonContext(season=...)."
        )
    chosen = eval_ctx.season_context.season
    if seasons is not None and seasons[0] != chosen:
        raise ValueError(
            f"Column {col!r} holds season {seasons[0]}, but the context uses {chosen} constants "
            f"(metrics affected: {names}). Pass context=SeasonContext(season={seasons[0]})."
        )
    if seasons is None:
        warnings.warn(
            f"No season was given and the data holds no usable season value, so {names} use "
            f"{DEFAULT_SEASON} constants. Pass season= or context=SeasonContext(season=...).",
            UserWarning,
            stacklevel=_user_stacklevel(),
        )


_BOX_DRAWING = str.maketrans(
    {
        **dict.fromkeys("─━╌╍┄┅┈┉", "-"),
        **dict.fromkeys("│┃╎╏┆┇┊┋", "|"),
        **dict.fromkeys("═║", "="),
        **dict.fromkeys(
            "┌┐└┘├┤┬┴┼╞╡╪╭╮╯╰╔╗╚╝",
            "+",
        ),
    }
)


def _ascii_safe(text: str) -> str:
    """Replace box-drawing characters (polars/DuckDB tables) so printing never fails on a legacy console."""
    return text.translate(_BOX_DRAWING).encode("ascii", "replace").decode("ascii")


@dataclass(frozen=True)
class CalculationResult:
    """Immutable result container returned by calculate(), calculate_suite(), calculate_available(), and calculate_rolling().

    Attributes:
        df: The resulting dataframe in the caller's native format (Polars, pandas, PyArrow, DuckDB).
        specs: Mapping of canonical metric name to its MetricSpec metadata & provenance.
        context: The resolved SeasonContext (including wOBA/FIP weights and park factor) used.
        requested_metrics: Tuple of canonical metric names requested by the caller.
        profile: Frozen ExecutionProfile recording stage-by-stage timing and throughput.
    """

    df: Any
    specs: Mapping[str, MetricSpec]
    context: SeasonContext
    requested_metrics: tuple[str, ...]
    profile: ExecutionProfile

    def __repr__(self) -> str:
        """Compact, ASCII-only representation: safe to print on cp1252 and other legacy consoles."""
        p = self.profile
        header = (
            f"CalculationResult(metrics={list(self.requested_metrics)}, season={self.context.season}, "
            f"rows={p.rows_out:,}, backend={p.backend})"
        )
        return f"{header}\n{_ascii_safe(repr(self.df))}"

    def to_polars(self) -> Any:
        """Convert the result dataframe to a Polars DataFrame."""
        nw_df = nw.from_native(self.df)
        if isinstance(nw_df, nw.LazyFrame):
            nw_df = nw_df.collect()
        return pl.from_arrow(nw_df.to_arrow())

    def to_pandas(self) -> Any:
        """Convert the result dataframe to a pandas DataFrame."""
        nw_df = nw.from_native(self.df)
        if isinstance(nw_df, nw.LazyFrame):
            nw_df = nw_df.collect()
        return nw_df.to_pandas()

    def to_arrow(self) -> Any:
        """Convert the result dataframe to a PyArrow Table."""
        nw_df = nw.from_native(self.df)
        if isinstance(nw_df, nw.LazyFrame):
            nw_df = nw_df.collect()
        return nw_df.to_arrow()

    def summary(self) -> str:
        """Return a formatted provenance summary of all computed metrics, formulas, citations, and execution speed."""
        p = self.profile
        lines = [
            f"sabermetricspy CalculationResult (Season={self.context.season}, League={self.context.league}, PF={self.context.park_factor})",
            f"Execution Profile: backend={p.backend} | {p.rows_in:,} -> {p.rows_out:,} rows | {p.total_ms:.3f} ms ({p.rows_per_sec:,.0f} rows/sec)",
            "-" * 96,
            f"{'Metric':<18} | {'Display':<12} | {'Category':<28} | {'Citation'}",
            "-" * 96,
        ]
        for key in self.requested_metrics:
            spec = self.specs[key]
            lines.append(
                f"{spec.name:<18} | {spec.display_name:<12} | {spec.category!s:<28} | {spec.citation}"
            )
        return "\n".join(lines)


@profiled(category="engine")
def calculate(
    df: IntoFrame,
    metrics: Sequence[Metric | str] | Metric | str,
    *,
    by: Sequence[str] | str | None = None,
    context: SeasonContext | None = None,
    season: int | None = None,
    preset: str | Path | SourceTranslator | None = None,
    column_map: Mapping[str, str] | None = None,
    strict: bool = True,
) -> CalculationResult:
    """Calculate one or more sabermetrics over any Polars, DuckDB, PyArrow, or pandas table.

    A DuckDB relation is read into memory once as Arrow, evaluated on Polars, and returned as a DuckDB relation on
    DuckDB's default connection (ADR-0056); aggregate a table larger than memory in DuckDB before passing it.

    Executes the two-stage additive pipeline and records stage-by-stage timing in `.profile`:
    1. Optional declarative YAML `preset` translation (`retrosheetpy_events`, `statcast`, `lahman_batting`, or custom YAML).
    2. Normalizes column aliases via the YAML nomenclature registry and converts baseball `ip` notation to integer `outs`.
    3. If `by` is provided, sums all additive counting columns across the grouping keys before
       evaluating any rate/ratio formulas (never averaging ratios).
    4. Resolves the metric dependency DAG in topological order and evaluates each expression once.
    """
    t0 = time.perf_counter_ns()
    backend_name = _detect_backend_name(df)

    if isinstance(metrics, (str, Metric)):
        requested_list: list[Metric | str] = [metrics]
    else:
        requested_list = list(metrics)

    nw_df = nw.from_native(df)
    from_duckdb = _is_duckdb(nw_df)
    if from_duckdb:
        nw_df = nw.from_native(_duckdb_to_polars(nw_df))
    rows_in = _safe_row_count(nw_df)

    t_trans_0 = time.perf_counter_ns()
    if preset is not None:
        translator = get_source_translator(preset)
        nw_df = translator.transform_nw(nw_df)
    t_trans_1 = time.perf_counter_ns()

    nw_df = normalize_columns(nw_df, column_map=column_map)
    t_norm_1 = time.perf_counter_ns()

    inferred = context is None and season is None
    resolved_ctx = resolve_context(
        context, season=_default_season(nw_df) if season is None else season
    )
    assert resolved_ctx.weights is not None

    # Resolve DAG
    dag = REGISTRY.resolve_dag(requested_list)
    requested_keys = tuple(REGISTRY.resolve_name(m) for m in requested_list)

    if by is not None:
        per_row = [reg.spec.name for reg in dag if reg.spec.per_row]
        if per_row:
            raise ValueError(
                f"{', '.join(per_row)} can only be calculated on one row per game: grouping with by= "
                "would sum its inputs first. Calculate it without by=, then aggregate the results."
            )

    # Check required base columns
    available_cols = set(nw_df.columns)
    if not strict:
        valid_dag = []
        for reg in dag:
            reqs = REGISTRY.required_base_columns([reg.spec.name])
            if reqs.issubset(available_cols):
                valid_dag.append(reg)
        dag = valid_dag
        valid_keys = {r.spec.name for r in dag}
        requested_keys = tuple(k for k in requested_keys if k in valid_keys)
    else:
        missing_by_metric: dict[str, list[str]] = {}
        for reg in dag:
            missing = [c for c in reg.spec.required_columns if c not in available_cols]
            if missing:
                missing_by_metric[reg.spec.name] = missing
        if missing_by_metric:
            details = ", ".join(f"{m} (missing {cols})" for m, cols in missing_by_metric.items())
            raise ValueError(f"Missing required input columns for requested metrics: {details}")

    _check_season(
        nw_df,
        dag,
        inferred,
        EvalContext(
            season_context=resolved_ctx,
            weights=resolved_ctx.weights,
            available_columns=frozenset(available_cols | {r.spec.name for r in dag}),
        ),
    )

    # Stage 1: Optional additive grouping (`by=...`)
    t_agg_0 = time.perf_counter_ns()
    if by is not None:
        group_keys = [by] if isinstance(by, str) else list(by)
        needed_cols: set[str] = set()
        for reg in dag:
            needed_cols.update(reg.spec.required_columns)
            needed_cols.update(c for c in reg.spec.optional_columns if c in available_cols)
        for extra_c in ("b1", "ubb", "pa", "outs", "bbe", "contacts"):
            if extra_c in available_cols:
                needed_cols.add(extra_c)
        agg_cols = sorted(c for c in needed_cols if c in available_cols and c not in group_keys)
        if agg_cols:
            nw_df = nw_df.group_by(group_keys).agg([nw.col(c).sum() for c in agg_cols])
        available_cols = set(nw_df.columns)
    t_agg_1 = time.perf_counter_ns()

    # Stage 2: Evaluate topological DAG expressions sequentially by dependency wave
    t_dag_0 = time.perf_counter_ns()
    eval_ctx = EvalContext(
        season_context=resolved_ctx,
        weights=resolved_ctx.weights,
        available_columns=frozenset(available_cols),
    )

    # An eager Polars frame would run each metric as its own pass over every column; one deferred plan is far cheaper.
    defer = isinstance(nw_df, nw.DataFrame) and nw_df.implementation is nw.Implementation.POLARS
    if defer:
        nw_df = nw_df.lazy()

    specs_out: dict[str, MetricSpec] = {}
    for reg in dag:
        expr = reg.builder(eval_ctx).alias(reg.spec.name)
        nw_df = nw_df.with_columns(expr)
        available_cols.add(reg.spec.name)
        eval_ctx = EvalContext(
            season_context=resolved_ctx,
            weights=resolved_ctx.weights,
            available_columns=frozenset(available_cols),
        )
        specs_out[reg.spec.name] = reg.spec

    if defer and isinstance(nw_df, nw.LazyFrame):
        nw_df = nw_df.collect()
    native_out = nw.to_native(nw_df)
    if from_duckdb:
        import duckdb

        native_out = duckdb.from_arrow(native_out.to_arrow())
    t_end = time.perf_counter_ns()

    rows_out = _safe_row_count(nw_df)
    total_ms = (t_end - t0) / 1_000_000.0
    effective_rows = max(rows_in, rows_out, 1)
    rows_per_sec = (effective_rows / (total_ms / 1000.0)) if total_ms > 0 else 0.0

    profile = ExecutionProfile(
        backend=backend_name,
        rows_in=rows_in,
        rows_out=rows_out,
        metrics_evaluated=len(dag),
        translation_ms=round((t_trans_1 - t_trans_0) / 1_000_000.0, 4),
        normalization_ms=round((t_norm_1 - t_trans_1) / 1_000_000.0, 4),
        aggregation_ms=round((t_agg_1 - t_agg_0) / 1_000_000.0, 4),
        dag_eval_ms=round((t_end - t_dag_0) / 1_000_000.0, 4),
        total_ms=round(total_ms, 4),
        rows_per_sec=round(rows_per_sec, 1),
    )

    return CalculationResult(
        df=native_out,
        specs=specs_out,
        context=resolved_ctx,
        requested_metrics=requested_keys,
        profile=profile,
    )


def calculate_suite(
    df: IntoFrame,
    suite: Sequence[MetricSuite | str] | MetricSuite | str = MetricSuite.TRADITIONAL_BATTING,
    *,
    by: Sequence[str] | str | None = None,
    context: SeasonContext | None = None,
    season: int | None = None,
    preset: str | Path | SourceTranslator | None = None,
    column_map: Mapping[str, str] | None = None,
    strict: bool = False,
) -> CalculationResult:
    """Calculate all metrics belonging to one or more curated MetricSuites.

    Defaults to `strict=False` so optional metrics within a suite whose optional columns
    are absent in `df` are gracefully skipped while all supported metrics in the suite run.
    """
    if isinstance(suite, (str, MetricSuite)):
        suites_list: list[MetricSuite | str] = [suite]
    else:
        suites_list = list(suite)
    metric_names: list[str] = []
    for s in suites_list:
        for m in REGISTRY.expand_suite(s):
            if m not in metric_names and (by is None or not REGISTRY.spec(m).per_row):
                metric_names.append(m)
    return calculate(
        df,
        metric_names,
        by=by,
        context=context,
        season=season,
        preset=preset,
        column_map=column_map,
        strict=strict,
    )


def calculate_available(
    df: IntoFrame,
    *,
    by: Sequence[str] | str | None = None,
    context: SeasonContext | None = None,
    season: int | None = None,
    preset: str | Path | SourceTranslator | None = None,
    column_map: Mapping[str, str] | None = None,
) -> CalculationResult:
    """Inspect `df`'s columns and automatically compute every metric in the registry that `df` supports."""
    nw_df = nw.from_native(df)
    if preset is not None:
        nw_df = get_source_translator(preset).transform_nw(nw_df)
    nw_df = normalize_columns(nw_df, column_map=column_map)
    avail_specs = REGISTRY.available_for_columns(nw_df.columns)
    metric_names = [s.name for s in avail_specs if by is None or not s.per_row]
    return calculate(
        df,
        metric_names,
        by=by,
        context=context,
        season=season,
        preset=preset,
        column_map=column_map,
        strict=True,
    )


@profiled(category="engine")
def calculate_rolling(
    df: IntoFrame,
    metrics: Sequence[Metric | str] | Metric | str,
    *,
    window: int = 15,
    by: Sequence[str] | str | None = None,
    order_by: Sequence[str] | str | None = None,
    min_periods: int = 1,
    context: SeasonContext | None = None,
    season: int | None = None,
    preset: str | Path | SourceTranslator | None = None,
    column_map: Mapping[str, str] | None = None,
) -> CalculationResult:
    """Calculate rolling N-game or N-appearance sabermetrics using strictly additive window sums.

    Never averages ratios:
    1. Applies optional YAML `preset` translation and column alias normalization.
    2. Sorts by `(by, order_by)` if `order_by` is provided.
    3. Replaces each required/optional additive counting column with its rolling window sum
       over `window` periods (partitioned by `by`).
    4. Evaluates the topological metric DAG over the rolling count sums.
    """
    if window < 1:
        raise ValueError(f"window must be >= 1, got {window}.")

    t0 = time.perf_counter_ns()
    backend_name = _detect_backend_name(df)

    if isinstance(metrics, (str, Metric)):
        requested_list: list[Metric | str] = [metrics]
    else:
        requested_list = list(metrics)

    nw_df = nw.from_native(df)
    t_trans_0 = time.perf_counter_ns()
    if preset is not None:
        nw_df = get_source_translator(preset).transform_nw(nw_df)
    t_trans_1 = time.perf_counter_ns()

    nw_df = normalize_columns(nw_df, column_map=column_map)
    t_norm_1 = time.perf_counter_ns()

    pl_df = to_polars_df(nw.to_native(nw_df))
    rows_in = len(pl_df)

    group_keys = ([by] if isinstance(by, str) else list(by)) if by is not None else []
    order_keys = (
        ([order_by] if isinstance(order_by, str) else list(order_by))
        if order_by is not None
        else []
    )

    sort_cols = [c for c in [*group_keys, *order_keys] if c in pl_df.columns]
    if sort_cols:
        pl_df = pl_df.sort(sort_cols)

    dag = REGISTRY.resolve_dag(requested_list)
    available_cols = set(pl_df.columns)
    needed_cols: set[str] = set()
    for reg in dag:
        needed_cols.update(reg.spec.required_columns)
        needed_cols.update(c for c in reg.spec.optional_columns if c in available_cols)
    for extra_c in ("b1", "ubb", "pa", "outs", "bbe", "contacts"):
        if extra_c in available_cols:
            needed_cols.add(extra_c)

    roll_cols = sorted(
        c
        for c in needed_cols
        if c in available_cols and c not in group_keys and c not in order_keys
    )
    t_agg_0 = time.perf_counter_ns()
    if roll_cols:
        roll_exprs: list[pl.Expr] = []
        for c in roll_cols:
            e = pl.col(c).rolling_sum(window_size=window, min_samples=min_periods)
            if group_keys:
                e = e.over(group_keys)
            roll_exprs.append(e.alias(c))
        pl_df = pl_df.with_columns(*roll_exprs)
    t_agg_1 = time.perf_counter_ns()

    # Evaluate metric DAG on the rolling sums via Narwhals
    t_dag_0 = time.perf_counter_ns()
    res = calculate(
        pl_df,
        requested_list,
        by=None,
        context=context,
        season=season,
        strict=True,
    )
    t_end = time.perf_counter_ns()

    out_pl: pl.DataFrame = res.df
    if isinstance(df, pl.DataFrame):
        native_out: Any = out_pl
    else:
        arrow_tbl = out_pl.to_arrow()
        native_out = arrow_tbl.to_pandas() if backend_name == "pandas" else arrow_tbl

    total_ms = (t_end - t0) / 1_000_000.0
    rows_per_sec = (max(rows_in, 1) / (total_ms / 1000.0)) if total_ms > 0 else 0.0
    profile = ExecutionProfile(
        backend=backend_name,
        rows_in=rows_in,
        rows_out=len(out_pl),
        metrics_evaluated=len(dag),
        translation_ms=round((t_trans_1 - t_trans_0) / 1_000_000.0, 4),
        normalization_ms=round((t_norm_1 - t_trans_1) / 1_000_000.0, 4),
        aggregation_ms=round((t_agg_1 - t_agg_0) / 1_000_000.0, 4),
        dag_eval_ms=round((t_end - t_dag_0) / 1_000_000.0, 4),
        total_ms=round(total_ms, 4),
        rows_per_sec=round(rows_per_sec, 1),
    )

    return CalculationResult(
        df=native_out,
        specs=res.specs,
        context=res.context,
        requested_metrics=res.requested_metrics,
        profile=profile,
    )


@dataclass(frozen=True)
class BenchmarkResult:
    """Frozen multi-backend benchmark report."""

    summary_df: pl.DataFrame
    rows_in: int
    groups: int
    metrics_evaluated: int
    repeats: int

    def format_table(self) -> str:
        """Return a clean human-readable benchmark comparison table."""
        lines = [
            f"sabermetricspy Multi-Backend Benchmark ({self.rows_in:,} rows -> {self.groups:,} groups | {self.metrics_evaluated} metrics | {self.repeats} repeats)",
            "-" * 96,
            f"{'Backend':<12} | {'Min (ms)':>10} | {'Median (ms)':>12} | {'Mean (ms)':>10} | {'Throughput (rows/s)':>22} | {'Rel Speed':>10}",
            "-" * 96,
        ]
        for row in self.summary_df.iter_rows(named=True):
            lines.append(
                f"{row['backend']:<12} | {row['min_ms']:>10.3f} | {row['median_ms']:>12.3f} | "
                f"{row['mean_ms']:>10.3f} | {row['rows_per_sec']:>22,.0f} | {row['relative_speedup']:>9.2f}x"
            )
        return "\n".join(lines)


def benchmark(
    df: IntoFrame | None = None,
    *,
    metrics: Sequence[Metric | str] | None = None,
    rows: int = 50_000,
    groups: int = 250,
    backends: Sequence[str] = ("polars", "duckdb", "pyarrow", "pandas"),
    warmup: int = 1,
    repeats: int = 3,
    season: int = 2024,
) -> BenchmarkResult:
    """Benchmark `sabermetricspy` throughput across Polars, DuckDB, PyArrow, and pandas."""
    import duckdb

    if metrics is None:
        target_metrics: list[Metric | str] = [
            Metric.AVG,
            Metric.OBP,
            Metric.SLG,
            Metric.OPS,
            Metric.ISO,
            Metric.BABIP,
            Metric.BB_PCT,
            Metric.K_PCT,
            Metric.WOBA,
            Metric.WRAA,
            Metric.WRC,
            Metric.WRC_PLUS,
        ]
    else:
        target_metrics = list(metrics)

    if df is None:
        idx = pl.int_range(0, rows, eager=True)
        base_pl = pl.DataFrame(
            {
                "player_id": (idx % groups).cast(pl.Utf8),
                "pa": pl.repeat(4, rows, eager=True),
                "ab": pl.repeat(3, rows, eager=True),
                "h": (idx % 3 == 0).cast(pl.Int64),
                "b2": (idx % 11 == 0).cast(pl.Int64),
                "b3": (idx % 67 == 0).cast(pl.Int64),
                "hr": (idx % 19 == 0).cast(pl.Int64),
                "bb": (idx % 5 == 0).cast(pl.Int64),
                "ibb": (idx % 47 == 0).cast(pl.Int64),
                "hbp": (idx % 37 == 0).cast(pl.Int64),
                "sf": (idx % 41 == 0).cast(pl.Int64),
                "so": (idx % 4 == 0).cast(pl.Int64),
            }
        )
    else:
        base_pl = to_polars_df(df)
        rows = len(base_pl)
        groups = base_pl["player_id"].n_unique() if "player_id" in base_pl.columns else rows

    arrow_tbl = base_pl.to_arrow()
    conn = duckdb.connect()
    conn.register("bench_v", arrow_tbl)

    records: list[dict[str, Any]] = []
    for b_name in backends:
        b = b_name.lower().strip()
        if b == "polars":
            in_frame: Any = base_pl
        elif b == "pyarrow":
            in_frame = arrow_tbl
        elif b == "pandas":
            in_frame = base_pl.to_pandas()
        elif b == "duckdb":
            in_frame = conn.sql("SELECT * FROM bench_v")
        else:
            raise ValueError(f"Unsupported benchmark backend {b_name!r}.")

        for _ in range(max(0, warmup)):
            if b == "duckdb":
                in_frame = conn.sql("SELECT * FROM bench_v")
            calculate(in_frame, target_metrics, by="player_id", season=season)

        timings_ms: list[float] = []
        last_res: CalculationResult | None = None
        for _ in range(max(1, repeats)):
            if b == "duckdb":
                in_frame = conn.sql("SELECT * FROM bench_v")
            t_start = time.perf_counter_ns()
            last_res = calculate(in_frame, target_metrics, by="player_id", season=season)
            # Materialize DuckDB relation so execution time is measured fairly
            if b == "duckdb":
                _ = last_res.df.pl()
            elapsed_ms = (time.perf_counter_ns() - t_start) / 1_000_000.0
            timings_ms.append(elapsed_ms)

        min_ms = min(timings_ms)
        med_ms = statistics.median(timings_ms)
        mean_ms = statistics.mean(timings_ms)
        rps = (rows / (med_ms / 1000.0)) if med_ms > 0 else 0.0
        assert last_res is not None
        records.append(
            {
                "backend": b,
                "rows_in": rows,
                "rows_out": groups,
                "metrics_evaluated": last_res.profile.metrics_evaluated,
                "min_ms": round(min_ms, 3),
                "median_ms": round(med_ms, 3),
                "mean_ms": round(mean_ms, 3),
                "rows_per_sec": round(rps, 1),
            }
        )

    summary_pl = pl.DataFrame(records)
    slowest_med = summary_pl["median_ms"].max()
    max_med = (
        float(slowest_med) if isinstance(slowest_med, (int, float)) and slowest_med > 0 else 1.0
    )
    summary_pl = summary_pl.with_columns(
        (pl.lit(max_med) / pl.col("median_ms")).round(2).alias("relative_speedup")
    ).sort("median_ms")

    return BenchmarkResult(
        summary_df=summary_pl,
        rows_in=rows,
        groups=groups,
        metrics_evaluated=int(summary_pl["metrics_evaluated"][0]) if len(summary_pl) > 0 else 0,
        repeats=repeats,
    )
