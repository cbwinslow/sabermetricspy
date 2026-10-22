# pitcher-war Specification

## Purpose
Defines pitcher WAR as the documented FanGraphs method, so results can be traced to a published algorithm and its run-environment inputs rather than to ad-hoc constants.

## Requirements

### Requirement: Pitcher WAR follows the documented FanGraphs method
Pitcher WAR SHALL be computed from ifFIP (infield flies counted as strikeouts, using the MLB ifFIP constant), converted to the run-average scale by adding the MLB difference between league RA9 and league ERA, divided by the FIP park factor, compared with the pitcher's league (AL or NL) FIP on the same scale, converted to wins with the dynamic runs-per-win formula, and combined with replacement wins of 0.03 per game for relievers and 0.12 per game for starters.

#### Scenario: Published worked example
- **WHEN** WAR is calculated for Marcus Stroman 2016 (IP 204, G 32, GS 32, HR 21, BB 54, HBP 4, K 166, IFFB 7, AL, FIP park factor 101)
- **THEN** the ifFIP constant is 3.34, ifFIP 3.84, FIPR9 4.17, pFIPR9 4.12, AL FIPR9 4.56, dRPW 9.61, WAR before correction 3.76 (within rounding of the page), and WAR after the 2016 correction is within 0.03 of the page's unrounded 3.62

#### Scenario: Relievers
- **WHEN** a pitcher has no starts
- **THEN** replacement is 0.03 wins per game and WAR before correction is multiplied by (1 + gmLI) / 2

### Requirement: Run-environment constants are sourced per league and season
The library SHALL bundle, for every season 1990-2025, the AL and NL pitching totals (innings, runs, earned runs, home runs, walks, hit batters, strikeouts, infield flies) needed to derive the MLB ifFIP constant, league RA9 and ERA, and AL/NL league FIP, with source and retrieval date, and infield flies SHALL be treated as zero for seasons without published values.

#### Scenario: Totals are consistent
- **WHEN** the AL and NL totals for a season are added
- **THEN** they equal the MLB totals used for league ERA, FIP and cFIP in the same season

#### Scenario: Infield flies unavailable
- **WHEN** a season has no published infield-fly totals
- **THEN** the ifFIP constant and each pitcher's ifFIP are computed with infield flies equal to zero

### Requirement: League correction is explicit
The league correction (a per-inning amount) SHALL be applied only when a sourced value is available or the caller supplies one, and results without a correction SHALL be documented as uncorrected.

#### Scenario: Season with a published correction
- **WHEN** WAR is calculated for 2016 with no override
- **THEN** the published correction of -0.000682902 wins per inning is applied

#### Scenario: Season without a published correction
- **WHEN** WAR is calculated for a season with no supplied correction and no override
- **THEN** no correction is applied and the metric's caveats state that results are uncorrected

### Requirement: Mixed starter and reliever lines are handled as published
Rows with both starts and relief appearances SHALL use the blended replacement level 0.03*(1-GS/G)+0.12*GS/G, and the documentation SHALL state that FanGraphs computes starter and reliever WAR separately and that separate role rows give the published result.

#### Scenario: Separate role rows
- **WHEN** a pitcher's starting and relief lines are supplied as separate rows
- **THEN** each row is valued by its own role and the caller can sum them

### Requirement: Agreement with live leaderboard values is reported
The repository SHALL compare calculated WAR with FanGraphs leaderboard WAR for a recorded set of 2016 pitchers, and SHALL state the observed difference and the tolerance used.

#### Scenario: Leaderboard comparison
- **WHEN** WAR is calculated for the recorded 2016 starters and relievers using the published 2016 correction
- **THEN** each result is within the documented tolerance of the leaderboard value, and mixed-role lines are listed as documented divergences
