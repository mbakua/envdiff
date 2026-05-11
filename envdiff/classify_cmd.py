"""CLI entry point for the classify subcommand."""

import argparse
import json
import sys

from envdiff.cli import _load
from envdiff.differ import diff_envs
from envdiff.classifier import classify_diff


def build_classify_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff classify",
        description="Classify diff keys by category (security, database, network, …)",
    )
    p.add_argument("left", help="Base env file")
    p.add_argument("right", help="Target env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--category",
        default=None,
        help="Show only keys in this category",
    )
    return p


def run_classify(args: argparse.Namespace) -> int:
    left = _load(args.left)
    right = _load(args.right)
    diff = diff_envs(left, right)
    classified = classify_diff(diff)

    if args.category:
        keys = classified.keys_in(args.category)
        if args.format == "json":
            print(json.dumps({args.category: keys}, indent=2))
        else:
            if not keys:
                print(f"No keys found in category '{args.category}'.")
            else:
                print(f"[{args.category}]")
                for k in sorted(keys):
                    print(f"  {k}")
        return 0

    if args.format == "json":
        print(json.dumps(
            {cat: sorted(keys) for cat, keys in classified.categories.items() if keys},
            indent=2,
        ))
    else:
        for cat in sorted(classified.all_categories()):
            print(f"[{cat}]")
            for k in sorted(classified.keys_in(cat)):
                print(f"  {k}")
    return 0


def main(argv=None) -> None:
    parser = build_classify_parser()
    args = parser.parse_args(argv)
    sys.exit(run_classify(args))


if __name__ == "__main__":
    main()
