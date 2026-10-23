# golden-tieouts Specification

## Purpose
Verify that core sabermetric calculations, constants, and models exactly reproduce verified external benchmarks and golden fixtures without internet access.

## Requirements

### Requirement: baseballr Benchmark Verification
Golden fixtures taken from baseballr SHALL record the function call, package version and run date, and tests SHALL compare `sabermetricspy` output to them.

#### Scenario: Constants, wOBA and FIP match baseballr
- **GIVEN** `tests/golden/baseballr/baseballr_tieout.json`
- **WHEN** supplied constants, `Metric.WOBA` and `Metric.FIP` are computed
- **THEN** they equal `fg_guts()`, `woba_plus()` and `fip_plus()` within baseballr's rounding.

#### Scenario: Fixture provenance
- **GIVEN** a baseballr fixture file
- **WHEN** it is reviewed
- **THEN** its header names the exact baseballr call, version and date the values came from.

### Requirement: The Library Never Fetches Data
The library SHALL perform no network access. Callers supply the Chadwick Register, the Lahman database and seasonal constants as local files; a missing input SHALL fail with an error that says where to obtain it.

#### Scenario: Register missing
- **WHEN** `load_register()` is called and no register exists at the path or in `$SABERMETRICSPY_REGISTER`
- **THEN** a `FileNotFoundError` names the Chadwick repository and the setting, and nothing is downloaded.

