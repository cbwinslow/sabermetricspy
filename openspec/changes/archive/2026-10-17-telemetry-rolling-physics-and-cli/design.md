# Design: Execution Telemetry, Rolling Engine, Pitch Physics, and CLI

## 1. Hybrid Telemetry & Benchmarking Architecture (`ADR-0021`)
- **Zero-Overhead Internal Telemetry (`ExecutionProfile`)**:
  - Uses Python's standard library `time.perf_counter_ns()` around each pipeline stage in `calculate()`:
    1. `translation_ms`: Optional YAML `SourceTranslator` execution.
    2. `normalization_ms`: Column alias normalization and `ip` $\to$ `outs` conversion.
    3. `aggregation_ms`: Group-by or rolling-window additive summation.
    4. `dag_eval_ms`: Topological DAG expression evaluation.
    5. `total_ms`, `rows_in`, `rows_out`, `rows_per_sec`, and `backend` (`"polars"`, `"duckdb"`, `"pyarrow"`, `"pandas"`).
  - Stored as a frozen Pydantic model on `CalculationResult.profile`.
- **Multi-Backend Benchmark Runner (`sb.benchmark`)**:
  - Accepts any input DataFrame (or generates a synthetic play/pitch dataset of $N$ rows), converts it into each requested backend (`polars`, `duckdb`, `pyarrow`, `pandas`), runs `warmup` + `repeats` iterations of `calculate()`, and returns a frozen `BenchmarkResult` containing a summary Polars DataFrame (`backend`, `rows`, `metrics_count`, `min_ms`, `median_ms`, `mean_ms`, `rows_per_sec`, `relative_speedup`).
- **Vectorized `WinProbabilityModel.transform()`**:
  - Replaces the row-by-row Python loop with pure vectorized Polars expressions using Abramowitz & Stegun's high-precision polynomial approximation to $\text{erf}(x)$ (maximum absolute error $\le 1.5 \times 10^{-7}$), achieving $>1,000,000$ rows/sec.
- **`pytest-benchmark` Dev Suite (`tests/test_benchmarks.py`)**:
  - Uses `pytest-benchmark` fixtures to benchmark batting leaderboards, pitching leaderboards, YAML `SourceTranslator`, `RE24`, `RE288`, and vectorized `WPA`.

## 2. Additive Rolling-Window Engine (`calculate_rolling`, `ADR-0022`)
- **Mathematical Rule**:
  - A 15-game rolling `OBP` or 50-PA rolling `wOBA` is **never** the rolling average of per-game `OBP` or `wOBA`.
  - `calculate_rolling(df, metrics, window=15, *, by="player_id", order_by="game_date", min_periods=1)`:
    1. Sorts by `(by, order_by)`.
    2. Computes rolling sums (`rolling_sum(window_size=window, min_samples=min_periods).over(by)`) for all required and optional additive counting columns (`pa`, `ab`, `h`, `b2`, `b3`, `hr`, `bb`, `ibb`, `hbp`, `sf`, `outs`, `er`, `so`, `pitches`, `swings`, `whiffs`, etc.).
    3. Evaluates the exact same Narwhals topological metric DAG over those rolling additive count columns.

## 3. Pitch-Tracking Physics & Statcast Expected Metrics (`ADR-0023`)
- **Expected Offense (`MetricSuite.STATCAST_EXPECTED`)**:
  - `Stat.XBA_SUM`, `Stat.XSLG_SUM`, `Stat.XWOBA_SUM`, `Stat.XWOBA_COUNT` accumulated from pitch/play rows (`estimated_ba_using_speedangle`, `estimated_slg_using_speedangle`, `estimated_woba_using_speedangle`).
  - `Metric.XBA = xba_sum / ab` (or `xwoba_count`), `Metric.XSLG = xslg_sum / ab`, `Metric.XWOBA = xwoba_sum / xwoba_count`, `Metric.WOBA_MINUS_XWOBA = woba - xwoba`, `Metric.BA_MINUS_XBA = avg - xba`.
- **Pitch Kinematics & Physics (`MetricSuite.PITCH_PHYSICS`)**:
  - `Metric.AVG_VELO = velo_sum / velo_count` (`release_speed`).
  - `Metric.AVG_SPIN = spin_sum / spin_count` (`release_spin_rate`).
  - `Metric.AVG_EXTENSION = ext_sum / ext_count` (`release_extension`).
  - `Metric.IVB = ivb_sum / break_count` (Induced Vertical Break in inches, `pfx_z * 12`).
  - `Metric.HB = hb_sum / break_count` (Horizontal Break in inches, `pfx_x * 12`).
  - `Metric.TOTAL_BREAK = sqrt(ivb^2 + hb^2)`.
  - `Metric.EFFECTIVE_VELO = eff_velo_sum / eff_velo_count` (`effective_speed`).
  - `Metric.VAA = vaa_sum / vaa_count` (Vertical Approach Angle in degrees at home plate derived from Statcast 9-parameter kinematics $y_0=50\text{ ft}, v_{y0}, v_{z0}, a_y, a_z$: $t = \frac{-v_{y0} - \sqrt{v_{y0}^2 - 2 a_y (50 - 1.417)}}{a_y}$, $v_{yf} = v_{y0} + a_y t$, $v_{zf} = v_{z0} + a_z t$, $\text{VAA} = \arctan2(v_{zf}, -v_{yf}) \times \frac{180}{\pi}$).

## 4. Command-Line Interface (`sabermetrics` CLI, `ADR-0024`)
- Implemented in `src/sabermetricspy/cli/__init__.py` using `argparse`:
  - `sabermetrics list [--category <cat>]` — tabular listing of all registered metrics (Tier 1, Tier 2, Tier 3, category, required columns).
  - `sabermetrics info <metric>` — full provenance card (Tier 1/2/3 names, LaTeX formula, required/optional columns, dependencies, citation).
  - `sabermetrics suites` — list all `MetricSuite` bundles and their expanded metrics.
  - `sabermetrics benchmark [--rows 100000] [--repeats 5]` — run live multi-backend throughput benchmark and print formatted table.
