"""CLI command: envdiff snapshot-delta — compare two snapshot files and show delta."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.snapshotter import load_snapshot
from envdiff.differ import diff_envs
from envdiff.differ_snapshot_delta import compute_snapshot_delta


def build_snapshot_delta_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff snapshot-delta",
        description="Show what changed in the left-side env between two snapshots.",
    )
    p.add_argument("before", help="Path to the 'before' snapshot JSON file")
    p.add_argument("after", help="Path to the 'after' snapshot JSON file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color in text output",
    )
    return p


def run_snapshot_delta(args: argparse.Namespace) -> int:
    try:
        before_snap = load_snapshot(args.before)
        after_snap = load_snapshot(args.after)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading snapshots: {exc}", file=sys.stderr)
        return 1

    before_diff = diff_envs(before_snap["env"], {})
    after_diff = diff_envs(after_snap["env"], {})
    delta = compute_snapshot_delta(before_diff, after_diff)

    if args.format == "json":
        print(json.dumps(delta.to_dict(), indent=2))
    else:
        use_color = not args.no_color
        _print_text(delta, use_color)

    return 0 if delta.is_empty else 1


def _print_text(delta, use_color: bool) -> None:
    def _c(text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if use_color else text

    print(f"Snapshot delta — {delta.summary()}")
    for e in delta.added:
        print(f"  {_c('+', '32')} {e.key} = {e.after!r}")
    for e in delta.removed:
        print(f"  {_c('-', '31')} {e.key} (was {e.before!r})")
    for e in delta.changed:
        print(f"  {_c('~', '33')} {e.key}: {e.before!r} -> {e.after!r}")


def main(argv=None) -> None:
    parser = build_snapshot_delta_parser()
    args = parser.parse_args(argv)
    sys.exit(run_snapshot_delta(args))


if __name__ == "__main__":
    main()
