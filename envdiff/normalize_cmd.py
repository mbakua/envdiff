"""CLI sub-command: normalize an env file and print the result."""

from __future__ import annotations

import argparse
import sys

from envdiff.normalizer import NormalizeOptions, normalize_env
from envdiff.parser import parse_env_file
from envdiff.formatter import format_dotenv, format_json


def build_normalize_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff normalize",
        description="Normalize an env file and print the result.",
    )
    p.add_argument("file", help="Path to the .env file to normalize")
    p.add_argument(
        "--lowercase-keys",
        action="store_true",
        default=False,
        help="Convert all keys to lowercase",
    )
    p.add_argument(
        "--uppercase-keys",
        action="store_true",
        default=False,
        help="Convert all keys to UPPERCASE",
    )
    p.add_argument(
        "--remove-empty",
        action="store_true",
        default=False,
        help="Drop keys whose value is empty after stripping",
    )
    p.add_argument(
        "--default-value",
        default=None,
        metavar="VAL",
        help="Replace empty values with VAL",
    )
    p.add_argument(
        "--format",
        choices=["dotenv", "json"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    return p


def run_normalize(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    opts = NormalizeOptions(
        strip_whitespace=True,
        lowercase_keys=args.lowercase_keys,
        uppercase_keys=args.uppercase_keys,
        remove_empty=args.remove_empty,
        default_value=args.default_value,
    )

    normalized = normalize_env(env, opts)

    if args.format == "json":
        import json
        print(json.dumps(normalized, indent=2))
    else:
        for k, v in sorted(normalized.items()):
            print(f"{k}={v}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_normalize_parser()
    args = parser.parse_args()
    sys.exit(run_normalize(args))


if __name__ == "__main__":  # pragma: no cover
    main()
