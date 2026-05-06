"""Merge two environment variable dicts with configurable conflict resolution."""

from enum import Enum
from typing import Dict, Optional


class MergeStrategy(str, Enum):
    LEFT = "left"      # left (base) wins on conflict
    RIGHT = "right"    # right (override) wins on conflict
    STRICT = "strict"  # raise on any conflict


class MergeConflictError(Exception):
    """Raised when STRICT strategy encounters a conflicting key."""

    def __init__(self, key: str, left_val: str, right_val: str) -> None:
        self.key = key
        self.left_val = left_val
        self.right_val = right_val
        super().__init__(
            f"Conflict on key '{key}': '{left_val}' vs '{right_val}'"
        )


def merge_envs(
    left: Dict[str, str],
    right: Dict[str, str],
    strategy: MergeStrategy = MergeStrategy.RIGHT,
    prefix: Optional[str] = None,
) -> Dict[str, str]:
    """Merge *left* and *right* env dicts according to *strategy*.

    Args:
        left: Base environment variables.
        right: Override environment variables.
        strategy: Conflict-resolution strategy.
        prefix: When given, only keys starting with this prefix are merged
                from *right*; other keys come from *left* unchanged.

    Returns:
        A new dict containing the merged result.

    Raises:
        MergeConflictError: If *strategy* is STRICT and a conflicting key
            is found.
    """
    merged: Dict[str, str] = dict(left)

    for key, value in right.items():
        if prefix and not key.startswith(prefix):
            continue

        if key in merged and merged[key] != value:
            if strategy == MergeStrategy.STRICT:
                raise MergeConflictError(key, merged[key], value)
            if strategy == MergeStrategy.RIGHT:
                merged[key] = value
            # LEFT: keep existing value — no action needed
        else:
            merged[key] = value

    return merged


def conflicts(
    left: Dict[str, str], right: Dict[str, str]
) -> Dict[str, tuple]:
    """Return keys present in both dicts with differing values.

    Returns:
        Mapping of key -> (left_value, right_value).
    """
    return {
        k: (left[k], right[k])
        for k in left.keys() & right.keys()
        if left[k] != right[k]
    }
