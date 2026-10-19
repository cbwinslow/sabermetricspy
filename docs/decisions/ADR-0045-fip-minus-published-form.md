# ADR-0045: FIP- and xFIP- Use the Published Form

Status: Accepted

## Context
The FanGraphs Library page (https://library.fangraphs.com/pitching/era-fip-xfip/, read 2026-10-19) prints
`ERA- = 100 * (ERA + (ERA - ERA * PF/100)) / (AL or NL ERA)` and says "The calculations are identical for FIP and xFIP."
The library still computed `100 * FIP / (lgFIP * PF)` with the MLB-wide FIP. An independent review reported the mismatch.

## Decision
`fip_minus` is `100 * FIP * (2 - PF/100) / lgFIP` with the pitcher's own league FIP. The AL and NL league FIPs
(`lg_fip_al`, `lg_fip_nl`) are bundled for 1990 to 2025, computed as `(13 HR + 3 (BB + HBP) - 2 SO) / IP + cFIP` from the
AL/NL totals in `pitcher_war.yaml`. As an outside check, their IP-weighted mean equals FanGraphs' published MLB league FIP in
all 36 seasons (`tests/test_fip_minus.py`). `xfip_minus` takes the same park term but keeps the MLB-wide xFIP, since AL
and NL xFIP need league fly-ball totals that are not bundled.

Measured on the 7 FanGraphs fixtures (published / old form / new form): Johnson 2001 47.27 / 46.31 / 46.37, Schilling 2001
69.48 / 67.64 / 67.72, Mussina 2001 66.21 / 67.40 / 67.16, Maddux 2001 71.44 / 72.02 / 72.19, Morris 2001 68.99 / 70.43 /
70.60, Pedro Martinez 2000 47.61 / 45.06 / 44.48, Skubal 2024 59.58 / 60.54 / 60.32. The published form is not closer, so the
remaining 0.2 to 3.1 point gap comes from an input FanGraphs does not publish (its FIP park factor), not the formula.

Alternatives considered: (a) keep the old form, not chosen now because it is not the printed method even though it fits
equally well; (b) reverse-engineer a park factor from the published values, not chosen now because it would fit the
fixtures without being a published method; revisit if FanGraphs publishes its FIP park factors for these seasons.

## Consequences
`fip_minus` stays `approximate` (golden evidence, residual recorded). `lg_fip_al` and `lg_fip_nl` are new optional constants;
without them the MLB-wide FIP is used.
