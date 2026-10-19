## Why

The project ships only methods that are publicly documented and reproduce outside reference values. An independent review plus checks on the recorded Skubal 2024 Statcast sample found five pieces with no public method behind them: `PitchQualityModel` (crashes on real Statcast data with null spin values), `ExpectedOutcomeModel` (scored on its own training data, reporting perfect fit), `CatcherFramingModel`, `OutsAboveAverageModel` and the `xera` metric (Savant publishes no xERA formula; it is 0.06 runs off).

## What Changes

- **BREAKING** Remove `PitchQualityModel`, `ExpectedOutcomeModel`, `CatcherFramingModel`, `OutsAboveAverageModel` and their result types.
- **BREAKING** Remove the `xera` metric (`Metric.XERA`).
- Remove their audit entries, benchmarks, tests and example sections; rename example 06.
- Drop `scikit-learn` and `statsmodels` from the core dependencies (nothing else imports them).
- Add ADR-0047.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `modeled-estimators-and-advanced-metrics`: the metric list loses `XERA`; the open-model requirement is removed.

## Impact

- `src/sabermetricspy/models/modeled.py` deleted; exports, telemetry benchmark, enums, pitching metrics, audit data and docs updated.
- Users who need these quantities should read Savant's published `estimated_*_using_speedangle` fields (already consumed by `xba`, `xslg`, `xwoba`), Savant's xERA, framing and OAA leaderboards.
- `WinProbabilityModel` and `CountExpectancyMatrix` are unchanged here; they are handled separately.
