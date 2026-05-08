"""CLI command for tracking key stability across multiple env diff snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.snapshotter import load_snapshot
from envdiff.differ import diff_envs
from envdiff.tracker import track_diffs, TrackingReport


def build_track_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-track",
        description="Track key stability across multiple snapshot pairs.",
    )
    parser.add_argument(
        "snapshots",
        nargs="+",
        metavar="SNAPSHOT",
        help="Snapshot files to compare sequentially (must be even count: left right ...).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--unstable-only",
        action="store_true",
        help="Only show keys that changed at least once.",
    )
    return parser


def run_track(args: argparse.Namespace) -> int:
    paths = args.snapshots
    if len(paths) % 2 != 0:
        print("error: snapshot list must contain pairs (left right ...)", file=sys.stderr)
        return 1

    labeled_diffs = []
    for i in range(0, len(paths), 2):
        left_path, right_path = Path(paths[i]), Path(paths[i + 1])
        try:
            left_env = load_snapshot(left_path)["env"]
            right_env = load_snapshot(right_path)["env"]
        except Exception as exc:
            print(f"error loading snapshots: {exc}", file=sys.stderr)
            return 1
        label = f"{left_path.stem}↔{right_path.stem}"
        labeled_diffs.append((label, diff_envs(left_env, right_env)))

    report = track_diffs(labeled_diffs)
    keys = report.unstable_keys if args.unstable_only else list(report.entries.keys())

    if args.format == "json":
        output = {
            k: {
                "appearances": report.entries[k].appearances,
                "statuses": report.entries[k].statuses,
                "change_count": report.entries[k].change_count,
                "is_stable": report.entries[k].is_stable,
            }
            for k in keys
        }
        print(json.dumps(output, indent=2))
    else:
        print(report.summary())
        for k in keys:
            h = report.entries[k]
            stability = "stable" if h.is_stable else f"unstable ({h.change_count} change(s))"
            print(f"  {k}: {stability}")

    return 0


def main() -> None:
    parser = build_track_parser()
    args = parser.parse_args()
    sys.exit(run_track(args))


if __name__ == "__main__":
    main()
