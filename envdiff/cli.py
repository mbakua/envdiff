"""Command-line interface for envdiff."""

import argparse
import os
import sys

from envdiff.differ import diff_envs, has_differences
from envdiff.parser import parse_current_env, parse_env_file
from envdiff.reporter import render_diff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Diff environment variable sets across deployment stages.",
    )
    parser.add_argument(
        "left",
        metavar="LEFT",
        help="Path to the first .env file, or '-' to read from the current environment.",
    )
    parser.add_argument(
        "right",
        metavar="RIGHT",
        help="Path to the second .env file, or '-' to read from the current environment.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output.",
    )
    parser.add_argument(
        "--only-mismatches",
        action="store_true",
        default=False,
        help="Only show keys that differ (omit matching keys).",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if differences are found, 0 otherwise.",
    )
    return parser


def _load(source: str) -> dict:
    """Load an env dict from a file path or the live environment."""
    if source == "-":
        return parse_current_env()
    if not os.path.isfile(source):
        print(f"envdiff: error: file not found: {source}", file=sys.stderr)
        sys.exit(2)
    return parse_env_file(source)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    left_env = _load(args.left)
    right_env = _load(args.right)

    result = diff_envs(left_env, right_env)

    output = render_diff(
        result,
        left_label=args.left,
        right_label=args.right,
        color=not args.no_color,
        only_mismatches=args.only_mismatches,
    )
    print(output)

    if args.exit_code and has_differences(result):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
