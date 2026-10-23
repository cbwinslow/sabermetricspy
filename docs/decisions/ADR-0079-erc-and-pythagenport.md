# ADR-0079: Component ERA (ERC) and Pythagenport Winning Percentage

- **Status**: Accepted
- **Date**: 2026-10-23
- **OpenSpec change**: `add-erc-and-pythagenport`

## Context
Two widely respected closed-form sabermetric estimators with verified provenance were absent from `sabermetricspy`:
1. **Component ERA (`erc`)**: Bill James's classic pitching metric (*2004 Bill James Handbook*, ESPN Sortable Stats, TangoTiger Wiki) estimating what a pitcher's ERA should have been based on component events ($H, HR, BB, HBP, IBB, BF, Outs$). It uses a continuous piecewise linear spline at raw threshold 2.24 ($2.24 \times 0.75 = 1.68 = 2.24 - 0.56$) and falls back to a 0.475 walk coefficient when intentional walks are unavailable.
2. **Pythagenport Winning Percentage (`pythagenport_win_pct`)**: Clay Davenport and Keith Woolner's dynamic base-10 logarithmic exponent formulation (*Baseball Prospectus* 1999 article 342) $\gamma = 1.50 \log_{10}(\text{RPG}) + 0.45$. Adding Pythagenport completes our Pythagorean suite alongside fixed 1.83 and Pythagenpat ($\gamma = \text{RPG}^{0.287}$).

## Decision
- Add `Metric.ERC` (`"erc"`, "ERC") to category `defense_independent_pitching`. Evaluates component PTB, computes raw ERA on BF and IP ($outs / 3.0$), and applies the continuous threshold at 2.24. Safe division returns null when BF or outs is 0.
- Add `Metric.PYTHAGENPORT_WIN_PCT` (`"pythagenport_win_pct"`, "Pythagenport W%") to category `team`. Evaluates $\gamma = 1.50 \log_{10}(\text{RPG}) + 0.45$ over games $G = W + L$ and returns null when $G = 0$ or $\text{RPG} \le 0$.
- Both metrics are pure vectorized `narwhals` expressions tested against golden fixtures (`tests/golden/erc_and_pythagenport.yaml`), unit and property tests in `tests/test_golden_erc_and_pythagenport.py`, and verified across Polars, DuckDB, PyArrow, and pandas backends.

## Consequences
- Two new canonical metrics registered in `Metric` enum and registry.
- `methodology.yaml` and `docs/METHODOLOGY.md` updated with audit status `matches` / `golden`.
- 100% compliance with zero-denominator null safety and pure vectorized expressions.
