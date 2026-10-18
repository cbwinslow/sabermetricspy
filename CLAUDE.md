# sabermetricspy Development Guide

## Quick Commands
- **Environment Setup:**
  - `uv sync --all-extras`
- **Testing & Quality Gates:**
  - Run all tests: `uv run pytest`
  - Run specific test: `uv run pytest tests/ -k "test_batting"`
  - Lint & Format: `uv run ruff check .` and `uv run ruff format .`
  - Strict Type Check: `uv run pyright`
- **OpenSpec Workflow:**
  - View status: `openspec status`
  - List changes: `openspec list`
  - Validate specs: `openspec validate`

## Package Structure
- `src/sabermetricspy/types/`: `StrEnum` definitions (`Metric`, `Stat`, `MetricSuite`, `Category`, `ImplKind`, `Direction`, `Handedness`, `PitchOutcome`, `PlayOutcome`, `BattedBallType`, `BaseState`) and frozen context models.
- `src/sabermetricspy/schema/`: Canonical column definitions, alias resolution, safe division helpers, and innings (`"6.2"` <-> `20` outs) conversion utilities.
- `src/sabermetricspy/constants/`: Seasonal constants loader (`wOBA` weights, `FIP` constants, park factors) backed by bundled YAML in `src/sabermetricspy/data/constants/`.
- `src/sabermetricspy/registry/`: `MetricSpec`, `@register_metric`, topological DAG dependency solver, and `MetricSuite` expansion.
- `src/sabermetricspy/metrics/`: Pure vectorized `narwhals` expressions for batting, weighted offense, pitching, DIPS, plate discipline, batted-ball, baserunning, fielding, and team estimators.
- `src/sabermetricspy/engine/`: Two-stage calculation engine (`calculate`, `calculate_suite`, `calculate_available`) returning frozen `CalculationResult`.
- `src/sabermetricspy/expectancy/`: Empirical state matrices (`RunExpectancyMatrix` RE24, `CountExpectancyMatrix` RE288, `LinearWeightsEstimator`, `WinProbabilityModel`).
- `src/sabermetricspy/value/`: Park adjustments, replacement level, and modular `WARFramework`.
- `src/sabermetricspy/models/`: Forecasting and matchup estimators (`MarcelProjector`, `Log5Model`, `MarkovChainModel`, `MonteCarloSimulator`).
- `src/sabermetricspy/uncertainty/`: Analytical confidence intervals and seeded bootstrap estimator.
- `src/sabermetricspy/presets/`: Built-in column and event mappers for `retrosheetpy`, `statcast`, and `lahman`.
- `src/sabermetricspy/telemetry/`: Decorator-based performance telemetry (`@profiled`, `PerformanceTracker`, `sb.telemetry`) and benchmark registry (`@register_benchmark`, `run_registered_benchmarks`).

## Key Rules
1. Follow the **3-Tier Naming Standard** in `docs/NAMING_CONVENTIONS.md` without exception.
2. Never use per-row Python loops in metric calculations; always build `narwhals.Expr` expressions.
3. Always sum counting stats before dividing to compute rate metrics.
4. Always decorate new calculation functions, translators, and estimator `.fit()` / `.transform()` / `.predict()` / `.simulate()` methods with `@profiled(category=...)`, and register new subsystem benchmarks with `@register_benchmark(...)`.
5. Keep `openspec/` specs and `docs/DECISIONS.md` synchronized with architectural changes.
