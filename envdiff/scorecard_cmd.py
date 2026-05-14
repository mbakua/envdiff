"""CLI command: envdiff scorecard — rank multiple env pairs by diff score."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict

from envdiff.cli import _load
from envdiff.differ import diff_envs, DiffResult
from envdiff.differ_scorecard import build_scorecard, DiffScorecard


def build_scorecard_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff scorecard",
        description="Rank multiple env-file pairs by their diff score.",
    )
    p.add_argument(
        "--pair",
        metavar="LABEL:LEFT:RIGHT",
        action="append",
        dest="pairs",
        required=True,
        help="Colon-separated label, left file, right file. Repeat for multiple pairs.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return p


def _parse_pairs(raw: list[str]) -> Dict[str, DiffResult]:
    labeled: Dict[str, DiffResult] = {}
    for item in raw:
        parts = item.split(":")
        if len(parts) != 3:
            print(f"ERROR: invalid --pair '{item}' (expected LABEL:LEFT:RIGHT)", file=sys.stderr)
            sys.exit(1)
        label, left_path, right_path = parts
        left_env = _load(left_path)
        right_env = _load(right_path)
        labeled[label] = diff_envs(left_env, right_env)
    return labeled


def run_scorecard(args: argparse.Namespace) -> None:
    labeled = _parse_pairs(args.pairs)
    card: DiffScorecard = build_scorecard(labeled)

    if args.format == "json":
        print(json.dumps(card.to_dict(), indent=2))
        return

    print(f"{'Rank':<6} {'Label':<20} {'Score':>6} {'Grade':>6}")
    print("-" * 42)
    for rank, entry in enumerate(card.ranked(), start=1):
        print(f"{rank:<6} {entry.label:<20} {entry.score.score:>6} {entry.score.grade:>6}")
    print("-" * 42)
    avg = card.average_score()
    print(f"{'Average':<27} {avg:>6.1f}")
    if card.best():
        print(f"Best:  {card.best().label}")
    if card.worst():
        print(f"Worst: {card.worst().label}")


def main(argv: list[str] | None = None) -> None:
    parser = build_scorecard_parser()
    args = parser.parse_args(argv)
    run_scorecard(args)


if __name__ == "__main__":
    main()
