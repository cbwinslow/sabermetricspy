# Proposal: Add Component ERA (ERC) and Pythagenport Winning Percentage

## Why
Two classic, widely cited sabermetric estimators are currently absent from `sabermetricspy` despite strong historical lineage and clear mathematical formulation:
1. **Component ERA (`ERC`, Bill James)**: Formulated in the *2004 Bill James Handbook* and utilized by ESPN Sortable Stats and TangoTiger Wiki, ERC predicts a pitcher's earned run average from component events ($H, HR, BB, HBP, IBB, BF, Outs$) without sequencing or cluster luck.
2. **Pythagenport Winning Percentage (`PYTHAGENPORT_WIN_PCT`, Davenport & Woolner 1999)**: Introduced in Baseball Prospectus article 342, Pythagenport pioneered dynamic Pythagorean exponents with $\gamma = 1.50 \log_{10}(\text{RPG}) + 0.45$. Adding it completes our Pythagorean expectation suite alongside fixed-exponent Pythagorean ($\gamma = 1.83$) and Pythagenpat ($\gamma = \text{RPG}^{0.287}$).

## What Changes
1. Register `Metric.ERC` in `sabermetricspy.types.enums` (`Category.PITCHING`, Tier 2 `erc`, Tier 3 `ERC`).
2. Implement vectorized `calc_erc` in `sabermetricspy.metrics.pitching` using pure Narwhals expressions with safe division for zero batters faced or zero innings pitched, continuous piecewise spline at 2.24, and graceful fallback when `ibb` is omitted.
3. Register `Metric.PYTHAGENPORT_WIN_PCT` in `sabermetricspy.types.enums` (`Category.TEAM`, Tier 2 `pythagenport_win_pct`, Tier 3 `Pythagenport W%`).
4. Implement vectorized `calc_pythagenport_win_pct` in `sabermetricspy.metrics.specialized` using Narwhals base-10 log expression and zero-division protection.
5. Provide golden tests, algebraic property-based tests via `hypothesis`, and multi-backend verification across Polars, DuckDB, PyArrow, and pandas.
6. Register both in `methodology.yaml`, document in `docs/METHODOLOGY.md`, and record in `docs/decisions/ADR-0079-erc-and-pythagenport.md`.

## Capabilities
### New Capabilities
- `component-era`: Calculation of Bill James's Component ERA with piecewise continuous threshold at 2.24.
- `pythagenport-winning-pct`: Calculation of Davenport and Woolner's Pythagenport winning percentage with dynamic base-10 log exponent.

## Impact
Zero breaking changes. Additive metrics registered into canonical registries and available via standard calculation engine calls.
