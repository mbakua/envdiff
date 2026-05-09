"""CLI entry-point for the matrix comparison command."""
from __future__ import annotations
import argparse
import json
import sys
from envdiff.parser import parse_env_file
from envdiff.differ_matrix import build_matrix


def build_matrix_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-matrix",
        description="Compare multiple .env files pairwise and show a diff matrix.",
    )
    p.add_argument(
        "envfiles",
        nargs="+",
        metavar="LABEL=FILE",
        help="One or more label=filepath pairs, e.g. dev=.env.dev prod=.env.prod",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--only-diff",
        action="store_true",
        help="Show only pairs that have differences",
    )
    return p


def _parse_label_files(args_list):
    result = {}
    for item in args_list:
        if "=" not in item:
            raise SystemExit(f"Expected LABEL=FILE, got: {item!r}")
        label, path = item.split("=", 1)
        result[label] = parse_env_file(path)
    return result


def run_matrix(args: argparse.Namespace) -> int:
    envs = _parse_label_files(args.envfiles)
    if len(envs) < 2:
        print("Error: at least two LABEL=FILE entries required.", file=sys.stderr)
        return 1

    matrix = build_matrix(envs)
    cells = matrix.pairs_with_differences() if args.only_diff else matrix.cells

    if args.format == "json":
        out = {
            f"{c.left_label}:{c.right_label}": {
                "only_in_left": list(c.result.only_in_left.keys()),
                "only_in_right": list(c.result.only_in_right.keys()),
                "value_mismatches": list(c.result.value_mismatches.keys()),
                "issue_count": c.issue_count,
            }
            for c in cells
        }
        print(json.dumps(out, indent=2))
    else:
        for c in cells:
            status = "DIFF" if c.has_differences else "OK"
            print(f"[{status}] {c.left_label} vs {c.right_label}: {c.issue_count} issue(s)")
            if c.result.only_in_left:
                print(f"  Only in {c.left_label}: {', '.join(c.result.only_in_left)}")
            if c.result.only_in_right:
                print(f"  Only in {c.right_label}: {', '.join(c.result.only_in_right)}")
            if c.result.value_mismatches:
                print(f"  Mismatches: {', '.join(c.result.value_mismatches)}")
    return 0


def main():
    parser = build_matrix_parser()
    args = parser.parse_args()
    sys.exit(run_matrix(args))


if __name__ == "__main__":
    main()
