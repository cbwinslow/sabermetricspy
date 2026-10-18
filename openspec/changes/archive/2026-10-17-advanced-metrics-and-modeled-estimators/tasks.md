# Tasks: Advanced Metrics Expansion & Modeled Sabermetric Estimators

- [x] 1. Expand `Stat` and `Metric` enums (`src/sabermetricspy/types/enums.py`) and register 24+ new deterministic & contextual metrics across `batting.py`, `weighted.py`, `pitching.py`, and `specialized.py` (pushing total registered metrics past 105).
- [x] 2. Implement `WARFramework.calculate_position_player_df()` in `src/sabermetricspy/value/__init__.py` decorated with `@profiled(category="valuation")`.
- [x] 3. Implement `EmpiricalBayesShrinker` (`EmpiricalBayesResults`) in `src/sabermetricspy/uncertainty/__init__.py` decorated with `@profiled(category="uncertainty")`.
- [x] 4. Implement `ExpectedOutcomeModel` (`ExpectedOutcomeResults`), `PitchQualityModel` (`PitchQualityResults`), `CatcherFramingModel` (`CatcherFramingResults`), and `OutsAboveAverageModel` (`OutsAboveAverageResults`) in `src/sabermetricspy/models/` decorated with `@profiled(category="modeling")`, and register new workloads with `@register_benchmark`.
- [x] 5. Record `ADR-0026` in `docs/DECISIONS.md` and `docs/decisions/ADR-0026-modeled-estimators-and-100-plus-metrics.md`.
- [x] 6. Add comprehensive unit, property-based (`hypothesis`), and golden tests in `tests/test_sabermetricspy.py` plus runnable Demo 06 (`examples/06_advanced_models_stuff_plus_framing_and_ebayes.py`).
- [x] 7. Validate with `openspec validate --all`, `uv run ruff check .`, `uv run pyright`, and `uv run pytest`, then archive the change.
