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
- `src/sabermetricspy/constants/`: Seasonal constants loader (`wOBA` weights, `FIP` constants, park factors, WAR inputs) reading YAML from a directory the caller supplies (`use_constants`, `$SABERMETRICSPY_CONSTANTS`); no constants are shipped (ADR-0068, `docs/CONSTANTS.md`).
- `src/sabermetricspy/fetch/`: On-request fetch of Guts!, park factors and league totals into the user cache (`update_constants`, `sabermetrics constants update`); the only network code in the package (ADR-0069).
- `src/sabermetricspy/registry/`: `MetricSpec`, `@register_metric`, topological DAG dependency solver, and `MetricSuite` expansion.
- `src/sabermetricspy/metrics/`: Pure vectorized `narwhals` expressions for batting, weighted offense, pitching, DIPS, plate discipline, batted-ball, baserunning, fielding, and team estimators.
- `src/sabermetricspy/engine/`: Two-stage calculation engine (`calculate`, `calculate_suite`, `calculate_available`) returning frozen `CalculationResult`.
- `src/sabermetricspy/expectancy/`: Empirical state matrices (`RunExpectancyMatrix` RE24, `CountExpectancyMatrix` RE288, `LinearWeightsEstimator`).
- `src/sabermetricspy/value/`: Park adjustments, replacement level, and modular `WARFramework`.
- `src/sabermetricspy/models/`: Forecasting and matchup estimators (`MarcelProjector`, `Log5Model`, `MarkovChainModel`).
- `src/sabermetricspy/ids/`: Chadwick Register player-id crosswalk (`translate_ids`, `find_players`, `player_id`, `load_register`); the caller downloads the register, the library never does (ODC-BY 1.0).
- `src/sabermetricspy/lahman/`: League constants (runs per PA, OBP, SLG, ERA, cFIP, kwERA, caught-stealing run value) computed from Lahman files the caller supplies (`league_constants`); the library never downloads them.
- `src/sabermetricspy/uncertainty/`: Analytical confidence intervals and seeded bootstrap estimator.
- `src/sabermetricspy/presets/`: Built-in column and event mappers for `retrosheetpy`, `statcast`, and `lahman`.
- `src/sabermetricspy/telemetry/`: Decorator-based performance telemetry (`@profiled`, `PerformanceTracker`, `sb.telemetry`) and benchmark registry (`@register_benchmark`, `run_registered_benchmarks`).

- `docs/VERIFICATION.md`: what is confirmed against outside values, measured gaps, and the research queue. Update it with every audit change.

## Key Rules
1. Follow the **3-Tier Naming Standard** in `docs/NAMING_CONVENTIONS.md` without exception.
2. Never use per-row Python loops in metric calculations; always build `narwhals.Expr` expressions.
3. Always sum counting stats before dividing to compute rate metrics.
4. Always decorate new calculation functions, translators, and estimator `.fit()` / `.transform()` / `.predict()` / `.simulate()` methods with `@profiled(category=...)`, and register new subsystem benchmarks with `@register_benchmark(...)`.
5. Keep `openspec/` specs and `docs/DECISIONS.md` synchronized with architectural changes.
6. If an existing tool or library would easily solve a problem, bring it up and consider using it before writing our own. Do not rule options out for arbitrary reasons; a tool that was a poor fit earlier may become viable later.
7. Only ship metrics and models that use widely established, publicly documented methods and reproduce outside reference values in a test. If there is no consensus method or no outside value to check against, do not ship it as a supported feature; propose removing or clearly quarantining it instead of approximating. Plain arithmetic ratios of standard counting stats (for example HR/PA) are allowed when the name states the denominator and a hand-computed test pins the value.
8. Every new ADR gets an **Alternatives** section. Phrase each as "not chosen now, because X; revisit if Y", never as a permanent rejection.
