"""CLI sub-command: envdiff recommend — show fix recommendations for a diff."""

from __future__ import annotations

import argparse
import sys

from envdiff.cli import _load
from envdiff.differ import diff_envs
from envdiff.recommender import recommend, RecommendationReport

_SEVERITY_COLOURS = {
    "error": "\033[31m",
    "warning": "\033[33m",
    "info": "\033[36m",
}
_RESET = "\033[0m"


def build_recommend_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff recommend",
        description="Suggest fixes for environment variable mismatches.",
    )
    p.add_argument("left", help="Base .env file or '-' for current process env")
    p.add_argument("right", help="Target .env file")
    p.add_argument(
        "--no-color", action="store_true", default=False, help="Disable colour output"
    )
    p.add_argument(
        "--severity",
        choices=["error", "warning", "info"],
        default=None,
        help="Only show recommendations at this severity level",
    )
    p.add_argument(
        "--fail-on-error",
        action="store_true",
        default=False,
        help="Exit with code 1 if any error-level recommendations exist",
    )
    return p


def _print_report(report: RecommendationReport, no_color: bool, severity_filter) -> None:
    items = report.recommendations
    if severity_filter:
        items = [r for r in items if r.severity == severity_filter]
    if not items:
        print("No recommendations.")
        return
    for rec in items:
        colour = "" if no_color else _SEVERITY_COLOURS.get(rec.severity, "")
        reset = "" if no_color else _RESET
        print(f"{colour}{rec}{reset}")
    print()
    print(f"Summary: {report.summary()}")


def run_recommend(args: argparse.Namespace) -> int:
    left_env = _load(args.left)
    right_env = _load(args.right)
    diff = diff_envs(left_env, right_env)
    report = recommend(diff)
    _print_report(report, args.no_color, args.severity)
    if args.fail_on_error and report.errors:
        return 1
    return 0


def main(argv=None) -> None:
    parser = build_recommend_parser()
    args = parser.parse_args(argv)
    sys.exit(run_recommend(args))


if __name__ == "__main__":
    main()
