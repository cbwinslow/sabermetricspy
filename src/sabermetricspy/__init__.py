"""sabermetricspy — Fast, strongly-typed, dataframe-agnostic baseball sabermetrics library."""

from __future__ import annotations

from sabermetricspy import evaluation as evaluation
from sabermetricspy.constants import (
    ConstantsNotFoundError,
    get_fip_park_factor,
    get_park_factor,
    get_woba_weights,
    load_custom_constants_yaml,
    load_guts,
    resolve_context,
    use_constants,
    use_guts,
)
from sabermetricspy.engine import (
    BenchmarkResult,
    CalculationResult,
    ExecutionProfile,
    benchmark,
    calculate,
    calculate_available,
    calculate_rolling,
    calculate_suite,
)
from sabermetricspy.evaluation import CalibrationBin, CalibrationResults
from sabermetricspy.expectancy import (
    WALSH_COUNT_RUN_VALUES,
    CountExpectancyMatrix,
    LinearWeightsEstimator,
    LinearWeightsResults,
    MarkovWinExpectancy,
    MarkovWinExpectancyResults,
    RE24Results,
    RE288Results,
    RunExpectancyMatrix,
    WinExpectancyMatrix,
    WinExpectancyResults,
    count_run_value,
)
from sabermetricspy.ids import (
    PlayerRegister,
    TranslationResult,
    find_players,
    load_register,
    normalize_name,
    player_id,
    translate_ids,
)
from sabermetricspy.models import (
    Log5Model,
    MarcelProjector,
    MarcelResults,
    MarkovChainModel,
    MarkovInningResults,
)
from sabermetricspy.models.glicko2 import (
    GLICKO2_SCALE,
    Glicko2Rating,
    glicko2_expected_score,
    glicko2_update,
)
from sabermetricspy.presets import (
    SourceTranslator,
    get_source_translator,
    load_custom_metrics_yaml,
    load_source_translator_yaml,
    prepare_retrosheet_events,
    prepare_statcast_pitches,
    register_source_translator,
)
from sabermetricspy.registry import (
    REGISTRY,
    EvalContext,
    MetricRegistry,
    MetricSpec,
    register_metric,
)
from sabermetricspy.schema import (
    get_column_aliases,
    ip_expr_to_outs,
    ip_notation_to_outs_scalar,
    normalize_columns,
    outs_to_ip_notation_scalar,
    register_column_aliases,
    register_column_aliases_yaml,
    safe_div,
)
from sabermetricspy.telemetry import (
    BenchmarkEntry,
    PerformanceTracker,
    RegisteredBenchmarkResult,
    SpanRecord,
    get_registered_benchmarks,
    profiled,
    register_benchmark,
    run_registered_benchmarks,
    telemetry,
)
from sabermetricspy.types import (
    BaseState,
    BattedBallType,
    Category,
    Direction,
    EvidenceTier,
    Handedness,
    ImplKind,
    Metric,
    MetricSuite,
    ParkFactor,
    PitchOutcome,
    PlayOutcome,
    ReferenceStatus,
    SeasonContext,
    SIERACoefficients,
    Stat,
    WOBAWeights,
)
from sabermetricspy.uncertainty import (
    EmpiricalBayesResults,
    EmpiricalBayesShrinker,
    JamesSteinResults,
    JamesSteinShrinker,
    UncertaintyInterval,
    binomial_rate_interval,
    bootstrap_interval,
)
from sabermetricspy.value import (
    POSITIONAL_ADJUSTMENTS_PER_162,
    WARComponents,
    WARFramework,
)

__version__ = "2.1.0"


def describe(metric: Metric | str) -> MetricSpec:
    """Return the complete MetricSpec metadata and provenance for a metric."""
    return REGISTRY.spec(metric)


def formula(metric: Metric | str) -> str:
    """Return the LaTeX mathematical formula for a metric."""
    return REGISTRY.spec(metric).formula_latex


def search_metrics(
    *,
    category: Category | str | None = None,
    kind: ImplKind | str | None = None,
    requires_column: str | None = None,
) -> list[MetricSpec]:
    """Search the metric registry by category, implementation kind, or required base column."""
    return REGISTRY.search(category=category, kind=kind, requires_column=requires_column)


__all__ = [
    "GLICKO2_SCALE",
    "POSITIONAL_ADJUSTMENTS_PER_162",
    "REGISTRY",
    "WALSH_COUNT_RUN_VALUES",
    "BaseState",
    "BattedBallType",
    "BenchmarkEntry",
    "BenchmarkResult",
    "CalculationResult",
    "CalibrationBin",
    "CalibrationResults",
    "Category",
    "ConstantsNotFoundError",
    "CountExpectancyMatrix",
    "Direction",
    "EmpiricalBayesResults",
    "EmpiricalBayesShrinker",
    "EvalContext",
    "EvidenceTier",
    "ExecutionProfile",
    "Glicko2Rating",
    "Handedness",
    "ImplKind",
    "JamesSteinResults",
    "JamesSteinShrinker",
    "LinearWeightsEstimator",
    "LinearWeightsResults",
    "Log5Model",
    "MarcelProjector",
    "MarcelResults",
    "MarkovChainModel",
    "MarkovInningResults",
    "MarkovWinExpectancy",
    "MarkovWinExpectancyResults",
    "Metric",
    "MetricRegistry",
    "MetricSpec",
    "MetricSuite",
    "ParkFactor",
    "PerformanceTracker",
    "PitchOutcome",
    "PlayOutcome",
    "PlayerRegister",
    "RE24Results",
    "RE288Results",
    "ReferenceStatus",
    "RegisteredBenchmarkResult",
    "RunExpectancyMatrix",
    "SIERACoefficients",
    "SeasonContext",
    "SourceTranslator",
    "SpanRecord",
    "Stat",
    "TranslationResult",
    "UncertaintyInterval",
    "WARComponents",
    "WARFramework",
    "WOBAWeights",
    "WinExpectancyMatrix",
    "WinExpectancyResults",
    "__version__",
    "benchmark",
    "binomial_rate_interval",
    "bootstrap_interval",
    "calculate",
    "calculate_available",
    "calculate_rolling",
    "calculate_suite",
    "count_run_value",
    "describe",
    "find_players",
    "formula",
    "get_column_aliases",
    "get_fip_park_factor",
    "get_park_factor",
    "get_registered_benchmarks",
    "get_source_translator",
    "get_woba_weights",
    "glicko2_expected_score",
    "glicko2_update",
    "ip_expr_to_outs",
    "ip_notation_to_outs_scalar",
    "load_custom_constants_yaml",
    "load_custom_metrics_yaml",
    "load_guts",
    "load_register",
    "load_source_translator_yaml",
    "normalize_columns",
    "normalize_name",
    "outs_to_ip_notation_scalar",
    "player_id",
    "prepare_retrosheet_events",
    "prepare_statcast_pitches",
    "profiled",
    "register_benchmark",
    "register_column_aliases",
    "register_column_aliases_yaml",
    "register_metric",
    "register_source_translator",
    "resolve_context",
    "run_registered_benchmarks",
    "safe_div",
    "search_metrics",
    "telemetry",
    "translate_ids",
    "use_constants",
    "use_guts",
]
