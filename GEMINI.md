# sabermetricspy — Gemini CLI & Antigravity Guide

Read [`openspec/project.md`](openspec/project.md), [`AGENTS.md`](AGENTS.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/NAMING_CONVENTIONS.md`](docs/NAMING_CONVENTIONS.md), and [`docs/DECISIONS.md`](docs/DECISIONS.md) before modifying code.

## 1. Core Architectural Mandates
- **100% Provider-Agnostic Calculation Core**:
  - Core equations (`src/sabermetricspy/metrics/`), expectancy matrices (`src/sabermetricspy/expectancy/`), valuation frameworks (`src/sabermetricspy/value/`), and forecasting models (`src/sabermetricspy/models/`) MUST NEVER hardcode provider-specific column names or event strings.
  - All translation between external data sources (`retrosheetpy`, `statcast`, `lahman`, `fangraphs`, `bref`, `mlb_api`, or custom user schemas) and our canonical Tier 2 columns lives in declarative **YAML Translator files** (`src/sabermetricspy/data/presets/`) loaded by `SourceTranslator`.
- **3-Tier Sabermetric Naming Convention**:
  - **Tier 1 (`StrEnum`)**: `UPPER_SNAKE_CASE` official baseball abbreviations (`Metric.WRC_PLUS`, `Metric.CSW_PCT`, `Stat.HR`, `Stat.OUTS`).
  - **Tier 2 (Canonical Columns & Functions)**: `lower_snake_case` (`"wrc_plus"`, `"csw_pct"`, `"hr"`, `"outs"`).
  - **Tier 3 (`MetricSpec.display_name`)**: Authentic sabermetric typography (`"wRC+"`, `"CSW%"`, `"HR"`, `"Outs"`).
- **Pure Vectorized Narwhals Expressions**:
  - Write formulas once using `narwhals` expressions (`nw.Expr`) for native execution on **Polars**, **DuckDB**, **PyArrow**, and **pandas**.
  - Always sum additive counts across groups (`by=...`) before dividing; never average ratios.
  - Store innings pitched internally as integer `outs` (`1 IP = 3 outs`).
- **Mandatory Telemetry & Benchmark Decorators (`@profiled` & `@register_benchmark`)**:
  - Always decorate new calculation entrypoints, translators, estimator `.fit()` / `.transform()` / `.predict()` / `.simulate()` methods, and valuation/uncertainty functions with `@profiled(category=...)`, and register new subsystem workloads with `@register_benchmark(...)`.

## 2. OpenSpec + TDD Workflow
1. Create or inspect active changes with `openspec status` / `openspec new change <name>`.
2. Complete all 4 planning artifacts (`proposal.md`, `design.md`, `specs/.../spec.md`, `tasks.md`) and validate with `openspec validate --all`.
3. Record architectural decisions in `docs/DECISIONS.md` and `docs/decisions/`.
4. Implement alongside unit tests, `hypothesis` property-based tests, and golden cross-check tests.
5. Verify with `uv run ruff check .`, `uv run pyright`, and `uv run pytest`, then archive with `openspec archive <name> --yes`.
