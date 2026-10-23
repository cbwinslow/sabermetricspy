# ADR-0073: Expected and Maximum Calibration Error

Status: Accepted (adopted by default from the research specs; owner to confirm the defaults listed below)

## Context
`evaluation.calibration_table` reports the Murphy decomposition but no single calibration number. ECE and MCE are the standard scalar summaries (Naeini, Cooper and Hauskrecht 2015; Guo et al. 2017). Neither paper prints a numeric example, and the papers leave the bin edges, the binning scheme and event versus predicted-class form to the implementer.

## Decision
Add `expected_calibration_error` and `maximum_calibration_error` to `sabermetricspy.evaluation`: event form (Naeini), equal-width bins, right-closed by default (ADR-0072), default 10 bins, optional weights, `ValueError` on invalid or empty input, empty bins skipped, `@profiled` and a registered benchmark. Methodology status `matches`, evidence tier `primary` (the formulas are quoted from the papers; there is no published number to reproduce, and the tests say so): hand arithmetic and library-computed fixture rows that an independent implementation also reproduced.

Defaults adopted without an owner answer (research spec `ece_mce_calibration`, O-ECE-1 to O-ECE-5): ship as `matches`/`primary` rather than `experimental`; event form, equal-width, right-closed, 10 bins; the same `closed` default as `calibration_table`; a `weight_col` extension; return a float.

**Rule 7:** neither paper prints an ECE or MCE number, so the outside value is an independent implementation: the per-bin counts, mean forecasts and observed rates equal scikit-learn 1.9.1 `calibration_curve` output recorded in `tests/golden/ece_mce.yaml`, and the ECE/MCE sums are hand arithmetic on those bins. The owner accepted this on 2026-10-23 (GitHub issue 13).

## Alternatives
- Ship as `experimental` (warns), not chosen now because the definition is standard and quoted from two papers; revisit if the owner holds that a definition without a printed numeric example fails rule 7.
- Equal-frequency (quantile) bins, not chosen now because no source fixes the edge definition, interpolation or tie handling; revisit if a source does.
- Guo's predicted-class (confidence) form, not chosen now because it needs multiclass input the library does not model; revisit with a multiclass forecasting model.
- Wrap scikit-learn, not chosen now because it has no ECE function in the pages retrieved and is not a dependency (ADR-0047); revisit if it gains one and is added as a dev dependency.

## Consequences
Two new public functions, two methodology entries, one benchmark, `docs/METHODOLOGY.md` regenerated.
