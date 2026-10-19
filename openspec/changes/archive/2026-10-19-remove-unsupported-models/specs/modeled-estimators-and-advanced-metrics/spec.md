## MODIFIED Requirements

### Requirement: Expanded 100+ Metric Registry
The `MetricRegistry` SHALL include at least 100 canonical sabermetric metrics across all 13 categories, adding `GPA`, `TA`, `RC27`, `BAT_K_PCT_PLUS`, `BAT_BB_PCT_PLUS`, `BF_PER_IP`, `PIT_BB_TO_K`, `PIT_K_TO_BB`, `K_PCT_PLUS`, `BB_PCT_PLUS`, `QERA`, `DIPS_BOP_PCT`, `BIP_PCT`, `PUTAWAY_PCT`, `TWO_STRIKE_CHASE_PCT`, `MEATBALL_SWING_PCT`, `BAUER_UNITS`, `HAA`, `RV_PER_100`, `WHIFF_PER_100`, `ERR_PCT`, `XBT_PCT`, `WGDP`, `BSR`, `PLI`, `WPA_LI`, `CLUTCH`, and `REW`.

#### Scenario: Calculating newly registered metrics across backends
- **WHEN** `sb.calculate(df, [Metric.GPA, Metric.QERA, Metric.BAUER_UNITS, Metric.CLUTCH])` is invoked on a DataFrame containing the required canonical columns
- **THEN** all metrics SHALL evaluate via vectorized Narwhals expressions and preserve the native DataFrame type.

## REMOVED Requirements

### Requirement: Open Contact Quality, Pitch Quality, and Defensive Opportunity Models
**Reason**: `ExpectedOutcomeModel`, `PitchQualityModel`, `CatcherFramingModel` and `OutsAboveAverageModel` have no publicly documented method to reproduce, and two failed on checks against real Statcast data (ADR-0047).
**Migration**: Use the metrics that sum Savant's published `estimated_*_using_speedangle` fields (`xba`, `xslg`, `xwoba`), or Savant's own framing and OAA leaderboards.
