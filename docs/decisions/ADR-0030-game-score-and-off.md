# ADR-0030: Game Score, Game Score 2.0 and Off

- **Status**: Accepted
- **Date**: 2026-10-18
- **OpenSpec change**: `game-score-and-off-metrics`

## Context
Entries 1, 3 and 4 of `docs/LITERATURE.md` were fully specified in sources read during the literature sweep and need only
columns already in the canonical schema.

## Decision
- `game_score` (James): 50 + outs + 2 per completed inning after the fourth + SO - 2 H - 4 ER - 2 unearned runs - BB.
  Reproduces the published games on the Wikipedia page (Kerry Wood 1998 = 105, Scherzer 2015 = 104); the formula is
  read from that secondary page.
- `game_score_v2` (Tango, FanGraphs): 40 + 2 outs + SO - 2 BB - 2 H - 6 HR - 3 R. The formula is verified against the article;
  the article prints no player value, so the 7 IP / 64 line in the tests is a hand-computed check, not a published
  example (corrected in the 2026-10-19 ADR audit). The yearly base shift is not modeled.
- `off` (FanGraphs Library): wRAA + (lgR/PA - PF*lgR/PA)*PA + (lgR/PA - lgwRC/PA non-pitchers)*PA + BsR, with the AL/NL
  constant when the season has it. The page prints no player value, so it is tiered `primary` and recomputed from the
  formula.

## Consequences
Game Score is per game and not additive; the metric caveats say so. Off inherits wRAA and BsR (BsR's UBR and wGDP
inputs are caller supplied).
