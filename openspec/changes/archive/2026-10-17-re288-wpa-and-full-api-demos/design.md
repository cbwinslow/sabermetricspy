# Design: Count Expectancy (RE288), Win Probability (WPA & LI), and End-to-End Demos

## 1. `CountExpectancyMatrix` (`RE288`)
- There are 12 legal pre-pitch ball-strike counts (`b in 0..3`, `s in 0..2`) and 24 base-out states (`outs in 0..2`, `bases in 8 states`), yielding 288 count-base-out states.
- `CountExpectancyMatrix.from_default()` initializes the 288-state table from the canonical MLB `RE24` baseline combined with Tom Tango / Jim Albert count run-value offsets relative to `0-0`:
  - `0-0`: `0.000`, `1-0`: `+0.038`, `2-0`: `+0.095`, `3-0`: `+0.205`
  - `0-1`: `-0.043`, `1-1`: `-0.015`, `2-1`: `+0.034`, `3-1`: `+0.135`
  - `0-2`: `-0.106`, `1-2`: `-0.082`, `2-2`: `-0.038`, `3-2`: `+0.052`
- `CountExpectancyMatrix.fit(df)` learns empirical 288-state expected runs from pitch-by-pitch data (`balls_before`, `strikes_before`, `outs_before`, `base_state_before`, `runs_rest_of_inning`) with optional Empirical Bayes shrinkage toward the 288-state prior.
- `CountExpectancyMatrix.transform(df)` computes `re288_before`, `re288_after`, `pitch_run_value`, and `count_leverage`.

## 2. `WinProbabilityModel` (`WPA` & `LI`)
- Models home/batting-team win probability as a function of `(inning, is_bottom, score_diff, outs, base_state)` using expected remaining runs (`RE24(outs, base_state) + expected_runs_per_inning * remaining_half_innings`) and a normal/logistic win-probability model calibrated to MLB home-field advantage (`+0.035` in tied states) and walk-off rules.
- Supports `.fit(df)` to learn empirical state win probabilities or run environment parameters, and `.transform(df)` to compute:
  - `wp_before`: Win probability before the play (from the batting team's perspective)
  - `wp_after`: Win probability after the play (from the batting team's perspective)
  - `wpa`: `wp_after - wp_before`
  - `li`: Leverage Index (ratio of expected win-probability swing in the state to the league-average swing `~0.035`)
  - `wpa_li`: Context-neutral `wpa / li`
