# ADR-0035: ERA- Follows the FanGraphs Formula

- **Status**: Accepted
- **Date**: 2026-10-18

## Context
ADR-0027 left ERA- approximate: the library computed `100 x ERA / (lgERA x PF)` with the MLB-wide league ERA, while the
FanGraphs Library page (https://library.fangraphs.com/pitching/era-fip-xfip/) prints
`100 x (ERA + (ERA - ERA x PF/100)) / league ERA` with the pitcher's own league (AL or NL).

## Decision
`era_minus` uses `ERA x (2 - PF/100) / lgERA` with `lg_era_al` / `lg_era_nl` (27 x ER / outs of all AL / NL pitchers,
bundled for 1990 to 2025 from `tests/golden/league_war_totals_snapshot.yaml`), falling back to the MLB-wide ERA.

| Check | Published | Before | After |
|---|---|---|---|
| Johnson 2001 (ARI, PF 104) | 55.01 | 54.14 | 54.74 |
| Schilling 2001 (ARI, PF 104) | 65.91 | 64.88 | 65.59 |
| Mussina 2001 (NYY, PF 98) | 71.80 | 72.73 | 71.68 |
| NL 2014, ERA 3.00, PF 95 / 98 / 102 | 86 / 84 / 80 | | 86 / 84 / 80 |
| Kershaw 2014 (ERA 1.77, PF 96, NL 3.66) | 50 | | 50 |

All seven leaderboard fixtures are now within 0.33 points. `era_minus` is `matches` with golden evidence. `fip_minus`
stays approximate: the same change leaves a 1 to 2 point residual, and Guts! publishes a separate FIP park factor
column that is not bundled; `xfip_minus` keeps the old method and is unchecked.
