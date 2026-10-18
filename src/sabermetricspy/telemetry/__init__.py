"""Decorator-based performance telemetry (`@profiled`) and benchmark registry (`@register_benchmark`)."""

from __future__ import annotations

import functools
import statistics
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, ParamSpec, TypeVar, overload

import polars as pl

P = ParamSpec("P")
R = TypeVar("R")


def _detect_frame_info(obj: Any) -> tuple[str, int] | None:
    """Return `(backend_name, row_count)` if `obj` is a recognized DataFrame/Table/Result."""
    if obj is None or isinstance(obj, (str, bytes, int, float, bool, dict, list, tuple, set)):
        return None
    if isinstance(obj, pl.DataFrame):
        return ("polars", len(obj))
    if isinstance(obj, pl.LazyFrame):
        return ("polars_lazy", 0)
    # Check CalculationResult-like object with .df and .profile
    prof = getattr(obj, "profile", None)
    if prof is not None and hasattr(prof, "backend") and hasattr(prof, "rows_out"):
        return (str(prof.backend), int(prof.rows_out))
    mod = type(obj).__module__
    if mod.startswith("pandas") and hasattr(obj, "__len__"):
        return ("pandas", len(obj))
    if mod.startswith("pyarrow") and hasattr(obj, "num_rows"):
        return ("pyarrow", int(obj.num_rows))
    if (mod.startswith("duckdb") or hasattr(obj, "pl")) and hasattr(obj, "shape"):
        try:
            return ("duckdb", int(obj.shape[0]))
        except Exception:
            return ("duckdb", 0)
    if hasattr(obj, "__len__") and hasattr(obj, "columns"):
        return ("dataframe", len(obj))
    return None


