# Proposal: Execution Telemetry & Benchmarking, Rolling-Window Engine, Pitch-Physics & Expected Metrics, and CLI

## Why
To ensure `sabermetricspy` maintains sub-second throughput across millions of play-by-play and pitch-level rows while expanding analytical coverage, we need:
1. **Hybrid Performance Telemetry & Benchmarking**:
   - Built-in zero-overhead `ExecutionProfile` attached to every `CalculationResult` (`.profile`) measuring stage-by-stage timing (`translation_ms`, `normalization_ms`, `aggregation_ms`, `dag_eval_ms`, `total_ms`, `rows_in`, `rows_out`, `rows_per_sec`, `backend`) using `time.perf_counter_ns()`.
   - A built-in multi-backend `benchmark()` utility for comparing execution throughput across Polars, DuckDB, PyArrow, and pandas.
   - Pure vectorized Polars/Narwhals expressions inside `WinProbabilityModel.transform()` (replacing `iter_rows`) so WPA and Leverage Index evaluate at `>1,000,000 rows/sec`.
   - Automated regression benchmarks in the test suite via `pytest-benchmark` (as a `dev` dependency).
2. **Additive Rolling-Window Engine (`calculate_rolling`)**:
   - Sabermetric analysts frequently evaluate rolling $N$-game or $N$-PA trends (`wOBA`, `wRC+`, `CSW%`, `HardHit%`, `FIP`). Because ratios must never be averaged, `calculate_rolling()` must sum additive counting columns over each rolling window first (`by=...`, `order_by=...`, `window=...`), and then evaluate all requested metric expressions over the rolling sums.
3. **Pitch-Tracking Physics & Statcast Expected Metrics (`xBA`, `xSLG`, `xwOBA`, `VAA`, `IVB`, `HB`, `EffectiveVelocity`)**:
   - Support aggregated Statcast expected metrics (`XBA`, `XSLG`, `XWOBA`, `XWOBA_DIFF`) and pitch-tracking kinematics/physics (`AVG_VELO`, `AVG_SPIN`, `AVG_EXTENSION`, `IVB` Induced Vertical Break, `HB` Horizontal Break, `TOTAL_BREAK`, `VAA` Vertical Approach Angle, `EFFECTIVE_VELO`).
4. **Command-Line Interface (`sabermetrics` CLI)**:
   - A rich, zero-dependency CLI entrypoint (`sabermetrics`) enabling users to list/search registered metrics, inspect LaTeX formulas & citations (`sabermetrics info wrc_plus`), and run live multi-backend throughput benchmarks (`sabermetrics benchmark --rows 250000`) directly from the terminal.

## What Changes
- **Modified**: `pyproject.toml` (add `pytest-benchmark` to `dev` dependency group; add `sabermetrics = "sabermetricspy.cli:main"` script entrypoint).
- **Modified**: `src/sabermetricspy/engine/__init__.py` (add `ExecutionProfile`, `BenchmarkReport`, `benchmark()`, `calculate_rolling()`, and attach `.profile` to `CalculationResult`).
- **Modified**: `src/sabermetricspy/expectancy/__init__.py` (vectorize `WinProbabilityModel.transform()` using Polars expressions and normal-approximation error function approximations).
- **Modified**: `src/sabermetricspy/types/enums.py`, `src/sabermetricspy/metrics/specialized.py`, `src/sabermetricspy/data/presets/aliases.yaml`, `src/sabermetricspy/data/presets/sources.yaml`, and `src/sabermetricspy/presets/__init__.py` (add pitch-physics & Statcast expected stats `Stat` and `Metric` members, `MetricSuite.STATCAST_EXPECTED`, `MetricSuite.PITCH_PHYSICS`, and YAML translation rules).
- **Added**: `src/sabermetricspy/cli/__init__.py` (implement `sabermetrics` CLI with `list`, `info`, `suites`, and `benchmark` subcommands).
- **Added**: `examples/05_benchmarking_rolling_physics_and_cli.py` and expanded tests in `tests/test_sabermetricspy.py` and `tests/test_benchmarks.py`.
