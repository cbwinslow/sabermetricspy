"""Metric registry, MetricSpec metadata model, DAG dependency resolver, and suite expansion."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from importlib.metadata import entry_points

import narwhals as nw
from pydantic import BaseModel, ConfigDict, Field

from sabermetricspy.types.context import SeasonContext, WOBAWeights
from sabermetricspy.types.enums import Category, Direction, ImplKind, Metric, MetricSuite


class MetricSpec(BaseModel):
    """Machine-readable metadata and provenance specification for a sabermetric."""

    model_config = ConfigDict(frozen=True)

    metric: Metric | str = Field(..., description="Canonical lower_snake_case metric identifier")
    display_name: str = Field(..., description="Official Tier 3 baseball typography (e.g. 'wRC+')")
    category: Category = Field(..., description="Domain category")
    kind: ImplKind = Field(default=ImplKind.DETERMINISTIC, description="Implementation type")
    required_columns: tuple[str, ...] = Field(
        default=(), description="Canonical additive count columns required"
    )
    optional_columns: tuple[str, ...] = Field(
        default=(), description="Optional canonical count columns"
    )
    requires: tuple[str, ...] = Field(
        default=(), description="Other metrics that must be evaluated before this metric"
    )
    direction: Direction = Field(default=Direction.HIGHER_IS_BETTER)
    formula_latex: str = Field(..., description="LaTeX mathematical representation")
    citation: str = Field(..., description="Primary academic or sabermetric source citation")
    description: str = Field(default="", description="Concise definition of the metric")
    caveats: tuple[str, ...] = Field(default=(), description="Known methodological caveats")
    version: str = Field(default="1.0")

    @property
    def name(self) -> str:
        """Return canonical lower_snake_case string name."""
        return str(self.metric)


@dataclass(frozen=True)
class EvalContext:
    """Runtime context passed into metric expression builders."""

    season_context: SeasonContext
    weights: WOBAWeights
    available_columns: frozenset[str]


MetricBuilder = Callable[[EvalContext], nw.Expr]


@dataclass(frozen=True)
class RegisteredMetric:
    """Pair of MetricSpec metadata and its vectorized Narwhals expression builder."""

    spec: MetricSpec
    builder: MetricBuilder


class MetricRegistry:
    """Central registry for built-in and plugin-defined baseball metrics."""

    def __init__(self) -> None:
        self._metrics: dict[str, RegisteredMetric] = {}
        self._display_lookup: dict[str, str] = {}
        self._plugins_loaded: bool = False

    def register(self, spec: MetricSpec, builder: MetricBuilder, *, overwrite: bool = False) -> None:
        """Register a metric specification and its Narwhals expression builder."""
        key = spec.name.lower()
        if key in self._metrics and not overwrite:
            raise ValueError(f"Metric {key!r} is already registered.")
        # Detect immediate self-dependency
        if key in [r.lower() for r in spec.requires]:
            raise ValueError(f"Metric {key!r} cannot depend on itself.")
        self._metrics[key] = RegisteredMetric(spec=spec, builder=builder)
        self._display_lookup[spec.display_name.lower()] = key

    def resolve_name(self, name_or_enum: Metric | str) -> str:
        """Resolve a Metric enum, canonical snake_case string, or display_name ('wRC+') to canonical key."""
        self.load_entry_point_plugins()
        raw = str(name_or_enum).strip()
        lower = raw.lower()
        if lower in self._metrics:
            return lower
        if lower in self._display_lookup:
            return self._display_lookup[lower]
        raise KeyError(
            f"Unknown metric {name_or_enum!r}. Use sabermetricspy.search_metrics() to list registered metrics."
        )

    def get(self, name_or_enum: Metric | str) -> RegisteredMetric:
        """Retrieve a RegisteredMetric by Metric enum, canonical name, or display name."""
        key = self.resolve_name(name_or_enum)
        return self._metrics[key]

    def spec(self, name_or_enum: Metric | str) -> MetricSpec:
        """Retrieve the MetricSpec for a metric."""
        return self.get(name_or_enum).spec

    def all_specs(self) -> list[MetricSpec]:
        """Return all registered MetricSpec instances."""
        self.load_entry_point_plugins()
        return [m.spec for m in self._metrics.values()]

    def search(
        self,
        *,
        category: Category | str | None = None,
        kind: ImplKind | str | None = None,
        requires_column: str | None = None,
    ) -> list[MetricSpec]:
        """Filter registered metrics by category, implementation kind, or required input column."""
        self.load_entry_point_plugins()
        results: list[MetricSpec] = []
        for reg in self._metrics.values():
            s = reg.spec
            if category is not None and str(s.category) != str(category).lower():
                continue
            if kind is not None and str(s.kind) != str(kind).lower():
                continue
            if requires_column is not None and requires_column.lower() not in s.required_columns:
                continue
            results.append(s)
        return results

    def resolve_dag(self, requested: Sequence[Metric | str]) -> list[RegisteredMetric]:
        """Resolve dependency graph in topological execution stages (Kahn's / DFS post-order).

        Raises ValueError if a circular dependency exists.
        """
        self.load_entry_point_plugins()
        ordered: list[RegisteredMetric] = []
        visited: dict[str, int] = {}  # 0=visiting, 1=visited

        def _visit(key: str) -> None:
            state = visited.get(key)
            if state == 1:
                return
            if state == 0:
                raise ValueError(f"Circular dependency detected involving metric {key!r}.")
            visited[key] = 0
            reg = self.get(key)
            for dep in reg.spec.requires:
                dep_key = self.resolve_name(dep)
                _visit(dep_key)
            visited[key] = 1
            ordered.append(reg)

        for item in requested:
            _visit(self.resolve_name(item))

        return ordered

    def required_base_columns(self, requested: Sequence[Metric | str]) -> set[str]:
        """Return the union of all canonical base columns needed to evaluate `requested` metrics."""
        dag = self.resolve_dag(requested)
        cols: set[str] = set()
        for reg in dag:
            cols.update(reg.spec.required_columns)
        return cols

    def available_for_columns(self, columns: Iterable[str]) -> list[MetricSpec]:
        """Return all registered metrics whose required base columns are satisfied by `columns`."""
        self.load_entry_point_plugins()
        col_set = {c.lower() for c in columns}
        available: list[MetricSpec] = []
        for key, reg in self._metrics.items():
            reqs = self.required_base_columns([key])
            if reqs.issubset(col_set):
                available.append(reg.spec)
        return available

    def expand_suite(self, suite: MetricSuite | str) -> list[str]:
        """Expand a MetricSuite enum into its constituent canonical metric names."""
        self.load_entry_point_plugins()
        s = MetricSuite(str(suite).lower())
        if s == MetricSuite.ALL:
            return list(self._metrics.keys())

        category_map: dict[MetricSuite, tuple[Category, ...]] = {
            MetricSuite.TRADITIONAL_BATTING: (Category.BATTING,),
            MetricSuite.WEIGHTED_OFFENSE: (Category.WEIGHTED_OFFENSE,),
            MetricSuite.BASERUNNING: (Category.BASERUNNING,),
            MetricSuite.TRADITIONAL_PITCHING: (Category.PITCHING,),
            MetricSuite.DEFENSE_INDEPENDENT_PITCHING: (Category.DEFENSE_INDEPENDENT_PITCHING,),
            MetricSuite.PLATE_DISCIPLINE: (Category.PLATE_DISCIPLINE,),
            MetricSuite.BATTED_BALL: (Category.BATTED_BALL,),
            MetricSuite.STATCAST_EXPECTED: (Category.STATCAST_EXPECTED,),
            MetricSuite.PITCH_PHYSICS: (Category.PITCH_PHYSICS,),
            MetricSuite.FIELDING: (Category.FIELDING,),
            MetricSuite.EXPECTANCY: (Category.EXPECTANCY,),
            MetricSuite.TEAM_ESTIMATORS: (Category.TEAM,),
            MetricSuite.OFFENSE_ALL: (
                Category.BATTING,
                Category.WEIGHTED_OFFENSE,
                Category.BASERUNNING,
                Category.STATCAST_EXPECTED,
            ),
            MetricSuite.PITCHING_ALL: (
                Category.PITCHING,
                Category.DEFENSE_INDEPENDENT_PITCHING,
                Category.PITCH_PHYSICS,
            ),
        }
        target_cats = category_map[s]
        return [
            key for key, reg in self._metrics.items() if reg.spec.category in target_cats
        ]

    def load_entry_point_plugins(self) -> None:
        """Discover and load third-party plugins registered under 'sabermetricspy.plugins'."""
        if self._plugins_loaded:
            return
        self._plugins_loaded = True
        eps = entry_points(group="sabermetricspy.plugins")
        for ep in eps:
            plugin_fn = ep.load()
            if callable(plugin_fn):
                plugin_fn(self)


REGISTRY = MetricRegistry()


def register_metric(
    spec: MetricSpec, *, overwrite: bool = False
) -> Callable[[MetricBuilder], MetricBuilder]:
    """Decorator to register a metric formula function with its MetricSpec."""

    def _decorator(fn: MetricBuilder) -> MetricBuilder:
        REGISTRY.register(spec, fn, overwrite=overwrite)
        return fn

    return _decorator
