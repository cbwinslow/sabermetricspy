# Proposal: 1.0.2 Research Closeout

## Why
`docs/VERIFICATION.md` listed open research. Three items could be settled with real sources: whether the geometric strike zone holds on another pitcher, why ERA+ ran low, and how far `LinearWeightsEstimator` is from FanGraphs.

## What Changes
- ERA+ uses the pitcher's own league ERA and is checked against Baseball-Reference's park factors (ADR-0063).
- A second strike-zone sample (Gerrit Cole 2023) and an opt-in Retrosheet 2016 linear-weights check.
- VERIFICATION.md, METHODOLOGY.md, CHANGELOG updated.

## Impact
`era_plus` values change for callers who set an AL/NL league. No removals.
