"""CLI command: envdiff report — consolidated diff report."""

import argparse
import json
import sys

from envdiff.cli import _load
from envdiff.differ import diff_envs
from envdiff.differ_report import build_report


def build_report_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff report",
        description="Show a consolidated diff report with stats, score, and recommendations.",
    )
    p.add_argument("left", help="Base env file or '-' for current environment")
    p.add_argument("right", help="Target env file or '-' for current environment")
    p.add_argument(
        "--label-left",
        default="left",
        metavar="LABEL",
        help="Display label for the left environment (default: left)",
    )
    p.add_argument(
        "--label-right",
        default="right",
        metavar="LABEL",
        help="Display label for the right environment (default: right)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with code 1 if the report has any issues",
    )
    return p


def run_report(args: argparse.Namespace) -> int:
    left_env = _load(args.left)
    right_env = _load(args.right)
    diff = diff_envs(left_env, right_env)
    report = build_report(diff, label_left=args.label_left, label_right=args.label_right)

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.summary())
        if report.recommendations.errors:
            print("\nErrors:")
            for r in report.recommendations.errors:
                print(f"  [error] {r}")
        if report.recommendations.warnings:
            print("\nWarnings:")
            for r in report.recommendations.warnings:
                print(f"  [warn]  {r}")

    if args.fail_on_issues and report.has_issues:
        return 1
    return 0


def main() -> None:
    parser = build_report_parser()
    args = parser.parse_args()
    sys.exit(run_report(args))


if __name__ == "__main__":
    main()
