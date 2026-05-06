"""CLI entry-point for the `envdiff watch` sub-command."""

import argparse
import sys

from envdiff.parser import parse_env_file
from envdiff.differ import has_differences
from envdiff.reporter import render_diff
from envdiff.watcher import watch_file, WatchError


def build_watch_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Build (or register) the argument parser for the watch command."""
    kwargs = dict(
        description="Watch an env file and print diffs when it changes.",
    )
    if parent is not None:
        parser = parent.add_parser("watch", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-watch", **kwargs)

    parser.add_argument("baseline", help="Baseline .env file (reference).")
    parser.add_argument("target", help="Target .env file to watch for changes.")
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 2.0).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    return parser


def run_watch(args: argparse.Namespace) -> int:
    """Execute the watch command; returns an exit code."""
    try:
        baseline_env = parse_env_file(args.baseline)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    use_color = not args.no_color

    def on_change(diff):
        if has_differences(diff):
            print(render_diff(diff, color=use_color))
        else:
            print("(no differences detected after change)")

    print(f"Watching {args.target!r} against baseline {args.baseline!r} …")
    try:
        watch_file(
            path=args.target,
            baseline=baseline_env,
            on_change=on_change,
            interval=args.interval,
        )
    except WatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


def main(argv=None) -> None:
    parser = build_watch_parser()
    args = parser.parse_args(argv)
    sys.exit(run_watch(args))


if __name__ == "__main__":
    main()
