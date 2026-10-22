# ADR-0072: Calibration Bin Convention and Outside Tie-Outs for the Brier Decomposition

Status: Accepted (adopted by default from the research specs; owner to confirm the defaults listed below)

## Context
`evaluation.calibration_table` (ADR-0039) assigned a forecast to bin `min(int(p * n), n - 1)`, i.e. left-closed bins `[k/n, (k+1)/n)` with 1.0 in the last bin. scikit-learn's `calibration_curve` (`np.searchsorted(bins[1:-1], p)`) and Guo et al. (2017, arXiv:1706.04599) use right-closed bins `((m-1)/M, m/M]`. `floor(p * n)` also mis-bins some decimal edges for large n (29/50 at n = 50; 29/100, 57/100, 58/100 at n = 100), because the float product falls just below the integer. The decomposition tests were hand-computed only; there was no outside value.

## Decision
- `calibration_table` gains `closed: Literal["left", "right"] = "right"`. Right-closed uses `np.searchsorted` on `np.linspace(0, 1, n + 1)[1:-1]` with `side="left"`, which never mis-bins a decimal edge in the tested range (n in 2, 3, 4, 5, 8, 10, 15, 20, 25, 50, 100); `closed="left"` keeps the previous formula. The default changes the bin of a forecast that lies exactly on an inner edge; no other result changes.
- Outside tests (`tests/golden/brier_murphy.yaml`): Brier (1950) printed example (P = 0.19, constants 0.42 and 0.44; the library's single-event value is half of Brier's two-class value) and Murphy (1973) printed partition (UNC 0.480, REL 0.136, RES 0.330, PS 0.286; exactly twice the single-event values). Bin-convention rows on a ten-point set are library-computed and labelled so.
- Methodology entries for `evaluation.brier_score` and `evaluation.calibration_table` are added; the evaluation module raises `ValueError` for bad input (its existing convention, distinct from ADR-0046 for metric expressions).

Defaults adopted without an owner answer (research spec `brier_murphy_decomposition`, O-BR-1 and O-BR-2): right-closed as the default, methodology entries added.

## Alternatives
- Keep left-closed as the default, not chosen now because the two reference implementations the outside world uses (scikit-learn, Guo et al.) are right-closed and `floor(p * n)` can mis-bin edges; revisit if existing users depend on the old edge behaviour.
- Add scikit-learn as a dependency and call `calibration_curve`, not chosen now because ADR-0047 dropped scikit-learn, and `calibration_curve` returns no per-bin counts; revisit if scikit-learn is accepted as a dev dependency for cross-checks only.
- Group by distinct forecast value (Murphy's own exact partition, `n_bins=None`), not chosen now because equal-width bins are the established calibration-table convention; revisit if exact-identity use cases appear.

## Consequences
Behaviour change for forecasts exactly on an inner bin edge (documented in the docstring and CHANGELOG). New golden test `tests/test_golden_brier_murphy.py`. `docs/METHODOLOGY.md` regenerated.
