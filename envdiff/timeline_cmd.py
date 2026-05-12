"""CLI entry-point for the timeline sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.parser import parse_env_file
from envdiff.differ_timeline import build_timeline


def build_timeline_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-timeline",
        description="Show how environment variable values evolve across ordered snapshots.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Ordered list of .env files (oldest first).",
    )
    p.add_argument(
        "--labels",
        nargs="+",
        metavar="LABEL",
        help="Human-readable label for each file (defaults to filename).",
    )
    p.add_argument(
        "--key",
        metavar="KEY",
        help="Restrict output to a single key.",
    )
    p.add_argument(
        "--unstable-only",
        action="store_true",
        help="Only show keys whose values changed across snapshots.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return p


def run_timeline(args: argparse.Namespace) -> int:
    labels: List[str] = args.labels if args.labels else args.files
    if len(labels) != len(args.files):
        print("error: --labels count must match number of files", file=sys.stderr)
        return 2

    snapshots = [parse_env_file(f) for f in args.files]
    report = build_timeline(snapshots, labels)

    timelines = report.timelines
    if args.key:
        timelines = {k: v for k, v in timelines.items() if k == args.key}
    if args.unstable_only:
        timelines = {k: v for k, v in timelines.items() if not v.is_stable()}

    if args.format == "json":
        subset = {k: t.to_dict() for k, t in timelines.items()}
        print(json.dumps(subset, indent=2))
        return 0

    if not timelines:
        print("No keys to display.")
        return 0

    for key, timeline in timelines.items():
        stability = "stable" if timeline.is_stable() else "CHANGED"
        print(f"[{stability}] {key}")
        for entry in timeline.entries:
            print(f"  {entry}")
    return 0


def main() -> None:
    parser = build_timeline_parser()
    args = parser.parse_args()
    sys.exit(run_timeline(args))


if __name__ == "__main__":
    main()
