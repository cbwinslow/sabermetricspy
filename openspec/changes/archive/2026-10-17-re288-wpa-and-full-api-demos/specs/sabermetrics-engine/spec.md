# Delta Specification: Count Expectancy (RE288), Win Probability (WPA & LI), and Full API Audit

## ADDED Requirements

### Requirement: 288-State Count Expectancy Matrix (RE288)
The library SHALL provide `CountExpectancyMatrix` supporting `.from_default()`, `.fit(df)`, `.transform(df)`, and frozen `.results` (`RE288Results`) across all 288 `(balls, strikes, outs, base_state)` states, computing `re288_before`, `re288_after`, `pitch_run_value`, and `count_leverage`.

#### Scenario: Valuing non-terminal and terminal pitches with RE288
- **WHEN** `CountExpectancyMatrix.from_default().transform(pitches_df)` is called on pitch records
- **THEN** a ball moving the count from `0-0` to `1-0` has a positive offensive `pitch_run_value`, a strike moving `0-0` to `0-1` has a negative offensive `pitch_run_value`, and `count_leverage` is positive for all legal counts

### Requirement: Win Probability Added (WPA) and Leverage Index (LI) Model
The library SHALL provide `WinProbabilityModel` supporting `.from_default()`, `.fit(df)`, `.transform(df)`, and frozen `.results` (`WinProbabilityResults`) that annotates play-by-play records with `wp_before`, `wp_after`, `wpa`, `li` (Leverage Index), and `wpa_li`.

#### Scenario: High-leverage late-game home run vs low-leverage blowout play
- **WHEN** `WinProbabilityModel.from_default().transform(plays_df)` evaluates a 9th-inning tie-breaking home run versus a 9th-inning single in a 10-run blowout
- **THEN** the 9th-inning tie-breaking home run has `li > 1.5` and `wpa > 0.30`, whereas the blowout play has `li < 0.2` and `|wpa| < 0.02`
