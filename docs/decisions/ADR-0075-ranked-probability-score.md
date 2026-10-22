# ADR-0075: Ranked Probability Score

Status: Accepted (adopted by default from the research specs; owner to confirm the defaults listed below)

## Context
The evaluation module scores binary probabilities (`brier_score`, `log_loss`). Outcomes such as run counts are ordered categories, and the standard score for ordered categories is the ranked probability score (Epstein 1969; Murphy 1971). The sources print it in three linearly related forms (Epstein's positively oriented S, Murphy's positively oriented RPS, and the unnormalised cumulative sum), so the orientation and normalisation need a decision.

## Decision
Add `ranked_probability_score(df, forecast_cols, outcome_col, *, normalise=True, weight_col=None)` to `sabermetricspy.evaluation`: a loss (lower is better), the sum of squared differences between the forecast and observed cumulative distributions divided by `K - 1` by default (so it equals the Brier score for K = 2), with the observed category given as a 0-based position in `forecast_cols`. Rows must sum to 1 (tolerance 1e-8, an implementation choice). Invalid input raises `ValueError`. Epstein's S is `1 - rps`. Status `matches`, evidence `golden`: 60 of the 62 printed cells of Epstein's Tables 1 and 2 reproduce; the other two cells print 0.92 where the formula gives 0.9389 (confirmed against the page image), so the paper itself is inconsistent and they are excluded, not adjusted. One benchmark `evaluation.ranked_probability_score`.

Defaults adopted without an owner answer (research spec `rps_epstein_murphy`, O-RPS-1 to O-RPS-5): loss orientation with 1/(K-1) normalisation and a `normalise=False` option; 0-based observed position; exclude the two disputed cells; ship now.

## Alternatives
- Positively oriented score (Epstein's S), not chosen now because every other loss in the module is lower-is-better; revisit if users expect the printed orientation (it is `1 - rps`).
- Observed category numbered 1..K, not chosen now because a 0-based index into the supplied column list is unambiguous; revisit on user feedback.
- Skip the score until the strict-propriety proof is read, not chosen now because both primary texts state it and the definition reproduces the printed tables; revisit if the owner wants the proof first.

## Consequences
One new public function, one methodology entry, one benchmark, `docs/METHODOLOGY.md` regenerated.
