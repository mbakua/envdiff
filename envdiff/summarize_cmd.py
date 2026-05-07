"""CLI entry-point for the summarize sub-command."""

import argparse
import sys

from envdiff.cli import _load
from envdiff.differ import diff_envs
from envdiff.summarizer import summarize_diff


def build_summarize_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="envdiff-summarize",
        description="Print a concise summary of differences between two env files.",
    )
    parser.add_argument("left", help="Base / left env file")
    parser.add_argument("right", help="Target / right env file")
    parser.add_argument(
        "--label-left", default="left", metavar="LABEL", help="Label for the left env (default: left)"
    )
    parser.add_argument(
        "--label-right", default="right", metavar="LABEL", help="Label for the right env (default: right)"
    )
    parser.add_argument(
        "--no-mask",
        action="store_true",
        default=False,
        help="Disable automatic masking of sensitive values",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 when differences are found",
    )
    return parser


def run_summarize(args: argparse.Namespace) -> int:
    left_env = _load(args.left)
    right_env = _load(args.right)
    diff = diff_envs(left_env, right_env)
    report = summarize_diff(
        diff,
        label_left=args.label_left,
        label_right=args.label_right,
        mask_secrets=not args.no_mask,
    )
    print(report)
    if args.exit_code and report.has_issues:
        return 1
    return 0


def main(argv=None) -> None:
    parser = build_summarize_parser()
    args = parser.parse_args(argv)
    sys.exit(run_summarize(args))


if __name__ == "__main__":
    main()
