## Decisions

1. **Game Score is per game.** It carries a fixed base (50 or 40), so it is not additive across games; the metrics document that they are meant for one row per start. Sources: Game score (Wikipedia, describing James's original; the original text was not retrieved) and "Game Score Version 2.0" (https://blogs.fangraphs.com/instagraphs/game-score-v2-0).
   - v1 = 50 + outs + 2 * max(0, completed innings - 4) + SO - 2 H - 4 ER - 2 (R - ER) - BB.
   - v2 = 40 + 2 outs + SO - 2 BB - 2 H - 6 HR - 3 R (the home run is also a hit, so it costs 8). The article's yearly base shift (50 as league average, 38 for 2015) is not modeled; the base is 40.
2. **Off** per https://library.fangraphs.com/offense/off/: wRAA + (lgR/PA - PF * lgR/PA) * PA + (lgR/PA - league non-pitcher wRC/PA) * PA + BsR, using the AL/NL constant when the season has it, as wRC+ does. The page prints no player value, so the evidence tier is `primary`, and the test recomputes the formula from the library's own wRAA and BsR.
3. Naming follows the three-tier standard; all calculations are narwhals expressions decorated through the registry.
