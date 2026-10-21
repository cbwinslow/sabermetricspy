# Design: v1.0.0 Readiness

Boundary: `retrosheetpy / pybaseball / pipelines -> DataFrames -> sabermetricspy -> results`.

Ids: the register is a local directory of `people-*.csv`. `update_register()` compares the latest upstream commit with `provenance.json` and re-downloads atomically only when newer. Alternatives: auto-refresh inside `load_register`, not chosen now because calculations should not do network I/O; revisit if users want an opt-in flag.

baseballr: fixtures hold only values produced by a recorded baseballr run. Alternative: hand-typed values from memory, not chosen because they cannot be audited.
