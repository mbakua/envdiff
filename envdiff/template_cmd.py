"""CLI sub-command: generate an env template from two environment files."""

from __future__ import annotations

import argparse
import sys

from envdiff.cli import _load
from envdiff.differ import diff_envs
from envdiff.templater import generate_template


def build_template_parser(
    parser: argparse.ArgumentParser | None = None,
) -> argparse.ArgumentParser:
    if parser is None:
        parser = argparse.ArgumentParser(
            prog="envdiff-template",
            description="Generate a .env template from two environment files.",
        )
    parser.add_argument("left", help="Base / source env file")
    parser.add_argument("right", help="Target env file")
    parser.add_argument(
        "--include-right-only",
        action="store_true",
        default=False,
        help="Include keys that only exist in the right env as optional entries",
    )
    parser.add_argument(
        "--no-mismatch-comments",
        action="store_true",
        default=False,
        help="Suppress comments on mismatch entries",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        metavar="FILE",
        help="Write template to FILE instead of stdout",
    )
    return parser


def run_template(args: argparse.Namespace) -> int:
    left_env = _load(args.left)
    right_env = _load(args.right)

    diff = diff_envs(left_env, right_env)
    template = generate_template(
        diff,
        include_right_only=args.include_right_only,
        comment_mismatches=not args.no_mismatch_comments,
    )

    rendered = template.render()

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(rendered)
            print(f"Template written to {args.output}")
        except OSError as exc:
            print(f"Error writing template: {exc}", file=sys.stderr)
            return 1
    else:
        print(rendered, end="")

    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_template_parser()
    args = parser.parse_args(argv)
    sys.exit(run_template(args))


if __name__ == "__main__":
    main()
