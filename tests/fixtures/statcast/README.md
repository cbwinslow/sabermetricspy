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
