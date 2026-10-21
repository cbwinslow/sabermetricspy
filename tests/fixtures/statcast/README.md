# Statcast pitch-level sample

`skubal_2024_pitches.csv` holds every regular-season pitch thrown by Tarik Skubal (MLBAM id 669373) in 2024:
2,868 rows, 54 of the 119 columns Baseball Savant returns (the columns the library's `statcast` preset and the
plate-discipline and pitch-physics audits read).

- **Source:** the public Baseball Savant Statcast Search CSV export,
  `https://baseballsavant.mlb.com/statcast_search/csv` with `hfSea=2024|`, `hfGT=R|`,
  `player_type=pitcher`, `pitchers_lookup[]=669373`, `type=details`. An ordinary unauthenticated request
  returned it; no bot protection was bypassed.
- **Retrieved:** 2026-10-18. The row count (2,868), strikes (1,985) and balls (883) equal the FanGraphs
  pitcher leaderboard for the same player and season, which is how the sample was gated.
- **Use:** unit-test input for `tests/test_golden_plate_discipline.py` (and later the pitch-physics audit).
  Statcast data belongs to MLB Advanced Media; this small sample is kept only as a verification fixture and is
  not redistributed as a data product. Re-download it with the URL above if it is ever refreshed.

## Added 2026-10-20 (ADR-0050)

Both files come from the same public Baseball Savant Statcast Search CSV export and are verification fixtures only.

- `cabrera_2024_pitches.csv`: every regular-season pitch thrown by Edward Cabrera (MLBAM id 665795) in 2024, 1,734 rows,
  columns `player_name`, `pitcher`, `game_year`, `game_type`, `description`, `zone`, `type`. Second pin for Meatball%
  and Meatball Swing% (`tests/test_golden_strike_breakdown.py`).
- `four_seamers_2023_haa.csv`: the four-seamers (`pitch_type == FF`) of five 2023 pitchers (Cole, Gausman, Javier, Cease,
  Morton), columns `vx0`, `vy0`, `ax`, `ay` and identifiers. Reproduces the HAA table in Chamberlain's FanGraphs primer.

## Added 2026-10-21

- `cole_2023_zone.csv`: every regular-season pitch thrown by Gerrit Cole (MLBAM id 543037) in 2023, 3,286 rows, columns
  `player_name`, `pitcher`, `game_year`, `game_type`, `description`, `zone`, `type`, `balls`, `strikes`, `plate_x`,
  `plate_z`, `sz_top`, `sz_bot`. Same Baseball Savant Statcast Search CSV export (`hfSea=2023|`, `pitchers_lookup[]=543037`),
  retrieved 2026-10-21 with an ordinary request. Second sample (different pitcher, season) for the geometric strike zone
  (`tests/test_golden_strike_zone_second_sample.py`, ADR-0062). Verification fixture only.
