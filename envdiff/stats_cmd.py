"""CLI sub-command: envdiff stats — print diff statistics."""
import argparse
import json
import sys

from envdiff.cli import _load
from envdiff.differ import diff_envs
from envdiff.differ_stats import compute_stats


def build_stats_parser(parent: argparse.ArgumentParser = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="envdiff-stats",
        description="Show statistics for a diff between two env files.",
    )
    parser.add_argument("left", help="Base / left env file")
    parser.add_argument("right", help="Target / right env file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    return parser


def run_stats(args: argparse.Namespace, out=sys.stdout) -> int:
    left_env = _load(args.left)
    right_env = _load(args.right)
    diff = diff_envs(left_env, right_env)
    stats = compute_stats(diff)

    if args.fmt == "json":
        out.write(json.dumps(stats.to_dict(), indent=2))
        out.write("\n")
    else:
        out.write(str(stats))
        out.write("\n")
    return 0


def main(argv=None) -> None:  # pragma: no cover
    parser = build_stats_parser()
    args = parser.parse_args(argv)
    sys.exit(run_stats(args))


if __name__ == "__main__":  # pragma: no cover
    main()
