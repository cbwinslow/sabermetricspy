# sabermetricspy

<p align="center"><b>Fast, strongly-typed, dataframe-agnostic baseball sabermetrics calculation engine, expectancy matrix builder, and forecasting library.</b></p>

<p align="center">
  <a href="https://pypi.org/project/sabermetricspy/"><img src="https://img.shields.io/pypi/v/sabermetricspy.svg?color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/sabermetricspy/"><img src="https://img.shields.io/pypi/pyversions/sabermetricspy.svg" alt="Python Versions"></a>
  <a href="https://github.com/cbwinslow/sabermetricspy/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/cbwinslow/sabermetricspy/ci.yml?branch=main" alt="CI Status"></a>
  <a href="https://github.com/cbwinslow/sabermetricspy/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-green.svg" alt="License"></a>
</p>

---

`sabermetricspy` is a modular Python calculation and modeling engine for baseball analytics. Powered by [`narwhals`](https://github.com/narwhals-dev/narwhals) and [`pydantic`](https://docs.pydantic.dev/), every formula is authored once as a vectorized column expression and executes natively on **Polars**, **DuckDB**, **PyArrow**, and **pandas** across millions of rows with zero per-row Python loops.

It integrates seamlessly with [`retrosheetpy`](https://github.com/cbwinslow/retrosheetpy), [`chadwickpy`](https://github.com/cbwinslow/chadwickpy), Baseball Savant (Statcast), and Lahman schemas.

---

## Key Features

- **Dataframe-Agnostic & Fast**: Native execution on Polars (`DataFrame` & `LazyFrame`), DuckDB (`DuckDBPyRelation`), PyArrow (`Table`), and pandas (`DataFrame`).
- **3-Tier Sabermetric Naming Standard**:
  - **Tier 1 (`StrEnum`)**: `Metric.WRC_PLUS`, `Metric.CSW_PCT`, `Metric.XFIP`, `Stat.HR`, `Stat.OUTS`
  - **Tier 2 (Columns & Functions)**: `"wrc_plus"`, `"csw_pct"`, `"xfip"`, `"hr"`, `"outs"`
  - **Tier 3 (Official Display Labels)**: `"wRC+"`, `"CSW%"`, `"xFIP"`, `"HR"`, `"Outs"`
- **Two-Stage Additive Engine**: Classify raw pitch/play events into additive counts, sum across any grouping (`by=["player_id", "season"]`) or rolling window, and compute ratios strictly from summed counts.
- **DAG Dependency Resolution & Suites**: Request `Metric.WRC_PLUS` and `sabermetricspy` automatically resolves `WOBA -> WRAA -> WRC_PLUS`, or run `calculate_suite(df, MetricSuite.TRADITIONAL_BATTING)` / `calculate_available(df)` to compute all supported metrics in a single pass.
- **Provenance & Bundled YAML Constants**: Every metric carries a frozen `MetricSpec` with its LaTeX formula, primary academic/sabermetric citation, required columns, and seasonal constants (`wOBA`, `FIP`, park factors).
- **Scikit-Learn Style Estimators + Statsmodels Diagnostics**:
  - Empirical Expectancy: `RunExpectancyMatrix` (`RE24`), `CountExpectancyMatrix` (`RE288`), `LinearWeightsEstimator`, `WinProbabilityModel` (`WPA`, `LI`, `pLI`).
  - Forecasting & Simulation: `MarcelProjector`, `Log5Model`, `MarkovChainModel`, `MonteCarloSimulator`, and modular `WARFramework`.

---

## Quickstart

```python
import polars as pl
import sabermetricspy as sp
from sabermetricspy import Metric, MetricSuite, SeasonContext

# 1. Compute specific metrics with full provenance.
# One call uses one season's constants, so pass a single season's rows (several seasons raise an error).
res = sp.calculate(
    batting_df,  # rows for 2024 only
    metrics=[
        Metric.AVG,
        Metric.OBP,
        Metric.SLG,
        Metric.OPS,
        Metric.ISO,
        Metric.BABIP,
        Metric.WOBA,
        Metric.WRC_PLUS,
    ],
    by=["player_id", "season"],
    context=SeasonContext(season=2024),
)

print(res.df)  # Native Polars DataFrame with computed metric columns
print(res.summary())  # Provenance table: formulas, citations, and constants used

# 2. Compute an entire curated suite or auto-discover all computable metrics
pitching_res = sp.calculate_suite(
    pitching_df,
    suite=MetricSuite.DEFENSE_INDEPENDENT_PITCHING,
    by=["player_id", "season"],
)
all_res = sp.calculate_available(batting_df, by=["player_id", "season"])

# 3. Fit an empirical RE24 Run Expectancy Matrix on retrosheetpy play-by-play events
from sabermetricspy.expectancy import RunExpectancyMatrix

re24 = RunExpectancyMatrix().fit(retrosheet_events_df)
valued_plays = re24.transform(retrosheet_events_df)
print(re24.results.matrix_df)
```

---

## Player ids across sources

Statcast, Retrosheet, Baseball-Reference, FanGraphs and Lahman name players differently. `sabermetricspy.ids` translates
between them using the [Chadwick Bureau Register](https://github.com/chadwickbureau/register) (ODC-BY 1.0; credit the
Chadwick Bureau). The register is not bundled: download it once, then use it on any Polars, pandas, PyArrow or DuckDB frame.

```python
import sabermetricspy as sp

sp.download_register()  # ~68 MB into ~/.cache/sabermetricspy, or pass a path
# Using the default location needs no setup: load_register() / translate_ids() download the register when it is missing
# and re-download it when the Chadwick repo has a newer commit (checked at most once a day; offline uses your copy).
# Turn it off with SABERMETRICSPY_AUTO_UPDATE=0, or call sp.update_register() yourself.
res = sp.translate_ids(
    df, "retro", "mlbam"
)  # adds key_mlbam; res.unmatched, res.release, res.license
sp.player_id("mlbam", "Mike", "Trout", birth_year=1991)  # 545361
```

Ambiguous names and ids shared by two people raise an error that lists the candidates; nothing is guessed.

## Accuracy and Provenance

- Seasonal constants (wOBA weights, cFIP, league run environment, non-pitcher wRC/PA) are FanGraphs Guts! and
  leaderboard values for 1990-2025, with source and retrieval date; values with no published source are absent,
  not defaulted.
- Park-adjusted metrics (`wRC+`, `OPS+`, `ERA+`/`ERA-`/`FIP-`) use a park factor of `100` (no adjustment) unless you
  pass the published one: `SeasonContext(season=2001, league="NL", park_factor=96.0)`.
- DuckDB input gives the same results as the other backends. It is read into memory once as Arrow, evaluated on Polars, and returned as a DuckDB relation on DuckDB's default connection (ADR-0056); aggregate a table larger than memory in DuckDB first.
- In 1.0, 106 of 141 metrics and 4 of 15 models `match` their published method; the rest are `approximate`, each with the
  reason and the size of the gap in [Methodology Audit](docs/METHODOLOGY.md). Check `reference_status` before relying on one.
- Every metric reports a `reference_status` (`matches`, `approximate`, `divergent`, `unverified`) against its
  published method; see [Methodology Audit](docs/METHODOLOGY.md). Published-value tests live in `tests/golden/`.

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Methodology Audit](docs/METHODOLOGY.md)
- [Naming Conventions & Baseball Nomenclature](docs/NAMING_CONVENTIONS.md)
- [Architecture Decision Records (ADRs)](docs/DECISIONS.md)
- [OpenSpec Project Constitution](openspec/project.md)
- [Credits and how to cite](docs/CREDITS.md)

---

## License

Licensed under the [Apache License, Version 2.0](LICENSE). Use it freely, including commercially; keep the
[NOTICE](NOTICE) file with any redistribution. To cite the library, see `CITATION.cff`, and please also cite the
original authors of the methods you use ([credits](docs/CREDITS.md)).
