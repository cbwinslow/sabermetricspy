# modeled-estimators-and-advanced-metrics Specification

## Purpose
TBD - created by archiving change 2026-10-17-advanced-metrics-and-modeled-estimators. Update Purpose after archive.

## Requirements

### Requirement: Expanded 100+ Metric Registry
The `MetricRegistry` SHALL include at least 100 canonical sabermetric metrics across all 13 categories, adding `GPA`, `TA`, `RC27`, `BAT_K_PCT_PLUS`, `BAT_BB_PCT_PLUS`, `BF_PER_IP`, `PIT_BB_TO_K`, `PIT_K_TO_BB`, `K_PCT_PLUS`, `BB_PCT_PLUS`, `QERA`, `DIPS_BOP_PCT`, `I_TO_STR`, `F_TO_STR`, `PUTAWAY_PCT`, `TWO_STRIKE_CHASE_PCT`, `MEATBALL_SWING_PCT`, `BAUER_UNITS`, `HAA`, `RV_PER_100`, `WHIFF_PER_100`, `ERR_PCT`, `XBT_PCT`, `WGDP`, `BSR`, `PLI`, `WPA_LI`, `CLUTCH`, and `REW`.

#### Scenario: Calculating newly registered metrics across backends
- **WHEN** `sb.calculate(df, [Metric.GPA, Metric.QERA, Metric.BAUER_UNITS, Metric.CLUTCH])` is invoked on a DataFrame containing the required canonical columns
- **THEN** all metrics SHALL evaluate via vectorized Narwhals expressions and preserve the native DataFrame type.

### Requirement: Empirical Bayes Shrinkage Estimator
`EmpiricalBayesShrinker` SHALL fit a Beta-Binomial Empirical Bayes prior $(\hat{\alpha}_0, \hat{\beta}_0)$ on observed successes and exposure trials and transform player rows with shrunk posterior rates, shrinkage weights, and 95% credible intervals.

#### Scenario: Shrinking small-sample batting averages toward the population mean
- **WHEN** `EmpiricalBayesShrinker(success_col="h", trials_col="ab").fit(df).transform(df)` is executed
- **THEN** a player with `4` hits in `10` AB (`.400` raw) SHALL be shrunk closer to the population mean than a player with `200` hits in `500` AB (`.400` raw), and `.results` SHALL report `alpha_0`, `beta_0`, `prior_mean`, and `stabilization_trials`.

### Requirement: Vectorized Position-Player WAR DataFrame Calculation
`WARFramework.calculate_position_player_df(df)` SHALL compute `positional_runs`, `replacement_runs`, `runs_above_replacement`, and `war` across any Polars, DuckDB, PyArrow, or pandas DataFrame and be decorated with `@profiled(category="valuation")`.

#### Scenario: Vectorized position-player WAR matches scalar WAR
- **WHEN** `WARFramework(season=2024).calculate_position_player_df(df)` is called on a player table
- **THEN** each row's `war` and `runs_above_replacement` SHALL match `calculate_position_player_scalar` to within `1e-9`.
