"""Core diffing logic for comparing environment variable sets."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiffResult:
    """Holds the result of comparing two environment variable sets."""

    only_in_left: Dict[str, str] = field(default_factory=dict)
    only_in_right: Dict[str, str] = field(default_factory=dict)
    value_mismatches: Dict[str, tuple] = field(default_factory=dict)  # key -> (left_val, right_val)
    matching: Dict[str, str] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_left or self.only_in_right or self.value_mismatches)

    @property
    def summary(self) -> str:
        lines: List[str] = []
        if self.only_in_left:
            lines.append(f"  Only in left  : {len(self.only_in_left)} key(s)")
        if self.only_in_right:
            lines.append(f"  Only in right : {len(self.only_in_right)} key(s)")
        if self.value_mismatches:
            lines.append(f"  Value mismatch: {len(self.value_mismatches)} key(s)")
        if not lines:
            return "No differences found."
        return "Differences detected:\n" + "\n".join(lines)


def diff_envs(
    left: Dict[str, str],
    right: Dict[str, str],
    ignore_keys: Optional[List[str]] = None,
) -> DiffResult:
    """Compare two environment variable dictionaries.

    Args:
        left: The baseline environment (e.g. staging).
        right: The target environment (e.g. production).
        ignore_keys: Optional list of keys to exclude from comparison.

    Returns:
        A DiffResult describing the differences.
    """
    ignore = set(ignore_keys or [])
    left_filtered = {k: v for k, v in left.items() if k not in ignore}
    right_filtered = {k: v for k, v in right.items() if k not in ignore}

    left_keys = set(left_filtered)
    right_keys = set(right_filtered)

    result = DiffResult()

    for key in left_keys - right_keys:
        result.only_in_left[key] = left_filtered[key]

    for key in right_keys - left_keys:
        result.only_in_right[key] = right_filtered[key]

    for key in left_keys & right_keys:
        if left_filtered[key] != right_filtered[key]:
            result.value_mismatches[key] = (left_filtered[key], right_filtered[key])
        else:
            result.matching[key] = left_filtered[key]

    return result
