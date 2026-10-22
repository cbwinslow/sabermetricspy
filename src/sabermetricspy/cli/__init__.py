"""Command-line interface (`sabermetrics`) for inspecting metrics, formulas, suites, and running multi-backend benchmarks."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from sabermetricspy.engine import benchmark
from sabermetricspy.registry import REGISTRY
from sabermetricspy.telemetry import run_registered_benchmarks
from sabermetricspy.types.enums import Category, Metric, MetricSuite


def _cmd_list(category: str | None) -> int:
    specs = REGISTRY.search(category=category) if category else REGISTRY.all_specs()
    print(f"sabermetricspy Registry ({len(specs)} metrics)")
    print("-" * 104)
    print(
        f"{'Tier 1 (Enum)':<22} | {'Tier 2 (Col)':<20} | {'Tier 3':<12} | {'Category':<28} | {'Required Cols'}"
    )
    print("-" * 104)
    val_to_enum = {m.value: m.name for m in Metric}
    for s in specs:
        t1 = val_to_enum.get(s.name, s.name.upper())
        reqs = ", ".join(s.required_columns)
        print(f"{t1:<22} | {s.name:<20} | {s.display_name:<12} | {s.category!s:<28} | {reqs}")
    return 0


def _cmd_info(metric_name: str) -> int:
    try:
        spec = REGISTRY.spec(metric_name)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    val_to_enum = {m.value: m.name for m in Metric}
    t1 = val_to_enum.get(spec.name, spec.name.upper())
    print("=" * 88)
    print(f"Metric: {spec.display_name} (Metric.{t1} / {spec.name!r})")
    print("=" * 88)
    print(f"Category:          {spec.category!s}")
    print(f"Kind:              {spec.kind!s}")
    print(f"Reference status:  {spec.reference_status!s}")
    if spec.reference_url:
        print(f"Reference source:  {spec.reference_url}")
    print(f"Direction:         {spec.direction!s}")
    print(f"Required Columns:  {', '.join(spec.required_columns) or '(none)'}")
    print(f"Optional Columns:  {', '.join(spec.optional_columns) or '(none)'}")
    print(f"Requires Metrics:  {', '.join(spec.requires) or '(none)'}")
    print(f"LaTeX Formula:     {spec.formula_latex}")
    print(f"Citation:          {spec.citation}")
    print(f"Description:       {spec.description}")
    for caveat in spec.caveats:
        print(f"Caveat:            {caveat}")
    return 0


def _cmd_suites() -> int:
    print(f"sabermetricspy Curated MetricSuites ({len(MetricSuite)} suites)")
    print("-" * 96)
    for suite in MetricSuite:
        expanded = REGISTRY.expand_suite(suite)
        preview = ", ".join(expanded[:8]) + (
            f" ... (+{len(expanded) - 8} more)" if len(expanded) > 8 else ""
        )
        print(f"MetricSuite.{suite.name:<30} ({len(expanded):>2} metrics): {preview}")
    return 0


def _cmd_benchmark(rows: int, groups: int, repeats: int, *, registered: bool = False) -> int:
    if registered:
        reg_res = run_registered_benchmarks(repeats=repeats)
        print(reg_res.format_table())
        return 0
    res = benchmark(rows=rows, groups=groups, repeats=repeats)
    print(res.format_table())
    return 0


def _cmd_constants(args: argparse.Namespace) -> int:
    from sabermetricspy.constants import constants_dir
    from sabermetricspy.types.context import ConstantsNotFoundError

    if args.constants_action == "path":
        try:
            print(constants_dir())
        except ConstantsNotFoundError as exc:
            print(exc, file=sys.stderr)
            return 1
        return 0
    from sabermetricspy.fetch import FetchError, update_constants

    try:
        report = update_constants(args.dir, first_season=args.first_season)
    except FetchError as exc:
        print(f"update failed: {exc}", file=sys.stderr)
        return 1
    print(f"constants in {report.directory}")
    for name, seasons in report.fetched.items():
        span = f"{min(seasons)}-{max(seasons)}" if seasons else "nothing new"
        print(f"  {name}: {len(seasons)} seasons fetched ({span})")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the `sabermetrics` CLI."""
    reconf = getattr(sys.stdout, "reconfigure", None)
    if callable(reconf):
        reconf(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="sabermetrics",
        description="sabermetricspy — Fast, strongly-typed, dataframe-agnostic baseball sabermetrics CLI.",
    )
    sub = parser.add_subparsers(dest="subcommand")

    p_list = sub.add_parser(
        "list", help="List registered sabermetric formulas and required columns."
    )
    p_list.add_argument(
        "--category",
        choices=[c.value for c in Category],
        default=None,
        help="Filter metrics by domain category.",
    )

    p_info = sub.add_parser(
        "info", help="Display full provenance, LaTeX formula, and citation for a metric."
    )
    p_info.add_argument("metric", help="Metric identifier (e.g. wrc_plus, 'wRC+', FIP, vaa).")

    sub.add_parser("suites", help="List all curated MetricSuite bundles.")

    p_bench = sub.add_parser(
        "benchmark", help="Run a live multi-backend or decorator-registered benchmark suite."
    )
    p_bench.add_argument(
        "--rows", type=int, default=50_000, help="Number of synthetic rows (default: 50000)."
    )
    p_bench.add_argument(
        "--groups", type=int, default=250, help="Number of player groups (default: 250)."
    )
    p_bench.add_argument("--repeats", type=int, default=3, help="Timed repetitions (default: 3).")
    p_bench.add_argument(
        "--registered",
        action="store_true",
        help="Run all @register_benchmark subsystem workloads across engine, translator, expectancy, valuation, and forecasting.",
    )

    p_const = sub.add_parser(
        "constants", help="Fetch or locate the seasonal constants tables (ADR-0069)."
    )
    const_sub = p_const.add_subparsers(dest="constants_action", required=True)
    p_update = const_sub.add_parser(
        "update",
        help="Fetch Guts!, park factors and league totals to your cache; only missing seasons plus the latest two.",
    )
    p_update.add_argument("--dir", default=None, help="Destination (default: the cache directory).")
    p_update.add_argument(
        "--first-season", type=int, default=1990, help="First season (default: 1990)."
    )
    const_sub.add_parser("path", help="Print the directory constants are read from.")

    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.subcommand == "constants":
        return _cmd_constants(args)
    if args.subcommand == "list":
        return _cmd_list(args.category)
    if args.subcommand == "info":
        return _cmd_info(args.metric)
    if args.subcommand == "suites":
        return _cmd_suites()
    if args.subcommand == "benchmark":
        return _cmd_benchmark(
            args.rows, args.groups, args.repeats, registered=bool(args.registered)
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
