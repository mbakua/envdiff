"""Formats and renders DiffResult objects for human-readable output."""

from typing import IO, Optional
import sys

from envdiff.differ import DiffResult


ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def render_diff(
    result: DiffResult,
    left_label: str = "left",
    right_label: str = "right",
    output: Optional[IO[str]] = None,
    use_color: bool = True,
) -> None:
    """Print a human-readable diff report to the given output stream.

    Args:
        result: The DiffResult to render.
        left_label: Display name for the left (baseline) environment.
        right_label: Display name for the right (target) environment.
        output: Stream to write to; defaults to stdout.
        use_color: Whether to emit ANSI color codes.
    """
    out = output or sys.stdout

    if not result.has_differences:
        out.write(_colorize("✔ Environments are identical.\n", ANSI_GREEN, use_color))
        return

    if result.only_in_left:
        out.write(_colorize(f"\n─── Only in [{left_label}] ───\n", ANSI_YELLOW, use_color))
        for key, val in sorted(result.only_in_left.items()):
            out.write(f"  - {key}={val}\n")

    if result.only_in_right:
        out.write(_colorize(f"\n─── Only in [{right_label}] ───\n", ANSI_YELLOW, use_color))
        for key, val in sorted(result.only_in_right.items()):
            out.write(f"  + {key}={val}\n")

    if result.value_mismatches:
        out.write(_colorize("\n─── Value mismatches ───\n", ANSI_RED, use_color))
        for key, (lval, rval) in sorted(result.value_mismatches.items()):
            out.write(f"  {key}:\n")
            out.write(_colorize(f"    < {lval}  ({left_label})\n", ANSI_RED, use_color))
            out.write(_colorize(f"    > {rval}  ({right_label})\n", ANSI_GREEN, use_color))

    out.write("\n" + result.summary + "\n")
