# Tasks: Execution Telemetry & Benchmarking, Rolling-Window Engine, Pitch-Physics & Expected Metrics, and CLI

- [x] 1. **Dependencies, Enums, and Pitch-Physics / Expected Metrics**
  - [x] 1.1 Update `pyproject.toml` to add `pytest-benchmark>=5.1.0` to `dev` dependencies and register `[project.scripts] sabermetrics = "sabermetricspy.cli:main"`.
  - [x] 1.2 Add `Stat`, `Metric`, and `MetricSuite` (`STATCAST_EXPECTED`, `PITCH_PHYSICS`) enum members to `src/sabermetricspy/types/enums.py` and `src/sabermetricspy/registry/__init__.py`.
  - [x] 1.3 Register Statcast expected (`xba`, `xslg`, `xwoba`, `woba_minus_xwoba`, `ba_minus_xba`) and pitch-physics (`avg_velo`, `avg_spin`, `avg_extension`, `ivb`, `hb`, `total_break`, `effective_velo`, `vaa`) metrics in `src/sabermetricspy/metrics/specialized.py`, and update `aliases.yaml`, `sources.yaml`, and `src/sabermetricspy/presets/__init__.py` (including exact 9-parameter kinematics VAA derivation).
- [x] 2. **Execution Telemetry (`ExecutionProfile`), `benchmark()`, Rolling Engine (`calculate_rolling`), and Vectorized `WPA`**
  - [x] 2.1 Add `ExecutionProfile`, `BenchmarkResult`, `benchmark()`, and `calculate_rolling()` to `src/sabermetricspy/engine/__init__.py` and attach `.profile` to `CalculationResult`.
  - [x] 2.2 Vectorize `WinProbabilityModel.transform()` in `src/sabermetricspy/expectancy/__init__.py` using Polars expressions.
- [x] 3. **CLI Tool (`sabermetrics`), Demo 05, and Benchmark / Unit Tests**
  - [x] 3.1 Create `src/sabermetricspy/cli/__init__.py` implementing `sabermetrics list`, `sabermetrics info`, `sabermetrics suites`, and `sabermetrics benchmark`, and export new symbols in `src/sabermetricspy/__init__.py`.
  - [x] 3.2 Create `examples/05_benchmarking_rolling_physics_and_cli.py`, add tests to `tests/test_sabermetricspy.py`, and create `tests/test_benchmarks.py` using `pytest-benchmark`.
  - [x] 3.3 Record `ADR-0021` through `ADR-0024` in `docs/DECISIONS.md`, run all quality gates (`ruff`, `pyright`, `pytest`, `openspec validate --all`), and archive the change.
