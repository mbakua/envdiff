"""CLI command for comparing two saved diff snapshots."""

import argparse
import json
import sys
from pathlib import Path

from envdiff.comparator import compare_diffs
from envdiff.snapshotter import load_snapshot
from envdiff.differ import DiffResult


def build_compare_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-compare",
        description="Compare two envdiff snapshots to track drift over time.",
    )
    parser.add_argument("before", help="Path to the earlier snapshot file.")
    parser.add_argument("after", help="Path to the more recent snapshot file.")
    parser.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output result as JSON.",
    )
    parser.add_argument(
        "--fail-on-regression", action="store_true",
        help="Exit with code 1 if new issues were introduced.",
    )
    return parser


def _load_diff(path: str) -> DiffResult:
    data = load_snapshot(path)
    env = data.get("env", {})
    # Snapshots store raw env; reconstruct a minimal DiffResult from metadata
    meta = data.get("meta", {})
    only_left = meta.get("only_in_left", {})
    only_right = meta.get("only_in_right", {})
    mismatches = meta.get("value_mismatches", {})
    matching = meta.get("matching_keys", {})
    return DiffResult(
        only_in_left=only_left,
        only_in_right=only_right,
        value_mismatches=mismatches,
        matching_keys=matching,
    )


def run_compare(args: argparse.Namespace) -> int:
    try:
        before = _load_diff(args.before)
        after = _load_diff(args.after)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = compare_diffs(before, after)

    if args.as_json:
        print(json.dumps({
            "resolved": result.resolved,
            "introduced": result.introduced,
            "unchanged_issues": result.unchanged_issues,
            "summary": result.summary(),
        }, indent=2))
    else:
        print(f"Summary: {result.summary()}")
        if result.resolved:
            print("  Resolved:", ", ".join(result.resolved))
        if result.introduced:
            print("  Introduced:", ", ".join(result.introduced))
        if result.unchanged_issues:
            print("  Still present:", ", ".join(result.unchanged_issues))

    if args.fail_on_regression and result.has_regressions:
        return 1
    return 0


def main() -> None:
    parser = build_compare_parser()
    args = parser.parse_args()
    sys.exit(run_compare(args))


if __name__ == "__main__":
    main()
