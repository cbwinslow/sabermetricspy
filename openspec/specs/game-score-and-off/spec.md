# game-score-and-off Specification

## Purpose
Define the per-game pitching metrics Game Score (Bill James) and Game Score 2.0 (Tom Tango), and Off, the FanGraphs sum of batting runs above average and baserunning runs.

## Requirements

### Requirement: Game Score
The library SHALL provide `game_score` (Bill James) and `game_score_v2` (Tom Tango) as per-game pitching metrics.

#### Scenario: Published games
- **WHEN** a start of 27 outs, 20 strikeouts, 1 hit and no walks or runs is evaluated
- **THEN** `game_score` is 105, and a start of 27 outs, 17 strikeouts and no hits, walks or runs gives 104

#### Scenario: Game Score 2.0 hand-computed example
- **WHEN** a start of 21 outs, 8 strikeouts, 2 walks, 5 hits including 1 home run and 2 runs is evaluated
- **THEN** `game_score_v2` is 64

### Requirement: Off
The library SHALL provide `off`, the FanGraphs sum of batting runs above average (with park and league adjustment) and base running runs.

#### Scenario: Composition
- **WHEN** `off` is calculated for a batter
- **THEN** it equals wRAA plus the park term plus the league term plus BsR from the FanGraphs formula
