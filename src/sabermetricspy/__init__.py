"""sabermetricspy — Fast, strongly-typed, dataframe-agnostic baseball sabermetrics library."""

from __future__ import annotations

from sabermetricspy.constants import (
    get_park_factor,
    get_woba_weights,
    load_custom_constants_yaml,
    resolve_context,
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
from sabermetricspy.expectancy import (
    CountExpectancyMatrix,
    LinearWeightsEstimator,
    LinearWeightsResults,
    RE24Results,
    RE288Results,
    RunExpectancyMatrix,
    WinProbabilityModel,
    WinProbabilityResults,
)
from sabermetricspy.models import (
    CatcherFramingModel,
    CatcherFramingResults,
    ExpectedOutcomeModel,
    ExpectedOutcomeResults,
    Log5Model,
    MarcelProjector,
    MarcelResults,
    MarkovChainModel,
    MarkovInningResults,
    MonteCarloSimulationResults,
    MonteCarloSimulator,
    OutsAboveAverageModel,
    OutsAboveAverageResults,
    PitchQualityModel,
    PitchQualityResults,
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
    UncertaintyInterval,
    binomial_rate_interval,
    bootstrap_interval,
)
from sabermetricspy.value import (
    POSITIONAL_ADJUSTMENTS_PER_162,
    WARComponents,
    WARFramework,
)

__version__ = "0.1.0"


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
    "POSITIONAL_ADJUSTMENTS_PER_162",
    "REGISTRY",
    "BaseState",
    "BattedBallType",
    "BenchmarkEntry",
    "BenchmarkResult",
    "CalculationResult",
    "CatcherFramingModel",
    "CatcherFramingResults",
    "Category",
    "CountExpectancyMatrix",
    "Direction",
    "EmpiricalBayesResults",
    "EmpiricalBayesShrinker",
    "EvalContext",
    "EvidenceTier",
    "ExecutionProfile",
    "ExpectedOutcomeModel",
    "ExpectedOutcomeResults",
    "Handedness",
    "ImplKind",
    "LinearWeightsEstimator",
    "LinearWeightsResults",
    "Log5Model",
    "MarcelProjector",
    "MarcelResults",
    "MarkovChainModel",
    "MarkovInningResults",
    "Metric",
    "MetricRegistry",
    "MetricSpec",
    "MetricSuite",
    "MonteCarloSimulationResults",
    "MonteCarloSimulator",
    "OutsAboveAverageModel",
    "OutsAboveAverageResults",
    "ParkFactor",
    "PerformanceTracker",
    "PitchOutcome",
    "PitchQualityModel",
    "PitchQualityResults",
    "PlayOutcome",
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
    "UncertaintyInterval",
    "WARComponents",
    "WARFramework",
    "WOBAWeights",
    "WinProbabilityModel",
    "WinProbabilityResults",
    "__version__",
    "benchmark",
    "binomial_rate_interval",
    "bootstrap_interval",
    "calculate",
    "calculate_available",
    "calculate_rolling",
    "calculate_suite",
    "describe",
    "formula",
    "get_column_aliases",
    "get_park_factor",
    "get_registered_benchmarks",
    "get_source_translator",
    "get_woba_weights",
    "ip_expr_to_outs",
    "ip_notation_to_outs_scalar",
    "load_custom_constants_yaml",
    "load_custom_metrics_yaml",
    "load_source_translator_yaml",
    "normalize_columns",
    "outs_to_ip_notation_scalar",
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
]
