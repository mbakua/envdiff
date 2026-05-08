"""CLI command: annotate — display annotated diff with contextual notes."""

import argparse
import sys
from typing import List

from envdiff.cli import _load
from envdiff.differ import diff_envs
from envdiff.annotator import annotate_diff, AnnotatedDiff


def build_annotate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff annotate",
        description="Show a diff with contextual annotations for each key.",
    )
    parser.add_argument("left", help="Base env file or '-' for current environment")
    parser.add_argument("right", help="Target env file")
    parser.add_argument(
        "--severity",
        choices=["info", "warning", "error"],
        default=None,
        help="Filter annotations by severity level",
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Show only error-level annotations (shorthand for --severity=error)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colour output",
    )
    return parser


_COLORS = {"error": "\033[31m", "warning": "\033[33m", "info": "\033[36m", "reset": "\033[0m"}


def _print_result(result: AnnotatedDiff, severity_filter, use_color: bool) -> None:
    annotations = result.annotations
    if severity_filter:
        annotations = [a for a in annotations if a.severity == severity_filter]

    if not annotations:
        print("No annotations match the given filters.")
        return

    for ann in annotations:
        prefix = f"[{ann.severity.upper()}]"
        if use_color:
            color = _COLORS.get(ann.severity, "")
            reset = _COLORS["reset"]
            print(f"{color}{prefix}{reset} {ann.key}: {ann.note}")
        else:
            print(f"{prefix} {ann.key}: {ann.note}")


def run_annotate(argv: List[str] = None) -> int:
    parser = build_annotate_parser()
    args = parser.parse_args(argv)

    left_env = _load(args.left)
    right_env = _load(args.right)
    diff = diff_envs(left_env, right_env)
    result = annotate_diff(diff)

    severity = "error" if args.errors_only else args.severity
    use_color = not args.no_color

    _print_result(result, severity, use_color)
    return 1 if result.has_errors() else 0


def main() -> None:
    sys.exit(run_annotate())


if __name__ == "__main__":
    main()
