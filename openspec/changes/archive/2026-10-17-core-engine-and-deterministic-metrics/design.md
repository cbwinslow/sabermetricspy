# Design: Core Calculation Engine, Registry, Expectancy, and Forecasting Models

## Context
`sabermetricspy` must execute across millions of rows of play-by-play (`retrosheetpy`), pitch-by-pitch (`statcast`), or seasonal (`lahman`) data on Polars, DuckDB, PyArrow, and pandas while preserving strict mathematical invariants and provenance.

## Key Architectural Decisions
1. **Narwhals Expression Engine**:
   - Every stateless metric function has the signature `(ctx: EvalContext) -> nw.Expr` and is decorated with `@register_metric(spec)`.
   - When `by=[...]` is provided to `calculate(df, metrics, by=...)`, Stage 1 sums all required counting columns grouped by `by`, and Stage 2 evaluates the topologically sorted `nw.Expr` DAG in minimal `with_columns` passes.
2. **Safe Division (`safe_div`)**:
   - All ratio formulas use `safe_div(num, den)` which constructs `nw.when(den != 0).then(num / den).otherwise(float("nan"))`, guaranteeing zero-denominator safety across Polars, DuckDB, Arrow, and pandas.
3. **Innings Pitched (`outs`)**:
   - Helper `ip_to_outs(ip_expr)` converts baseball notation (`6.2 -> 6 * 3 + 2 = 20` outs) and `outs_to_ip_display(outs_expr)` formats `20 -> "6.2"`. All internal formulas (`ERA`, `WHIP`, `FIP`, `K/9`) divide by `(outs / 3.0)`.
4. **Scikit-Learn + Statsmodels Estimator Pattern**:
   - Stateful/empirical models (`RunExpectancyMatrix`, `CountExpectancyMatrix`, `LinearWeightsEstimator`, `MarcelProjector`, `Log5Model`, `MarkovChainModel`, `MonteCarloSimulator`) implement `.fit(df)` returning `Self`, `.transform(df)` / `.predict(df)`, and `.results` returning a frozen Pydantic diagnostics model.
