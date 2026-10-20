# ADR-0050: Plate-Discipline Rates Follow Their Published Definitions

Status: Accepted

## Context
Five rates were library inventions with no source: `bip_pct` (balls in play over swings), `foul_pct` (fouls over swings),
`fp_swing_pct` (no published label), `meatball_swing_pct` (its heart-zone boundary was never found) and `haa` (never derived
by the preset). Research against Baseball-Reference, Baseball Savant and FanGraphs found an outside value for each one.

## Decision
- `bip_pct` becomes `i_to_str` (display I/Str): balls in play over total strikes, Baseball-Reference's definition, with strikes
  counted from Statcast pitch type S or X (new `strike_pitches` column). Tarik Skubal 2024: 481 of 1,985 prints 24.2 percent.
- `foul_pct` becomes `f_to_str` (F/Str): fouls over total strikes. Foul bunts count as fouls (the `fouls` column now includes
  `foul_bunt`), so 529 of 1,985 prints the Baseball-Reference 26.6 percent; foul only would give 26.4.
- `fp_swing_pct` is kept. Baseball-Reference's first-pitch split prints Swung 277 and Took 476 for Skubal, and the preset now derives
  `first_pitch_swings` with bunt attempts counted as swings (277). The F-Swing% name remains the library's own, by analogy with F-Strike%.
- `meatball_swing_pct` is kept and redefined: meatball is Statcast `zone == 5`, not the heart attack zone. Savant's Meatball% and Meatball
  Swing% reproduce for Skubal (8.9, 79.8) and Edward Cabrera (6.3, 72.7). The preset derives `meatball_pitches` and `meatball_swings`
  (bunt attempts included, as Savant does). Savant publishes no definition, so the status is `approximate`.
- `haa` is kept; the preset now derives `haa_sum` and `haa_count` using Chamberlain's formula, the same flight time and arctan series as
  VAA. The citation moves from Nathan to Chamberlain (FanGraphs, 2023). His table's 1.3 degrees reproduces for five pitchers within 0.1.
- `hr_pct` and `r_per_pa` become `matches` (Baseball-Reference HR%; FanGraphs Guts! R/PA in all 36 seasons). `rbi_per_pa` stays a
  documented plain ratio.
- `NAMING_CONVENTIONS.md` gains the `_per_<denominator>` rule for per-opportunity rates (`r_per_pa`, `rbi_per_pa`, `bf_per_ip`), with
  `_to_` kept for count-to-count ratios (`i_to_str`, `f_to_str`).

## Alternatives
- Keep `bip_pct` and `foul_pct` as renamed per-swing ratios: not chosen now, because published forms with outside values exist;
  revisit if users need per-swing contact splits.
- Implement Savant's heart attack zone: not chosen now, because its boundaries were not retrievable (the MLB glossary returns HTTP 406);
  revisit if Savant publishes them.
- Compute zone 5 from `plate_x`, `plate_z`, `sz_top` and `sz_bot`: not chosen now, because the padding (about 1.41 to 1.45 inches) is not
  exactly known and the `zone` column is authoritative; revisit if a source without `zone` needs it.
- Drop `haa`: not chosen now, because the formula and a printed table exist; revisit if the table cannot be reproduced on new data.
- Rename `fp_swing_pct` to `fp_swing_per_pa`: not chosen now, because it parallels `fp_strike_pct`; revisit if a published label differs.

## Consequences
`Metric.BIP_PCT` and `Metric.FOUL_PCT` are gone (`bip_pct`, `foul_pct` columns no longer resolve); use `i_to_str` and `f_to_str`.
`fouls` now includes foul bunts. New fixtures: `tests/fixtures/statcast/cabrera_2024_pitches.csv` and `four_seamers_2023_haa.csv`.
Tests: `tests/test_golden_strike_breakdown.py`, `tests/golden/strike_breakdown_rates.yaml`.
