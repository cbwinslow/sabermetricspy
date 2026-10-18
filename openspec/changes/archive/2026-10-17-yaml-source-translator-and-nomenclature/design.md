# Design: Declarative YAML SourceTranslator and Nomenclature Registry

## Context
Users may feed `sabermetricspy` data from `retrosheetpy`, Baseball Savant Statcast, Lahman, FanGraphs exports, Baseball-Reference exports, MLB Stats API, TrackMan college CSVs, or custom SQL tables. Hardcoding column aliases or event-to-count logic in Python limits extensibility.

## Architecture
1. **`aliases.yaml` & `NomenclatureRegistry`**:
   - `src/sabermetricspy/data/presets/aliases.yaml` stores canonical Tier 2 target columns (`pa`, `ab`, `h`, `b1`, `b2`, `b3`, `hr`, `bb`, `ibb`, `ubb`, `hbp`, `so`, `outs`, etc.) mapped to lists of known provider aliases.
   - `register_column_aliases(mapping)` and `register_column_aliases_yaml(path_or_yaml)` allow users to add their own nomenclature aliases dynamically without touching library code.
2. **`SourceTranslator` Pydantic Spec & Vectorized Narwhals Compiler**:
   - A YAML source preset defines:
     - `name`: identifier (e.g. `"statcast"`, `"retrosheetpy_events"`, `"lahman_batting"`, `"my_custom_source"`).
     - `description`: human-readable summary.
     - `column_map`: direct column renames (`{"BAT_ID": "player_id", "PIT_ID": "pitcher_id"}`).
     - `value_rules`: maps a source column matching a set of values into a `0`/`1` count column (e.g. `source_col: "EVENT_CD"`, `values: [14, 15]` -> `target_col: "bb"`).
     - `range_rules`: maps a numeric source column within `[min_val, max_val]` into a `0`/`1` count column (e.g. `source_col: "launch_speed"`, `min_val: 95.0` -> `target_col: "hard_hit_bbe"`).
   - `SourceTranslator.transform(df)` compiles these rules into a single vectorized `nw_df.with_columns(...)` call across Polars, DuckDB, PyArrow, and pandas.
