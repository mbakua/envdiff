"""CLI sub-command for linting environment files."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envdiff.parser import parse_env_file, parse_current_env
from envdiff.linter import lint_env, LintResult


def build_lint_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        description="Lint environment variable keys and values for common issues."
    )
    if parent is not None:
        parser = parent.add_parser('lint', **kwargs)
    else:
        parser = argparse.ArgumentParser(prog='envdiff lint', **kwargs)

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('file', nargs='?', help='Path to a .env file to lint')
    source.add_argument(
        '--current-env', action='store_true',
        help='Lint the current process environment instead of a file',
    )
    parser.add_argument(
        '--errors-only', action='store_true',
        help='Only report errors, suppress warnings',
    )
    parser.add_argument(
        '--strict', action='store_true',
        help='Exit with non-zero status if any warnings exist',
    )
    return parser


def _print_result(result: LintResult, errors_only: bool) -> None:
    issues = result.errors if errors_only else result.issues
    for issue in issues:
        print(issue)
    print(result.summary())


def run_lint(args: argparse.Namespace) -> int:
    if args.current_env:
        env = parse_current_env()
    else:
        try:
            env = parse_env_file(args.file)
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            return 2

    result = lint_env(env)
    _print_result(result, errors_only=getattr(args, 'errors_only', False))

    if result.errors:
        return 1
    if getattr(args, 'strict', False) and result.warnings:
        return 1
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_lint_parser()
    args = parser.parse_args(argv)
    sys.exit(run_lint(args))


if __name__ == '__main__':
    main()
