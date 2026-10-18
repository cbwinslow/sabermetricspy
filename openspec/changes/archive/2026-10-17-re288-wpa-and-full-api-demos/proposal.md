# Proposal: Count Expectancy (RE288), Win Probability (WPA & LI), and End-to-End API Demos

## Why
To ensure 100% of the classes and metrics described in our architecture blueprint (`openspec/project.md` and `docs/ARCHITECTURE.md`) are implemented, verified, and demonstrated end-to-end, we need to complete `CountExpectancyMatrix` (`RE288` 288-state ball-strike-base-out expectancy), `WinProbabilityModel` (`WPA`, `LeverageIndex` `LI`, `pLI`, `Shutdown`/`Meltdown`), and build runnable demonstration scripts (`examples/`) plus an exhaustive test verifying every single `Metric` enum member and public class.

## What Changes
1. **Count Expectancy (`CountExpectancyMatrix` / `RE288`) in `sabermetricspy.expectancy`**:
   - Implement `CountExpectancyMatrix` covering all 288 `(balls, strikes, outs, base_state)` states (`12 counts x 24 base-out states`), pitch-level run value (`pitch_run_value`), and Jim Albert's `count_leverage = |RV(next strike) - RV(next ball)|`.
2. **Win Probability & Leverage Index (`WinProbabilityModel`) in `sabermetricspy.expectancy`**:
   - Implement `WinProbabilityModel` (`.fit()`, `.transform()`, `.results`) computing pre-play and post-play win probability (`wp_before`, `wp_after`), Win Probability Added (`wpa`), situational Leverage Index (`li`), and player-level `wpa_per_li`, `pLI`, `shutdowns` (`WPA >= +0.06`), and `meltdowns` (`WPA <= -0.06`).
3. **End-to-End Runnable Demo Suite (`examples/`)**:
   - `examples/01_batting_and_pitching_leaderboards.py`: Multi-backend (`Polars`, `DuckDB`, `PyArrow`, `pandas`) batting & pitching leaderboards and provenance summaries.
   - `examples/02_yaml_translators_and_custom_metrics.py`: `retrosheetpy`, `statcast`, and custom YAML provider translation + custom YAML metric formulas.
   - `examples/03_expectancy_re24_re288_and_wpa.py`: `RunExpectancyMatrix` (`RE24`), `CountExpectancyMatrix` (`RE288`), `LinearWeightsEstimator`, and `WinProbabilityModel` (`WPA` & `LI`).
   - `examples/04_war_and_forecasting_models.py`: `WARFramework`, `MarcelProjector`, `Log5Model`, `MarkovChainModel`, `MonteCarloSimulator`, and uncertainty intervals.
4. **Exhaustive 100% Metric & Class Audit Test**:
   - Add a test in `tests/test_sabermetricspy.py` that iterates through every member of `Metric` and `MetricSuite`, plus `CountExpectancyMatrix` and `WinProbabilityModel`, confirming 100% of registered metrics and classes execute cleanly.

## Impact
- Completes the entire `expectancy` module (`RE24`, `RE288`, `LinearWeights`, `WPA`, `LI`) and provides live, runnable demos verifying every feature in `sabermetricspy`.
