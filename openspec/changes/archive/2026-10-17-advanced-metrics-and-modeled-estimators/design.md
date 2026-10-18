# Design: Advanced Metrics Expansion & Modeled Sabermetric Estimators

## 1. Pure Vectorized Narwhals Expressions for the 24 New Registry Metrics
All 24 new metrics registered in `src/sabermetricspy/metrics/` follow the exact same architectural invariants as the initial 81 metrics:
- **Additive Counts First, Ratios Second**: Every new metric declares its required `Stat` columns (`two_strike_so`, `two_strike_pitches`, `haa_sum`, `haa_count`, `pitch_rv_sum`, `xbt`, `xbt_opp`, `li_sum`, `wpa`, `re24`, etc.) so `sb.calculate(..., by=...)` and `sb.calculate_rolling(...)` sum the additive numerators and denominators before evaluating ratios.
- **3-Tier Naming**: Every metric is added to `Metric(StrEnum)` (`UPPER_SNAKE_CASE` -> `lower_snake_case`) and registered with a complete `MetricSpec` (`display_name`, `formula_latex`, `citation`, `caveats`).

## 2. Modeled & Empirical Estimators (`scikit-learn` + `statsmodels` Hybrid)
Per ADR-0005 and the research blueprint:
- Every estimator class implements `.fit(df)` and `.transform(df)` / `.predict(df)`, returning `Self` from `.fit(df)` and attaching an immutable Pydantic `.results` object containing statistical diagnostics ($R^2$, F-statistic, p-values, Brier score, learned prior parameters, etc.).
- Every public `.fit()`, `.transform()`, and `.predict()` method is decorated with `@profiled(category=...)`, and subsystem benchmark workloads are registered via `@register_benchmark(...)`.

### 2.1 `EmpiricalBayesShrinker` (`category="uncertainty"`)
- Estimates Beta prior parameters $(\hat{\alpha}_0, \hat{\beta}_0)$ from observed player successes $k_i$ and trials $n_i$ via empirical method-of-moments (with fallback minimum stabilization $M = \alpha_0 + \beta_0$).
- Computes posterior parameters $\alpha_i^* = \hat{\alpha}_0 + k_i$ and $\beta_i^* = \hat{\beta}_0 + (n_i - k_i)$, yielding:
  $$\hat{p}_i^{EB} = \frac{\hat{\alpha}_0 + k_i}{\hat{\alpha}_0 + \hat{\beta}_0 + n_i} = (1 - B_i)\frac{k_i}{n_i} + B_i \mu_0$$
  where $B_i = \frac{M}{n_i + M}$ is the shrinkage factor, along with exact Beta posterior standard deviation and 95% credible intervals (`ci_lower`, `ci_upper`).

### 2.2 `ExpectedOutcomeModel` (`category="modeling"`)
- Fits a non-parametric / k-NN contact-quality estimator (`sklearn.neighbors.KNeighborsRegressor` or multi-output probability estimator over standardized `(launch_speed, launch_angle, sprint_speed)`) to estimate expected batting average (`xba_est`), expected slugging (`xslg_est`), and expected wOBA (`xwoba_est`) on batted balls, while blending actual strikeout (`0`), walk (`w_bb`), and HBP (`w_hbp`) values for plate appearances.

### 2.3 `PitchQualityModel` (`category="modeling"`)
- Fits an OLS (`statsmodels.api.OLS`) or Gradient Boosting model predicting pitch run value (`pitch_rv`) from:
  - **Stuff features**: `release_speed`, `ivb`, `hb`, `release_extension`, `spin_rate`, `vaa`, `haa`.
  - **Location features**: `plate_x`, `plate_z`, distance from strike-zone edge, and count leverage.
- Converts predicted run value $\hat{y}_i$ into the plus scale where $100$ is league average and $10$ is one standard deviation, inverted so lower run value allowed = higher `Stuff+` / `Location+` / `Pitching+`:
  $$\text{PitchQuality}^+ = 100 - 10 \times \frac{\hat{y}_i - \mu_{\hat{y}}}{\sigma_{\hat{y}}}$$
- Attaches `PitchQualityResults` containing `r_squared`, `f_statistic`, `f_pvalue`, `feature_coefficients`, `feature_pvalues`, `mean_rv`, and `std_rv`.

### 2.4 `CatcherFramingModel` & `OutsAboveAverageModel` (`category="modeling"`)
- **`CatcherFramingModel`**: Fits a regularized logistic regression / polynomial surface over shadow-zone `plate_x`, `plate_z`, `balls`, and `strikes` to estimate $\hat{P}(\text{Called Strike})$, computes `strikes_above_avg = is_called_strike - cs_prob`, and summarizes catcher `framing_runs = strikes_above_avg * run_value_per_called_strike` (default `0.125` runs).
- **`OutsAboveAverageModel`**: Fits a logistic catch-probability model over `(opportunity_distance, hang_time, sprint_speed)` to estimate $\hat{P}(\text{Out})$, computes `oaa = is_out - catch_prob`, and summarizes `fielding_runs = oaa * run_value_per_out`.

### 2.5 `WARFramework.calculate_position_player_df()` (`category="valuation"`)
- Vectorized Narwhals implementation of position-player WAR over any DataFrame containing `pa` and `batting_runs` (or `wraa`), plus optional `baserunning_runs` (`bsr` / `wsb`), `fielding_runs` (`frv`), `position`, and `league_runs`.
