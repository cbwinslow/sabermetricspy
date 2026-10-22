# ADR-0076: Diebold-Mariano Test

Status: Accepted (adopted by default from the research specs; owner to confirm the defaults listed below)

## Context
The evaluation module reports each forecast's score (`rmse`, `mae`, `brier_score`, `log_loss`) but not whether two forecasts differ significantly. The Diebold-Mariano (1995) test is the standard answer. The paper prints no numeric example. Its long-run variance uses a uniform lag window, which can be negative in small samples (it is for h = 2 on the 12-point research sample); statsmodels 0.15.0 offers an implementation (Bartlett weights) that is not a library dependency. Harvey, Leybourne and Newbold (1997) propose a small-sample correction, derived for the uniform-window estimator.

## Decision
Add `diebold_mariano_test(df, actual_col, forecast_a_col, forecast_b_col, *, horizon=1, power=2.0, lags=None)` and frozen `DieboldMarianoResult` to `sabermetricspy.evaluation`. Loss differential `|e_a|**power - |e_b|**power`; statistic `mean(d) / sqrt(lrv / T)`; long-run variance with `horizon - 1` lags by default and Bartlett weights; two-sided normal p-value; positive statistic means forecast A is worse; rows must be in time order. Raises `ValueError` for invalid input and a zero long-run variance. Methodology status `matches`, evidence `primary` (no printed example exists): hand arithmetic and the recorded statsmodels 0.15.0 output agree with the implementation to about 1e-15 for horizons 1 to 3. **The HLN correction is not implemented.** One benchmark `evaluation.diebold_mariano_test`.

Defaults adopted without an owner answer (research spec `diebold_mariano_hln`, O-DM-1 to O-DM-5): statistic only; Bartlett weights only; raise on zero variance. Because the HLN primary shows its correction belongs to the uniform-window estimator, shipping it with Bartlett weights would apply it outside its derivation, so it waits for an owner decision.

## Alternatives
- Ship the HLN factor as an opt-in flag labelled secondary (the research spec's recommendation before the paper was read), not chosen now because the primary ties the factor to the uniform-window variance; revisit if the owner accepts the mismatch or the uniform window with a null-on-negative-variance rule.
- Use the paper's uniform window, not chosen now because it can give a non-positive variance; revisit with HLN (option above).
- Wrap statsmodels, not chosen now because ADR-0047 removed heavyweight dependencies and the arithmetic is about 20 lines; revisit if statsmodels is accepted as an optional dependency.
- Return NaN for a zero variance, not chosen now because an undefined statistic should not pass silently; revisit on user feedback.

## Consequences
One new public function and result class, one methodology entry, one benchmark; `docs/METHODOLOGY.md` regenerated.