def _inspect_call_inputs(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[str, int]:
    """Scan positional and keyword arguments for the primary input DataFrame."""
    for val in args:
        info = _detect_frame_info(val)
        if info is not None:
            return info
    for val in kwargs.values():
        info = _detect_frame_info(val)
        if info is not None:
            return info
    return ("scalar", 0)


def _inspect_call_output(result: Any, fallback_rows: int) -> int:
    """Extract output row count from a function return value."""
    info = _detect_frame_info(result)
    if info is not None:
        return info[1]
    return fallback_rows


@dataclass(frozen=True, slots=True)
class SpanRecord:
    """Immutable telemetry record captured by `@profiled` for a single function call."""

    name: str
    category: str
    backend: str
    rows_in: int
    rows_out: int
    duration_ms: float
    rows_per_sec: float


@dataclass(slots=True)
class PerformanceTracker:
    """Collector for `@profiled` execution spans across `sabermetricspy` and user functions."""

    enabled: bool = True
    _spans: list[SpanRecord] = field(default_factory=list)

    @property
    def spans(self) -> tuple[SpanRecord, ...]:
        """Return an immutable snapshot of all recorded execution spans."""
        return tuple(self._spans)

    def record(self, span: SpanRecord) -> None:
        """Append a `SpanRecord` if telemetry tracking is enabled."""
        if self.enabled:
            self._spans.append(span)

    def reset(self) -> None:
        """Clear all recorded execution spans."""
        self._spans.clear()

    @contextmanager
    def session(self, *, reset_first: bool = True) -> Generator[PerformanceTracker]:
        """Context manager that enables telemetry tracking (and optionally resets existing spans)."""
        prev_enabled = self.enabled
        if reset_first:
            self.reset()
        self.enabled = True
        try:
            yield self
        finally:
            self.enabled = prev_enabled

    def summary_df(self) -> pl.DataFrame:
        """Aggregate recorded spans by `(name, category, backend)` into a Polars DataFrame."""
        if not self._spans:
            return pl.DataFrame(
                schema={
                    "name": pl.Utf8,
                    "category": pl.Utf8,
                    "backend": pl.Utf8,
                    "calls": pl.Int64,
                    "total_rows_in": pl.Int64,
                    "total_ms": pl.Float64,
                    "mean_ms": pl.Float64,
                    "min_ms": pl.Float64,
                    "max_ms": pl.Float64,
                    "rows_per_sec": pl.Float64,
                }
            )
        raw = pl.DataFrame(
            [
                {
                    "name": s.name,
                    "category": s.category,
                    "backend": s.backend,
                    "rows_in": s.rows_in,
                    "duration_ms": s.duration_ms,
                }
                for s in self._spans
            ]
        )
        return (
            raw.group_by(["name", "category", "backend"], maintain_order=True)
            .agg(
                pl.len().cast(pl.Int64).alias("calls"),
                pl.col("rows_in").sum().cast(pl.Int64).alias("total_rows_in"),
                pl.col("duration_ms").sum().round(3).alias("total_ms"),
                pl.col("duration_ms").mean().round(3).alias("mean_ms"),
                pl.col("duration_ms").min().round(3).alias("min_ms"),
                pl.col("duration_ms").max().round(3).alias("max_ms"),
            )
            .with_columns(
                pl.when(pl.col("total_ms") > 0.0)
                .then(
                    (
                        pl.col("total_rows_in").cast(pl.Float64) / (pl.col("total_ms") / 1000.0)
                    ).round(1)
                )
                .otherwise(0.0)
                .alias("rows_per_sec")
            )
        )

    def format_table(self) -> str:
        """Render a human-readable ASCII summary table of all recorded `@profiled` spans."""
        df = self.summary_df()
        if len(df) == 0:
            return "No @profiled spans recorded."
        lines = [
            f"{'Function / Method':<34} | {'Category':<12} | {'Backend':<8} | {'Calls':>5} | {'Rows In':>9} | {'Total ms':>9} | {'Mean ms':>8} | {'Rows/sec':>12}",
            "-" * 116,
        ]
        for row in df.iter_rows(named=True):
            lines.append(
                f"{str(row['name'])[:34]:<34} | {str(row['category'])[:12]:<12} | {str(row['backend'])[:8]:<8} | "
                f"{int(row['calls']):>5d} | {int(row['total_rows_in']):>9,d} | "
                f"{float(row['total_ms']):>9.3f} | {float(row['mean_ms']):>8.3f} | {float(row['rows_per_sec']):>12,.0f}"
            )
        return "\n".join(lines)


# Global singleton tracker exported as `sb.telemetry`
telemetry = PerformanceTracker()


@overload
def profiled(
    func: Callable[P, R], /, *, name: str | None = None, category: str = "general"
) -> Callable[P, R]: ...


@overload
def profiled(
    func: None = None, /, *, name: str | None = None, category: str = "general"
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def profiled(
    func: Callable[P, R] | None = None,
    /,
    *,
    name: str | None = None,
    category: str = "general",
) -> Any:
    """Decorator that automatically measures execution time, row counts, and backend into `sb.telemetry`.

    Can be applied bare (`@profiled`) or parameterized (`@profiled(category="expectancy")`).
    """

    def _decorator(fn: Callable[P, R]) -> Callable[P, R]:
        raw_name = getattr(fn, "__qualname__", getattr(fn, "__name__", "unknown"))
        span_name = name or raw_name.split(".<locals>.")[-1]

        @functools.wraps(fn)
        def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not telemetry.enabled:
                return fn(*args, **kwargs)
            backend, rows_in = _inspect_call_inputs(args, kwargs)
            t0 = time.perf_counter_ns()
            result = fn(*args, **kwargs)
            t1 = time.perf_counter_ns()

            prof = getattr(result, "profile", None)
            if prof is not None and hasattr(prof, "backend") and hasattr(prof, "rows_in"):
                backend = str(prof.backend)
                rows_in = int(prof.rows_in)
                rows_out = int(prof.rows_out)
            else:
                rows_out = _inspect_call_output(result, rows_in)

            duration_ms = round((t1 - t0) / 1_000_000.0, 4)
            eff_rows = max(rows_in, rows_out, 1) if (rows_in > 0 or rows_out > 0) else 0
            rows_per_sec = (
                round(eff_rows / (duration_ms / 1000.0), 1)
                if duration_ms > 0 and eff_rows > 0
                else 0.0
            )

            telemetry.record(
                SpanRecord(
                    name=span_name,
                    category=category,
                    backend=backend,
                    rows_in=rows_in,
                    rows_out=rows_out,
                    duration_ms=duration_ms,
                    rows_per_sec=rows_per_sec,
                )
            )
            return result

        return _wrapper

    if func is not None:
        return _decorator(func)
    return _decorator


@dataclass(frozen=True, slots=True)
class BenchmarkEntry:
    """Metadata for a function decorated with `@register_benchmark`."""

    name: str
    category: str
    default_rows: int
    fn: Callable[..., Any]


@dataclass(frozen=True, slots=True)
class RegisteredBenchmarkResult:
    """Results from executing `@register_benchmark` workloads via `run_registered_benchmarks()`."""

    records: tuple[dict[str, Any], ...]

    def summary_df(self) -> pl.DataFrame:
        """Return a Polars DataFrame of benchmark results sorted by category and name."""
        return pl.DataFrame(list(self.records))

    def format_table(self) -> str:
        """Render a clean ASCII table of all executed `@register_benchmark` workloads."""
        df = self.summary_df()
        if len(df) == 0:
            return "No registered benchmarks executed."
        lines = [
            f"{'Benchmark Name':<32} | {'Category':<12} | {'Rows':>8} | {'Median ms':>9} | {'Mean ms':>9} | {'Min ms':>9} | {'Rows/sec':>12}",
            "-" * 107,
        ]
        for row in df.iter_rows(named=True):
            lines.append(
                f"{str(row['name'])[:32]:<32} | {str(row['category'])[:12]:<12} | {int(row['rows']):>8,d} | "
                f"{float(row['median_ms']):>9.3f} | {float(row['mean_ms']):>9.3f} | {float(row['min_ms']):>9.3f} | "
                f"{float(row['rows_per_sec']):>12,.0f}"
            )
        return "\n".join(lines)


_BENCHMARK_REGISTRY: dict[str, BenchmarkEntry] = {}
_builtins_registered: bool = False


@overload
def register_benchmark(
    func: Callable[P, R],
    /,
    *,
    name: str | None = None,
    category: str = "general",
    default_rows: int = 10_000,
) -> Callable[P, R]: ...


@overload
def register_benchmark(
    func: None = None,
    /,
    *,
    name: str | None = None,
    category: str = "general",
    default_rows: int = 10_000,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def register_benchmark(
    func: Callable[P, R] | None = None,
    /,
    *,
    name: str | None = None,
    category: str = "general",
    default_rows: int = 10_000,
) -> Any:
    """Decorator to register a function in the `sabermetricspy` benchmark suite (`@register_benchmark`)."""

    def _decorator(fn: Callable[P, R]) -> Callable[P, R]:
        raw_name = getattr(fn, "__qualname__", getattr(fn, "__name__", "benchmark"))
        bench_name = name or raw_name.split(".<locals>.")[-1]
        _BENCHMARK_REGISTRY[bench_name] = BenchmarkEntry(
            name=bench_name,
            category=category,
            default_rows=default_rows,
            fn=fn,
        )
        return fn

    if func is not None:
        return _decorator(func)
    return _decorator


def _ensure_builtin_benchmarks() -> None:
    """Lazily register built-in subsystem benchmark workloads across all 5 sabermetricspy layers."""
    global _builtins_registered
    if _builtins_registered:
        return
    _builtins_registered = True

    from sabermetricspy.engine import calculate_rolling, calculate_suite
    from sabermetricspy.expectancy import WinProbabilityModel
    from sabermetricspy.models import MarcelProjector, PitchQualityModel
    from sabermetricspy.presets import prepare_statcast_pitches
    from sabermetricspy.types.enums import Metric, MetricSuite
    from sabermetricspy.uncertainty import EmpiricalBayesShrinker
    from sabermetricspy.value import WARFramework

    @register_benchmark(name="engine.calculate_suite", category="engine", default_rows=20_000)
    def _bench_engine_suite(rows: int = 20_000) -> Any:
        idx = pl.int_range(0, rows, eager=True)
        df = pl.DataFrame(
            {
                "player_id": (idx % 200).cast(pl.Utf8),
                "pa": pl.repeat(4, rows, eager=True),
                "ab": pl.repeat(3, rows, eager=True),
                "r": (idx % 4 == 0).cast(pl.Int64),
                "h": (idx % 3 == 0).cast(pl.Int64),
                "b2": (idx % 11 == 0).cast(pl.Int64),
                "b3": (idx % 67 == 0).cast(pl.Int64),
                "hr": (idx % 19 == 0).cast(pl.Int64),
                "rbi": (idx % 4 == 0).cast(pl.Int64),
                "bb": (idx % 5 == 0).cast(pl.Int64),
                "ibb": (idx % 47 == 0).cast(pl.Int64),
                "hbp": (idx % 37 == 0).cast(pl.Int64),
                "sf": (idx % 41 == 0).cast(pl.Int64),
                "sh": pl.repeat(0, rows, eager=True),
                "so": (idx % 4 == 0).cast(pl.Int64),
            }
        )
        return calculate_suite(
            df,
            [MetricSuite.TRADITIONAL_BATTING, MetricSuite.WEIGHTED_OFFENSE],
            by="player_id",
            season=2024,
        )

    @register_benchmark(name="engine.calculate_rolling", category="engine", default_rows=10_000)
    def _bench_engine_rolling(rows: int = 10_000) -> Any:
        idx = pl.int_range(0, rows, eager=True)
        df = pl.DataFrame(
            {
                "player_id": (idx % 100).cast(pl.Utf8),
                "game_num": (idx // 100).cast(pl.Int64),
                "pa": pl.repeat(4, rows, eager=True),
                "ab": pl.repeat(3, rows, eager=True),
                "h": (idx % 3 == 0).cast(pl.Int64),
                "b2": (idx % 11 == 0).cast(pl.Int64),
                "b3": pl.repeat(0, rows, eager=True),
                "hr": (idx % 19 == 0).cast(pl.Int64),
                "bb": (idx % 5 == 0).cast(pl.Int64),
                "ibb": pl.repeat(0, rows, eager=True),
                "hbp": pl.repeat(0, rows, eager=True),
                "sf": pl.repeat(0, rows, eager=True),
            }
        )
        return calculate_rolling(
            df,
            [Metric.AVG, Metric.OBP, Metric.SLG, Metric.WOBA],
            window=15,
            by="player_id",
            order_by="game_num",
        )

    @register_benchmark(
        name="translator.statcast_pitches", category="translator", default_rows=10_000
    )
    def _bench_statcast_translator(rows: int = 10_000) -> Any:
        idx = pl.int_range(0, rows, eager=True)
        raw = pl.DataFrame({"idx": idx}).select(
            (pl.col("idx") % 100).cast(pl.Utf8).alias("batter"),
            pl.when(pl.col("idx") % 7 == 0)
            .then(pl.lit("home_run"))
            .when(pl.col("idx") % 3 == 0)
            .then(pl.lit("single"))
            .otherwise(pl.lit("field_out"))
            .alias("events"),
            pl.lit("hit_into_play").alias("description"),
            pl.lit(4).alias("zone"),
            pl.lit(95.2).alias("launch_speed"),
            pl.lit(14.0).alias("launch_angle"),
            pl.lit(0.340).alias("estimated_ba_using_speedangle"),
            pl.lit(0.580).alias("estimated_slg_using_speedangle"),
            pl.lit(0.395).alias("estimated_woba_using_speedangle"),
        )
        return prepare_statcast_pitches(raw)

    @register_benchmark(name="expectancy.wpa_transform", category="expectancy", default_rows=10_000)
    def _bench_wpa_transform(rows: int = 10_000) -> Any:
        idx = pl.int_range(0, rows, eager=True)
        plays = pl.DataFrame({"idx": idx}).select(
            ((pl.col("idx") % 9) + 1).cast(pl.Int64).alias("inning"),
            pl.when(pl.col("idx") % 2 == 0)
            .then(pl.lit("top"))
            .otherwise(pl.lit("bottom"))
            .alias("half_inning"),
            (pl.col("idx") % 3).cast(pl.Int64).alias("outs_before"),
            pl.when(pl.col("idx") % 4 == 0)
            .then(pl.lit("12-"))
            .otherwise(pl.lit("---"))
            .alias("base_state_before"),
            ((pl.col("idx") % 7) - 3).cast(pl.Int64).alias("home_score_diff_before"),
            ((pl.col("idx") + 1) % 4).cast(pl.Int64).alias("outs_after"),
            pl.lit("---").alias("base_state_after"),
            (pl.col("idx") % 5 == 0).cast(pl.Int64).alias("runs_on_play"),
        )
        wp = WinProbabilityModel.from_default()
        return wp.transform(plays)

    @register_benchmark(name="valuation.pitcher_war_df", category="valuation", default_rows=5_000)
    def _bench_pitcher_war(rows: int = 5_000) -> Any:
        idx = pl.int_range(0, rows, eager=True)
        df = pl.DataFrame(
            {
                "player_id": idx.cast(pl.Utf8),
                "outs": pl.repeat(540, rows, eager=True),
                "g": pl.repeat(30, rows, eager=True),
                "gs": pl.repeat(30, rows, eager=True),
                "hr": (idx % 25),
                "bb": (idx % 60),
                "hbp": (idx % 8),
                "so": (100 + idx % 120),
            }
        )
        fw = WARFramework(season=2024)
        return fw.calculate_pitcher_war_df(df)

    @register_benchmark(
        name="forecasting.marcel_projector", category="forecasting", default_rows=3_000
    )
    def _bench_forecasting(rows: int = 3_000) -> Any:
        idx = pl.int_range(0, rows, eager=True)
        df = pl.DataFrame(
            {
                "player_id": (idx % max(rows // 3, 1)).cast(pl.Utf8),
                "season": (2022 + (idx % 3)).cast(pl.Int64),
                "age": (26 + (idx % 3)).cast(pl.Int64),
                "pa": pl.repeat(550, rows, eager=True),
                "ab": pl.repeat(480, rows, eager=True),
                "h": (130 + (idx % 35)).cast(pl.Int64),
                "hr": (15 + (idx % 20)).cast(pl.Int64),
                "bb": (45 + (idx % 25)).cast(pl.Int64),
                "so": (95 + (idx % 40)).cast(pl.Int64),
            }
        )
        marcel = MarcelProjector(
            target_season=2025, rate_cols=("hr", "bb", "so"), exposure_col="pa"
        )
        return marcel.fit(df).predict()

    @register_benchmark(name="modeling.pitch_quality_plus", category="modeling", default_rows=5_000)
    def _bench_pitch_quality(rows: int = 5_000) -> Any:
        idx = pl.int_range(0, rows, eager=True)
        f_idx = idx.cast(pl.Float64)
        pitches = pl.DataFrame(
            {
                "release_speed": 92.0 + (f_idx % 7.0),
                "ivb": 12.0 + (f_idx % 11.0),
                "hb": -6.0 + (f_idx % 13.0),
                "release_extension": 6.0 + (f_idx % 5.0) * 0.2,
                "spin_rate": 2200.0 + (f_idx % 17.0) * 25.0,
                "vaa": -5.2 + (f_idx % 19.0) * 0.1,
                "plate_x": -0.8 + (f_idx % 23.0) * 0.07,
                "plate_z": 1.6 + (f_idx % 29.0) * 0.06,
                "pitch_rv": -0.015 * ((f_idx % 7.0) - 3.0) - 0.008 * ((f_idx % 11.0) - 5.0),
            }
        )
        pq = PitchQualityModel()
        return pq.fit(pitches).transform(pitches)

    @register_benchmark(
        name="uncertainty.empirical_bayes", category="uncertainty", default_rows=5_000
    )
    def _bench_empirical_bayes(rows: int = 5_000) -> Any:
        idx = pl.int_range(0, rows, eager=True)
        df = pl.DataFrame(
            {
                "player_id": idx.cast(pl.Utf8),
                "ab": 50 + (idx % 500),
                "h": 12 + ((idx * 3) % 140),
            }
        )
        eb = EmpiricalBayesShrinker(success_col="h", trials_col="ab")
        return eb.fit(df).transform(df)


def get_registered_benchmarks() -> dict[str, BenchmarkEntry]:
    """Return a copy of all `@register_benchmark` entries (initializing built-ins if needed)."""
    _ensure_builtin_benchmarks()
    return dict(_BENCHMARK_REGISTRY)


def run_registered_benchmarks(
    *,
    repeats: int = 3,
    category: str | None = None,
    rows: int | None = None,
) -> RegisteredBenchmarkResult:
    """Execute all `@register_benchmark` functions and return a `RegisteredBenchmarkResult`."""
    _ensure_builtin_benchmarks()
    records: list[dict[str, Any]] = []
    for entry in _BENCHMARK_REGISTRY.values():
        if category is not None and entry.category != category:
            continue
        target_rows = rows if rows is not None else entry.default_rows
        # Warmup once
        try:
            entry.fn(target_rows)
        except TypeError:
            entry.fn()

        timings_ms: list[float] = []
        for _ in range(max(repeats, 1)):
            t0 = time.perf_counter_ns()
            try:
                entry.fn(target_rows)
            except TypeError:
                entry.fn()
            t1 = time.perf_counter_ns()
            timings_ms.append((t1 - t0) / 1_000_000.0)

        med_ms = statistics.median(timings_ms)
        mean_ms = statistics.mean(timings_ms)
        min_ms = min(timings_ms)
        rps = (target_rows / (med_ms / 1000.0)) if med_ms > 0 else 0.0
        records.append(
            {
                "name": entry.name,
                "category": entry.category,
                "rows": target_rows,
                "repeats": max(repeats, 1),
                "median_ms": round(med_ms, 3),
                "mean_ms": round(mean_ms, 3),
                "min_ms": round(min_ms, 3),
                "rows_per_sec": round(rps, 1),
            }
        )
    return RegisteredBenchmarkResult(records=tuple(records))


__all__ = [
    "BenchmarkEntry",
    "PerformanceTracker",
    "RegisteredBenchmarkResult",
    "SpanRecord",
    "get_registered_benchmarks",
    "profiled",
    "register_benchmark",
    "run_registered_benchmarks",
    "telemetry",
]
