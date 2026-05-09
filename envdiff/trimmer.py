"""trimmer.py — Remove keys from a DiffResult that match given criteria."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Collection, Iterable

from envdiff.differ import DiffResult


@dataclass
class TrimResult:
    """Wrapper around a trimmed DiffResult with metadata about what was removed."""

    diff: DiffResult
    removed_keys: list[str] = field(default_factory=list)

    @property
    def removal_count(self) -> int:
        return len(self.removed_keys)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"TrimResult(removed={self.removal_count}, "
            f"remaining_left={len(self.diff.only_in_left)}, "
            f"remaining_right={len(self.diff.only_in_right)}, "
            f"mismatches={len(self.diff.value_mismatches)})"
        )


def trim_keys(diff: DiffResult, keys: Collection[str]) -> TrimResult:
    """Remove specific keys from all sections of *diff*.

    Keys are matched case-sensitively.
    """
    key_set = set(keys)
    removed: list[str] = []

    def _drop(mapping: dict) -> dict:
        kept = {}
        for k, v in mapping.items():
            if k in key_set:
                removed.append(k)
            else:
                kept[k] = v
        return kept

    trimmed = DiffResult(
        only_in_left=_drop(diff.only_in_left),
        only_in_right=_drop(diff.only_in_right),
        value_mismatches=_drop(diff.value_mismatches),
        matching_keys=_drop(diff.matching_keys),
    )
    # De-duplicate removed list while preserving first-seen order
    seen: set[str] = set()
    unique_removed = []
    for k in removed:
        if k not in seen:
            seen.add(k)
            unique_removed.append(k)

    return TrimResult(diff=trimmed, removed_keys=unique_removed)


def trim_matching(diff: DiffResult) -> TrimResult:
    """Remove all keys that are identical in both environments."""
    removed = list(diff.matching_keys.keys())
    trimmed = DiffResult(
        only_in_left=dict(diff.only_in_left),
        only_in_right=dict(diff.only_in_right),
        value_mismatches=dict(diff.value_mismatches),
        matching_keys={},
    )
    return TrimResult(diff=trimmed, removed_keys=removed)


def trim_by_prefix(diff: DiffResult, prefix: str) -> TrimResult:
    """Remove all keys whose name starts with *prefix* (case-insensitive)."""
    prefix_lower = prefix.lower()

    def _all_keys(d: DiffResult) -> Iterable[str]:
        yield from d.only_in_left
        yield from d.only_in_right
        yield from d.value_mismatches
        yield from d.matching_keys

    matched = {k for k in _all_keys(diff) if k.lower().startswith(prefix_lower)}
    return trim_keys(diff, matched)
