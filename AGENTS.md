# sabermetricspy — Agent Contract

Read `openspec/project.md` first, along with `docs/ARCHITECTURE.md`, `docs/NAMING_CONVENTIONS.md`, and `docs/DECISIONS.md`.

## 1. Architecture & Mathematical Rules
- **Pure Vectorized Expressions**: All core metrics MUST be written using `narwhals` expressions (`nw.Expr`) so they execute natively on Polars, DuckDB, PyArrow, and pandas. Never write per-row Python `for` loops.
- **3-Tier Naming Convention**:
  - **Tier 1 (`StrEnum`)**: `UPPER_SNAKE_CASE` official baseball abbreviations (`Metric.WRC_PLUS`, `Metric.CSW_PCT`, `Stat.HR`, `Stat.OUTS`).
  - **Tier 2 (Columns & Functions)**: `lower_snake_case` (`"wrc_plus"`, `"csw_pct"`, `"hr"`, `"outs"`).
  - **Tier 3 (`MetricSpec.display_name`)**: Authentic sabermetric typography (`"wRC+"`, `"CSW%"`, `"HR"`, `"Outs"`).
- **Additive Counts First, Ratios Second**: Always aggregate counting columns across the requested grouping (`by=...`) or window before evaluating division/rate formulas. Never average ratios.
- **Innings as Integer Outs**: Always store and calculate innings pitched as integer `outs` (`1 IP = 3 outs`). Convert baseball notation (`"6.2"` = 20 outs) strictly at I/O edges.
- **Zero-Denominator & Null Safety**: Division by zero MUST evaluate to `null`/`NaN` (using safe division helper expressions), never `inf` or `ZeroDivisionError`.
- **Immutable Return Objects**: Stateless calculations return frozen `CalculationResult` objects; fitted estimators (`RunExpectancyMatrix`, `MarcelProjector`, `Log5Model`, etc.) implement `.fit()` / `.transform()` / `.predict()` and attach frozen `.results` objects.
- **Provenance & Citations**: Every metric in the registry MUST declare a complete `MetricSpec` including LaTeX formula, primary citation, required columns, and caveats. Never invent unverified constants.
- **Mandatory Telemetry & Benchmark Decorators (`@profiled` & `@register_benchmark`)**: Always decorate new calculation entrypoints, translators, estimator `.fit()` / `.transform()` / `.predict()` / `.simulate()` methods, and valuation/uncertainty functions with `@profiled(category=...)` from `sabermetricspy.telemetry`, and register representative subsystem benchmark workloads with `@register_benchmark(...)`.

## 2. Spec-Driven & Test-Driven Workflow (OpenSpec + TDD)
- Work through OpenSpec changes (`openspec/changes/`) and specifications (`openspec/specs/`).
- Every metric or model implementation requires:
  1. **Unit Tests**: Edge cases (`0` denominators, missing optional columns, `5.1`/`5.2` IP conversions).
  2. **Property-Based Tests (`hypothesis`)**: Mathematical identities (`OPS == OBP + SLG`, `ISO == SLG - AVG`, `0 <= AVG <= OBP`, `K_MINUS_BB_PCT == K_PCT - BB_PCT`).
  3. **Golden Cross-Check Tests**: Verified against published FanGraphs, Baseball-Reference, Retrosheet, or `baseballr` player-season benchmarks.
  4. **Multi-Backend Verification**: Tested across Polars, DuckDB, PyArrow, and pandas.

## 3. Quality Gate Commands
- Lint & format check: `uv run ruff check .` and `uv run ruff format --check .`
- Strict type check: `uv run pyright`
- Test suite: `uv run pytest`
