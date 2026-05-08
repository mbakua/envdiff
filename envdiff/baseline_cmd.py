"""CLI sub-command: baseline — compare live env against a saved snapshot."""

from __future__ import annotations

import argparse
import sys

from envdiff.baseline import compare_to_baseline
from envdiff.parser import parse_current_env, parse_env_file
from envdiff.reporter import render_diff


def build_baseline_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        prog="envdiff baseline",
        description="Compare an environment against a saved snapshot baseline.",
    )
    if parent is not None:
        parser = parent.add_parser("baseline", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        "snapshot",
        help="Path to the snapshot JSON file produced by 'envdiff snapshot save'.",
    )
    parser.add_argument(
        "--env-file",
        metavar="FILE",
        default=None,
        help="Dotenv file to compare against the baseline (default: live process env).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        default=False,
        help="Exit with code 1 when drift is detected.",
    )
    return parser


def run_baseline(args: argparse.Namespace) -> int:
    if args.env_file:
        current = parse_env_file(args.env_file)
    else:
        current = parse_current_env()

    report = compare_to_baseline(current, args.snapshot)

    print(report.summary())
    if not report.is_clean:
        print()
        print(render_diff(report.diff, color=not args.no_color))

    if args.fail_on_drift and not report.is_clean:
        return 1
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_baseline_parser()
    args = parser.parse_args(argv)
    sys.exit(run_baseline(args))


if __name__ == "__main__":  # pragma: no cover
    main()
