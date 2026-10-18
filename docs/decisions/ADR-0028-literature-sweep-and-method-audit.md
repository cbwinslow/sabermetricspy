# ADR-0028: Method Audit of Every Metric and Model, Evidence Tiers, and the Defects It Found

- **Status**: Accepted
- **Date**: 2026-10-18
- **OpenSpec change**: `literature-sweep-and-method-audit`

## Context
After ADR-0027, 97 metrics and 16 models were still marked `unverified`. Each was compared with a primary source
(FanGraphs Library and leaderboards, Baseball-Reference, Baseball Savant, Tango, Wikipedia for textbook formulas).
Fetched figures were recomputed from their raw counts before being trusted (the recomputation gate), then encoded
as fixtures under `tests/golden/`. Pitch-level checks use a recorded public Baseball Savant export
(`tests/fixtures/statcast/skubal_2024_pitches.csv`, 2,868 pitches whose counts equal FanGraphs').

## Decision
1. **Every entry carries an evidence tier** (`EvidenceTier`): `golden` (reproduces a published value in a test),
   `primary` (the method matches a primary definition; no published value was compared), or `secondary` (relies on
   a secondary description). The consistency test requires a tier on every audited entry, and a note naming
   "secondary" for any `matches` entry resting on secondary evidence.
2. **Defects were fixed where the published value was reproducible**, each with a failing test first:

| Defect | Before | After | Published |
|---|---|---|---|
| Pull% / Cent% / Oppo% divided by balls in play (Skubal 2024) | 38.99 / 36.06 / 25.79 | 38.67 / 35.76 / 25.57 | 38.67 / 35.76 / 25.57 (FanGraphs; denominator is Pull+Cent+Oppo) |
| Batter BB%+ divided by the MLB rate (Judge 2024) | 230.9 | 232.5 | 232.5 (own-league, non-pitcher rate) |
| Batter BB%+ (Witt 2024 / Ohtani 2024) | 98.3 / 135.4 | 99.0 / 134.5 | 98.95 / 134.47 |
| Pitcher K%+ (Fernandez 2016 / Scherzer 2016) | 162.5 / 149.1 | 161.1 / 147.7 | 161.09 / 147.75 (own league, all-pitcher SO/TBF) |
| Pitcher BB%+ (Fernandez 2016 / Scherzer 2016) | 91.3 / 75.9 | 88.5 / 73.6 | 88.52 / 73.65 |
| Total Average subtracted CS in the numerator (sample line 0.8529) | 0.8529 | 0.8725 | Tango wiki and Wikipedia: (TB + BB + HBP + SB) / (AB - H + CS + GIDP) |
| Zone% divided by all pitches, including untracked ones (Skubal 2024) | 54.67 | 55.25 | 55.38 (within the 0.2-point tolerance) |
| Bunt attempts counted as swings (O-Swing% / Swing%) | 31.69 / 51.74 | 30.94 / 51.57 | 30.88 / 51.52 |
| Foul balls counted as batted-ball events for contact quality: Hard-Hit% | 39.50 | 33.68 | 33.68 (162 of 481, FanGraphs) |
| Same defect, average exit velocity (mph) | 82.25 | 86.92 | 87.45 (FanGraphs; still approximate, see below) |
| Default RE24 table was an unsourced "2024 canonical" table, up to 0.086 runs from any published matrix | e.g. runner on third, 0 out: 1.350 | 1.426 | FanGraphs RE24 matrix (roughly neutral for 2014): all 24 cells now equal it |

   Each fix is guarded by a golden test: `test_golden_batted_ball.py`, `test_golden_indices.py`,
   `test_golden_pitching_indices.py`, `test_golden_plate_discipline.py`, `test_golden_pitch_physics.py`,
   `test_golden_run_expectancy.py`, plus `test_metric_values.py` for Total Average.
3. **Out-of-zone metrics use located pitches** (Savant zone 1 to 14) and the Statcast preset no longer treats
   bunt attempts as swings, whiffs or fouls; `ev_sum`, `ev_count`, `hard_hit_bbe` and `sweet_spot_bbe` count balls in
   play only. New optional `WOBAWeights` fields hold the AL/NL league BB% and K% for batters and pitchers
   (`lg_bb_pct_*`, `lg_k_pct_*`, `lg_pit_bb_pct_*`, `lg_pit_k_pct_*`, 1990 to 2025, sourced from FanGraphs league
   leaderboards, with the MLB-wide value as fallback).
4. **Labels instead of fixes where the source defines the method opaquely or needs data we cannot bundle.** Each
   keeps `approximate` with the reason and the measured gap in `methodology.yaml`:
   - ERA+ runs 2 to 6% under Baseball-Reference (park handling differs; the page returns 403).
   - xERA 2.62 against Savant's 2.68 for Skubal 2024 (Savant publishes no formula).
   - xBA / xSLG omit sprint speed at the pitch level: 0.2036 against 0.205 and 0.3296 against 0.332.
   - Barrels: 28 against 32 for the recorded sample (the barrel zone is approximated from the glossary anchor).
   - Average exit velocity: 86.92 against 87.45 (FanGraphs appears to drop the slowest rollers; no rule published).
   - Whiff%: FanGraphs counts foul tips as contact, Savant as misses (23.3 against 27.7); the library follows FanGraphs.
   - F-Strike%: FanGraphs divides by 753 batters faced, Savant shows 754 first pitches; tests use 753.
   - Marcel pitchers (`divergent`): 5/4/3 weights and 134 IP regression versus Tango's 3/2/1 and 25 or 60 IP.
5. **Models.** Six open reimplementations (`ExpectedOutcomeModel`, `PitchQualityModel`, `CatcherFramingModel`,
   `OutsAboveAverageModel`, `CountExpectancyMatrix`, `WinProbabilityModel`) stay `unverified` with a written reason
   each: there is no published model or table to reproduce, or none could be retrieved. Their default constants
   (count offsets, 0.125 runs per called strike, 0.75 runs per out) are caller-overridable and unsourced; follow-up
   changes should source them before they are relied on.

## Outcome
Metrics: 136 audited (`matches` 90, `approximate` 46, none `unverified`); by tier, `golden` 84, `primary` 27,
`secondary` 25. Models: 16 entries (9 `matches` or `approximate`, 1 `divergent`, 6 `unverified` each with a written reason).

## Consequences
- Several published-method metrics now change value for existing callers (listed in the table above); the changes
  move results toward the published value in every case.
- The default RE24 table is a 2014 matrix, not a current season: `WinProbabilityModel`, `RunExpectancyMatrix.from_default`
  and the RE288 default all inherit it; callers needing a season should fit `RunExpectancyMatrix` to play-by-play.
- Position-player WAR replacement, pitcher-WAR residuals and the unsourced `lg_wsb`/`lg_gidp_rate` remain out of scope.
- Literature catalogue and sweep tooling are delivered under the same change (`docs/LITERATURE.md`,
  `docs/LITERATURE_SWEEP.md`); each catalogued method becomes its own later change.
