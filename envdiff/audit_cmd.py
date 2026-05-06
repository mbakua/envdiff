"""CLI sub-commands for the audit log feature."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.auditor import DEFAULT_AUDIT_LOG, load_audit_log


def build_audit_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    if parent is None:
        parser = argparse.ArgumentParser(
            prog="envdiff-audit",
            description="Inspect the envdiff audit log.",
        )
    else:
        parser = parent

    parser.add_argument(
        "--log",
        default=str(DEFAULT_AUDIT_LOG),
        metavar="FILE",
        help="Path to the audit log (default: %(default)s)",
    )
    sub = parser.add_subparsers(dest="audit_cmd")

    sub.add_parser("list", help="List all audit entries")

    stats_p = sub.add_parser("stats", help="Summarise audit log statistics")
    stats_p.add_argument("--user", metavar="NAME", help="Filter by user")

    return parser


def run_list(args: argparse.Namespace) -> int:
    entries = load_audit_log(Path(args.log))
    if not entries:
        print("No audit entries found.")
        return 0
    for e in entries:
        parts = [e.timestamp, e.operation]
        if e.left_source or e.right_source:
            parts.append(f"{e.left_source or '?'} vs {e.right_source or '?'}")
        if e.user:
            parts.append(f"user={e.user}")
        print("  ".join(parts))
    return 0


def run_stats(args: argparse.Namespace) -> int:
    entries = load_audit_log(Path(args.log))
    user_filter = getattr(args, "user", None)
    if user_filter:
        entries = [e for e in entries if e.user == user_filter]
    if not entries:
        print("No matching audit entries.")
        return 0
    total = len(entries)
    total_left = sum(len(e.keys_only_left) for e in entries)
    total_right = sum(len(e.keys_only_right) for e in entries)
    total_mismatch = sum(len(e.keys_mismatched) for e in entries)
    print(f"Total operations : {total}")
    print(f"Keys only-left   : {total_left}")
    print(f"Keys only-right  : {total_right}")
    print(f"Value mismatches : {total_mismatch}")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_audit_parser()
    args = parser.parse_args(argv)
    cmd = getattr(args, "audit_cmd", None)
    if cmd == "list":
        sys.exit(run_list(args))
    elif cmd == "stats":
        sys.exit(run_stats(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
