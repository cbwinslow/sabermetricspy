# sabermetricspy — Constitution & Project Blueprint

## 1. What It Is
`sabermetricspy` is a high-performance, strongly-typed, dataframe-agnostic Python calculation engine and modeling library for baseball analytics (sabermetrics).

It computes traditional statistics, weighted linear-weight metrics, batted-ball and plate-discipline rates, run/count/win expectancy matrices (RE24, RE288, WPA, LI), defense-independent pitching estimators, Statcast contact/movement features, composite value frameworks (WAR), and statistical forecasting models (Marcel, Log5, Pythagorean/Pythagenpat, BaseRuns, Markov Chains, and Monte Carlo simulations).

## 2. Ecosystem & Boundaries
```text
chadwickpy     = pure-Python port of Chadwick C tools (raw event parsing).
retrosheetpy   = downloads, caches, parses, and ingests Retrosheet archives into DuckDB/Parquet/Polars/Arrow/dlt.
sabermetricspy = pure calculation, expectancy, valuation, and forecasting engine over any DataFrame/table.
mlb            = downstream analytics warehouse, pipelines, and applications.
```
Dependency rule: `sabermetricspy` core is a **pure calculation and modeling engine**. It performs zero network I/O and zero scraper maintenance. Data acquisition lives in `retrosheetpy`, `pybaseball`, or database queries, with thin preset mappings inside `sabermetricspy.presets` and `sabermetricspy.adapters`.

## 3. Naming Conventions & Casing Standard (Mandatory)
Every symbol, enum, column, and display label in `sabermetricspy` follows a strict 3-tier convention that balances PEP 8 Python standards with authentic baseball sabermetric nomenclature:

### Tier 1: Enum Members & Constants (`UPPER_SNAKE_CASE` with Official Baseball Acronyms)
- `Metric` and `Stat` enum members use **`UPPER_SNAKE_CASE`** matching standard baseball abbreviations:
  - Counting stats: `Stat.PA`, `Stat.AB`, `Stat.H`, `Stat.B1` (`1B`), `Stat.B2` (`2B`), `Stat.B3` (`3B`), `Stat.HR`, `Stat.R`, `Stat.RBI`, `Stat.BB`, `Stat.IBB`, `Stat.UBB`, `Stat.HBP`, `Stat.SO`, `Stat.SF`, `Stat.SH`, `Stat.SB`, `Stat.CS`, `Stat.GIDP`, `Stat.OUTS`, `Stat.BF`, `Stat.ER`, `Stat.RA`, `Stat.PO`, `Stat.A`, `Stat.E`, `Stat.BBE`.
  - Rate & Advanced Metrics: `Metric.AVG`, `Metric.OBP`, `Metric.SLG`, `Metric.OPS`, `Metric.ISO`, `Metric.BABIP`, `Metric.BB_PCT`, `Metric.K_PCT`, `Metric.BB_TO_K`, `Metric.WOBA`, `Metric.WRAA`, `Metric.WRC`, `Metric.WRC_PLUS`, `Metric.OPS_PLUS`, `Metric.ERA`, `Metric.WHIP`, `Metric.FIP`, `Metric.XFIP`, `Metric.KWERA`, `Metric.SIERA`, `Metric.ERA_PLUS`, `Metric.ERA_MINUS`, `Metric.FIP_MINUS`, `Metric.CSW_PCT`, `Metric.SWSTR_PCT`, `Metric.O_SWING_PCT`, `Metric.Z_SWING_PCT`, `Metric.HARD_HIT_PCT`, `Metric.BARREL_PCT`, `Metric.RE24`, `Metric.WPA`, `Metric.LI`, `Metric.WAR`.

