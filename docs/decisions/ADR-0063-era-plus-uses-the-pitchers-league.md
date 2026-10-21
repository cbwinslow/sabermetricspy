# ADR-0063: ERA+ Uses the Pitcher's Own League ERA

Status: Accepted

## Context
ERA+ ran 1-5% below Baseball-Reference. The audit suspected the park factor; reading Baseball-Reference's team pages (2026-10-21) gave pitching park factors of 103 (Boston 2000), 107 (Arizona 2001) and 103 (Detroit 2024). With those and the pitcher's own league ERA the formula 100 x lgERA x PF / ERA gives 291.0, 187.7 and 173.2 against the published 291, 188 and 174.

## Decision
`era_plus` takes the AL or NL league ERA from `SeasonContext.league` (as `era_minus` already does) and the MLB-wide ERA when the league is MLB. Callers pass Baseball-Reference's pitching park factor; the default of 100 means no park adjustment. Status is now `matches`.

## Alternatives
- Keep the MLB-wide ERA, not chosen now because it is the cause of the remaining gap and ERA- already uses the league; revisit if a source defines ERA+ against the whole major leagues.
- Bundle Baseball-Reference's park factors, not chosen now because they are a per-team, per-season table that the site changes and that this package does not otherwise carry; revisit if a stable published table is licensed for redistribution.

## Consequences
Callers who set `league` to AL or NL get slightly different ERA+ values than in 1.0.1 (closer to Baseball-Reference). MLB-wide callers are unchanged.
