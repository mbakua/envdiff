"""CLI sub-command: envdiff heatmap — show key-change frequency across env file pairs."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.differ import diff_envs
from envdiff.differ_heatmap import build_heatmap, DiffHeatmap
from envdiff.parser import parse_env_file


def build_heatmap_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff heatmap",
        description="Rank keys by how often they differ across multiple env-file pairs.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Even number of env files interpreted as (left, right) pairs.",
    )
    p.add_argument("--top", type=int, default=10, metavar="N", help="Show top N keys (default: 10).")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON.")
    return p


def _parse_pairs(files: List[str]):
    if len(files) % 2 != 0:
        print("error: files must be supplied in (left, right) pairs", file=sys.stderr)
        sys.exit(1)
    pairs = [(files[i], files[i + 1]) for i in range(0, len(files), 2)]
    return pairs


def run_heatmap(args: argparse.Namespace) -> None:
    pairs = _parse_pairs(args.files)
    diffs = []
    for left_path, right_path in pairs:
        left = parse_env_file(left_path)
        right = parse_env_file(right_path)
        diffs.append(diff_envs(left, right))

    heatmap: DiffHeatmap = build_heatmap(diffs)

    if args.as_json:
        print(json.dumps(heatmap.to_dict(), indent=2))
        return

    print(f"Heatmap across {heatmap.total_diffs} diff(s)  (top {args.top})\n")
    for entry in heatmap.hottest(args.top):
        bar = "#" * int(entry.frequency * 20)
        print(f"  {entry.key:<30} {bar:<20} {entry}".rstrip())


def main(argv=None) -> None:
    parser = build_heatmap_parser()
    args = parser.parse_args(argv)
    run_heatmap(args)


if __name__ == "__main__":
    main()
