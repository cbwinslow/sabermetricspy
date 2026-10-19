# ADR-0026: 105+ Metric Registry & Open Modeled Estimators (`Stuff+`, `xwOBA`, `Framing`, `OAA`, `EmpiricalBayesShrinker`)

- **Status**: Accepted
- **Date**: 2026-10-17

## Context
Our research blueprint (`media_1792128562811_9f3851c1.md`) defines both:
1. Additional deterministic and contextual metrics across batting, pitching/DIPS (including Basco & Davies 2010 formulas such as `QERA` and `DIPS_BOP_PCT`), plate discipline (`PutAway%`, `2K Chase%`, `BIP%`), pitch kinematics (`Bauer Units`, `HAA`, `RV/100`), baserunning (`XBT%`, `wGDP`, `BsR`), and expectancy aggregates (`pLI`, `WPA/LI`, `Clutch`, `REW`).
2. Modeled and empirical estimators that follow a `scikit-learn` `.fit()` / `.transform()` interface with `statsmodels`-style frozen `.results` objects and mandatory `@profiled` / `@register_benchmark` decorators.

## Decision
1. **Expand `MetricRegistry` to 105 Canonical Metrics**:
   - Add 29 new metrics (`BAT_K_PCT_PLUS`, `BAT_BB_PCT_PLUS`, `RC27`, `GPA`, `TA`, `PIT_BB_TO_K`, `PIT_K_TO_BB`, `BF_PER_IP`, `K_PCT_PLUS`, `BB_PCT_PLUS`, `QERA`, `DIPS_BOP_PCT`, `XERA`, `HAA`, `BAUER_UNITS`, `RV_PER_100`, `WHIFF_PER_100`, `BIP_PCT`, `PUTAWAY_PCT`, `TWO_STRIKE_CHASE_PCT`, `MEATBALL_SWING_PCT`, `ERR_PCT`, `XBT_PCT`, `WGDP`, `BSR`, `PLI`, `WPA_LI`, `CLUTCH`, `REW`) and `MetricSuite.EXPECTANCY`.
2. **Implement Modeled & Empirical Estimators**:
   - `EmpiricalBayesShrinker` (`EmpiricalBayesResults`): Beta-Binomial Empirical Bayes shrinkage with learned $(\hat{\alpha}_0, \hat{\beta}_0)$, shrinkage weights, and Beta credible intervals.
   - `ExpectedOutcomeModel` (`ExpectedOutcomeResults`): Open k-NN contact-quality estimator predicting `xba_est`, `xslg_est`, and `xwoba_est`.
   - `PitchQualityModel` (`PitchQualityResults`): Open `statsmodels` OLS estimator producing `stuff_plus`, `location_plus`, and `pitching_plus` on the `100 ± 10` scale with $R^2$, F-statistic, and p-value diagnostics.
   - `CatcherFramingModel` (`CatcherFramingResults`) & `OutsAboveAverageModel` (`OutsAboveAverageResults`): Opportunity-based defensive models for shadow-zone framing (`cs_prob`, `strikes_above_avg`, `framing_runs`) and range (`catch_prob`, `oaa`, `fielding_runs`).
   - `WARFramework.calculate_position_player_df()`: Vectorized DataFrame position-player WAR matching `calculate_position_player_scalar`.
