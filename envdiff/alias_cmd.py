"""CLI sub-command: envdiff alias — show a diff with aliased key names."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.aliaser import apply_aliases, load_alias_map
from envdiff.cli import _load
from envdiff.differ import diff_envs
from envdiff.reporter import render_diff


def build_alias_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(description="Diff two env files, replacing keys with human-readable aliases.")
    if parent is not None:
        parser = parent.add_parser("alias", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff alias", **kwargs)

    parser.add_argument("left", help="Base env file")
    parser.add_argument("right", help="Target env file")
    parser.add_argument(
        "--alias-file",
        default=None,
        metavar="FILE",
        help="JSON file mapping raw keys to aliases (default: no aliases)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
    return parser


def _load_alias_file(path: str) -> dict:
    with open(path) as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Alias file must be a JSON object, got {type(data).__name__}")
    return data


def run_alias(args: argparse.Namespace) -> int:
    left_env = _load(args.left)
    right_env = _load(args.right)
    result = diff_envs(left_env, right_env)

    if args.alias_file:
        try:
            raw = _load_alias_file(args.alias_file)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"error: cannot load alias file: {exc}", file=sys.stderr)
            return 2
        alias_map = load_alias_map(raw)
        result = apply_aliases(result, alias_map)

    print(render_diff(result, use_color=not args.no_color))
    return 0


def main(argv=None) -> None:
    parser = build_alias_parser()
    args = parser.parse_args(argv)
    sys.exit(run_alias(args))


if __name__ == "__main__":  # pragma: no cover
    main()
