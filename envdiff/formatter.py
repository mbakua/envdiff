"""Formatters for exporting diff results in various output formats."""

import json
from typing import Any, Dict

from envdiff.differ import DiffResult


def _diff_to_dict(diff: DiffResult) -> Dict[str, Any]:
    """Convert a DiffResult into a plain dictionary."""
    return {
        "only_in_left": {k: v for k, v in diff.only_in_left.items()},
        "only_in_right": {k: v for k, v in diff.only_in_right.items()},
        "value_mismatches": {
            k: {"left": l, "right": r}
            for k, (l, r) in diff.value_mismatches.items()
        },
        "matching_keys": sorted(diff.matching_keys),
    }


def format_json(diff: DiffResult, indent: int = 2) -> str:
    """Render a DiffResult as a JSON string."""
    return json.dumps(_diff_to_dict(diff), indent=indent, sort_keys=True)


def format_dotenv(diff: DiffResult, side: str = "left") -> str:
    """Render the variables unique to one side as a .env-style string.

    Args:
        diff: The diff result to format.
        side: Either ``"left"`` or ``"right"``.

    Returns:
        A newline-separated list of ``KEY=VALUE`` pairs.
    """
    if side not in ("left", "right"):
        raise ValueError(f"side must be 'left' or 'right', got {side!r}")

    source = diff.only_in_left if side == "left" else diff.only_in_right
    lines = [f"{k}={v}" for k, v in sorted(source.items())]
    return "\n".join(lines)


def format_markdown(diff: DiffResult) -> str:
    """Render a DiffResult as a Markdown report."""
    sections: list[str] = ["# Environment Diff Report\n"]

    if diff.only_in_left:
        sections.append("## Only in left")
        sections.append("| Key | Value |")
        sections.append("|-----|-------|")
        for k, v in sorted(diff.only_in_left.items()):
            sections.append(f"| `{k}` | `{v}` |")
        sections.append("")

    if diff.only_in_right:
        sections.append("## Only in right")
        sections.append("| Key | Value |")
        sections.append("|-----|-------|")
        for k, v in sorted(diff.only_in_right.items()):
            sections.append(f"| `{k}` | `{v}` |")
        sections.append("")

    if diff.value_mismatches:
        sections.append("## Value mismatches")
        sections.append("| Key | Left | Right |")
        sections.append("|-----|------|-------|")
        for k, (l, r) in sorted(diff.value_mismatches.items()):
            sections.append(f"| `{k}` | `{l}` | `{r}` |")
        sections.append("")

    if diff.matching_keys:
        sections.append("## Matching keys")
        for k in sorted(diff.matching_keys):
            sections.append(f"- `{k}`")
        sections.append("")

    return "\n".join(sections)
