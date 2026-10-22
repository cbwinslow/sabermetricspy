# ADR-0070: Power-Speed Number

Status: Accepted (adopted by default from the research specs; owner to confirm the defaults listed below)

## Context
`docs/LITERATURE.md` has no Power-Speed Number entry. The metric is published on Baseball-Reference's career and progressive Power-Speed # leaderboards and in SABR's Baseball Research Journal (Sciarretta 1983). ADR-0065 removed `speed_score` because neither published form reproduced FanGraphs Spd; PSN is a different one-line metric whose printed values reproduce from Lahman totals.

## Decision
Add `Metric.POWER_SPEED_NUMBER` (`"power_speed_number"`, display name "PSN"), the harmonic mean `2 * HR * SB / (HR + SB)`, category batting, deterministic, requiring `hr` and `sb`. It is null when `HR + SB` is 0 (the library's zero-denominator rule, ADR-0008 and ADR-0046). It is computed from summed counts, so a career value uses career totals. Status `matches`, evidence `golden`: `tests/golden/power_speed_number.yaml` reproduces Baseball-Reference's career values for Bonds (613.90), Henderson (490.41) and Mays (447.93) and five season values printed by SABR and Wikipedia from Lahman 2025 home run and stolen base totals. Wikipedia's Mays 447.1 is stale (338 SB) and is not tested.

Defaults adopted without an owner answer (research spec `power_speed_number`, decisions O-PSN-1 to O-PSN-3): null rather than 0 for HR + SB = 0; both years cited (1980 per Lederer 2004, 1983 per Sciarretta 1983) because the retrieved texts disagree; category batting.

## Alternatives
- Return 0 when HR + SB is 0, not chosen now because the library returns null for every zero denominator and 0 would rank a player with no data as a poor power-speed player; revisit if Baseball-Reference is found to print 0 for such players.
- Use `scipy.stats.hmean`, not chosen now because it reduces a vector rather than building a column expression and has no null handling; revisit if a vector API is added.
- Name the member `PSN`, not chosen now because `NAMING_CONVENTIONS.md` has no tier-1 rule for an abbreviation that SABR and Baseball-Reference do not both use; revisit if the owner prefers abbreviations.
- Also ship geometric-mean or speed-score variants, not chosen now because no retrieved source prints values for them; revisit if one is found.

## Consequences
One new `Metric` member and methodology entry; `docs/METHODOLOGY.md` regenerated; the value-assertion guard in `tests/test_metric_values.py` lists the metric as covered by its own golden test.
