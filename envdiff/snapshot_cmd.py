"""CLI helpers for the 'snapshot' sub-command.

Exposes two actions:
  save   – capture an env file (or the live environment) into a snapshot
  diff   – compare two snapshots and print the diff
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional

from envdiff.differ import diff_envs
from envdiff.parser import parse_current_env, parse_env_file
from envdiff.reporter import render_diff
from envdiff.snapshotter import SnapshotError, load_snapshot, save_snapshot, snapshot_metadata


def build_snapshot_parser(parent: Optional[ArgumentParser] = None) -> ArgumentParser:
    """Return an ArgumentParser for the snapshot sub-command."""
    parser = parent or ArgumentParser(prog="envdiff snapshot")
    sub = parser.add_subparsers(dest="snap_action", required=True)

    # -- save ----------------------------------------------------------------
    save_p = sub.add_parser("save", help="Save an env snapshot to disk")
    save_p.add_argument(
        "output",
        help="Destination path for the snapshot JSON file",
    )
    save_p.add_argument(
        "--file",
        metavar="ENV_FILE",
        help="Read from a .env file instead of the live environment",
    )
    save_p.add_argument(
        "--label",
        default="",
        help="Human-readable label stored in the snapshot",
    )

    # -- diff ----------------------------------------------------------------
    diff_p = sub.add_parser("diff", help="Diff two snapshot files")
    diff_p.add_argument("left", help="Path to the left (base) snapshot")
    diff_p.add_argument("right", help="Path to the right (compare) snapshot")
    diff_p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )

    # -- info ----------------------------------------------------------------
    info_p = sub.add_parser("info", help="Print metadata for a snapshot file")
    info_p.add_argument("snapshot", help="Path to the snapshot JSON file")

    return parser


def run_save(args: Namespace) -> int:
    try:
        env = parse_env_file(args.file) if args.file else parse_current_env()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        dest = save_snapshot(env, args.output, label=args.label)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Snapshot saved to {dest} ({len(env)} keys)")
    return 0


def run_diff(args: Namespace) -> int:
    try:
        left_env = load_snapshot(args.left)
        right_env = load_snapshot(args.right)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = diff_envs(left_env, right_env)
    print(render_diff(result, color=not args.no_color))
    return 0


def run_info(args: Namespace) -> int:
    try:
        meta = snapshot_metadata(args.snapshot)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for key, value in meta.items():
        print(f"{key}: {value}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_snapshot_parser()
    args = parser.parse_args(argv)
    dispatch = {"save": run_save, "diff": run_diff, "info": run_info}
    return dispatch[args.snap_action](args)
