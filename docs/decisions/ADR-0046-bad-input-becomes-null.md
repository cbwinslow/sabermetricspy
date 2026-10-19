# ADR-0046: Bad Inputs Become Null, and Sacrifice Double Plays Are Counted

Status: Accepted

## Context
An independent review of the repository found three places where bad or unusual input gave a plausible wrong number.
1. The vectorized innings-pitched conversion mapped any unrecognised remainder to zero outs, so 6.5 became 18 outs and
   6.15 became 19, while the scalar conversion raises an error for the same inputs.
2. `safe_div` returned NaN for a zero or null denominator. In Polars NaN is a number: it poisons `mean()` and `is_null()`
   does not find it. ADR-0008 allows "null/NaN".
3. The Statcast preset did not recognise the event values `sac_fly_double_play` and `sac_bunt_double_play`, so those plate
   appearances were dropped from `pa`, `sf` and `sh`. That the values exist is documented only by pybaseball users'
   printed event lists (secondary); Savant's CSV docs do not list event values.

## Decision
`ip_expr_to_outs` accepts the same notation as the scalar function (.0, .1, .2 and the true thirds .333 and .667) and returns
null for anything else. `safe_div` returns null instead of NaN. The preset counts `sac_fly_double_play` as `pa` and `sf`, and
`sac_bunt_double_play` as `pa` and `sh`, neither as an at-bat; this follows the event names and the official sacrifice-fly rule
and is not checked against a published count.

Alternatives considered: (a) raise on bad innings inside the expression, not chosen now because a vectorized expression
cannot raise per row; revisit if the engine gains an input-validation pass; (b) keep NaN, not chosen now because it breaks
aggregation; (c) leave the sacrifice double plays out, not chosen now because dropped plate appearances change OBP.

## Consequences
Results that were NaN are now null. Rows with invalid innings notation produce null outs and therefore null rates instead of
wrong values. Tests: `tests/test_input_hygiene.py`.
