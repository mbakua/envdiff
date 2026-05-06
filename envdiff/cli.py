"""Command-line interface for envdiff."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import NoReturn

from envdiff.differ import diff_envs
from envdiff.formatter import format_dotenv, format_json, format_markdown
from envdiff.masker import mask_diff
from envdiff.parser import parse_current_env, parse_env_file
from envdiff.reporter import render_diff


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff",
        description="Diff environment variable sets across deployment stages.",
    )
    p.add_argument("left", nargs="?", help="Path to the left .env file (omit to use current environment).")
    p.add_argument("right", help="Path to the right .env file.")
    p.add_argument(
        "--format",
        choices=["text", "json", "dotenv", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output (text format only).",
    )
    p.add_argument(
        "--mask-secrets",
        action="store_true",
        default=False,
        help="Replace sensitive values with *** before output.",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 when differences are found.",
    )
    return p


def _load(path: str | None) -> dict[str, str]:
    if path is None:
        return parse_current_env()
    return parse_env_file(Path(path))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    left_env = _load(args.left)
    right_env = _load(args.right)

    result = diff_envs(left_env, right_env)

    if args.mask_secrets:
        result = mask_diff(result)

    if args.format == "json":
        print(format_json(result))
    elif args.format == "dotenv":
        print(format_dotenv(result))
    elif args.format == "markdown":
        print(format_markdown(result))
    else:
        print(render_diff(result, color=not args.no_color))

    if args.exit_code:
        from envdiff.differ import has_differences
        return 1 if has_differences(result) else 0

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
