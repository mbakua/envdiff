"""CLI command: envdiff digest — print a compact fingerprint of a diff."""

from __future__ import annotations

import argparse
import json
import sys

from envdiff.differ import diff_envs
from envdiff.differ_digest import digest_diff
from envdiff.cli import _load


def build_digest_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff digest",
        description="Print a compact fingerprint summary of two env files.",
    )
    p.add_argument("left", help="Base environment file")
    p.add_argument("right", help="Target environment file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when the diff is not clean",
    )
    return p


def run_digest(args: argparse.Namespace) -> int:
    left_env = _load(args.left)
    right_env = _load(args.right)
    result = diff_envs(left_env, right_env)
    digest = digest_diff(result)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "fingerprint": digest.fingerprint,
                    "total_keys": digest.total_keys,
                    "issue_keys": digest.issue_keys,
                    "is_clean": digest.is_clean,
                },
                indent=2,
            )
        )
    else:
        status = "CLEAN" if digest.is_clean else "DIRTY"
        print(f"Status     : {status}")
        print(f"Fingerprint: {digest.fingerprint}")
        print(f"Total keys : {digest.total_keys}")
        if digest.issue_keys:
            print(f"Issue keys : {', '.join(digest.issue_keys)}")

    if args.exit_code and not digest.is_clean:
        return 1
    return 0


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = build_digest_parser()
    args = parser.parse_args(argv)
    sys.exit(run_digest(args))


if __name__ == "__main__":  # pragma: no cover
    main()
