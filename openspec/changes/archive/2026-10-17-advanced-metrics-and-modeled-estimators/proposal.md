# Proposal: Advanced Metrics Expansion & Modeled Sabermetric Estimators

## Why
While `sabermetricspy` currently includes 81 registered metrics alongside RE24/RE288/WPA expectancy models, Marcel/Log5/Markov/Monte Carlo forecasting, and scalar/pitcher WAR, our research blueprint (`media_1792128562811_9f3851c1.md`) specifies an additional wave of classical and modern deterministic/contextual formulas (pushing the registry past **100+ canonical metrics**) plus the modeled/empirical estimator classes (`EmpiricalBayesShrinker`, `ExpectedOutcomeModel` for open `xBA`/`xSLG`/`xwOBA`, `PitchQualityModel` for open `Stuff+`/`Location+`/`Pitching+`, `CatcherFramingModel`, `OutsAboveAverageModel`, and vectorized `WARFramework.calculate_position_player_df`).

## What Changes
1. **Metric Registry Expansion (81 → 105 Canonical Metrics)**:
   - **Batting & Weighted Offense**: `GPA` (Gross Production Average), `TA` (Total Average), `RC27` (Runs Created per 27 Outs), `BAT_K_PCT_PLUS` (`K%+`), `BAT_BB_PCT_PLUS` (`BB%+`).
   - **Pitching & DIPS**: `BF_PER_IP` (`BF/IP`), `PIT_BB_TO_K` (`BB/K (Pit)`), `PIT_K_TO_BB` (`K/BB (Pit)`), `K_PCT_PLUS` (`K%+ (Pit)`), `BB_PCT_PLUS` (`BB%+ (Pit)`), `QERA` (Nate Silver's Quick ERA), `DIPS_BOP_PCT` (Voros McCracken's Balls Kept Out of Play %), `XERA` (`xERA` on the ERA scale).
   - **Plate Discipline**: `BIP_PCT` (`BIP%`), `PUTAWAY_PCT` (`PutAway%`), `TWO_STRIKE_CHASE_PCT` (`2K Chase%`), `MEATBALL_SWING_PCT` (`Meatball Swing%`).
   - **Pitch Kinematics & Arsenal**: `BAUER_UNITS` (`Bauer Units`), `HAA` (`HAA`, Horizontal Approach Angle), `RV_PER_100` (`RV/100`), `WHIFF_PER_100` (`Whiffs/100`).
   - **Baserunning & Fielding**: `ERR_PCT` (`Err%`), `XBT_PCT` (`XBT%`), `WGDP` (`wGDP`), `BSR` (`BsR`).
   - **Expectancy Aggregates**: `PLI` (`pLI`), `WPA_LI` (`WPA/LI`), `CLUTCH` (`Clutch`), `REW` (`REW`).
2. **Modeled & Empirical Estimator Classes (`scikit-learn` interface + `statsmodels`-style frozen `.results` + `@profiled` + `@register_benchmark`)**:
   - **`EmpiricalBayesShrinker`** (`EmpiricalBayesResults`): Beta-Binomial Empirical Bayes shrinkage estimator for stabilizing noisy rate metrics (`AVG`, `OBP`, `K%`, `BB%`, `HR%`, `BABIP`) with learned prior $\alpha_0, \beta_0$, stabilization constant $M = \alpha_0 + \beta_0$, posterior means, posterior SDs, and 95% credible intervals.
   - **`ExpectedOutcomeModel`** (`ExpectedOutcomeResults`): Open Statcast contact-quality model fitted on `(launch_speed, launch_angle, sprint_speed)` to predict batted-ball `xba_est`, `xslg_est`, and `xwoba_est` with Brier score and $R^2$ diagnostics.
   - **`PitchQualityModel`** (`PitchQualityResults`): Open `Stuff+`, `Location+`, and `Pitching+` estimator (scaled to mean $100$, SD $10$, higher is better) with `statsmodels` OLS / `scikit-learn` diagnostics ($R^2$, F-statistic, p-values, feature weights).
   - **`CatcherFramingModel`** (`CatcherFramingResults`): Shadow-zone called-strike probability model producing per-pitch `cs_prob`, `strikes_above_avg`, and catcher leaderboard `framing_runs`.
   - **`OutsAboveAverageModel`** (`OutsAboveAverageResults`): Opportunity-based fielding catch-probability model producing `catch_prob`, `oaa` ($\text{Out} - \hat{P}(\text{Out})$), and `fielding_runs` (`frv`).
   - **`WARFramework.calculate_position_player_df()`**: Vectorized position-player WAR over any Polars, DuckDB, PyArrow, or pandas DataFrame.

## Impact
- Additive expansion of `Metric`, `Stat`, `REGISTRY`, `sabermetricspy.models`, and `sabermetricspy.value`.
- Every new function and estimator method is decorated with `@profiled` and registered with `@register_benchmark`.
