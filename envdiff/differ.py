"""Core diff logic for comparing two environment variable sets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class DiffResult:
    """Holds the result of diffing two env dicts."""

    only_in_left: Dict[str, str] = field(default_factory=dict)
    only_in_right: Dict[str, str] = field(default_factory=dict)
    value_mismatches: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    matching: Dict[str, str] = field(default_factory=dict)


def has_differences(result: DiffResult) -> bool:
    """Return True if there are any differences in *result*."""
    return bool(
        result.only_in_left
        or result.only_in_right
        or result.value_mismatches
    )


def summary(result: DiffResult) -> str:
    """Return a one-line human-readable summary of *result*."""
    parts: List[str] = []
    if result.only_in_left:
        parts.append(f"{len(result.only_in_left)} only in left")
    if result.only_in_right:
        parts.append(f"{len(result.only_in_right)} only in right")
    if result.value_mismatches:
        parts.append(f"{len(result.value_mismatches)} mismatched")
    if not parts:
        return "No differences found."
    return "; ".join(parts) + "."


def diff_envs(
    left: Dict[str, str],
    right: Dict[str, str],
) -> DiffResult:
    """Compare *left* and *right* env dicts and return a :class:`DiffResult`.

    Args:
        left: The base (e.g. staging) environment variables.
        right: The target (e.g. production) environment variables.

    Returns:
        A populated :class:`DiffResult` instance.
    """
    left_keys = set(left)
    right_keys = set(right)

    only_in_left = {k: left[k] for k in left_keys - right_keys}
    only_in_right = {k: right[k] for k in right_keys - left_keys}
    common = left_keys & right_keys

    value_mismatches: Dict[str, Tuple[str, str]] = {}
    matching: Dict[str, str] = {}

    for k in common:
        if left[k] != right[k]:
            value_mismatches[k] = (left[k], right[k])
        else:
            matching[k] = left[k]

    return DiffResult(
        only_in_left=only_in_left,
        only_in_right=only_in_right,
        value_mismatches=value_mismatches,
        matching=matching,
    )
