"""CLI sub-command: envdiff score — print a health score for a diff."""

import argparse
import json
import sys

from envdiff.cli import _load
from envdiff.differ import diff_envs
from envdiff.scorer import score_diff


def build_score_parser(parent: argparse.ArgumentParser) -> argparse.ArgumentParser:  # noqa: D401
    """Add score-specific arguments to *parent* and return it."""
    parent.add_argument("left", help="Base env file (or '-' for current process env)")
    parent.add_argument("right", help="Target env file (or '-' for current process env)")
    parent.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parent.add_argument(
        "--weights",
        metavar="JSON",
        default=None,
        help='Custom penalty weights as JSON, e.g. \'{"missing":5,"extra":1,"mismatch":3}\'',
    )
    parent.add_argument(
        "--fail-under",
        type=int,
        default=0,
        metavar="N",
        help="Exit with code 1 if score is below N (default: 0 — never fail)",
    )
    return parent


def run_score(args: argparse.Namespace) -> int:
    """Execute the score sub-command.  Returns the process exit code."""
    left_env = _load(args.left)
    right_env = _load(args.right)
    diff = diff_envs(left_env, right_env)

    weights = None
    if args.weights:
        try:
            weights = json.loads(args.weights)
        except json.JSONDecodeError as exc:
            print(f"error: --weights is not valid JSON: {exc}", file=sys.stderr)
            return 2

    result = score_diff(diff, weights=weights)

    if args.format == "json":
        print(json.dumps({"score": result.score, "grade": result.grade, **result.details}, indent=2))
    else:
        print(result)
        for label, count in [
            ("  Missing keys (left-only)", result.details["missing_keys"]),
            ("  Extra keys  (right-only)", result.details["extra_keys"]),
            ("  Mismatched values       ", result.details["mismatched_keys"]),
            ("  Matching keys           ", result.details["matching_keys"]),
        ]:
            print(f"{label}: {count}")

    if args.fail_under and result.score < args.fail_under:
        return 1
    return 0


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="envdiff-score",
        description="Score the health of an environment diff.",
    )
    build_score_parser(parser)
    args = parser.parse_args(argv)
    sys.exit(run_score(args))


if __name__ == "__main__":  # pragma: no cover
    main()