### Tier 2: Canonical DataFrame Columns & Python Functions (`lower_snake_case`)
- Internal canonical column names and Python function identifiers use concise `lower_snake_case` baseball abbreviations (`pa`, `ab`, `h`, `b1`, `b2`, `b3`, `hr`, `bb`, `ibb`, `hbp`, `so`, `sf`, `sh`, `sb`, `cs`, `gidp`, `outs`, `er`, `ra`, `bf`, `woba`, `wrc_plus`, `fip`, `xfip`, `csw_pct`).
- Note on `1B`, `2B`, `3B`: Because Python identifiers cannot start with a digit, Python enums/identifiers use `B1`, `B2`, `B3` (with `"1b"`, `"2b"`, `"3b"`, `"1B"`, `"2B"`, `"3B"` automatically mapped via presets).

### Tier 3: Display Names & Leaderboard Formatting (`display_name` in `MetricSpec`)
- Every `MetricSpec` carries an official `display_name` using authentic sabermetric typography for reports, plots, and leaderboards:
  - `"AVG"`, `"OBP"`, `"SLG"`, `"OPS"`, `"OPS+"`, `"ISO"`, `"BABIP"`, `"BB%"`, `"K%"`, `"K-BB%"`, `"wOBA"`, `"wRAA"`, `"wRC"`, `"wRC+"`, `"ERA"`, `"ERA+"`, `"ERA-"`, `"FIP"`, `"FIP-"`, `"xFIP"`, `"xFIP-"`, `"kwERA"`, `"SIERA"`, `"CSW%"`, `"SwStr%"`, `"O-Swing%"`, `"Z-Swing%"`, `"HardHit%"`, `"Barrel%"`, `"RE24"`, `"WPA"`, `"pLI"`, `"WAR"`.

## 4. Architectural Invariants
1. **Dataframe-Agnostic Vectorized Core**: All formulas are written once using `narwhals` expressions, executing natively on **Polars**, **DuckDB**, **PyArrow**, and **pandas** without per-row Python loops.
2. **Two-Stage Additive Architecture**:
   - Stage 1 (Classify & Count): Convert raw pitch/play events into additive count columns.
   - Stage 2 (Aggregate & Compute): Sum counts across any arbitrary grouping or rolling window (`by=...`), then evaluate ratio/rate formulas from the summed counts—never average ratios.
3. **Innings Stored as Integer Outs**: Innings pitched are represented internally as integer `outs` (`1 IP = 3 outs`). Baseball display notation (`"6.2"`) is parsed/formatted strictly at I/O boundaries.
4. **Strict Null & Zero-Denominator Policy**:
   - Missing counting stats coerce to `0` only at the ingestion preset edge.
   - Missing physical measurements (`launch_speed`, `release_spin_rate`) remain `null`/`NaN`.
   - Any ratio with a zero denominator returns `null`/`NaN` (never `inf` or `ZeroDivisionError`).
5. **Immutable Results & Provenance**: Stateless calculations return a frozen `CalculationResult` (`.df`, `.specs`, `.context`, `.summary()`). Fitted estimators (`RunExpectancyMatrix`, `LinearWeightsEstimator`, `MarcelProjector`, `Log5Model`, `MarkovChainModel`) follow a `scikit-learn` (`fit`/`predict`/`transform`) API paired with frozen `statsmodels`-style `.results` diagnostics.
6. **Code vs. YAML Separation**:
   - Python (`StrEnum` + `@register_metric` + Pydantic `MetricSpec`) defines core metrics, types, and mathematical expressions.
   - Bundled YAML (`src/sabermetricspy/data/`) stores seasonal constants (wOBA weights, FIP constants, park factors), source presets (`retrosheetpy`, `statcast`, `lahman`), and user-extensible custom formulas.
7. **Spec-Driven & Test-Driven (SDD + TDD)**: Every module is specified in `openspec/`, verified via unit tests, `hypothesis` property-based mathematical identities, and golden cross-check fixtures against FanGraphs, Baseball-Reference, Retrosheet, and `baseballr`.
8. **Decorator Telemetry & Benchmark Registration (`@profiled` & `@register_benchmark`)**: Every public calculation entrypoint, translator, estimator method (`.fit()`, `.transform()`, `.predict()`, `.simulate()`), and valuation/uncertainty function MUST be decorated with `@profiled(category=...)`, and subsystem benchmark workloads MUST be registered via `@register_benchmark(...)`.
