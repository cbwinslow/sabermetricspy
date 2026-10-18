# Tasks: Count Expectancy (RE288), Win Probability (WPA & LI), and End-to-End API Demos

- [x] 1. **Implement `CountExpectancyMatrix` (`RE288`) and `WinProbabilityModel` (`WPA` & `LI`)**
  - [x] 1.1 Add `RE288Results`, `CountExpectancyMatrix`, `WinProbabilityResults`, and `WinProbabilityModel` to `src/sabermetricspy/expectancy/__init__.py` and export them in `src/sabermetricspy/__init__.py`.
- [x] 2. **Create End-to-End Runnable Demo Suite (`examples/`)**
  - [x] 2.1 Create `examples/01_batting_and_pitching_leaderboards.py` demonstrating multi-backend calculations, suites, auto-discovery, and provenance tables.
  - [x] 2.2 Create `examples/02_yaml_translators_and_custom_metrics.py` demonstrating `retrosheetpy`, `statcast`, custom YAML source translators, and custom YAML metric compilation.
  - [x] 2.3 Create `examples/03_expectancy_re24_re288_and_wpa.py` demonstrating `RunExpectancyMatrix` (`RE24`), `CountExpectancyMatrix` (`RE288`), `LinearWeightsEstimator`, and `WinProbabilityModel` (`WPA` & `LI`).
  - [x] 2.4 Create `examples/04_war_and_forecasting_models.py` demonstrating `WARFramework`, `MarcelProjector`, `Log5Model`, `MarkovChainModel`, `MonteCarloSimulator`, and uncertainty intervals.
- [x] 3. **Exhaustive API Audit & Verification**
  - [x] 3.1 Add `test_all_registered_metrics_and_suites_audit` and `test_re288_and_win_probability_model` to `tests/test_sabermetricspy.py`.
  - [x] 3.2 Execute all 4 demo scripts, run `uv run ruff check .`, `uv run pyright`, `uv run pytest --cov=sabermetricspy`, and `openspec validate --all`.
