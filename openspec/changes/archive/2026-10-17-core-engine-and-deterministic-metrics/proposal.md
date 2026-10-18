# Proposal: Core Engine, Registry, Presets, Expectancy, and Metrics Suite

## Why
Baseball researchers and engineers currently lack a strongly-typed, dataframe-agnostic Python calculation engine that unifies deterministic metrics, contextual seasonal constants (`wOBA`, `FIP`, `wRC+`), empirical play-by-play expectancy matrices (`RE24`, `RE288`, `WPA`), and statistical forecasting systems (`Marcel`, `Log5`, `MarkovChain`, `MonteCarlo`) with verifiable provenance and multi-backend performance (`Polars`, `DuckDB`, `PyArrow`, `pandas`).

## What Changes
1. **Foundational Types & Naming Architecture (`sabermetricspy.types`)**:
   - Implement the 3-tier naming convention via `StrEnum` classes (`Metric`, `Stat`, `MetricSuite`, `Category`, `ImplKind`, `Direction`, `Handedness`, `PitchOutcome`, `PlayOutcome`, `BattedBallType`, `BaseState`) and frozen Pydantic value objects (`SeasonContext`, `WOBAWeights`, `FIPConstants`, `SIERACoefficients`).
2. **Schema, Innings-to-Outs, & Safe Math Utilities (`sabermetricspy.schema`)**:
   - Implement canonical column resolution, alias mapping, baseball innings (`"6.2"` <-> `20` outs) conversion, and zero-denominator-safe Narwhals expression builders.
3. **Bundled YAML Constants & Presets (`sabermetricspy.constants`, `sabermetricspy.presets`)**:
   - Ship YAML seasonal constants (`woba_fangraphs.yaml`, `fip_constants.yaml`, `park_factors.yaml`) and first-class source presets for `retrosheetpy` (`events` & `gamelogs`), `statcast`, and `lahman`.
4. **Metric Registry & Topological DAG Engine (`sabermetricspy.registry`, `sabermetricspy.engine`)**:
   - Implement `MetricSpec`, `@register_metric`, automatic DAG dependency resolution, `MetricSuite` expansion, `calculate()`, `calculate_suite()`, `calculate_available()`, and the frozen `CalculationResult` object.
5. **Comprehensive Metrics Suite (`sabermetricspy.metrics`)**:
   - Traditional Batting, Weighted Offense (`wOBA`, `wRAA`, `wRC`, `wRC+`, `OPS+`, `Runs Created`, `BaseRuns`), Traditional Pitching, Defense-Independent Pitching (`FIP`, `xFIP`, `kwERA`, `SIERA`, `DICE`, `ERA+`, `ERA-`, `FIP-`, `xFIP-`), Plate Discipline, Batted-Ball Quality, Baserunning, Fielding, and Team Pythagorean/Pythagenpat estimators.
6. **Empirical Expectancy & Fitted Forecasting Models (`sabermetricspy.expectancy`, `sabermetricspy.models`, `sabermetricspy.value`, `sabermetricspy.uncertainty`)**:
   - Implement `RunExpectancyMatrix` (`RE24`), `CountExpectancyMatrix` (`RE288`), `LinearWeightsEstimator`, `WinProbabilityModel` (`WPA`, `LI`), `WARFramework`, `MarcelProjector`, `Log5Model`, `MarkovChainModel`, `MonteCarloSimulator`, and analytical/bootstrap uncertainty intervals.

## Impact
- Establishes the complete `v0.1.0` architecture and test suite (`pytest`, `hypothesis`, `pyright --strict`, `ruff`) for `sabermetricspy`.
